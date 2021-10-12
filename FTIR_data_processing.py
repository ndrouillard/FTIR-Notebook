# -*- coding: utf-8 -*-
"""
Created on Tue Oct  5 09:27:55 2021

@author: Nathan Drouillard

This script is purely meant for the data processing of interferograms.
It loads unprocessed data using pickle. 

"""
from datetime import datetime
# import sys
import numpy as np
import matplotlib.pyplot as plt
#import thorlabs_apt as apt
import time
import serial
#from scipy.signal import butter, sosfilt #used in filter
from scipy.signal import iirnotch, lfilter, windows, filtfilt
from symfit import parameters, variables, Fit, Piecewise, exp, Eq, Model
import pickle
import pandas as pd

plt.close('all')

#%%

# figx = pickle.load(open('C:/Users/natha/OneDrive/Documents/ACME/Arduino Data/Sept24(1_apodized).pickle', 'rb'))
# figx.show()
# interferogram_data = figx.axes[0].lines[0].get_data()
# spectral_data = figx.axes[1].lines[1].get_data() #this line seems to pick up my vertical reference line, so fix that

#%% Read data

df = pd.read_csv('C:/Users/natha/OneDrive/Documents/ACME/Arduino Data/2021-10-08_13_47_19.csv')
pos_array_temp = df['OPD (mm)']
whole_set_temp = df['Voltage (mV)']
# wavnum1_temp = df['Wavenumber (1/cm)']
# volts_fft_temp = df['Spectral Amplitude']

pos_array = pos_array_temp.to_numpy(dtype ='float64')
whole_set = whole_set_temp.to_numpy(dtype ='float64')
# wavnum1 = wavnum1_temp.to_numpy(dtype ='float64')
# volts_fft = volts_fft_temp.to_numpy(dtype ='complex128')

pos_array = pos_array*0.31789
d = pos_array/10
ddelay = (d[1] - d[0])
dwavnum = 2*np.pi/(len(whole_set)*ddelay)
wavnum1 = np.arange(-(len(whole_set)-1)*dwavnum/2,(len(whole_set))*dwavnum/2,dwavnum)
volts_fft = np.fft.fftshift(np.fft.fft(np.fft.ifftshift(whole_set)))
#%% Plot original signal and spectrum
fig0, axs = plt.subplots(2, 1)
fig0.suptitle('Voltage-Delay Interferogram')
axs[0].plot(pos_array,whole_set,'.-', label = '2000 x 40nm steps \n2,000,000 baud rate')
axs[0].set_xlabel('Delay (mm)')
axs[0].set_ylabel('Voltage (mV)')
axs[0].grid(True)
axs[1].plot(wavnum1/(2*np.pi),np.log(np.abs(volts_fft)**2))
axs[1].axvline(x=15797.79, ymin=-12, ymax=12, color = 'r', label = 'HeNe wavenumber')
axs[1].set_xlabel('Wavenumber (1/cm)')
axs[1].set_ylabel('Logarithm of Amplitude (a.u.)')
axs[1].grid(True)
for ax in axs:
    ax.legend()

# pickle.dump(fig0, open(filepath1, 'wb'))

#%% Plot signal and spectrum after dc offset removal

y2 = whole_set - np.mean(whole_set)
ddelay = (d[1] - d[0])
dwavnum = 2*np.pi/(len(y2)*ddelay)
wavnum2 = np.arange(-((len(y2))-1)*dwavnum/2,(len(y2))*dwavnum/2,dwavnum)
y2_fft = np.fft.fftshift(np.fft.fft(np.fft.ifftshift(y2)))

fig, axs = plt.subplots(2, 1)
fig.suptitle('Voltage-Delay Interferogram w/o dc Offset')
axs[0].plot(pos_array,y2,'.-', label = '1000 x 40nm steps \n2,000,000 baud rate')
axs[0].set_xlabel('Delay (mm)')
axs[0].set_ylabel('Voltage (mV)')
axs[0].grid(True)
axs[1].plot(wavnum2/(2*np.pi),np.log(np.abs(y2_fft)**2))
axs[1].axvline(x=15797.79, ymin=-12, ymax=12, color = 'r', label = 'HeNe wavenumber')
axs[1].set_xlabel('Wavenumber (1/cm)')
axs[1].set_ylabel('Logarithm of Amplitude (a.u.)')
axs[1].grid(True)
for ax in axs:
    ax.legend()


#%% Plot '' '' '' after dc offset removal and apodization

# plt.close('all')
# HFT90D = [1, 1.942604, 1.340318, 0.440811, 0.043097]
# window = (windows.general_cosine(len(y2), HFT90D, sym=True))**2
window_len = 600
lower_bnd = int((len(whole_set) / 2) - (window_len / 2))
upper_bnd = -int(lower_bnd)
window = windows.tukey(window_len, alpha = 0.00) # 0 < alpha <= 1; alpha = 0 is a box, alpha = 1 is a Hanning
# X0 = 3.5e-4
# window = np.piecewise(pos_array, [pos_array < -0.500, ((pos_array >= -0.525) & (pos_array < -0.510)), pos_array >= -0.510], [lambda pos_array : 0, lambda pos_array : windows.tukey(352,alpha=0.70), lambda pos_array : 0])
noise_range = np.empty(286)

cos2_y2 = y2[lower_bnd:upper_bnd]*window
ddelay = (d[1] - d[0])
dwavnum = 2*np.pi/(len(cos2_y2)*ddelay)
wavnum3 = np.arange(-((len(cos2_y2))-1)*dwavnum/2,(len(cos2_y2))*dwavnum/2,dwavnum)
# y2_fft = np.fft.fftshift(np.fft.fft(np.fft.fftshift(cos2_y2)))
cos2_y2_fft = np.fft.fftshift(np.fft.fft(np.fft.ifftshift(cos2_y2)))

# noise_range[:] = [x for x in wavnum3 if x>=25000]
len_noise_range = int(np.ndarray.sum(wavnum3))
specint = np.log(np.abs(cos2_y2_fft)**2)
noise_floor = np.average(specint[len_noise_range:])
print('Noise floor:', noise_floor)
signal_peak = np.max(specint)
print('Signal peak:', signal_peak)
print('SNR = ', np.abs(signal_peak-noise_floor))

fig2, axs = plt.subplots(2, 1)
fig2.suptitle('Voltage-Delay Interferogram After Apodization')
axs[0].plot(pos_array[lower_bnd:upper_bnd],cos2_y2,'.-')# label = '1000 x 40nm steps \n2,000,000 baud rate')
axs[0].set_xlabel('Delay (mm)')
axs[0].set_ylabel('Voltage (mV)')
axs[0].grid(True)
axs[1].plot(wavnum3/(2*np.pi),np.log(np.abs(cos2_y2_fft)**2))
axs[1].axvline(x=15797.79, ymin=-12, ymax=12, color = 'r', label = 'HeNe wavenumber')
axs[1].set_xlabel('Wavenumber (1/cm)')
axs[1].set_ylabel('Logarithm of Amplitude (a.u.)')
axs[1].grid(True)
for ax in axs:
    ax.legend()
