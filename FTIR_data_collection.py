# -*- coding: utf-8 -*-
"""
Created on Thu Oct  7 10:13:07 2021

@author: Nathan Drouillard

Made from Jul30_Arduino.py

"""
#%%
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import time
import serial
import pickle
import pandas as pd

plt.close('all')

#%%
# Major / "global" variables to change
global TRUE, FALSE
TRUE = 1
FALSE = 0
Nt = 5000
directory = "C:/Users/natha/OneDrive/Documents/ACME/Arduino Data/"
timestr = time.strftime("%Y%m%d-%H%M%S")
# now = str(datetime.now())
suffix = "_original.pickle"
suffix2 = "_apodized.pickle"
filepath0 = directory + timestr
filepath1 = filepath0 + suffix
filepath2 = filepath0 + suffix2

# ser = serial.Serial('/dev/ttyUSB_MICRONIX',38400)
ser = serial.Serial('COM4',38400,timeout=10)
ser2 = serial.Serial('COM6', 2000000) 

#%% Data I/O

now = datetime.now() # current date and time
year = now.strftime("%Y")
print("year:", year)
month = now.strftime("%m")
print("month:", month)
day = now.strftime("%d")
print("day:", day)
tim = now.strftime("%H:%M:%S")
print("time:", tim)
date_time = now.strftime("%Y-%m-%d_%H_%M_%S")

#%% Micronix Stuff

#Home the stage
def home():

    # ser.write(b'1ENC0.001\r') #set encoder resolution 
    # ser.flush()
    # ser.write(b'1REZx\r') #set DAC steps/micron resolution
    # ser.flush()
    ser.write(b'1FBK3\r')
    ser.flush()
    time.sleep(1)
    ser.write(b'1HOM\r') #home the stage
    ser.flush()
    time.sleep(1)
    #ser.write(b'1WTM42\r')
    ser.write(b'1WST\r')
    time.sleep(1)
    print("stopped")
    ser.flush()
    ser.write(b'1ZRO\r') #zero the stage
    time.sleep(1)
    ser.flush()
    print("zeroed")
    
def params():
    # min_pos = float(startpos.get())
    # max_pos = float(stoppos.get())

    ser.write(b'1VEL2.5\r') #set velocity to 5 mm/s
    time.sleep(1)
    ser.flush()
    #velset = ser.readline()
    #print("velset")
    ser.write(b'1ACC500\r')
    ser.flush()

    ser.write(b'1EPL1\r') #ensure the correct encoder polarity for the feedback loop
    ser.flush()
    #polset = ser.readline()
    ser.write(b'1FBK3\r') #closed loop feedback mode
    ser.flush()
    #fbkset = ser.readline()
    ser.write(b'1DBD0,0\r') #set closed loop deadband parameters (0 means it will never timeout)
    ser.flush()
    time.sleep(1)
    ser.write(b'1SAV\r')
    ser.flush()
    time.sleep(1)
    #print("Params set")
    #dbdset = ser.readline()

# Close COM port (important)
def close():

    ser.close()

#%%
whole_set = np.empty(1)
y_avg = np.empty(1)
DATA = 0
pos_array = np.empty(1)
tic = time.time()
time.sleep(0.5)
old_y1 = 0
step_size_array = np.empty(1)
params()
home()
 
for i in range(0,Nt):
    
    ser.write(b'1MVR-0.000099\r') #move by x mm in positive direction #0.00004/1.208
    ser.flush()
    ser.write(b'1WST\r')
    ser.flush()
    ser.write(b'1WST\r')
    ser.flush()
    
    value = ser2.readline() #read voltage from Arduino
    val_str = str(value)
    count_decimals = val_str.count('.')
    count_slashes = val_str.count('\\')
        
    if len(val_str) >=8 and len(val_str) < 17 and count_decimals < 2 and count_slashes < 3:
        w = val_str.strip("'b")
        z = w[:-4]
        y1 = float(z)
    else:
        y1 = old_y1
        print("Bad value")
        
    whole_set = np.append(whole_set,y1) #append voltage reading to master array of voltages
    
    ser.write(b'1POS?\r') #read position of the stage
    pos = ser.readline()
    pos_str = str(pos)
    pos_splt = pos.strip().split(b",")
    enc_pos_str = pos_splt[1]
    enc_pos_val = float(enc_pos_str)
    #print(enc_pos_val)
    pos_array = np.append(pos_array, enc_pos_val) #append position value to master array of positions
    ser.flush()
    step_size = pos_array[i] - pos_array[i-1]
    step_size_array = np.append(step_size_array, step_size)

toc = time.time()
toe = toc-tic
print('Time taken:', toe)

#close both serial ports 
ser.close()
ser2.close()

#%% Calculate wavenumbers and spectrum

whole_set = whole_set[427:]#get rid of garbage at beginning that always shows up
pos_array = pos_array[427:]
pos_array = pos_array*2
d = (pos_array)/10 #multiply by 2 for OPD, then divide by 10 to convert mm to cm for wavenumbers
y_good = whole_set

ddelay = (d[1] - d[0])
dwavnum = 2*np.pi/(len(whole_set)*ddelay)
wavnum1 = np.arange(-(len(whole_set)-1)*dwavnum/2,(len(whole_set))*dwavnum/2,dwavnum)
volts_fft = np.fft.fftshift(np.fft.fft(np.fft.ifftshift(whole_set)))

#%% Data for File I/O

df = pd.DataFrame({"OPD (mm)" : pos_array, "Voltage (mV)" : whole_set, 'Wavenumber (1/cm)': wavnum1, 'Spectral Amplitude':volts_fft})
df.to_csv(r"C:/Users/natha/OneDrive/Documents/ACME/Arduino Data/" + date_time + ".csv", index=False)

#%% Plot original signal and spectrum
fig0, axs = plt.subplots(2, 1)
fig0.suptitle('Voltage-Delay Interferogram')
axs[0].plot(pos_array,whole_set,'.-', label = '')
axs[0].set_xlabel('Delay (mm)')
axs[0].set_ylabel('Voltage (mV)')
axs[0].grid(True)
axs[1].plot(wavnum1,np.log(np.abs(volts_fft)))
axs[1].axvline(x=15797.79, ymin=-12, ymax=12, color = 'r', label = 'HeNe wavenumber')
axs[1].set_xlabel('Wavenumber (1/cm)')
axs[1].set_ylabel('Logarithm of Amplitude (a.u.)')
axs[1].grid(True)
for ax in axs:
    ax.legend()

# pickle.dump(fig0, open(filepath1, 'wb'))



