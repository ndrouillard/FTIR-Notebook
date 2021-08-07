# -*- coding: utf-8 -*-
"""
Created on Fri Jul 30 15:59:31 2021

@author: natha
"""

# -*- coding: utf-8 -*-
"""
Created on Fri Jul 23 10:54:53 2021

@author: Nathan Drouillard

Modified from LIFTER.py and stream_basic.py (from Labjack examples)
A combination of stream_correct_vals.py and Cluster_3.0.py

"""
#%%
from datetime import datetime
import sys
from labjack import ljm
import numpy as np
import matplotlib.pyplot as plt
#import thorlabs_apt as apt
import time
import serial
#from scipy.signal import butter, sosfilt #used in filter
from scipy.signal import iirnotch, lfilter, windows, filtfilt
from symfit import parameters, variables, Fit, Piecewise, exp, Eq, Model

plt.close('all')

#%%
# Major / "global" variables to change
global TRUE, FALSE
TRUE = 1
FALSE = 0

# ser = serial.Serial('/dev/ttyUSB_MICRONIX',38400)
ser = serial.Serial('COM4',38400,timeout=10)
ser2 = serial.Serial('COM6', 2000000) 

#%% Micronix Stuff

#Home the stage
def home():

    ser.write(b'1ENC0.001\r') #set encoder resolution 
    ser.flush()
    # ser.write(b'1REZx\r') #set DAC steps/micron resolution
    # ser.flush()
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
    
    ser.write(b'1VEL2.0\r') #set velocity to x mm/s
    time.sleep(1)
    ser.flush()

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

home()

ser.write(b'1MVA1.0\r')
ser.write(b'1POS?\r') #read position of the stage
pos = ser.readline()
pos_str = str(pos)
pos_splt = pos.strip().split(b",")
enc_pos_str = pos_splt[1]
enc_pos_val = float(enc_pos_str)
print("Starting encoder position:", enc_pos_val)
 
for i in range(0,1000):
    
    ser.write(b'1MVR0.00004\r') #move by x mm in positive direction
    ser.flush()
    ser.write(b'1WST\r')
    ser.flush()
    
    value = ser2.readline() #read voltage from Arduino
    val_str = str(value)
    count_decimals = val_str.count('.')
    count_slashes = val_str.count('\\')
        
    if len(val_str) >=8 and len(val_str) < 14 and count_decimals < 2 and count_slashes < 3:
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

toc = time.time()
toe = toc-tic
print('Time taken:', toe)

#close both serial ports 
ser.close()
ser2.close()

#%% Plot original signal and spectrum

whole_set = whole_set[1:]
pos_array = pos_array[1:]
d = pos_array/10
y_good = whole_set

ddelay = (d[1] - d[0])
dwavnum = 2*np.pi/(len(whole_set)*ddelay)
wavnum1 = np.arange(-(len(whole_set)-1)*dwavnum/2,(len(whole_set))*dwavnum/2,dwavnum)
volts_fft = np.fft.fftshift(np.fft.fft(np.fft.ifftshift(whole_set)))

fig, axs = plt.subplots(2, 1)
fig.suptitle('Voltage-Delay Interferogram')
axs[0].plot(pos_array,whole_set,'.-', label = '2000 x 40nm steps \n2,000,000 baud rate')
axs[0].set_xlabel('Delay (mm)')
axs[0].set_ylabel('Voltage (mV)')
axs[0].grid(True)
axs[1].plot(wavnum1,np.log(np.abs(volts_fft)))
axs[1].axvline(x=15797.79, ymin=-12, ymax=12, color = 'r', label = 'HeNe wavenumber')
axs[1].set_xlabel('Wavenumber (1/cm)')
axs[1].set_ylabel('Logarithm of Intensity (a.u.)')
axs[1].grid(True)
for ax in axs:
    ax.legend()


#%% Plot signal and spectrum after dc offset removal

y2 = whole_set - np.mean(whole_set)
ddelay = (d[1] - d[0])
dwavnum = 2*np.pi/(len(y2)*ddelay)
wavnum2 = np.arange(-((len(y2))-1)*dwavnum/2,(len(y2))*dwavnum/2,dwavnum)
y2_fft = np.fft.fftshift(np.fft.fft(np.fft.ifftshift(y2)))

