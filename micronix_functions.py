# -*- coding: utf-8 -*-
"""
Created on Fri Jan 15 15:19:44 2021

@author: Nathan Drouillard
"""

import serial

#%% Open the COM port

ser = serial.Serial('COM3',38400,timeout=10)

#%% Home the stage

def home():
    
    ser.write(b'1HOM\r')
    ser.write(b'1WST\r')
    ser.flush()
    isstopped = ser.readline()
    print(isstopped)
    print("homed")
    ser.write(b'1ZRO\r')
    ser.flush()
    zeroed = ser.readline()
    print("zeroed")

#%% Setup for feedback loop

def params():
    min_pos = -1
    max_pos = 1
    
    ser.write(b'1VEL5.0\r') #set velocity to 5 mm/s
    ser.flush()
    velset = ser.readline()
    
    min_pos_str = "1TLN" + str(min_pos) + "\r"
    # ser.write(b'1POS?\r')
    # ser.write(b'1MVA0\r')
    min_pos_byt = str.encode(min_pos_str) #encode soft travel limit in the negative direction
    ser.write(min_pos_byt) #write it to the controller
    ser.flush()
    neglim = ser.readline()
    
    max_pos_str = "1TLP" + str(max_pos) + "\r"
    max_pos_byt = str.encode(max_pos_str)
    ser.write(max_pos_byt)
    ser.flush()
    poslim = ser.readline()
    
    ser.write(b'1EPL1\r') #ensure the correct encoder polarity for the feedback loop
    ser.flush()
    polset = ser.readline()
    ser.write(b'1FBK3\r') #closed loop feedback mode
    ser.flush()
    fbkset = ser.readline()
    ser.write(b'4DBD5,0\r') #set closed loop deadband parameters (0 means it will never timeout)
    ser.flush()
    dbdset = ser.readline()

#%% Move the stage (moves one way, but not back and forth)

def move():

    for i in range(0,3):
        # ser.write(b'1PGL0\r') #loop program continuously
        ser.write(b'1MLN\r') #move to negative limit
        # ser.write(b'1MVA-2\r')
        ser.write(b'1WST\r')
        ser.flush()
        movedneg = ser.readline()
        print("moved forward")
        ser.flush()
        # ser.write(b'1WTM5000\r') #wait for 5000 ms
        ser.write(b'1MLP\r') #move to positive limit
        # ser.write(b'1MVA2\r')
        ser.write(b'1WST\r')
        ser.flush()
        movedpos = ser.readline()
        print("moved back")

#%% Close COM port (important)

def close():
    
    ser.close()
    
    

