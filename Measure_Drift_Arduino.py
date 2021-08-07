# -*- coding: utf-8 -*-
"""
Created on Tue Aug  3 14:53:12 2021

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
import timeit
from datetime import datetime
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

    ser.write(b'1HOM\r')
    ser.flush()
    time.sleep(1)
    #ser.write(b'1WTM42\r')
    ser.write(b'1WST\r')
    time.sleep(1)
    print("stopped")
    ser.flush()
    #isstopped = ser.readline()
    ser.write(b'1ZRO\r')
    time.sleep(1)
    ser.flush()
    #zeroed = ser.readline()
    print("zeroed")
    
    ser.write(b'1VEL2.0\r') #set velocity to x mm/s
    time.sleep(1)
    ser.flush()
    # ser.write(b'1VEL?\r')
    # vel = ser.readline()
    # vel_str = str(vel)
    # # vel_splt = vel_str.strip().split(b"#")
    # # enc_vel_str = vel_splt[1]
    # enc_vel_val = float(enc_vel_str)
    # print(enc_vel_val)
    # print("velset")
    ser.write(b'1MVR0.1\r')
    ser.flush()

# Close COM port (important)
def close():

    ser.close()

#%%
whole_set = np.empty(1)
y_avg = np.empty(1)

#%%
home()
DATA = 0
pos_array = np.empty(1)
t_array = np.empty(1)
# whole_set = np.empty(1)
tic = time.time()
time.sleep(0.5)

ser.write(b'1MVR1.0\r')
ser.flush()
ser.write(b'1WST\r')
ser.flush()
old_y1 = 0
for i in range(0,5001):
# while i < 10000:
    
    # ser.write(b'1MVR0.00004\r') #move by x mm in positive direction
    # ser.write(b'1MVR0.1\r')
    #time.sleep(1)
    # ser.flush()
    # ser.write(b'1WST\r')
    #time.sleep(1)
    # ser.flush()
    value = ser2.readline() #read voltage from Arduino
    val_str = str(value)
    count_decimals = val_str.count('.')
    count_slashes = val_str.count('\\')
    # x_check = val_str.find('x')
    if len(val_str) >=8 and len(val_str) < 14 and count_decimals < 2 and count_slashes < 3:
        w = val_str.strip("'b")
        z = w[:-4]
        y1 = float(z)
    else:
        y1 = old_y1
        print("Bad value")
        
    whole_set = np.append(whole_set,y1) #append voltage reading to master array of voltages
    
    # t = time.time()
    curr_time = time.time()
    # formatted_time = curr_time.strftime('%S.%f')
    t = float(curr_time)
    t_array = np.append(t_array, t)

toc = time.time()
toe = toc-tic

print('Time taken:', toe)
#close both serial ports 
ser.close()
ser2.close()

t_array = t_array[1:]
whole_set = whole_set[1:]
#%% Plot original signal and spectrum

fig, axs = plt.subplots(2, 1)
fig.suptitle('Voltage Drift Over Time')
axs[0].plot((t_array-tic),whole_set,'.-')
axs[0].set_xlabel('Time (s)')
axs[0].set_ylabel('Voltage (mV)')
axs[0].grid(True)
# axs[1].plot(wavnum1,np.log(np.abs(volts_fft)))
# axs[1].axvline(x=15797.79, ymin=-12, ymax=12, color = 'r', label = 'HeNe wavenumber')
# axs[1].set_xlabel('Wavenumber (1/cm)')
# axs[1].set_ylabel('Logarithm of Intensity (a.u.)')
# axs[1].grid(True)


# #%% Plot signal and spectrum after dc offset removal

# y2 = whole_set - np.mean(whole_set)
# ddelay = (d[1] - d[0])
# dwavnum = 2*np.pi/(len(y2)*ddelay)
# wavnum2 = np.arange(-((len(y2))-1)*dwavnum/2,(len(y2))*dwavnum/2,dwavnum)
# y2_fft = np.fft.fftshift(np.fft.fft(np.fft.ifftshift(y2)))

# fig, axs = plt.subplots(2, 1)
# fig.suptitle('Voltage-Delay Interferogram')
# axs[0].plot(pos_array,y2,'.-', label = '1000 x 40nm steps \n2,000,000 baud rate')
# axs[0].set_xlabel('Delay (mm)')
# axs[0].set_ylabel('Voltage (mV)')
# axs[0].grid(True)
# axs[1].plot(wavnum2,np.log(np.abs(y2_fft)))
# axs[1].axvline(x=15797.79, ymin=-12, ymax=12, color = 'r', label = 'HeNe wavenumber')
# axs[1].set_xlabel('Wavenumber (1/cm)')
# axs[1].set_ylabel('Logarithm of Intensity (a.u.)')
# axs[1].grid(True)
# for ax in axs:
#     ax.legend()


# #%% Plot '' '' '' after dc offset removal and apodization

# HFT90D = [1, 1.942604, 1.340318, 0.440811, 0.043097]
# window = (windows.general_cosine(len(y2), HFT90D, sym=True))**2

# cos2_y2 = y2*window
# ddelay = (d[1] - d[0])
# dwavnum = 2*np.pi/(len(cos2_y2)*ddelay)
# wavnum3 = np.arange(-((len(cos2_y2))-1)*dwavnum/2,(len(cos2_y2))*dwavnum/2,dwavnum)
# # y2_fft = np.fft.fftshift(np.fft.fft(np.fft.fftshift(cos2_y2)))
# cos2_y2_fft = np.fft.fftshift(np.fft.fft(np.fft.ifftshift(cos2_y2)))

# fig, axs = plt.subplots(2, 1)
# fig.suptitle('Voltage-Delay Interferogram')
# axs[0].plot(pos_array,cos2_y2,'.-', label = '1000 x 40nm steps \n2,000,000 baud rate')
# axs[0].set_xlabel('Delay (mm)')
# axs[0].set_ylabel('Voltage (mV)')
# axs[0].grid(True)
# axs[1].plot(wavnum3/np.pi,np.log(np.abs(cos2_y2_fft)))
# axs[1].axvline(x=15797.79, ymin=-12, ymax=12, color = 'r', label = 'HeNe wavenumber')
# axs[1].set_xlabel('Wavenumber (1/cm)')
# axs[1].set_ylabel('Logarithm of Intensity (a.u.)')
# axs[1].grid(True)
# for ax in axs:
#     ax.legend()

# #%% Plot '' '' '' after '' '' '' '' '' and line noise filtering

# # def line_noise_filt(signal,f0,Q,fs):
    
# #     b, a = iirnotch(f0,3,fs)
# #     # zi = signal.lfilter_zi(b, a)
# #     # wav = filtfilt(b, a, signal)
# #     y = filtfilt(b, a, signal)
    
# #     return y

# # for i in range(0,4):

# #     f = (i+1)*60
# #     filtered_signal = line_noise_filt(cos2_y2,f,3,scanRate)
    
# # ddelay = (d[1] - d[0])
# # dwavnum = 2*np.pi/(len(filtered_signal)*ddelay)
# # wavnum4 = np.arange(-((len(filtered_signal))-1)*dwavnum/2,(len(filtered_signal))*dwavnum/2,dwavnum)
# # filtered_fft = np.fft.fftshift(np.fft.fft(np.fft.ifftshift(filtered_signal)))

# # fig, axs = plt.subplots(2, 1)
# # fig.suptitle('Voltage-Delay Interferogram')
# # axs[0].plot(pos_array,filtered_signal,'.-')
# # axs[0].set_xlabel('Delay (mm)')
# # axs[0].set_ylabel('Voltage (V)')
# # axs[0].grid(True)
# # axs[1].plot(wavnum4,np.log(np.abs(filtered_fft)))
# # axs[1].set_xlabel('Wavenumber (1/cm)')
# # axs[1].set_ylabel('Intensity (a.u.)')
# # axs[1].grid(True)

