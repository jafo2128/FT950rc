#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  read_beacon_list.py
#  
#  Copyright 2016 michael <michael@idefix>
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
#  
import os
import re
import sqlite3

def ReadG3USF(strFileIn, dbStations, dbMode):
    
    fobjFileIn = open(strFileIn, "r")
    fobjFileOut = open("beacon_list.txt", "a")
    conn = sqlite3.connect(dbStations)
    curs = conn.cursor()

    # Check Mode
    if dbMode == "overwrite":
        print ("overwrite")
        curs.execute("DROP TABLE IF EXISTS stations")
        curs.execute("CREATE TABLE stations (freq integer, station text, locator text, ) ")
        
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
            #strFreq = strFreqK + strFreqH
            strStation = line[8:16].strip()
            strLoc = line[31:37].strip()
            
            if upper(strLoc[:4]) != "WSPR":
                # DB Insert
                
                curs.execute("INSERT INTO stations VALUES (?, ?, ?);", (intFreq, strStation, strLoc))
                
                strData = str(intFreq) + ";" + strStation + ";" + strLoc + "\n"
                #print(strData)
                print(upper(strLoc[:4]))
                fobjFileOut.write(strData)
    
    # Commit and close DB
    conn.commit()
    conn.close()
    # Close
    fobjFileIn.close()
    
    return


# Get Working Path
strPath = os.getcwd()

# DB
dbStations = "beacons.db"

# Input1
dbMode = "overwrite"
strFileIn = "G3USF's Worldwide List of HF Beacons.htm"
test = ReadG3USF(strFileIn, dbStations, dbMode)

# Input2
dbMode = "append"
strFileIn = "G3USF's Worldwide List of 50MHz Beacons.htm"
ReadG3USF(strFileIn, dbStations, dbMode)


def main(args):
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