fig, axs = plt.subplots(2, 1)
fig.suptitle('Voltage-Delay Interferogram')
axs[0].plot(pos_array,y2,'.-', label = '1000 x 40nm steps \n2,000,000 baud rate')
axs[0].set_xlabel('Delay (mm)')
axs[0].set_ylabel('Voltage (mV)')
axs[0].grid(True)
axs[1].plot(wavnum2,np.log(np.abs(y2_fft)))
axs[1].axvline(x=15797.79, ymin=-12, ymax=12, color = 'r', label = 'HeNe wavenumber')
axs[1].set_xlabel('Wavenumber (1/cm)')
axs[1].set_ylabel('Logarithm of Intensity (a.u.)')
axs[1].grid(True)
for ax in axs:
    ax.legend()


#%% Plot '' '' '' after dc offset removal and apodization

# HFT90D = [1, 1.942604, 1.340318, 0.440811, 0.043097]
# window = (windows.general_cosine(len(y2), HFT90D, sym=True))**2
window = windows.tukey(len(y2), alpha = 0.15) #smaller alpha makes it wider, 0 < alpha <= 1

cos2_y2 = y2*window
ddelay = (d[1] - d[0])
dwavnum = 2*np.pi/(len(cos2_y2)*ddelay)
wavnum3 = np.arange(-((len(cos2_y2))-1)*dwavnum/2,(len(cos2_y2))*dwavnum/2,dwavnum)
# y2_fft = np.fft.fftshift(np.fft.fft(np.fft.fftshift(cos2_y2)))
cos2_y2_fft = np.fft.fftshift(np.fft.fft(np.fft.ifftshift(cos2_y2)))

fig, axs = plt.subplots(2, 1)
fig.suptitle('Voltage-Delay Interferogram')
axs[0].plot(pos_array,cos2_y2,'.-', label = '1000 x 40nm steps \n2,000,000 baud rate')
axs[0].set_xlabel('Delay (mm)')
axs[0].set_ylabel('Voltage (mV)')
axs[0].grid(True)
axs[1].plot(wavnum3/np.pi,np.log(np.abs(cos2_y2_fft)))
axs[1].axvline(x=15797.79, ymin=-12, ymax=12, color = 'r', label = 'HeNe wavenumber')
axs[1].set_xlabel('Wavenumber (1/cm)')
axs[1].set_ylabel('Logarithm of Intensity (a.u.)')
axs[1].grid(True)
for ax in axs:
    ax.legend()

#%% Plot '' '' '' after '' '' '' '' '' and line noise filtering

# def line_noise_filt(signal,f0,Q,fs):
    
#     b, a = iirnotch(f0,3,fs)
#     # zi = signal.lfilter_zi(b, a)
#     # wav = filtfilt(b, a, signal)
#     y = filtfilt(b, a, signal)
    
#     return y

# for i in range(0,4):

#     f = (i+1)*60
#     filtered_signal = line_noise_filt(cos2_y2,f,3,scanRate)
    
# ddelay = (d[1] - d[0])
# dwavnum = 2*np.pi/(len(filtered_signal)*ddelay)
# wavnum4 = np.arange(-((len(filtered_signal))-1)*dwavnum/2,(len(filtered_signal))*dwavnum/2,dwavnum)
# filtered_fft = np.fft.fftshift(np.fft.fft(np.fft.ifftshift(filtered_signal)))

# fig, axs = plt.subplots(2, 1)
# fig.suptitle('Voltage-Delay Interferogram')
# axs[0].plot(pos_array,filtered_signal,'.-')
# axs[0].set_xlabel('Delay (mm)')
# axs[0].set_ylabel('Voltage (V)')
# axs[0].grid(True)
# axs[1].plot(wavnum4,np.log(np.abs(filtered_fft)))
# axs[1].set_xlabel('Wavenumber (1/cm)')
# axs[1].set_ylabel('Intensity (a.u.)')
# axs[1].grid(True)

