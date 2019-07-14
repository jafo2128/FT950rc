#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  rigcontrol2.py
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
import pyaudio

# used by class RigControl
import sys
#import time
import serial

from PyQt5 import QtWidgets, QtCore, uic, QtGui
from PyQt5.QtWidgets import QTableWidget,QTableWidgetItem
from PyQt5.QtCore import *

#**************************
# Serial Port Basic Settings
#**************************
port = serial.Serial("/dev/ttyUSB0", baudrate=38400, timeout=0.1)
port.rts = False
port.dtr = False

#**************************
# Audio Devices List
#**************************
p = pyaudio.PyAudio()
i = 0
print("\n\n\n\n")
for i in range(p.get_device_count()):
    test = p.get_device_info_by_index(i)
    print (str(test["index"]) + " " + test["name"])

#**************************
# Variables
#**************************
strBand = ""


#**************************
# Initialize Rig Data
#**************************
port.write(b"EX111;")
rcv = port.read(12)
strPout = str(rcv[5:8],'utf-8')
print("Power: " + strPout)
port.write(b"IF;")
rcv = port.read(27)
# slicing frequency info, because of byte data
rcvk = rcv[5:10]         # khz
rcvh = rcv[10:13]        # hz
#self.frVfo.qrgA.set(rcvk + b"." + rcvh)
rcvcd = rcv[13:14]       # clarifier direction +/-
rcvco = rcv[14:18]       # clarifier h
rcvm = rcv[20:21]   # mode
# Poll Width of Filter
port.write(b"SH0;")
rcv = port.read(12)
rcvw = rcv[3:5]     # width

mode = str(rcvm,'utf-8')
print(str(rcvk,'utf-8') + str(rcvh,'utf-8') + " " + mode + " " + str(rcvw,'utf-8'))



