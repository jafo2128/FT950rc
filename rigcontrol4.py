#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  rigcontrol4.py
#
#  Copyright 2016 Michael Steiner, OE1MSB <michael@msteiner.at>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
 
# used by class Stations 
import os
import re
import sqlite3
import array
#import pyaudio

# used by class RigControl
import sys
#import time
import serial

from PyQt5 import QtWidgets, QtCore, uic, QtGui
from PyQt5.QtWidgets import QTableWidget,QTableWidgetItem
from PyQt5.QtCore import *

# load external module beacon.py
import beacons

#******************************
# Read INI File into dictionary
#******************************
fobjINI = open("FT950.ini", "r")
iniDict = {}
for iniLines in fobjINI:
    iniLine = iniLines.strip()
    if iniLine[0] == "[":
        continue
    (iniK, iniV) = iniLine.split("=")
    iniDict[iniK] = iniV
    print(iniK, iniV)

#***************************
# Serial Port Basic Settings
#***************************
try:
    port = serial.Serial(iniDict['cpName'], baudrate=int(iniDict['cpSpeed']) , timeout=float(iniDict['cpTimeoutRead']), write_timeout=float(iniDict['cpTimeoutWrite']))
    if iniDict['cpLineRTS'] == "Low":
        port.rts = False
    if iniDict['cpLineDTR'] == "Low":
        port.dtr = False
except:
    if sys.platform == "win32":
        serPort = "COM3"
    else:
        serPort = "/dev/ttyUSB0"
        port = serial.Serial(serPort, baudrate=38400, timeout=0.1, write_timeout=0.1)
        port.rts = False
        port.dtr = False
    print(serPort)




#**************************
# Audio Devices List
#**************************
#p = pyaudio.PyAudio()
#i = 0
#print("\n\n\n\n")
#for i in range(p.get_device_count()):
#    test = p.get_device_info_by_index(i)
#    print (str(test["index"]) + " " + test["name"])

#**************************
# Variables
#**************************
strBand = ""


#=====================================
# INITIALIZE UI with actual RIG DATA
# Read Rig Data to set starting values
#=====================================
# READ POWER
try:
    port.write(b"EX111;")
    rcv = port.read(12)
    strPout = str(rcv[5:8],'utf-8')
    print("Power: " + strPout)
except:
    #print("Timeout1")
    pass
# READ FREQUENCY and MODE 
try:
    port.write(b"IF;")
    rcv = port.read(27)
    # slicing frequency info, because of byte data
    rcvk = rcv[5:10]         # khz
    rcvh = rcv[10:13]        # hz
    #self.frVfo.qrgA.set(rcvk + b"." + rcvh)
    rcvcd = rcv[13:14]       # clarifier direction +/-
    rcvco = rcv[14:18]       # clarifier h
    rcvm = rcv[20:21]        # mode
except:
    print("Timeout2")
    rcvk = b"3500"
    rcvh = b"200"
    rcvm = b"2"
# READ FILTER Width
try:
    port.write(b"SH0;")
    rcv = port.read(12)
    rcvw = rcv[3:5]
except:
    print("Timeout3")
    rcvw = b"111"

print(str(rcvk,'utf-8') + str(rcvh,'utf-8') + " " + str(rcvm,'utf-8') + " " + str(rcvw,'utf-8'))
#===== INITIALIZE UI END =====#


#=======================================#
# Function write2port                   #
#=======================================#
def write2port(self, strPortData):
    #print(strPortData)
    try:
        port.write(strPortData)
    except:
        #print("COM-Timeout")
        pass
#===== End of function write2port  =====#

