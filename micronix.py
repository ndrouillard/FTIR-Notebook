# -*- coding: utf-8 -*-
"""
Created on Thu May 28 23:39:16 2020

@author: TJ Hammond
"""

import serial

ser = serial.Serial('COM3',38400,timeout=10)

#%%

ser.write(b'1VER?\r')
ser.flush()
version = ser.readline()
print(version)

ser.write(b'1WST\r')

#%%
ser.write(b'1VEL?\r')
ser.flush()
velo = ser.readline()
print(velo)

#%%
ser.write(b'1VMX?\r')
ser.flush()
maxvelo = ser.readline()
print(maxvelo)

velonum = float(velo.decode()[2:])

#%%

ser.write(b'1HOM\r')

ser.write(b'1WST\r')

#%%
for count in range(0,40):
    ser.write(b'1POS?\r')
    ser.flush()
    pos1 = float(ser.readline()[-9:])
    print(pos1)

ser.write(b'1WST\r')
#%%

ser.write(b'1ZRO\r')

ser.write(b'1WST\r')

#%%

while True:
    ser.write(b'1POS?\r')
    ser.flush()
    pos2 = ser.readline()
    print(pos2)

ser.write(b'1WST\r')

#%% For closed-loop feedback

ser.write(b'1FBK3\r')

# ser.write(b'1WST\r')

#%% To loop program continuously (not working yet)

ser.write(b'1FBK3\r')
ser.write(b'1PGL0\r') #loops the function continuously
ser.write(b'1POS?\r')
ser.flush()
pos1 = float(ser.readline()[-9:])
print(pos1)
ser.write(b'1WST\r')

#%%

ser.write(b'1FBK?\r')
ser.flush()
isfeedback = ser.readline()
print(isfeedback)
#%%

ser.write(b'1POS?\r')
ser.flush()
pos3 = ser.readline()
print(pos3)
ser.write(b'1WST\r')

#%% Try to take repeated scans (doesn't work)

abspos = 5
abspos2 = 0

while True:
    
    move_abs_str = "1MVA"+ str(abspos) + "\r"
    ser.write(b'1POS?\r')
    # ser.write(b'1MVA0\r')
    move_abs_byt = str.encode(move_abs_str)
    ser.write(move_abs_byt)
    ser.write(b'1WST\r')
    ser.flush()
    
    move_abs_str2 = "1MVA"+ str(abspos2) + "\r"
    ser.write(b'POS?\r')
    move_abs_byt2 = str.encode(move_abs_str2)
    ser.write(move_abs_byt2)
    ser.write(b'1WST\r')
    ser.flush()

ser.write(b'1WST\r')

#%% Check encoder polarity

ser.write(b'nEPL?\r')
ser.flush()
polarity = ser.readline()
print(polarity)

#%%

ser.close()