class RigControl(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(RigControl, self).__init__(parent)

        # Thread for polling the RIG
        self.thread = QThread()
        self.w = RigPoll()
        self.w.mySignal[str, str, str, str].connect(self.onFinished)
        self.w.moveToThread(self.thread)
        self.thread.started.connect(self.w.work)
        self.thread.start()

        #init user interface
        self.ui = uic.loadUi("rigcontrol2.ui", self)

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

        self.ui.btnBeaImp.clicked.connect(Stations.ImpBeacon)

        self.ui.liStations.clicked.connect(self.selStation)
        
        self.ui.rbtSrtCall.clicked.connect(self.srtStation)

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

    def onExit(self):
        self.close()

    @pyqtSlot(str, str, str, str)
    def onFinished(self, vfo, mode, width, pwr):
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
        self.ui.slidPower.setValue(int(pwr))
        Pout = "Pout " + str(int(pwr)) + " Watt"
        self.ui.lblPower.setText(Pout)
        #print(self.ui.slidPower.value())
            

    def done(self, test):
        print(test)
        exit()

    # SET VFO to selected Station
    def selStation(self, event):
        i = self.ui.liStations.currentItem()
        text = i.text()
        textsplit = text.split(" ")
        textqrg = textsplit[0]
        if len(textqrg) == 7:
            textqrg = "0" + textqrg
        qrg = ("FA" + textqrg + ";").encode('utf-8')
        port.write(qrg)
    
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
        self.ui.liStations.clear()
        self.ui.tblStations.clear()
        rowTbl = [1,2,3,4]
        rowIndex = 0
        dbStations = "beacons.db"
        self.conn = sqlite3.connect(dbStations)
        self.curs = self.conn.cursor()
        if(self.ui.rbtSrtCall.isChecked()):
            self.curs.execute("SELECT * FROM stations WHERE freq >= " + strBandLo + " AND freq <= " + strBandHi + " ORDER BY station")
        else:
            self.curs.execute("SELECT * FROM stations WHERE freq >= " + strBandLo + " AND freq <= " + strBandHi + " ORDER BY freq")
        
        for row in self.curs:
            (intFreqDB, strStationDB, strLocDB, strCountry, strCont) = row
            # Prepare Data
            strFreqDB = str(intFreqDB)
            if len(strFreqDB) == 7:
                strFreqDB = "0" + strFreqDB
            if len(strStationDB) == 3:
                strStationDB = strStationDB + "   "
            if len(strStationDB) == 4:
                strStationDB = strStationDB + "  "
            if len(strStationDB) == 5:
                strStationDB = strStationDB + " "
            # Write data
            row1 = (strFreqDB + " " + strStationDB + " " + strLocDB + " " + strCont + " " + strCountry)
            self.ui.liStations.addItem(row1)
            
            # Write data to table
            rowTbl[1] = strFreqDB
            rowTbl[2] = strStationDB
            rowTbl[3] = strLocDB
            # add more if there is more columns in the database.
            self.ui.tblStations.setRowCount(rowIndex +1)
            self.ui.tblStations.setItem(rowIndex, 0, QTableWidgetItem(rowTbl[1]))
            self.ui.tblStations.setItem(rowIndex, 1, QTableWidgetItem(rowTbl[2]))
            self.ui.tblStations.setItem(rowIndex, 2, QTableWidgetItem(rowTbl[3]))
            # increase index and row-count
            rowIndex = rowIndex + 1
            
        self.conn.close()
        return
        
    # SET Mode
    def setMLSB(self):
        #self.ui.stwBW.setCurrentIndex(1)
        port.write(b"MD01;")
    def setMUSB(self):
        #self.ui.stwBW.setCurrentIndex(1)
        port.write(b"MD02;")
    def setMCW(self):
        #self.ui.stwBW.setCurrentIndex(0)
        port.write(b"MD03;")
    def setMAM(self):
        #self.ui.stwBW.setCurrentIndex(2)
        port.write(b"MD05;")
    # SET Att 0db - -18dB
    def setAtt0(self):
        port.write(b"RA00;")
    def setAtt6(self):
        port.write(b"RA01;")
    def setAtt12(self):
        port.write(b"RA02;")
    def setAtt18(self):
        port.write(b"RA03;")
        # SET AMP Off - 2
    def setAmpOff(self):
        port.write(b"PA00;")
    def setAmp1(self):
        port.write(b"PA01;")
    def setAmp2(self):
        port.write(b"PA02;")

    # Toggle NAR / WIDE
    def setBWNW(self, mode):
        if mode == "CW":
            if self.width2 <= "06" and self.width1 >= "07":
                port.write(b"NA01;")
            elif self.width2 >= "07" and self.width1 <= "06":
                port.write(b"NA00;")
        if mode == "SSB":
            if self.width2 <= "08" and self.width1 >= "09":
                port.write(b"NA01;")
            elif self.width2 >= "09" and self.width1 <= "08":
                port.write(b"NA00;")        
        return
        
    # Bandwidth CW        
    def setBwCw100(self):
        self.width2 = "03"
        self.setBWNW("CW")
        port.write(b"SH003;")
    def setBwCw200(self):
        self.width2 = "04"
        self.setBWNW("CW")
        port.write(b"SH004;")
    def setBwCw300(self):
        self.width2 = "05"
        self.setBWNW("CW")
        port.write(b"SH005;")
    def setBwCw400(self):
        self.width2 = "06"
        self.setBWNW("CW")
        port.write(b"SH006;")
    def setBwCw500(self):
        self.width2 = "07"
        self.setBWNW("CW")
        port.write(b"SH007;")
    def setBwCw800(self):
        self.width2 = "08"
        self.setBWNW("CW")
        port.write(b"SH008;")
    def setBwCw1200(self):
        self.width2 = "09"
        self.setBWNW("CW")
        port.write(b"SH009;")
    def setBwCw1400(self):
        self.width2 = "10"
        self.setBWNW()
        port.write(b"SH010;")
    def setBwCw1700(self):
        self.width2 = "11"
        self.setBWNW("CW")
        port.write(b"SH011;")
    def setBwCw2000(self):
        self.width2 = "12"
        self.setBWNW("CW")
        port.write(b"SH012;")
    def setBwCw2400(self):
        self.width2 = "13"
        self.setBWNW("CW")
        port.write(b"SH013;")

    # Bandwidth SSB       
    def setBwSSB0200(self):
        self.width2 = "01"
        self.setBWNW("SSB")
        port.write(b"SH001;")
    def setBwSSB0400(self):
        self.width2 = "02"
        self.setBWNW("SSB")
        port.write(b"SH002;")
    def setBwSSB0600(self):
        self.width2 = "03"
        self.setBWNW("SSB")
        port.write(b"SH003;")
    def setBwSSB0850(self):
        self.width2 = "04"
        self.setBWNW("SSB")
        port.write(b"SH004;")
    def setBwSSB1100(self):
        self.width2 = "05"
        self.setBWNW("SSB")
        port.write(b"SH005;")
    def setBwSSB1350(self):
        self.width2 = "06"
        self.setBWNW("SSB")
        port.write(b"SH006;")
    def setBwSSB1500(self):
        self.width2 = "07"
        self.setBWNW("SSB")
        port.write(b"SH007;")
    def setBwSSB1650(self):
        self.width2 = "08"
        self.setBWNW("SSB")
        port.write(b"SH008;")
    def setBwSSB1800(self):
        self.width2 = "09"
        self.setBWNW("SSB")
        port.write(b"SH009;")
    def setBwSSB1950(self):
        self.width2 = "10"
        self.setBWNW("SSB")
        port.write(b"SH010;")
    def setBwSSB2100(self):
        self.width2 = "11"
        self.setBWNW("SSB")
        port.write(b"SH011;")
    def setBwSSB2250(self):
        self.width2 = "12"
        self.setBWNW("SSB")
        port.write(b"SH012;")
    def setBwSSB2400(self):
        self.width2 = "13"
        self.setBWNW("SSB")
        port.write(b"SH013;")
    def setBwSSB2450(self):
        self.width2 = "14"
        self.setBWNW("SSB")
        port.write(b"SH014;")
    def setBwSSB2500(self):
        self.width2 = "15"
        self.setBWNW("SSB")
        port.write(b"SH015;")
    def setBwSSB2600(self):
        self.width2 = "16"
        self.setBWNW("SSB")
        port.write(b"SH016;")
    def setBwSSB2700(self):
        self.width2 = "17"
        self.setBWNW("SSB")
        port.write(b"SH017;")
    def setBwSSB2800(self):
        self.width2 = "18"
        self.setBWNW("SSB")
        port.write(b"SH018;")
    def setBwSSB2900(self):
        self.width2 = "19"
        self.setBWNW("SSB")
        port.write(b"SH019;")
    def setBwSSB3000(self):
        self.width2 = "20"
        self.setBWNW("SSB")
        port.write(b"SH020;")    

class sigButtons(QObject):
    mySignal1 = pyqtSignal(str)
        
class RigPoll(QObject):    
    mySignal = pyqtSignal(str, str, str, str)
    
    def __init__(self):
        #print ("Thread1")
        super().__init__()
        
    def __del__(self):
        print ("Thread2")
        #self.wait()

    def work(self):
        while True:
            #print ("Thread3")
            # Poll VFO A
            port.write(b"IF;")
            rcv = port.read(27)
            # slicing frequency info, because of byte data
            rcvk = rcv[5:10]          # khz
            rcvh = rcv[10:13]         # hz
            #self.frVfo.qrgA.set(rcvk + b"." + rcvh)
            #rcvcd = rcv[13:14]       # clarifier direction +/-
            #rcvco = rcv[14:18]       # clarifier h
            rcvm = rcv[20:21]         # mode
            # Poll Width of Filter
            port.write(b"SH0;")
            rcv = port.read(12)
            rcvw = rcv[3:5]           # width
            # Poll Output power
            port.write(b"EX111;")
            rcv = port.read(12)
            rcvp = rcv[5:8]
            
            mode = str(rcvm,'utf-8')
            vfo = str(rcvk,'utf-8')+"."+str(rcvh,'utf-8')
            width = str(rcvw, 'utf-8')
            pwr = str(rcvp,'utf-8')
            self.mySignal.emit(vfo, mode, width, pwr)

class Stations():
    print("Stations1")
    
    
    def __init__(self):
        super().__init__()

    def ImpBeacon(self):
        # Get Working Path
        strPath = os.getcwd()
        
        # DB
        dbStations = "beacons.db"
        
        # Input1
        dbMode = "overwrite"
        strFileIn = "G3USF's Worldwide List of HF Beacons.htm"
        Stations.ReadG3USF(self, strFileIn, dbStations, dbMode)
        
        # Input2
        #dbMode = "append"
        #strFileIn = "G3USF's Worldwide List of 50MHz Beacons.htm"
        #Stations.ReadG3USF(self, strFileIn, dbStations, dbMode)
        
    def ReadG3USF(self, strFileIn, dbStations, dbMode):
        
        fobjFileIn = open(strFileIn, "r")
        fobjFileOut = open("beacon_list.txt", "w")
        conn = sqlite3.connect(dbStations)
        curs = conn.cursor()
        
        dicCountry = {
        "1A":["Sovereign Military Order of Malta","EU"],
        "1B":["Cyprus","EU"],
        "1S":["Spratly Is",""],
        "2E":["England (Novices)","EU"],
        "2D":["Isle Of Man (Novices)","EU"],
        "2I":["Northern Ireland (Novices)","EU"],
        "2J":["Jersey (Novices)","EU"],
        "2M":["Scotland (Novices)","EU"],
        "2U":["Guernsey & Dependencies (Novices)","EU"],
        "2W":["Wales (Novices)","EU"],
        "3A":["Monaco","EU"],
        "3B":["Mauritius",""],
        "3B6":["Agalega",""],
        "3B7":["Agalega",""],
        "3B8":["Mauritius",""],
        "3B9":["Rodriguez Is",""],
        "3C":["Equatorial Guinea",""],
        "3C0":["Annobon",""],
        "3D2":["Conway Reef",""],
        "3D2":["Fiji Is",""],
        "3D2":["Rotuma",""],
        "3D2/C":["Conway Reef",""],
        "3D2/F":["Fiji Islands",""],
        "3D2/R":["Rotuma",""],
        "3D6":["Swaziland",""],
        "3DA0":["Swaziland",""],
        "3G":["Chile",""],
        "3V":["Tunisia","AF"],
        "3W":["Vietnam",""],
        "3X":["Guinea",""],
        "3Y":["Bouvet Is",""],
        "3Y":["Peter Is",""],
        "3Y/B":["Bouvet",""],
        "3Y/P":["Peter Is",""],
        "3Z":["Poland","EU"],
        "4A":["Mexico",""],
        "4B":["Mexico",""],
        "4C":["Mexico",""],
        "4D":["Philippines",""],
        "4F":["Philippines",""],
        "4I":["Philippines",""],
        "4J":["Azerbaijan",""],
        "4J1":["Malyj Vysotskij",""],
        "4K":["Russian Polar Sta",""],
        "4L":["Georgia",""],
        "4M":["Venezuela",""],
        "4N1":["Yugoslavia (Regular)","EU"],
        "4N4":["Bosnia Herzegovina","EU"],
        "4N5":["Macedonia","EU"],
        "4N6":["Yugoslavia (Regular)","EU"],
        "4N7":["Yugoslavia (Regular)","EU"],
        "4N8":["Yugoslavia (Regular)","EU"],
        "4N9":["Yugoslavia (Reserved)","EU"],
        "4N0":["Yugoslavia (Reserved)","EU"],
        "4O1":["Yugoslavia (Special)","EU"],
        "4O4":["Bosnia Herzegovina","EU"],
        "4O5":["Macedonia","EU"],
        "4O6":["Yugoslavia (Special)","EU"],
        "4O7":["Yugoslavia (Special)","EU"],
        "4O8":["Yugoslavia (Special)","EU"],
        "4O9":["Yugoslavia (Reserved)","EU"],
        "4O0":["Yugoslavia (Reserved)","EU"],
        "4P":["Sri Lanka",""],
        "4Q":["Sri Lanka",""],
        "4R":["Sri Lanka",""],
        "4S":["Sri Lanka",""],
        "4T":["Peru",""],
        "4U":["I.T.U. Geneva",""],
        "4U":["U.N. N.Y.",""],
        "4U1VIC":["Vienna Int. Congress Center.",""],
        "4V":["Haiti",""],
        "4W":["Yemen",""],
        "4X":["Israel",""],
        "4Z":["Israel",""],
        "5A":["Libya",""],
        "5B":["Cyprus",""],
        "5C":["Morocco",""],
        "5D":["Morocco",""],
        "5H":["Tanzania",""],
        "5I":["Tanzania",""],
        "5J":["Columbia",""],
        "5K":["Columbia",""],
        "5L":["Liberia",""],
        "5N":["Nigeria",""],
        "5O":["Nigeria",""],
        "5R":["Malagasy Rep ",""],
        "5S":["Malagasy Rep",""],
        "5T":["Mauritania",""],
        "5U":["Niger",""],
        "5V":["Togo",""],
        "5W":["Western Samoa",""],
        "5X":["Uganda",""],
        "5Y":["Kenya",""],
        "5Z":["Kenya",""],
        "6D":["Mexico",""],
        "6E":["Mexico",""],
        "6G":["Mexico",""],
        "6I":["Mexico",""],
        "6K":["South Korea",""],
        "6O":["Somalia",""],
        "6T":["Sudan",""],
        "6V":["Senegal",""],
        "6W":["Senegal",""],
        "6Y":["Jamaica",""],
        "7J":["Japan",""],
        "7K":["Japan",""],
        "7L":["Japan",""],
        "7M":["Japan",""],
        "7N":["Japan",""],
        "7O":["Yemen Peo Rep",""],
        "7P":["Lesotho",""],
        "7Q":["Malawi",""],
        "7S":["Sweden","EU"],
        "7T":["Algeria",""],
        "7U":[" Algeria",""],
        "7V":["Algeria",""],
        "7W":["Algeria",""],
        "7X":["Algeria",""],
        "7Y":["Algeria",""],
        "7Z":["Saudi Arabia",""],
        "8A":["Indonesia",""],
        "8B":["Indonesia",""],
        "8C":["Indonesia",""],
        "8D":["Indonesia",""],
        "8E":["Indonesia",""],
        "8F":["Indonesia",""],
        "8G":["Indonesia",""],
        "8H":["Indonesia",""],
        "8I":["Indonesia",""],
        "8J":["Japan",""],
        "8O":["Botswana",""],
        "8P":["Barbados",""],
        "8Q":["Maldive Is",""],
        "8R":["Guyana",""],
        "8S":["Sweden","EU"],
        "8T":["India",""],
        "8T4":["Andaman Is",""],
        "8T7":["Laccadive Is",""],
        "8U":["India",""],
        "8U4":["Andaman Is",""],
        "8U7":["Laccadive Is",""],
        "8V":["India",""],
        "8V4":["Andaman Is",""],
        "8V7":["Laccadive Is",""],
        "8W":["India",""],
        "8W4":["Andaman Is",""],
        "8W7":["Laccadive Is",""],
        "8Z":["Saudi Arabia",""],
        "9A":["Croatia","EU"],
        "9D":["Iran",""],
        "9E":["Ethiopia",""],
        "9F":["Ethiopia",""],
        "9G":["Ghana",""],
        "9H":["Malta","EU"],
        "9I":["Zambia",""],
        "9J":["Zambia",""],
        "9K":["Kuwait",""],
        "9L":["Sierra Leone",""],
        "9M0":["Spratly Is",""],
        "9M2":["West Malaysia",""],
        "9M4":["West Malaysia",""],
        "9M6":["East Malaysia",""],
        "9M8":["East Malaysia",""],
        "9N":["Nepal",""],
        "9Q":["Zaire",""],
        "9R":["Zaire",""],
        "9S":["Zaire",""],
        "9T":["Zaire ",""],
        "9U":["Burundi",""],
        "9V":["Singapore",""],
        "9X":["Rwanda",""],
        "9Y":["Trinidad",""],
        "9Z":["Trinidad",""],
        "A15":["Abu Ail",""],
        "A2":["Botswana",""],
        "A3":["Tonga",""],
        "A4":["Oman",""],
        "A5":["Bhutan",""],
        "A51":["Bhutan",""],
        "A6":["United Arab Emirites",""],
        "A7":["Qatar",""],
        "A8":["Liberia",""],
        "A9":["Bahrain",""],
        "AA-AK":["USA","NA"],
        "AA":["USA","NA"],
        "AB":["USA","NA"],
        "AC":["USA","NA"],
        "AD":["USA","NA"],
        "AE":["USA","NA"],
        "AF":["USA","NA"],
        "AG":["USA","NA"],
        "AH":["USA","NA"],
        "AI":["USA","NA"],
        "AJ":["USA","NA"],
        "AK":["USA","NA"],
        "AC6":["West Carolines",""],
        "AH0":["Mariana Is",""],
        "AH1":["Baker Howland",""],
        "AH2":["Guam",""],
        "AH3":["Johnston Is",""],
        "AH4":["Midway Is",""],
        "AH5":["Palmyra Is",""],
        "AH5K":["Kingman Reef",""],
        "AH6":["Hawaii",""],
        "AH7K":["Kure Is",""],
        "AH8":["American Samoa",""],
        "AH9":["Wake Is",""],
        "AL":["USA Alaska","NA"],
        "AM":["Spain","EU"],
        "AM6":["Balearic Is",""],
        "AM8":["Canary Is","AF"],
        "AM9":["Ceuta-Melilla","AF"],
        "AN":["Spain","EU"],
        "AN6":["Balearic Is","EU"],
        "AN8":["Canary Is","AF"],
        "AN9":["Ceuta-Melilla","AF"],
        "AO":["Spain","EU"],
        "AO6":["Balearic Is","EU"],
        "AO8":["Canary Is","AF"],
        "AO9":["Ceuta-Melilla","AF"],
        "AP":["Pakistan","AS"],
        "AQ":["Pakistan","AS"],
        "AR":["Pakistan","AS"],
        "AS":["Pakistan","AS"],
        "AT":["India","AS"],
        "AT4":["Andaman Is",""],
        "AT7":["Laccadive Is",""],
        "AU":["India",""],
        "AU4":["Andaman Is",""],
        "AU7":["Laccadive Is",""],
        "AV":["India",""],
        "AV4":["Andaman Is",""],
        "AV7":["Laccadive Is",""],
        "AW":["India",""],
        "AW4":["Andaman Is",""],
        "AW7":["Laccadive Is",""],
        "AX":["Australia",""],
        "AY":["Argentina",""],
        "AZ":["Argentina",""],
        "BA-BU":["China","AS"],
        "BA":["China","AS"],
        "BB":["China","AS"],
        "BC":["China","AS"],
        "BD":["China","AS"],
        "BE":["China","AS"],
        "BF":["China","AS"],
        "BG":["China","AS"],
        "BH":["China","AS"],
        "BI":["China","AS"],
        "BJ":["China","AS"],
        "BK":["China","AS"],
        "BL":["China","AS"],
        "BM":["China","AS"],
        "BN":["China","AS"],
        "BO":["China","AS"],
        "BP":["China","AS"],
        "BQ":["China","AS"],
        "BR":["China","AS"],
        "BS":["China","AS"],
        "BT":["China","AS"],
        "BU":["China","AS"],
        "BV":["Taiwan","AS"],
        "BW":["China","AS"],
        "BX":["China","AS"],
        "BY":["China","AS"],
        "BZ":["China","AS"],
        "C2":["Nauru",""],
        "C3":["Andorra","EU"],
        "C4":["Cyprus","EU"],
        "C5":["Gambia","AF"],
        "C6":["Bahamas","SA"],
        "C8":["Mozambique","AF"],
        "C9":["Mozambique","AF"],
        "CA":["Chile","SA"],
        "CB":["Chile","SA"],
        "CC":["Chile","SA"],
        "CD":["Chile","SA"],
        "CE":["Chile","SA"],
        "CE1-CE8":["Chile","SA"],
        "CE9":["Antarctica",""],
        "CE0A":["Easter Island",""],
        "CE0E":["Easter Island",""],
        "CE0F":["Easter Island",""],
        "CE0I":["Juan Fernandez ",""],
        "CE0X":["San Felix",""],
        "CE0Y":["Easter Island",""],
        "CE0Z":["Juan Fernandez",""],
        "CF":["Canada","NA"],
        "CG":["Canada","NA"],
        "CH":["Canada","NA"],
        "CI":["Canada","NA"],
        "CJ":["Canada","NA"],
        "CK":["Canada","NA"],
        "CL":["Cuba","NA"],
        "CM":["Cuba","NA"],
        "CN":["Morocco","AF"],
        "CO":["Cuba","NA"],
        "CP":["Bolivia","SA"],
        "CQ":["Portugal","EU"],
        "CQ3":["Madeira Is",""],
        "CQ9":["Madeira Is",""],
        "CR":["Portugal","EU"],
        "CR3":["Madeira Is",""],
        "CR9":["Madeira Is",""],
        "CS":["Portugal","EU"],
        "CT":["Portugal","EU"],
        "CT2":["Azores","AF"],
        "CT3":["Madeira Is","AF"],
        "CT9":["Madeira Is","AF"],
        "CU":["Azores Is","AF"],
        "CV":["Uruguay","SA"],
        "CW":["Uruguay","SA"],
        "CX":["Uruguay ","SA"],
        "CY":["Canada","NA"],
        "CZ":["Canada","NA"],
        "D2":["Angola","AF"],
        "D3":["Angola","AF"],
        "D4":["Cape Verde",""],
        "D6":["Comoros",""],
        "D7":["South Korea","AS"],
        "D8":["South Korea","AS"],
        "D9":["South Korea","AS"],
        "DA":["Germany","EU"],
        "DB":["Germany","EU"],
        "DC":["Germany","EU"],
        "DD":["Germany","EU"],
        "DE":["Germany","EU"],
        "DF":["Germany","EU"],
        "DG":["Germany","EU"],
        "DH":["Germany","EU"],
        "DI":["Germany","EU"],
        "DJ":["Germany","EU"],
        "DK":["Germany","EU"],
        "DL":["Germany","EU"],
        "DM":["Germany","EU"],
        "DN":["Germany","EU"],
        "DO":["Germany","EU"],
        "DP":["Germany","EU"],
        "DQ":["Germany","EU"],
        "DR":["Germany","EU"],
        "DS":["South Korea","AS"],
        "DT":["South Korea","AS"],
        "DU":["Philippines","AS"],
        "DV":["Philippines ","AS"],
        "DX":["Philippines ","AS"],
        "DY":["Philippines","AS"],
        "DZ":["Philippines","AS"],
        "E2":["Thailand","AS"],
        "E3":["Eritrea","AS"],
        "E4":["Palestina","AS"],
        "EA":["Spain","EU"],
        "EA6":["Balearic Is","EU"],
        "EA8":["Canary Is","AF"],
        "EA9":["Ceuta","AF"],
        "EB":["Spain","EU"],
        "EB6":["Balearic Is","EU"],
        "EB8":["Canary Is","AF"],
        "EB9":["Ceuta","AF"],
        "EC":["Spain","EU"],
        "EC6":["Balearic Is","EU"],
        "EC8":["Canary Is",""],
        "EC9":["Ceuta",""],
        "EC9":["Melilla",""],
        "ED":["Spain","EU"],
        "ED6":["Balearic Is","EU"],
        "ED8":["Canary Is",""],
        "ED9":["Ceuta",""],
        "ED9":["Melilla",""],
        "EE":["Spain","EU"],
        "EE6":["Balearic Is","EU"],
        "EE8":["Canary Is",""],
        "EE9":["Ceuta",""],
        "EF":["Spain","EU"],
        "EF6":["Balearic Is","EU"],
        "EF8":["Canary Is",""],
        "EF9":["Ceuta",""],
        "EG":["Spain","EU"],
        "EG6":["Balearic Is","EU"],
        "EG8":["Canary Is",""],
        "EG9":["Ceuta",""],
        "EH":["Spain","EU"],
        "EH6":["Balearic Is","EU"],
        "EH8":["Canary Is",""],
        "EH9":["Ceuta",""],
        "EI":["Ireland","EU"],
        "EJ":["Ireland","EU"],
        "EK":["Armenia",""],
        "EL":["Liberia",""],
        "EM":["Ukraine","EU"],
        "EN":["Ukraine","EU"],
        "EO":["Ukraine","EU"],
        "EP":["Iran",""],
        "EQ":["Iran",""],
        "ER":["Moldova","EU"],
        "ES":["Estonia","EU"],
        "ET":["Ethiopia",""],
        "EU":["Belarus","EU"],
        "EV":["Belarus","EU"],
        "EW":["Belarus","EU"],
        "EX":["Kyrgyzstan",""],
        "EY":["Tadjikistan",""],
        "EZ":["Turkmenistan",""],
        "F1":["France","EU"],
        "F2":["France","EU"],
        "F3":["France","EU"],
        "F4":["France","EU"],
        "F5":["France","EU"],
        "F6":["France","EU"],
        "F7":["France","EU"],
        "F8":["France","EU"],
        "F9":["France","EU"],
        "FB":["France","EU"],
        "FC":["Corsica","EU"],
        "FD":["France","EU"],
        "FE":["France","EU"],
        "FF":["France","EU"],
        "FG":["Guadeloupe",""],
        "FH":["Mayotte",""],
        "FJ":["St Martin",""],
        "FK":["New Caledonia",""],
        "FM":["Martinique",""],
        "FO":["Clipperton",""],
        "FO":["Tahiti",""],
        "FO/C":["Clipperton",""],
        "FP":["St Pierre Miquelon",""],
        "FR":["Glorioso",""],
        "FR":["Juan De Nova",""],
        "FR":["Reunion",""],
        "FR":["Tromelin",""],
        "FR/G":["Glorioso",""],
        "FR/J":["Juan De Nova",""],
        "FR/T":["Tromelin",""],
        "FS":["St Martin",""],
        "FT0W":["Crozet",""],
        "FT0X":["Kerguelen Is",""],
        "FT0Z":["Amsterdam Paul",""],
        "FT2W":["Crozet",""],
        "FT2X":["Kerguelen Is",""],
        "FT2Z":["Amsterdam Paul",""],
        "FT5W":["Crozet",""],
        "FT5X":["Kerguelen Is",""],
        "FT5Z":["Amsterdam Paul",""],
        "FT8W":["Crozet",""],
        "FT8X":["Kerguelen Is",""],
        "FT8Y":["Antarctica",""],
        "FT8Z":["Amsterdam Paul",""],
        "FU":["France","EU"],
        "FV":["France","EU"],
        "FW":["Wallis Is","EU"],
        "FY":["French Guiana",""],
        "G0":["GB England","EU"],
        "G1":["GB England","EU"],
        "G2":["GB England","EU"],
        "G3":["GB England","EU"],
        "G4":["GB England","EU"],
        "G5":["GB England","EU"],
        "G6":["GB England","EU"],
        "G7":["GB England","EU"],
        "G8":["GB England","EU"],
        "G9":["GB England","EU"],
        "G":["GB England","EU"],
        "GB":["GB","EU"],
        "GC":["GB Wales","EU"],
        "GD":["GB Isle of Man","EU"],
        "GH":["GB Jersey","EU"],
        "GI":["Northern Ireland","EU"],
        "GJ":["GB Jersey","EU"],
        "GM":["Scotland","EU"],
        "GN":["Northern Ireland","EU"],
        "GP":["GB Guernsey & Dependencies","EU"],
        "GS":["Scotland","EU"],
        "GT":["GB Isle of Man","EU"],
        "GU":["GB Guernsey & Dependencies","EU"],
        "GW":["GB Wales","EU"],
        "GX":["GB England","EU"],
        "H2":["Cyprus","EU"],
        "H3":["Panama",""],
        "H4":["Solomon Is",""],
        "H5":["So Africa",""],
        "H6":["Nicaragua",""],
        "H7":["Nicaragua",""],
        "H8":["Panama",""],
        "H9":["Panama",""],
        "HA":["Hungary","EU"],
        "HB":["Switzerland","EU"],
        "HB0":["Liechtenstein","EU"],
        "HC":["Ecuador",""],
        "HC8":["Galapagos",""],
        "HD":["Ecuador",""],
        "HD8":["Galapagos",""],
        "HE":["Switzerland","EU"],
        "HF":["Poland","EU"],
        "HF0":["So Shetland",""],
        "HG":["Hungary","EU"],
        "HH":["Haiti",""],
        "HI":["Dominican Rep",""],
        "HJ":["Columbia",""],
        "HK":["Colombia",""],
        "HK0":["Malpelo Is",""],
        "HK0":["San Andres Is",""],
        "HK0/A":["San Andres Is",""],
        "HK0/M":["Malpelo Is",""],
        "HL":["South Korea",""],
        "HM":["North Korea",""],
        "HN":["Iraq","AS"],
        "HO":["Panama","SA"],
        "HP":["Panama","SA"],
        "HQ":["Honduras","SA"],
        "HR":["Honduras","SA"],
        "HS":["Thailand","AS"],
        "HT":["Nicaragua","SA"],
        "HU":["El Salvador","SA"],
        "HV":["Vatican City","EU"],
        "HW":["France","EU"],
        "HX":["France","EU"],
        "HY":["France","EU"],
        "HZ":["Saudi Arabia",""],
        "I0":["Italy","EU"],
        "I1":["Italy","EU"],
        "I2":["Italy","EU"],
        "I3":["Italy","EU"],
        "I4":["Italy","EU"],
        "I5":["Italy","EU"],
        "I6":["Italy","EU"],
        "I7":["Italy","EU"],
        "I8":["Italy","EU"],
        "I9":["Italy","EU"],
        "I":["Italy","EU"],
        "IA":["Italy","EU"],
        "IB":["Italy","EU"],
        "IC":["Italy","EU"],
        "ID":["Italy","EU"],
        "IE":["Italy","EU"],
        "IF":["Italy","EU"],
        "IG":["Italy","EU"],
        "IH":["Italy","EU"],
        "II":["Italy","EU"],
        "IJ":["Italy","EU"],
        "IK":["Italy","EU"],
        "IL":["Italy","EU"],
        "IM":["Italy","EU"],
        "IN":["Italy","EU"],
        "IO":["Italy","EU"],
        "IP":["Italy","EU"],
        "IQ":["Italy","EU"],
        "IR":["Italy","EU"],
        "IS":["Sardinia","EU"],
        "IT":["Sicily","EU"],
        "IU":["Italy","EU"],
        "IV":["Italy","EU"],
        "IW":["Italy","EU"],
        "IX":["Italy","EU"],
        "IY":["Italy","EU"],
        "IZ":["Italy","EU"],
        "J2":["Djibouti",""],
        "J2/A":["Abu Ail",""],
        "J3":["Grenada",""],
        "J4":["Greece","EU"],
        "J45":["Dodecanese",""],
        "J49":["Crete","EU"],
        "J5":["Guinea Bissau",""],
        "J6":["St Lucia",""],
        "J7":["Dominica",""],
        "J8":["St Vincent",""],
        "JA":["Japan",""],
        "JB":["Japan",""],
        "JC":["Japan",""],
        "JD":["Minami Torishima",""],
        "JD":["Ogasawara ",""],
        "JD/O":["Ogasawara",""],
        "JE":["Japan","AS"],
        "JF":["Japan","AS"],
        "JG":["Japan","AS"],
        "JH":["Japan","AS"],
        "JI":["Japan","AS"],
        "JJ":["Japan","AS"],
        "JK":["Japan","AS"],
        "JL":["Japan","AS"],
        "JM":["Japan","AS"],
        "JN":["Japan","AS"],
        "JO":["Japan","AS"],
        "JP":["Japan","AS"],
        "JQ":["Japan","AS"],
        "JR":["Japan","AS"],
        "JS":["Japan","AS"],
        "JT":["Mongolia ","AS"],
        "JU":["Mongolia","AS"],
        "JV":["Mongolia","AS"],
        "JW":["Svalbard Is",""],
        "JX":["Jan Mayen",""],
        "JY":["Jordan","AS"],
        "K":["USA","NA"],
        "K1":["USA","NA"],
        "K2":["USA","NA"],
        "K3":["USA","NA"],
        "K4":["USA","NA"],
        "K5":["USA","NA"],
        "K6":["USA","NA"],
        "K7":["USA","NA"],
        "K8":["USA","NA"],
        "K9":["USA","NA"],
        "KA":["USA","NA"],
        "KB":["USA","NA"],
        "KC":["USA","NA"],
        "KD":["USA","NA"],
        "KE":["USA","NA"],
        "KF":["USA","NA"],
        "KG":["USA","NA"],
        "KH":["USA","NA"],
        "KI":["USA","NA"],
        "KJ":["USA","NA"],
        "KK":["USA","NA"],
        "KL":["USA  Alaska","NA"],
        "KM":["USA","NA"],
        "KN":["USA","NA"],
        "KO":["USA","NA"],
        "KP":["USA","NA"],
        "KQ":["USA","NA"],
        "KR":["USA","NA"],
        "KS":["USA","NA"],
        "KT":["USA","NA"],
        "KU":["USA","NA"],
        "KV":["USA","NA"],
        "KW":["USA","NA"],
        "KX":["USA","NA"],
        "KY":["USA","NA"],
        "KZ":["USA","NA"],
        "KA-KZ":["USA","NA"],
        "KC4":["Antarctica Bryd",""],
        "KC4":["Antarctica McMurdo",""],
        "KC4":["Antarctica Palmer",""],
        "KC6":["East Carolines",""],
        "KC6":["West Carolines",""],
        "KC6/E":["East Caroline",""],
        "KC6/W":["West Carolines",""],
        "KG4":["USA OR Guantanamo Bay",""],
        "KG6":["Guam",""],
        "KH0":["Mariana Is",""],
        "KH1":["Baker Howland",""],
        "KH2":["Guam",""],
        "KH3":["Johnston Is",""],
        "KH4":["Midway Is",""],
        "KH5":["Palmyra Is",""],
        "KH5K":["Kingman Reef",""],
        "KH6":["Hawaii",""],
        "KH6":["Hawaii",""],
        "KH7":["Kure Is",""],
        "KH7K":["Kure Is",""],
        "KH8":["American Samoa",""],
        "KH9":["Wake Is",""],
        "KL":["Alaska",""],
        "KP1":["Navassa Is",""],
        "KP2":["Virgin Is",""],
        "KP3":["Puerto Rico",""],
        "KP4":["Puerto Rico",""],
        "KP5":["Desecheo Is",""],
        "KV4":["Virgin Is",""],
        "L1":["Argentina",""],
        "L2":["Argentina",""],
        "L3":["Argentina",""],
        "L4":["Argentina",""],
        "L5":["Argentina",""],
        "L6":["Argentina",""],
        "L7":["Argentina",""],
        "L8":["Argentina",""],
        "L9":["Argentina",""],
        "LA- LN":["Norway ","EU"],
        "LA":["Norway ","EU"],
        "LB":["Norway ","EU"],
        "LC":["Norway ","EU"],
        "LD":["Norway ","EU"],
        "LE":["Norway ","EU"],
        "LF":["Norway ","EU"],
        "LG":["Norway ","EU"],
        "LH":["Norway ","EU"],
        "LI":["Norway ","EU"],
        "LJ":["Norway ","EU"],
        "LK":["Norway ","EU"],
        "LL":["Norway ","EU"],
        "LM":["Norway ","EU"],
        "LN":["Norway ","EU"],
        "LO":["Argentina",""],
        "LP":["Argentina",""],
        "LQ":["Argentina",""],
        "LR":["Argentina",""],
        "LS":["Argentina",""],
        "LT":["Argentina",""],
        "LU":["Argentina",""],
        "LV":["Argentina",""],
        "LW":["Argentina",""],
        "LX":["Luxembourg","EU"],
        "LY":["Lithuania ","EU"],
        "LZ":["Bulgaria","EU"],
        "M1":["San Marino","EU"],
        "M":["England","EU"],
        "MC":["Wales (Clubs)","EU"],
        "MD":["Isle of Man","EU"],
        "MH":["Jersey (Clubs)","EU"],
        "MI":["Northern Ireland","EU"],
        "MJ":["Jersey","EU"],
        "MM":["Scotland","EU"],
        "MN":["Northern Ireland (Clubs)","EU"],
        "MP":["Guernsey & Dependencies(Clubs)",""],
        "MS":["Scotland (Clubs)","EU"],
        "MT":["Isle Of Man (Clubs)","EU"],
        "MU":["Guernsey & Dependencies","EU"],
        "MW":["Wales","EU"],
        "MX":["England (Clubs)","EU"],
        "N":["USA","NA"],
        "N1":["USA","NA"],
        "N2":["USA","NA"],
        "N3":["USA","NA"],
        "N4":["USA","NA"],
        "N5":["USA","NA"],
        "N6":["USA","NA"],
        "N7":["USA","NA"],
        "N8":["USA","NA"],
        "N9":["USA","NA"],
        "NA-NZ":["USA","NA"],
        "NA":["USA","NA"],
        "NB":["USA","NA"],
        "NC":["USA","NA"],
        "ND":["USA","NA"],
        "NE":["USA","NA"],
        "NF":["USA","NA"],
        "NG":["USA","NA"],
        "NH":["USA","NA"],
        "NI":["USA","NA"],
        "NJ":["USA","NA"],
        "NK":["USA","NA"],
        "NL":["USA Alaska","NA"],
        "NM":["USA","NA"],
        "NN":["USA","NA"],
        "NO":["USA","NA"],
        "NP":["USA","NA"],
        "NQ":["USA","NA"],
        "NR":["USA","NA"],
        "NS":["USA","NA"],
        "NT":["USA","NA"],
        "NU":["USA","NA"],
        "NV":["USA","NA"],
        "NW":["USA","NA"],
        "NX":["USA","NA"],
        "NY":["USA","NA"],
        "NZ":["USA","NA"],
        "NC6":["Eastern Carolines",""],
        "NC6":["Western Carolines",""],
        "NH0":["Mariana Is",""],
        "NH1":["Baker Howland",""],
        "NH2":["Guam",""],
        "NH3":["Johnston Is",""],
        "NH4":["Midway Is",""],
        "NH5":["Palmyra Is",""],
        "NH5K":["Kingman Reef",""],
        "NH6":["Hawaii",""],
        "NH6":["Hawaii",""],
        "NH7K":["Kure Is",""],
        "NH8":["American Samoa",""],
        "NH9":["Wake Is",""],
        "NL":["Alaska",""],
        "NP1":["Navassa Is","SA"],
        "NP2":["Virgin Is","So"],
        "NP3":["Puerto Rico","Mo"],
        "NP4":["Puerto Rico","Di"],
        "NP5":["Desecheo Is","Mi"],
        "OA":["Peru","Do"],
        "OB":["Peru","Fr"],
        "OC":["Peru","Sa"],
        "OD":["Lebanon","AS"],
        "OE":["Austria","EU"],
        "OF":["Finland","EU"],
        "OF0":["Aland Is","EU"],
        "OG":["Finland","EU"],
        "OG0":["Aland Is","EU"],
        "OH":["Finland","EU"],
        "OH0":["Aland Is","EU"],
        "OH0M":["Market Reef ","EU"],
        "OI":["Finland","EU"],
        "OJ0":["Market Reef ","EU"],
        "OK":["Czech Republic","EU"],
        "OL":["Czech Republic","EU"],
        "OM":["Slovakia","EU"],
        "ON":["Belgium ","EU"],
        "OO":["Belgium","EU"],
        "OP":["Belgium","EU"],
        "OQ":["Belgium","EU"],
        "OR":["Belgium","EU"],
        "OS":["Belgium","EU"],
        "OT":["Belgium","EU"],
        "OX":["Greenland",""],
        "OY":["Faroe Is",""],
        "OZ":["Denmark","EU"],
        "P2":["Papua",""],
        "P3":["Cyprus","EU"],
        "P30":["Cyprus","EU"],
        "P36":["Cyprus","EU"],
        "P4":["Aruba",""],
        "P5":["North Korea","AS"],
        "P6":["North Korea","AS"],
        "P7":["North Korea","AS"],
        "P8":["North Korea","AS"],
        "P9":["North Korea","AS"],
        "PA":["Netherlands","EU"],
        "PB":["Netherlands","EU"],
        "PC":["Netherlands","EU"],
        "PD":["Netherlands","EU"],
        "PE":["Netherlands","EU"],
        "PF":["Netherlands","EU"],
        "PG":["Netherlands","EU"],
        "PH":["Netherlands","EU"],
        "PI":["Netherlands","EU"],
        "PJ":["Netherlands Antilles St Maarten","SA"],
        "PJ0":["Neth Antilles","SA"],
        "PJ1":["Neth Antilles","SA"],
        "PJ2":["Neth Antilles","SA"],
        "PJ3":["Neth Antilles","SA"],
        "PJ4":["Neth Antilles","SA"],
        "PJ5":["St Maarten","SA"],
        "PJ7":["St Maarten","SA"],
        "PJ9":["Neth Antilles","SA"],
        "PK":["Indonesia","AS"],
        "PL":["Indonesia","AS"],
        "PM":["Indonesia","AS"],
        "PN":["Indonesia","AS"],
        "PO":["Indonesia","AS"],
        "PP":["Brazil","SA"],
        "PQ":["Brazil","SA"],
        "PQ":["Brazil","SA"],
        "PR":["Brazil","SA"],
        "PS":["Brazil","SA"],
        "PT":["Brazil","SA"],
        "PU":["Brazil","SA"],
        "PY":["Brazil  (Also See Awards)","SA"],
        "PZ":["Suriname",""],
        "R0":["Russia","AS"],
        "R1":["Russia","EU"],
        "R2":["Russia","AS"],
        "R3":["Russia","EU"],
        "R4":["Russia","EU"],
        "R5":["Russia","EU"],
        "R6":["Russia","EU"],
        "R7":["Russia","AS"],
        "R8":["Russia","AS"],
        "R9":["Russia","AS"],
        "RA":["Russia","EU"],
        "RB":["Russia","EU"],
        "RC":["Russia","EU"],
        "RD":["Russia","EU"],
        "RE":["Russia","EU"],
        "RF":["Russia","EU"],
        "RD":["Russia","EU"],
        "RE":["Russia","EU"],
        "RF":["Russia","EU"],
        "RG":["Russia","EU"],
        "RH":["Russia","EU"],
        "RI":["Russia","EU"],
        "RJ":["Russia","EU"],
        "RK":["Russia","EU"],
        "RL":["Russia","EU"],
        "RM":["Russia","EU"],
        "RN":["Russia","EU"],
        "RO":["Russia","EU"],
        "RP":["Russia","EU"],
        "RQ":["Russia","EU"],
        "RR":["Russia","EU"],
        "RS":["Russia","EU"],
        "RT":["Russia","EU"],
        "RU":["Russia","EU"],
        "RV":["Russia","EU"],
        "RW":["Russia","EU"],
        "RX":["Russia","EU"],
        "RY":["Russia","EU"],
        "RZ":["Russia","EU"],
        "S0":["Western Sahara","AF"],
        "S2":["Bangladesh","AS"],
        "S3":["Bangladesh","AS"],
        "S4":["South Africa","AF"],
        "S5":["Slovenia","EU"],
        "S7":["Seychelles",""],
        "S8":["South Africa","AF"],
        "S9":["Sao Tome",""],
        "SI":["Sweden","EU"],
        "SJ":["Sweden","EU"],
        "SK":["Sweden","EU"],
        "SL":["Sweden","EU"],
        "SM":["Sweden","EU"],
        "SN":["Poland","EU"],
        "SO":["Poland","EU"],
        "SP":["Poland","EU"],
        "SQ":["Poland","EU"],
        "ST":["Sudan",""],
        "ST0":["Southern Sudan",""],
        "SU":["Egypt",""],
        "SV":["Greece","EU"],
        "SV/A":["Mount Athos","EU"],
        "SV5":["Dodecanese","EU"],
        "SV9":["Crete","EU"],
        "SW":["Greece","EU"],
        "SW5":["Dodecanese","EU"],
        "SW9":["Crete","EU"],
        "SX":["Greece","EU"],
        "SX5":["Dodecanese","EU"],
        "SX9":["Crete","EU"],
        "SY":["Mount Athos","EU"],
        "T2":["Tuvalu",""],
        "T3":["Banaba Is",""],
        "T3":["Central Kiribati",""],
        "T3":["East Kiribati",""],
        "T3":["West Kiribati",""],
        "T30":["West Kiribati",""],
        "T31":["Central Kiribati",""],
        "T32":["East Kiribati",""],
        "T33":["Banaba Is",""],
        "T4":["Cuba","NA"],
        "T5":["Somalia",""],
        "T6":["Afghanistan","AS"],
        "T7":["San Marino","EU"],
        "T8":["So Africa","AF"],
        "T88":["Belau (Palau)(KC6)",""],
        "T9":["Bosnia Herzegovina","EU"],
        "TA":["Turkey","AS"],
        "TD":["Guatemala","SA"],
        "TE":["Costa Rica","SA"],
        "TF":["Iceland","EU"],
        "TG":["Guatemala","SA"],
        "TH":["France","EU"],
        "TI":["Costa Rica","SA"],
        "TI9":["Cocos Is",""],
        "TJ":["Cameroon",""],
        "TK":["Corsica","EU"],
        "TL":["Central Africa Rep",""],
        "TM":["France/Europe (Outside France) mostly used during contests.",""],
        "TN":["Congo","AF"],
        "TO":["France (Outside France) -- TO is for DOM (Departements d'outre-mer)",""],
        "TO5M":["St. Pierre Miquelon (Typical Assignment)",""],
        "TP":["France EU Straßburg","EU"],
        "TQ":["France","EU"],
        "TR":["Gabon",""],
        "TT":["Chad","AS"],
        "TU":["Ivory Coast",""],
        "TV":["France","EU"],
        "TW":["France","EU"],
        "TX":["France -- TX is for TOM (Territoires d'outre-mer)",""],
        "TY":["Benin",""],
        "TZ":["Mali",""],
        "U0":["Russia",""],
        "U1":["Russia","EU"],
        "U2":["Russia",""],
        "U3":["Russia","EU"],
        "U4":["Russia","EU"],
        "U5":["Russia","EU"],
        "U6":["Russia","EU"],
        "U7":["Russia","EU"],
        "U8":["Russia","EU"],
        "U9":["Russia","EU"],
        "UA":["Russia","EU"],
        "UB":["Russia","EU"],
        "UC":["Russia","EU"],
        "UD":["Russia","EU"],
        "UE":["Russia","EU"],
        "UF":["Russia","EU"],
        "UG":["Russia","EU"],
        "UH":["Russia","EU"],
        "UI":["Russia","EU"],
        "UJ":["Uzbekistan","AS"],
        "UK":["Uzbekistan","AS"],
        "UL":["Uzbekistan","AS"],
        "UM":["Uzbekistan","AS"],
        "UN":["Kazakhstan","AS"],
        "UO":["Kazakhstan","AS"],
        "UP":["Kazakhstan","AS"],
        "UQ":["Kazakhstan","AS"],
        "UR":["Ukraine","EU"],
        "US":["Ukraine","EU"],
        "UT":["Ukraine","EU"],
        "UU":["Ukraine","EU"],
        "UV":["Ukraine","EU"],
        "UW":["Ukraine","EU"],
        "UX":["Ukraine","EU"],
        "UY":["Ukraine","EU"],
        "UZ":["Ukraine","EU"],
        "V2":["Antigua",""],
        "V3":["Belize",""],
        "V4":["St Kitts",""],
        "V5":["Namibia","AF"],
        "V50":["Namibia","AF"],
        "V51":["Namibia","AF"],
        "V6":["Fed Micronesia",""],
        "V63":["Fed Micronesia",""],
        "V7":["Marshall Is",""],
        "V73":["Marshall Is",""],
        "V8":["Brunei","AS"],
        "V85":["Brunei","AS"],
        "VA":["Canada","NA"],
        "VB":["Canada","NA"],
        "VC":["Canada","NA"],
        "VD":["Canada","NA"],
        "VE":["Canada","NA"],
        "VF":["Canada","NA"],
        "VG":["Canada","NA"],
        "VH":["Australia","AU"],
        "VI":["Australia","AU"],
        "VJ":["Australia","AU"],
        "VK":["Australia","AU"],
        "VK0":["Heard Is","AU"],
        "VK0":["Macquarie Is","AU"],
        "VK1":["Australia","AU"],
        "VK2":["Australia","AU"],
        "VK3":["Australia","AU"],
        "VK4":["Australia","AU"],
        "VK5":["Australia","AU"],
        "VK6":["Australia","AU"],
        "VK7":["Australia","AU"],
        "VK8":["Australia","AU"],
        "VK9":["Australia","AU"],
        "VL":["Australia","AU"],
        "VM":["Australia","AU"],
        "VN":["Australia","AU"],
        "VO":["Canada","NA"],
        "VP":["GB Islands ",""],
        "VQ":["GB Chagos","AS"],
        "VR":["China","AS"],
        "VR2":["Hong Kong","AS"],
        "VR6":["Was Pitcairn Is -- Now China","AS"],
        "VS6":["Hong Kong","AS"],
        "VT":["India","AS"],
        "VU":["India","AS"],
        "VU4":["Andaman Is","AS"],
        "VU7":["Laccadive Is","AS"],
        "VV":["India","AS"],
        "VW":["India","AS"],
        "VX":["Canada","NA"],
        "VY":["Canada","NA"],
        "VZ":["Australia","AU"],
        "W0":["USA","NA"],
        "W1":["USA","NA"],
        "W2":["USA","NA"],
        "W3":["USA","NA"],
        "W4":["USA","NA"],
        "W5":["USA","NA"],
        "W6":["USA","NA"],
        "W7":["USA","NA"],
        "W8":["USA","NA"],
        "W9":["USA","NA"],
        "WA":["USA","NA"],
        "WB":["USA","NA"],
        "WC":["USA","NA"],
        "WD":["USA","NA"],
        "WE":["USA","NA"],
        "WF":["USA","NA"],
        "WG":["USA","NA"],
        "WH":["USA","NA"],
        "WI":["USA","NA"],
        "WJ":["USA","NA"],
        "WK":["USA","NA"],
        "WL":["USA","NA"],
        "WM":["USA","NA"],
        "WN":["USA","NA"],
        "WO":["USA","NA"],
        "WP":["USA","NA"],
        "WQ":["USA","NA"],
        "WR":["USA","NA"],
        "WR":["USA","NA"],
        "WS":["USA","NA"],
        "WT":["USA","NA"],
        "WU":["USA","NA"],
        "WV":["USA","NA"],
        "WW":["USA","NA"],
        "WX":["USA","NA"],
        "WY":["USA","NA"],
        "WZ":["USA","NA"],
        "WL":["Alaska",""],
        "X5":["Bosnia Herzegovina (Unofficial???)","EU"],
        "XA":["Mexico","NA"],
        "XB":["Mexico","NA"],
        "XC":["Mexico","NA"],
        "XD":["Mexico","NA"],
        "XE":["Mexico","NA"],
        "XF":["Mexico","NA"],
        "XG":["Mexico","NA"],
        "XH":["Mexico","NA"],
        "XJ":["Canada","NA"],
        "XK":["Canada","NA"],
        "XL":["Canada","NA"],
        "XM":["Canada","NA"],
        "XN":["Canada","NA"],
        "XO":["Canada","NA"],
        "XP":["Denmark","EU"],
        "XQ":["Chile","SA"],
        "XR":["Chile","SA"],
        "XS":["China","AS"],
        "XT":["Burkina Faso","AS"],
        "XU":["Kampuchea","AS"],
        "XV":["Vietnam","AS"],
        "XW":["Laos","AS"],
        "XX":["Macao","AS"],
        "XY":["Burma","AS"],
        "XZ":["Burma","AS"],
        "Y2":["Germany","EU"],
        "Y3":["Germany","EU"],
        "Y4":["Germany","EU"],
        "Y5":["Germany","EU"],
        "Y6":["Germany","EU"],
        "Y7":["Germany","EU"],
        "Y8":["Germany","EU"],
        "Y9":["Germany","EU"],
        "Y90":["Antarctica","AN"],
        "YA":["Afghanistan","AS"],
        "YB":["Indonesia","AS"],
        "YC":["Indonesia","AS"],
        "YD":["Indonesia","AS"],
        "YE":["Indonesia","AS"],
        "YF":["Indonesia","AS"],
        "YG":["Indonesia","AS"],
        "YH":["Indonesia","AS"],
        "YI":["Iraq","AS"],
        "YJ":["Vanuatu","AS"],
        "YK":["Syria","AS"],
        "YL":["Latvia","AS"],
        "YM":["Turkey","AS"],
        "YN":["Nicaragua","SA"],
        "YO":["Romania","EU"],
        "YP":["Romania","EU"],
        "YQ":["Romania","EU"],
        "YR":["Romania","EU"],
        "YS":["El Salvador","SA"],
        "YT":["Yugoslavia","EU"],
        "YT1":["Yugoslavia","EU"],
        "YT4":["Bosnia Herzegovina","EU"],
        "YT5":["Macedonia","EU"],
        "YT6":["Yugoslavia","EU"],
        "YT7":["Yugoslavia","EU"],
        "YT8":["Yugoslavia","EU"],
        "YU":["Yugoslavia","EU"],
        "YU1":["Yugoslavia","EU"],
        "YU4":["Bosnia Herzegovina","EU"],
        "YU5":["Macedonia","EU"],
        "YU6":["Yugoslavia","EU"],
        "YU7":["Yugoslavia","EU"],
        "YU8":["Yugoslavia","EU"],
        "YV":["Venezuela","SA"],
        "YV0":["Aves Is","So"],
        "YW":["Venezuela","Mo"],
        "YX":["Venezuela","Di"],
        "YX0":["Aves Is","Mi"],
        "YY":["Venezuela","Do"],
        "YZ":["Yugoslavia","EU"],
        "YZ4":["Bosnia Herzegovina","EU"],
        "YZ5":["Macedonia","EU"],
        "Z2":["Zimbabwe","AF"],
        "Z3":["Macedonia","EU"],
        "ZA":["Albania","EU"],
        "ZB":["Gibraltar","EU"],
        "ZC4":["UK Soverign Base",""],
        "ZD7":["St Helena",""],
        "ZD8":["Ascension Is",""],
        "ZD9":["Tristan Da Cunha",""],
        "ZE":["Zimbabwe","AF"],
        "ZF":["Cayman Is",""],
        "ZK1/N":["No Cook Is",""],
        "ZK1/S":["So Cook Is",""],
        "ZK2":["Niue Is",""],
        "ZK3":["Tokelaus",""],
        "ZL":["New Zealand","AU"],
        "ZL0":["Antarctica Scott","AU"],
        "ZL5":["Antarctica Scott","AU"],
        "ZL7":["Chatham Is","AU"],
        "ZL8":["Kermadec Is","AU"],
        "ZL9":["Auckland Campbell ","AU"],
        "ZM":["New Zealand","AU"],
        "ZM7":["Chatham Is","AU"],
        "ZM8":["Kermadec Is","AU"],
        "ZM9":["Auckland Campbell","AU"],
        "ZP":["Paraguay","SA"],
        "ZS":["So Africa","AF"],
        "ZS2":["Marion Is","AF"],
        "ZS3":["Namibia","AF"],
        "ZS8":["Marion Is","AF"],
        "ZS9":["Walvis Bay","AF"],
        "ZU":["So Africa","AF"],
        "ZV":["Brazil","SA"],
        "ZW":["Brazil","SA"],
        "ZX":["Brazil","SA"],
        "ZX0F":["Fer De Noronha",""],
        "ZX0S":["Peter Paul Rocks",""],
        "ZX0T":["Trindade",""],
        "ZY":["Brazil","SA"],
        "ZY0F":["Fer De Noronha",""],
        "ZY0S":["Peter Paul Rocks",""],
        "ZY0T":["Trindade",""],
        "ZZ":["Brazil","SA"],
        "ZZ0F":["Fer De Noronha",""],
        "ZZ0S":["Peter Paul Rocks",""],
        "ZZ0T":["Trindade",""]
        }
        
        # Check Mode
        if dbMode == "overwrite":
            print ("overwrite")
            curs.execute("DROP TABLE IF EXISTS stations")
            curs.execute("CREATE TABLE stations (freq integer, station text, locator text, country text, continent text )")
        
        if dbMode == "append":
            # nothing to do
            print ("append")
        
        # Read Data
        for line in fobjFileIn:
            line = line.strip()
            
            # Check if at least first 4 letters are digits
            line1 = line[0:4]
            if line1.isdigit():
                strFreq = line[0:8].strip()
                # in case instead of "." is "," or ";" assume it should be a dot.
                strFreq = re.sub(r"[,;]",".",strFreq)
                # Check if frequency has hz value. If true split it.
                if strFreq.count("."):
                    (strFreqK, strFreqH) = strFreq.split(".")
                    # Check if there is a none digit, eliminate it.
                    strFreqH = re.sub(r"[^0-9]","",strFreqH)
                    # Check if no. of decimals is 1, in this case add one 0
                    if len(strFreqH) == 1:
                        strFreqH = strFreqH + "00"
                    # Check if no. of decimals is 2
                    if len(strFreqH) == 2:
                        strFreqH = strFreqH + "0"
                else:
                    strFreqK = strFreq
                    strFreqH = "000"
                            
                # Check if there is a none digit, eliminate it.    
                strFreqK = re.sub(r"[^0-9]","",strFreqK)
                
                strFreq = strFreqK + strFreqH
                intFreq = int(strFreq)
                
                strStation = line[8:16].strip()
                
                strCoHelp = strStation[:2].strip()
                
                if (strCoHelp in dicCountry):
                    (strCountry, strCont) = dicCountry[strCoHelp]
                else:
                    strCountry = "undef"
                    strCont = "undef"
                
                strLoc = line[31:37].strip()
                
                # DB Insert
                strFreq = strFreqK + strFreqH
                curs.execute("INSERT INTO stations VALUES (?, ?, ?, ?, ?);", (intFreq, strStation, strLoc, strCountry, strCont))
                
                strData = str(intFreq) + ";" + strStation + ";" + strCoHelp + ";" + strLoc + ";" + strCountry + ";" + strCont + "\n"
                print(strData)
                fobjFileOut.write(strData)
        
        # Commit and close DB
        conn.commit()
        conn.close()
        # Close
        fobjFileIn.close()
        
        return

        



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


