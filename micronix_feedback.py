# -*- coding: utf-8 -*-
"""
Created on Wed Aug 12 19:13:02 2020

@author: Nathan Drouillard
"""

import serial

#%% Open the COM port

ser = serial.Serial('COM3',38400,timeout=10)

#%% Check velocity

ser.write(b'1VEL?\r')
ser.flush()
velo = ser.readline()
print(velo)

#%% Home the stage

ser.write(b'1HOM\r')
ser.write(b'1WST\r')

#%% Setup for feedback loop

min_pos = -1
max_pos = 1

ser.write(b'1VEL5.0\r') #set velocity to 5 mm/s

min_pos_str = "1TLN" + str(min_pos) + "\r"
ser.write(b'1POS?\r')
# ser.write(b'1MVA0\r')
min_pos_byt = str.encode(min_pos_str) #encode soft travel limit in the negative direction
ser.write(min_pos_byt) #write it to the controller

max_pos_str = "1TLP" + str(max_pos) + "\r"
max_pos_byt = str.encode(max_pos_str)
ser.write(max_pos_byt)

ser.write(b'1EPL1\r') #ensure the correct encoder polarity for the feedback loop
ser.write(b'1FBK3\r') #closed loop feedback mode
ser.write(b'4DBD5,0\r') #set closed loop deadband parameters (0 means it will never timeout)

#%% Check limit status

ser.write(b'1LIM?\r')
ser.flush()
lim = ser.readline()
print(lim)

#%% Move the stage (moves one way, but not back and forth)

# for i in range(0,5):
ser.write(b'1PGL0\r') #loop program continuously
ser.write(b'1MLN\r') #move to negative limit
ser.write(b'1WST\r')
ser.flush()
ser.write(b'1MLP\r') #move to positive limit
ser.write(b'1WST\r')

#%% Second attempt to move back and forth (this method works)

timeout = 5
j = 0
i = 0

# for i in range(0,timeout):
while True:
# while i < timeout:
# ser.write(b'1PGL0\r') #loop program continuously
    try:
        if j == 0:
            ser.write(b'1MLN\r') #move to negative limit
            ser.write(b'1WST\r')
            ser.flush()
            j = 1
            # i = i + 1
        else: 
            ser.write(b'1MLP\r') #move to positive limit
            ser.write(b'1WST\r')
            ser.flush()
            j = 0
            # i = i + 1
    except KeyboardInterrupt:
        pass

#%% Perform a trace (doesn't work)

ser.write(b'1TLN0.005\r')
ser.write(b'1TLP1.000\r')
ser.write(b'1TRA500,1,\r') #axis 1, trace with 50,000 samples at 10/1 kHz
ser.write(b'1DAT?') #dump trace data
ser.flush()
dat = ser.readline()
# ser.write(b'1EXC\r') #execute program

#%% Stop the stage

# ser.write(b'STP\r') #stop
ser.write(b'EST\r') #emergency stop

#%% Close COM port (important)

ser.close()















