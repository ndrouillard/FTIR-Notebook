# -*- coding: utf-8 -*-
"""
Created on Thu Jul 22 12:18:52 2021

@author: natha
"""

import numpy as np
import time
import matplotlib.pyplot as plt
from scipy.signal import iirnotch, lfilter, windows, filtfilt

plt.close('all')

#%% Create a voltage-delay interferogram

Nt = 10000000 #number of steps
t = np.linspace(0,10,Nt)
lambda_0 = (632.8)*(10**(-9)) #central wavelength in metres
wavnum_0 = (1/lambda_0)/100#/100 #central wavenumber, convert to 1/cm
delta = 10 #maximum retardation [cm]
V = 2*(0.2) #optical velocity = 2V' where V' is the mirror velocity [cm/s]
# d = np.linspace(-delta/2,delta/2,Nt) #array of retardations
d = np.linspace(V*t[0],V*t[-1],Nt)
dd = d[1] - d[0]
# t = np.empty(Nt)
# for i in range(0,Nt):
#     t[i] = d[i]/V #temporal retardation
B = 1 #pure spectrum (not sure what to do with this)
#wavnum = np.linspace(-wavnum_0, wavnum_0, Nt)
# wavnum = 2*np.pi/(2*dd)*np.linspace(-1,1,Nt)+

# wavnum = np.fft.fftshift(np.fft.fft(np.fft.fftshift(d)))
dwavnum = 2*np.pi/(Nt*dd)
wavnum = np.arange(-(Nt-1)*dwavnum/2,Nt*dwavnum/2,dwavnum)
volts = B*(np.cos(2*np.pi*wavnum_0*d)) 

# dwavnum = wavnum[1]-wavnum[0]
vw = np.fft.fftshift(np.fft.fft(np.fft.ifftshift(volts)))

#%% Pure signal and spectrum
plt.close('all')

plt.figure()
plt.plot(d*1e7,volts)
plt.xlabel("Delay (nm)")
plt.ylabel("Voltage (V)")
plt.title("Voltage-Delay Interferogram")
plt.show()

plt.figure()
plt.plot(wavnum/(2*np.pi),np.abs(vw)) #for some reason this factor of pi fixes it??? I get EXACTLY what I want
plt.xlabel("Wavenumber (1/cm)")
plt.ylabel("Intensity (a.u.)")
plt.title("Spectrum")
plt.show()

# #%% Create a voltage-time interferogram

# T = 10 #time in seconds
# t = np.linspace(0,T,Nt)

# volts2 = B*(np.cos(2*np.pi*wavnum*d))*V*t

# dt = t[1]-t[0]
# # w = 2*np.pi/(2*dt)*np.linspace(-1,1,len(volts))
# dw = 2*np.pi/Nt*dt
# w = np.arange(-(Nt-1)*dw/2,Nt*dw/2,dw)
# # dw = w[1]-w[0]
# volts_fft = np.fft.fftshift(np.fft.fft(np.fft.ifftshift(volts2)))

# plt.figure()
# plt.plot(t,volts2)
# plt.xlabel("Delay (mm)")
# plt.ylabel("Voltage (V)")
# plt.title("Voltage-Delay Interferogram")
# plt.show()

# plt.figure()
# plt.plot(w,np.abs(volts_fft))
# plt.xlabel("Wavenumber (1/cm)")
# plt.ylabel("Intensity (a.u.)")
# plt.title("Spectrum")
# plt.show()

# #%% Apodization

# HFT90D = [1, 1.942604, 1.340318, 0.440811, 0.043097]
# window = (windows.general_cosine(1000, HFT90D, sym=True))**2