#########################################
### Class RigControl Start            ###
#########################################
class RigControl(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(RigControl, self).__init__(parent)

        # Thread for polling the RIG
        self.thread = QThread()
        self.w = RigPoll()
        self.w.mySignal[str, str, str, str, str].connect(self.onFinished)
        self.w.moveToThread(self.thread)
        self.thread.started.connect(self.w.work)
        self.thread.start()

        #init user interface
        self.ui = uic.loadUi("rigcontrol4.ui", self)

        # Configure LCD Display
        self.ui.lcdVFO.setSegmentStyle(QtWidgets.QLCDNumber.Flat)
        palette = self.ui.lcdVFO.palette()
        palette.setColor(palette.WindowText, QtGui.QColor(85, 85, 255))
        #palette.setColor(palette.Light, QtGui.QColor(255, 0, 0))
        #palette.setColor(palette.Dark, QtGui.QColor(0, 255, 0))
        palette.setColor(palette.Window, QtGui.QColor(0, 170, 255))
        self.ui.lcdVFO.setPalette(palette)
        
        # Variables
        self.mode1=""
        self.pwr1=""
        self.gain1=""
        self.width1=""
        self.width2=""
        
        # Slots
        self.ui.btnExit.clicked.connect(self.onExit)
        
        self.ui.btnMLSB.clicked.connect(self.setMLSB)
        self.ui.btnMUSB.clicked.connect(self.setMUSB)
        self.ui.btnMCW.clicked.connect(self.setMCW)
        self.ui.btnMAM.clicked.connect(self.setMAM)

        self.ui.btnAtt0.clicked.connect(self.setAtt0)
        self.ui.btnAtt6.clicked.connect(self.setAtt6)
        self.ui.btnAtt12.clicked.connect(self.setAtt12)
        self.ui.btnAtt18.clicked.connect(self.setAtt18)

        self.ui.btnAmp0.clicked.connect(self.setAmpOff)
        self.ui.btnAmp1.clicked.connect(self.setAmp1)
        self.ui.btnAmp2.clicked.connect(self.setAmp2)

        self.ui.btnBeaImp.clicked.connect(beacons.Beacons.ImpBeacon)

        self.ui.tblStations.cellClicked.connect(self.selStation)
        
        self.ui.rbtSrtCall.clicked.connect(self.srtStation)
        self.ui.rbtSrtFreq.clicked.connect(self.srtStation)
        self.ui.cbxConEU.clicked.connect(self.srtStation)

        self.ui.btnBnd160.clicked.connect(self.setBnd160m)
        self.ui.btnBnd80.clicked.connect(self.setBnd80m)
        self.ui.btnBnd60.clicked.connect(self.setBnd60m)
        self.ui.btnBnd40.clicked.connect(self.setBnd40m)
        self.ui.btnBnd30.clicked.connect(self.setBnd30m)
        self.ui.btnBnd20.clicked.connect(self.setBnd20m)
        self.ui.btnBnd17.clicked.connect(self.setBnd17m)
        self.ui.btnBnd15.clicked.connect(self.setBnd15m)
        self.ui.btnBnd12.clicked.connect(self.setBnd12m)
        self.ui.btnBnd10.clicked.connect(self.setBnd10m)
        self.ui.btnBnd6.clicked.connect(self.setBnd6m)
        self.ui.btnBndAll.clicked.connect(self.setBndAll)

        self.ui.btnBwCw100.clicked.connect(self.setBwCw100)
        self.ui.btnBwCw200.clicked.connect(self.setBwCw200)
        self.ui.btnBwCw300.clicked.connect(self.setBwCw300)
        self.ui.btnBwCw400.clicked.connect(self.setBwCw400)
        self.ui.btnBwCw500.clicked.connect(self.setBwCw500)
        self.ui.btnBwCw800.clicked.connect(self.setBwCw800)
        self.ui.btnBwCw1200.clicked.connect(self.setBwCw1200)
        self.ui.btnBwCw1400.clicked.connect(self.setBwCw1400)
        self.ui.btnBwCw1700.clicked.connect(self.setBwCw1700)
        self.ui.btnBwCw2000.clicked.connect(self.setBwCw2000)
        self.ui.btnBwCw2400.clicked.connect(self.setBwCw2400)

        self.ui.btnBwSSB0200.clicked.connect(self.setBwSSB0200)
        self.ui.btnBwSSB0400.clicked.connect(self.setBwSSB0400)
        self.ui.btnBwSSB0600.clicked.connect(self.setBwSSB0600)
        self.ui.btnBwSSB0850.clicked.connect(self.setBwSSB0850)
        self.ui.btnBwSSB1100.clicked.connect(self.setBwSSB1100)
        self.ui.btnBwSSB1350.clicked.connect(self.setBwSSB1350)
        self.ui.btnBwSSB1500.clicked.connect(self.setBwSSB1500)
        self.ui.btnBwSSB1650.clicked.connect(self.setBwSSB1650)
        self.ui.btnBwSSB1800.clicked.connect(self.setBwSSB1800)
        self.ui.btnBwSSB1950.clicked.connect(self.setBwSSB1950)
        self.ui.btnBwSSB2100.clicked.connect(self.setBwSSB2100)
        self.ui.btnBwSSB2250.clicked.connect(self.setBwSSB2250)
        self.ui.btnBwSSB2400.clicked.connect(self.setBwSSB2400)
        self.ui.btnBwSSB2450.clicked.connect(self.setBwSSB2450)
        self.ui.btnBwSSB2500.clicked.connect(self.setBwSSB2500)
        self.ui.btnBwSSB2600.clicked.connect(self.setBwSSB2600)
        self.ui.btnBwSSB2700.clicked.connect(self.setBwSSB2700)
        self.ui.btnBwSSB2800.clicked.connect(self.setBwSSB2800)
        self.ui.btnBwSSB2900.clicked.connect(self.setBwSSB2900)
        self.ui.btnBwSSB3000.clicked.connect(self.setBwSSB3000)
        self.ui.slidPower.valueChanged.connect(self.setPwr)
        self.ui.slidAudio.valueChanged.connect(self.setAFgain)

    def onExit(self):
        self.close()

    @pyqtSlot(str, str, str, str, str)
    def onFinished(self, vfo, mode, width, pwr, gain):
        # Frequency
        self.ui.lcdVFO.display(vfo)
        # MODE
        if mode != self.mode1:
            #print ("Mode changed from " + self.mode1 + " to " + mode)
            self.mode1 = mode
            self.ui.btnMLSB.setStyleSheet("background-color: ")
            self.ui.btnMUSB.setStyleSheet("background-color: ")
            self.ui.btnMCW.setStyleSheet("background-color: ")
            self.ui.btnMAM.setStyleSheet("background-color: ")
            if mode == "1":
                self.ui.stwBW.setCurrentIndex(1)
                self.ui.btnMLSB.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
            elif mode == "2":
                self.ui.stwBW.setCurrentIndex(1)
                self.ui.btnMUSB.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
            elif mode == "3":
                self.ui.stwBW.setCurrentIndex(0)
                self.ui.btnMCW.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
            elif mode == "5":
                self.ui.stwBW.setCurrentIndex(2)
                self.ui.btnMAM.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
        # BANDWIDTH
        if width != self.width1:
            #print ("Bandwidth changed from " + self.width1 + " to " + width)
            self.width1 = width
            self.ui.btnBwCw100.setStyleSheet("background-color: ")
            self.ui.btnBwCw200.setStyleSheet("background-color: ")
            self.ui.btnBwCw300.setStyleSheet("background-color: ")
            self.ui.btnBwCw400.setStyleSheet("background-color: ")
            self.ui.btnBwCw500.setStyleSheet("background-color: ")
            self.ui.btnBwCw800.setStyleSheet("background-color: ")
            self.ui.btnBwCw1200.setStyleSheet("background-color: ")
            self.ui.btnBwCw1400.setStyleSheet("background-color: ")
            self.ui.btnBwCw1700.setStyleSheet("background-color: ")
            self.ui.btnBwCw2000.setStyleSheet("background-color: ")
            self.ui.btnBwCw2400.setStyleSheet("background-color: ")
            
            self.ui.btnBwSSB0200.setStyleSheet("background-color: ")
            self.ui.btnBwSSB0400.setStyleSheet("background-color: ")
            self.ui.btnBwSSB0600.setStyleSheet("background-color: ")
            self.ui.btnBwSSB0850.setStyleSheet("background-color: ")
            self.ui.btnBwSSB1100.setStyleSheet("background-color: ")
            self.ui.btnBwSSB1350.setStyleSheet("background-color: ")
            self.ui.btnBwSSB1500.setStyleSheet("background-color: ")
            self.ui.btnBwSSB1650.setStyleSheet("background-color: ")
            self.ui.btnBwSSB1800.setStyleSheet("background-color: ")
            self.ui.btnBwSSB1950.setStyleSheet("background-color: ")
            self.ui.btnBwSSB2100.setStyleSheet("background-color: ")
            self.ui.btnBwSSB2250.setStyleSheet("background-color: ")
            self.ui.btnBwSSB2400.setStyleSheet("background-color: ")
            self.ui.btnBwSSB2450.setStyleSheet("background-color: ")
            self.ui.btnBwSSB2500.setStyleSheet("background-color: ")
            self.ui.btnBwSSB2600.setStyleSheet("background-color: ")
            self.ui.btnBwSSB2700.setStyleSheet("background-color: ")
            self.ui.btnBwSSB2800.setStyleSheet("background-color: ")
            self.ui.btnBwSSB2900.setStyleSheet("background-color: ")
            self.ui.btnBwSSB3000.setStyleSheet("background-color: ")
            if width == "01":
                self.ui.btnBwSSB0200.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
            if width == "02":
                self.ui.btnBwSSB0400.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
            if width == "03":
                self.ui.btnBwSSB0600.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
                self.ui.btnBwCw100.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
            elif width == "04":
                self.ui.btnBwSSB0850.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
                self.ui.btnBwCw200.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
            elif width == "05":
                self.ui.btnBwSSB1100.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
                self.ui.btnBwCw300.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
            elif width == "06":
                self.ui.btnBwSSB1350.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
                self.ui.btnBwCw400.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
            elif width == "07":
                self.ui.btnBwSSB1500.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
                self.ui.btnBwCw500.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
            elif width == "08":
                self.ui.btnBwSSB1650.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
                self.ui.btnBwCw800.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
            elif width == "09":
                self.ui.btnBwSSB1800.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
                self.ui.btnBwCw1200.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
            elif width == "10":
                self.ui.btnBwSSB1950.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
                self.ui.btnBwCw1400.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
            elif width == "11":
                self.ui.btnBwSSB2100.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
                self.ui.btnBwCw1700.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
            elif width == "12":
                self.ui.btnBwSSB2250.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
                self.ui.btnBwCw2000.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
            elif width == "13":
                self.ui.btnBwSSB2400.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
                self.ui.btnBwCw2400.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
            elif width == "14":
                self.ui.btnBwSSB2450.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
            elif width == "15":
                self.ui.btnBwSSB2500.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
            elif width == "16":
                self.ui.btnBwSSB2600.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
            elif width == "17":
                self.ui.btnBwSSB2700.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
            elif width == "18":
                self.ui.btnBwSSB2800.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
            elif width == "19":
                self.ui.btnBwSSB2900.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
            elif width == "20":
                self.ui.btnBwSSB3000.setStyleSheet("background-color: qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(230,255,230, 255), stop:1 rgba(200, 230, 200, 255))")
        # Power
        try:
            float(pwr)
            if pwr != self.pwr1:
                self.pwr1 = pwr
                self.ui.slidPower.setValue(int(pwr))
                Pout = "RFout " + str(int(pwr)) + " Watt"
                self.ui.lblPower.setText(Pout)
                print(self.ui.slidPower.value())
        except:
            pwr = "5"
            if pwr != self.pwr1:
                self.pwr1 = pwr
                self.ui.slidPower.setValue(int(pwr))
                Pout = "RFout " + str(int(pwr)) + " Watt"
                self.ui.lblPower.setText(Pout)
                print(self.ui.slidPower.value())

        # AF-Gain
        try:
            float(gain)
            if gain != self.gain1:
                self.gain1 = gain
                self.ui.slidAudio.setValue(int(gain) / 2.5)
                AFgain = "AF-Gain " + str(int(int(gain) / 2.5)) + "%"
                self.ui.lblAudio.setText(AFgain)
                print(self.ui.slidAudio.value())
        except:
            gain = "10"
            if gain != self.gain1:
                self.gain1 = gain
                self.ui.slidAudio.setValue(int(gain) / 2.5)
                AFgain = "AF-Gain " + str(int(int(gain) / 2.5)) + "%"
                self.ui.lblAudio.setText(AFgain)
                print(self.ui.slidAudio.value())

    def done(self, test):
        print(test)
        exit()

    # Set RF Power
    def setPwr(self):
        locpwr = self.ui.slidPower.value()
        print(locpwr)
        if locpwr < 10:
            locpwr1 = ( "EX11100" + str(int(locpwr)) + ";" ).encode('utf-8')
        else:
            locpwr1 = ( "EX1110" + str(int(locpwr)) + ";" ).encode('utf-8')
        write2port(self, locpwr1)
    
    # Set AF Gain
    def setAFgain(self):
        locgain = self.ui.slidAudio.value()
        locgain = locgain * 2.5     # to convert value from slider 0-100% to TRX 0-255
        if locgain < 100:
            locgain1 = ( "AG00" + str(int(locgain)) + ";" ).encode('utf-8')
        elif locgain < 10:
            locgain1 = ( "AG000" + str(int(locgain)) + ";" ).encode('utf-8')
        else:
            locgain1 = ( "AG0" + str(int(locgain)) + ";" ).encode('utf-8')
        write2port(self, locgain1)

    # SET VFO to selected Station
    # get row and col of clicked cell
    # get data from row and col0=>frequency
    def selStation(self, tblRow, tblCol):
        #print(tblRow, tblCol)
        i = self.ui.tblStations.item(tblRow, 0)
        text = i.text()
        #print(text)
        textsplit = text.split(" ")
        textqrg = textsplit[0]
        if len(textqrg) == 7:
            textqrg = "0" + textqrg
        qrg = ("FA" + textqrg + ";").encode('utf-8')
        write2port(self, qrg)
    
    # SORT Station
    def srtStation(self, event):
        i = self.ui.rbtSrtCall.isChecked()
        print(i)
    
    
    # SET 160m Band
    def setBnd160m(self):
        strBandLo = "1800000"
        strBandHi = "2000000"
        self.setBand(strBandLo, strBandHi)
    # SET 80m Band
    def setBnd80m(self):    
        strBandLo = "3500000"
        strBandHi = "3800000"
        self.setBand(strBandLo, strBandHi)
    # SET 60m Band
    def setBnd60m(self):    
        strBandLo = "5100000"
        strBandHi = "5500000"
        self.setBand(strBandLo, strBandHi)
    # SET 40m Band
    def setBnd40m(self):
        strBandLo = "7000000"
        strBandHi = "7200000"
        self.setBand(strBandLo, strBandHi)
    # SET 30m Band
    def setBnd30m(self):    
        strBandLo = "10100000"
        strBandHi = "10150000"
        self.setBand(strBandLo, strBandHi)
    # SET 20m Band
    def setBnd20m(self):
        strBandLo = "14000000"
        strBandHi = "14350000"
        self.setBand(strBandLo, strBandHi)
    # SET 17m Band
    def setBnd17m(self):    
        strBandLo = "18068000"
        strBandHi = "18168000"
        self.setBand(strBandLo, strBandHi)
    # SET 15m Band
    def setBnd15m(self):
        strBandLo = "21000000"
        strBandHi = "21450000"
        self.setBand(strBandLo, strBandHi)
    # SET 12m Band
    def setBnd12m(self):    
        strBandLo = "24890000"
        strBandHi = "24990000"
        self.setBand(strBandLo, strBandHi)
    # SET 10m Band
    def setBnd10m(self):    
        strBandLo = "28000000"
        strBandHi = "29700000"
        self.setBand(strBandLo, strBandHi)
    # SET 6m Band
    def setBnd6m(self):    
        strBandLo = "50000000"
        strBandHi = "52500000"
        self.setBand(strBandLo, strBandHi)
    # SET All Bands
    def setBndAll(self):    
        strBandLo = "1800000"
        strBandHi = "52500000"
        self.setBand(strBandLo, strBandHi)    

    # SET Band
    def setBand(self, strBandLo, strBandHi):
        self.ui.tblStations.clear()
        strOrder = ""
        strWhere = ""
        rowTbl = [1,2,3,4,5,6]
        rowIndex = 0
        dbStations = "beacons.db"
        self.conn = sqlite3.connect(dbStations)
        self.curs = self.conn.cursor()
        
        # SET ORDER
        if(self.ui.rbtSrtCall.isChecked()):
            strOrder = " ORDER BY " + "station"
        elif(self.ui.rbtSrtFreq.isChecked()):
            strOrder = " ORDER BY " + "freq"
        else:
            strOrder = ""
            
        # SET WHERE
        strWhere = "WHERE freq >= " + strBandLo + " AND freq <= " + strBandHi
        if self.ui.cbxConEU.isChecked():
            strWhere = strWhere + " AND continent == " + '"EU"'
        
        #self.curs.execute("SELECT * FROM stations WHERE freq >= " + strBandLo + " AND freq <= " + strBandHi + strOrder)
        self.curs.execute("SELECT * FROM stations " + strWhere + " " + strOrder)
        
        for row in self.curs:
            (intFreqDB, strStationDB, strLocDB, strCountry, strCont) = row
            # Prepare Data
            strFreqDB = str(intFreqDB)
            if len(strFreqDB) == 7:
                strFreqDB = "0" + strFreqDB
            #if len(strStationDB) == 3:
            #    strStationDB = strStationDB + "   "
            #if len(strStationDB) == 4:
            #    strStationDB = strStationDB + "  "
            #if len(strStationDB) == 5:
            #    strStationDB = strStationDB + " "
                        
            # Write data to table
            rowTbl[1] = strFreqDB
            rowTbl[2] = strStationDB
            rowTbl[3] = strLocDB
            rowTbl[4] = strCountry
            rowTbl[5] = strCont
            # add more if there is more columns in the database.
            self.ui.tblStations.setRowCount(rowIndex +1)
            self.ui.tblStations.setItem(rowIndex, 0, QTableWidgetItem(rowTbl[1]))
            self.ui.tblStations.setItem(rowIndex, 1, QTableWidgetItem(rowTbl[2]))
            self.ui.tblStations.setItem(rowIndex, 2, QTableWidgetItem(rowTbl[3]))
            self.ui.tblStations.setItem(rowIndex, 3, QTableWidgetItem(rowTbl[4]))
            self.ui.tblStations.setItem(rowIndex, 4, QTableWidgetItem(rowTbl[5]))
            
            # increase index and row-count
            rowIndex = rowIndex + 1
            
        self.conn.close()
        return
        
    # SET Mode
    def setMLSB(self):
        #self.ui.stwBW.setCurrentIndex(1)
        write2port(self, b"MD01;")
    def setMUSB(self):
        #self.ui.stwBW.setCurrentIndex(1)
        write2port(self, b"MD02;")
    def setMCW(self):
        #self.ui.stwBW.setCurrentIndex(0)
        write2port(self, b"MD03;")
    def setMAM(self):
        #self.ui.stwBW.setCurrentIndex(2)
        write2port(self, b"MD05;")
    # SET Att 0db - -18dB
    def setAtt0(self):
        write2port(self, b"RA00;")
    def setAtt6(self):
        write2port(self, b"RA01;")
    def setAtt12(self):
        write2port(self, b"RA02;")
    def setAtt18(self):
        write2port(self, b"RA03;")
        # SET AMP Off - 2
    def setAmpOff(self):
        write2port(self, b"PA00;")
    def setAmp1(self):
        write2port(self, b"PA01;")
    def setAmp2(self):
        write2port(self, b"PA02;")

    # Toggle NAR / WIDE
    def setBWNW(self, mode):
        if mode == "CW":
            if self.width2 <= "06" and self.width1 >= "07":
                write2port(self, b"NA01;")
            elif self.width2 >= "07" and self.width1 <= "06":
                write2port(self, b"NA00;")
        if mode == "SSB":
            if self.width2 <= "08" and self.width1 >= "09":
                write2port(self, b"NA01;")
            elif self.width2 >= "09" and self.width1 <= "08":
                write2port(self, b"NA00;")        
        return
        
    # Bandwidth CW        
    def setBwCw100(self):
        self.width2 = "03"
        self.setBWNW("CW")
        write2port(self, b"SH003;")
    def setBwCw200(self):
        self.width2 = "04"
        self.setBWNW("CW")
        write2port(self, b"SH004;")
    def setBwCw300(self):
        self.width2 = "05"
        self.setBWNW("CW")
        write2port(self, b"SH005;")
    def setBwCw400(self):
        self.width2 = "06"
        self.setBWNW("CW")
        write2port(self, b"SH006;")
    def setBwCw500(self):
        self.width2 = "07"
        self.setBWNW("CW")
        write2port(self, b"SH007;")
    def setBwCw800(self):
        self.width2 = "08"
        self.setBWNW("CW")
        write2port(self, b"SH008;")
    def setBwCw1200(self):
        self.width2 = "09"
        self.setBWNW("CW")
        write2port(self, b"SH009;")
    def setBwCw1400(self):
        self.width2 = "10"
        self.setBWNW()
        write2port(self, b"SH010;")
    def setBwCw1700(self):
        self.width2 = "11"
        self.setBWNW("CW")
        write2port(self, b"SH011;")
    def setBwCw2000(self):
        self.width2 = "12"
        self.setBWNW("CW")
        write2port(self, b"SH012;")
    def setBwCw2400(self):
        self.width2 = "13"
        self.setBWNW("CW")
        write2port(self, b"SH013;")

    # Bandwidth SSB       
    def setBwSSB0200(self):
        self.width2 = "01"
        self.setBWNW("SSB")
        write2port(self, b"SH001;")
    def setBwSSB0400(self):
        self.width2 = "02"
        self.setBWNW("SSB")
        write2port(self, b"SH002;")
    def setBwSSB0600(self):
        self.width2 = "03"
        self.setBWNW("SSB")
        write2port(self, b"SH003;")
    def setBwSSB0850(self):
        self.width2 = "04"
        self.setBWNW("SSB")
        write2port(self, b"SH004;")
    def setBwSSB1100(self):
        self.width2 = "05"
        self.setBWNW("SSB")
        write2port(self, b"SH005;")
    def setBwSSB1350(self):
        self.width2 = "06"
        self.setBWNW("SSB")
        write2port(self, b"SH006;")
    def setBwSSB1500(self):
        self.width2 = "07"
        self.setBWNW("SSB")
        write2port(self, b"SH007;")
    def setBwSSB1650(self):
        self.width2 = "08"
        self.setBWNW("SSB")
        write2port(self, b"SH008;")
    def setBwSSB1800(self):
        self.width2 = "09"
        self.setBWNW("SSB")
        write2port(self, b"SH009;")
    def setBwSSB1950(self):
        self.width2 = "10"
        self.setBWNW("SSB")
        write2port(self, b"SH010;")
    def setBwSSB2100(self):
        self.width2 = "11"
        self.setBWNW("SSB")
        write2port(self, b"SH011;")
    def setBwSSB2250(self):
        self.width2 = "12"
        self.setBWNW("SSB")
        write2port(self, b"SH012;")
    def setBwSSB2400(self):
        self.width2 = "13"
        self.setBWNW("SSB")
        write2port(self, b"SH013;")
    def setBwSSB2450(self):
        self.width2 = "14"
        self.setBWNW("SSB")
        write2port(self, b"SH014;")
    def setBwSSB2500(self):
        self.width2 = "15"
        self.setBWNW("SSB")
        write2port(self, b"SH015;")
    def setBwSSB2600(self):
        self.width2 = "16"
        self.setBWNW("SSB")
        write2port(self, b"SH016;")
    def setBwSSB2700(self):
        self.width2 = "17"
        self.setBWNW("SSB")
        write2port(self, b"SH017;")
    def setBwSSB2800(self):
        self.width2 = "18"
        self.setBWNW("SSB")
        write2port(self, b"SH018;")
    def setBwSSB2900(self):
        self.width2 = "19"
        self.setBWNW("SSB")
        write2port(self, b"SH019;")
    def setBwSSB3000(self):
        self.width2 = "20"
        self.setBWNW("SSB")
        write2port(self, b"SH020;")
###### END of class RigControl ######

class sigButtons(QObject):
    mySignal1 = pyqtSignal(str)

#########################################
### Class RigPoll Start
#########################################        
class RigPoll(QObject):    
    mySignal = pyqtSignal(str, str, str, str, str)
    
    def __init__(self):
        super().__init__()
        
    def __del__(self):
        pass

    def work(self):
        while True:
            # Poll VFO A
            write2port(self, b"IF;")
            rcv = port.read(27)
            # slicing frequency info, because of byte data
            rcvk = rcv[5:10]          # khz
            rcvh = rcv[10:13]         # hz
            #self.frVfo.qrgA.set(rcvk + b"." + rcvh)
            #rcvcd = rcv[13:14]       # clarifier direction +/-
            #rcvco = rcv[14:18]       # clarifier h
            rcvm = rcv[20:21]         # mode
            # Poll Filter width
            write2port(self, b"SH0;")
            rcv = port.read(12)
            rcvw = rcv[3:5]
            # Poll Output power
            write2port(self, b"EX111;")
            rcv = port.read(12)
            rcvp = rcv[5:8]
            # Poll AF Gain
            write2port(self, b"AG0;")
            rcv = port.read(12)
            rcvg = rcv[3:6]
            
            mode = str(rcvm,'utf-8')
            vfo = str(rcvk,'utf-8')+"."+str(rcvh,'utf-8')
            width = str(rcvw, 'utf-8')
            pwr = str(rcvp,'utf-8')
            gain = str(rcvg,'utf-8')
            self.mySignal.emit(vfo, mode, width, pwr, gain)

###### END of class RigPoll ######

'''
# SET Audio Device to selected one
    def selDevAudio(self, event):
        i = self.lbAudio.curselection()
        text = self.lbAudio.get(i)
        print("Selected audio device: " + text)
        #textsplit = text.split(" ")
        #textqrg = textsplit[0]
        #if len(textqrg) == 7:
        #    textqrg = "0" + textqrg
        #qrg = ("FA" + textqrg + ";").encode('utf-8')
        #print(qrg)
        #port.write(qrg)
        #rcv = port.read(12)
        #print(rcv)
'''

if __name__ == '__main__':
    import sys
    
    app = QtWidgets.QApplication(sys.argv)
    mw = RigControl()
    mw.show()
    sys.exit(app.exec_())


