# -*- coding: utf-8 -*-
"""
Created on Thu Jun  3 10:35:37 2021

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

plt.close('all')

#%%
# Major / "global" variables to change

MAX_REQUESTS = 1   # The number of eStreamRead calls that will be performed.
scanRate = 50000 # sampling rate of the ADC
startpos = 5 # start position of the stage in mm
endpos = 10 # stop position of the stage in mm
global TRUE, FALSE
TRUE = 1
FALSE = 0

#%% Micronix Stuff
# ser = serial.Serial('/dev/ttyUSB_MICRONIX',38400)
ser = serial.Serial('COM4',38400,timeout=10)
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

# Close COM port (important)
def close():

    ser.close()

#%%
# Open Labjack T7 via USB
handle = ljm.openS("T7", "USB", "ANY")  # T7 device, Any connection, Any identifier

info = ljm.getHandleInfo(handle)
print("Opened a LabJack with Device type: %i, Connection type: %i,\n"
      "Serial number: %i, IP address: %s, Port: %i,\nMax bytes per MB: %i" %
      (info[0], info[1], info[2], ljm.numberToIP(info[3]), info[4], info[5]))

deviceType = info[0]

# Stream Configuration
ScanChannel = ["AIN2"]  # Scan list names to stream #can add channels here as needed
numAddresses = len(ScanChannel)
aScanList = ljm.namesToAddresses(numAddresses, ScanChannel)[0]
scansPerRead = int(scanRate / 2)
totalscans = scansPerRead * MAX_REQUESTS 
#creating array for corrected data
whole_set = np.empty(1)
y_avg = np.empty(1)

#%%
home()
DATA = 0
pos_array = np.empty(1)
t0 = time.time()
time.sleep(0.5)

try:
    
    if deviceType == ljm.constants.dtT4:
        # LabJack T4 configuration

        # AIN0 and AIN1 ranges are +/-10 V, stream settling is 0 (default) and
        # stream resolution index is 0 (default).
        aNames = ["AIN0_RANGE","AIN2_RANGE", "STREAM_SETTLING_US",
                  "STREAM_RESOLUTION_INDEX"]
        aValues = [10.0, 10.0, 0, 0]
    else:
        # LabJack T7 and other devices configuration

        # Ensure triggered stream is disabled.
        ljm.eWriteName(handle, "STREAM_TRIGGER_INDEX", 0)

        # Enabling internally-clocked stream.
        ljm.eWriteName(handle, "STREAM_CLOCK_SOURCE", 0)

        # All negative channels are single-ended, AIN0 and AIN1 ranges are
        # +/-10 V, stream settling is 0 (default) and stream resolution index
        # is 0 (default).
        aNames = ["AIN_ALL_NEGATIVE_CH", "AIN2_RANGE", "AIN1_RANGE",
                  "STREAM_SETTLING_US", "STREAM_RESOLUTION_INDEX"]
        aValues = [ljm.constants.GND, 0.0, 10.0, 10, 0]
    # Write the analog inputs' negative channels (when applicable), ranges,
    # stream settling time and stream resolution configuration.
    numFrames = len(aNames)
    ljm.eWriteNames(handle, numFrames, aNames, aValues)

    # Configure and start stream
    scanRate = ljm.eStreamStart(handle, scansPerRead, numAddresses, aScanList, scanRate)
    print("\nStream started with a scan rate of %0.0f Hz." % scanRate)

    # print("\nPerforming %i stream reads." % MAX_REQUESTS)
    totScans = 0
    totSkip = 0  # Total skipped samples

    i = 1
    timer_start = 0
    start = datetime.now()
        
    #while i <= MAX_REQUESTS:
    for i in range(0,10):#number of steps. The goal is to cover a total retardation of 0.15mm in 100nm steps
        
        if i == 0:
            
            ret = ljm.eStreamRead(handle) 
            aData = ret[0]
            
        else:
            
            ser.write(b'1MVR0.01\r') #move by 100nm in positive direction
    
            #time.sleep(1)
            ser.flush()
            #ser.write(b'1WST\r')
            #time.sleep(1)
            #ser.flush()
            ser.write(b'1POS?\r')
            pos = ser.readline()
            pos_str = str(pos)
            pos_splt = pos.strip().split(b",")
            enc_pos_str = pos_splt[1]
            enc_pos_val = float(enc_pos_str)
            #print(enc_pos_val)
            pos_array = np.append(pos_array, enc_pos_val)
            ser.flush()
            
            ret = ljm.eStreamRead(handle) 
        
            aData = ret[0]
                
            scans = len(aData) / numAddresses #this is only necessary for more than one channel
            totScans += scans
    
            # Count the skipped samples which are indicated by -9999 values. Missed
            # samples occur after a device's stream buffer overflows and are
            # reported after auto-recover mode ends.
            curSkip = aData.count(-9999.0)
            totSkip += curSkip
        
            aData_avg = np.average(aData)
            # y_avg = np.append(y_avg,aData_avg)
            aData_array = np.asarray(aData)
            whole_set = np.append(whole_set,aData_array)
            # i += 1
            
            if i==1:
                timer_start = datetime.now()
        
    end = datetime.now()
    timer_end = datetime.now()
    
    # y = (whole_set * 10)
    #y1 = y[int(scanRate/2):-1] #dropping the data from the first stream read
    y1 = whole_set
    y11 = y1 - np.mean(y1)
    
    # pos_interp = np.interp(y1, pos_array, y_avg)
    
    # pos_axis = np.linspace(0,pos_array[99],2475000)
    # y_interp = np.interp(pos_axis,pos_array,y_avg)
    
    timer_len = (timer_end - timer_start).seconds + float((timer_end-timer_start).microseconds) / 1000000

    print("\nTotal scans = %i" % (totScans))
    tt = (end - start).seconds + float((end - start).microseconds) / 1000000
    print("Time taken = %f seconds" % (tt))
    print("LJM Scan Rate = %f scans/second" % (scanRate))
    print("Timed Scan Rate = %f scans/second" % (totScans / tt))
    print("Timed Sample Rate = %f samples/second" % (totScans * numAddresses / tt))
    print("Skipped scans = %0.0f" % (totSkip / numAddresses))
except ljm.LJMError:
    ljme = sys.exc_info()[1]
    print(ljme)
except Exception:
    e = sys.exc_info()[1]
    print(e)

try:
    print("\nStop Stream")
    ljm.eStreamStop(handle)
except ljm.LJMError:
    ljme = sys.exc_info()[1]
    print(ljme)
except Exception:
    e = sys.exc_info()[1]
    print(e)

# Close handle
ljm.close(handle)
ser.close()

#%% 

Time = np.linspace(np.abs(tt - timer_len),timer_len ,len(y1))
#Time = np.linspace(0, (endpos - startpos)/(3*(10**8)), len(y1) )
x = np.linspace(pos_array[0],pos_array[-1],len(y1))
# x = np.linspace(0,len(y1),len(y1))

plt.figure()
plt.title('Voltage-Delay Interferogram')
plt.xlabel('Delay (mm)')
plt.ylabel('Voltage (V)')
# plt.plot(pos_axis[1:],y_interp[1:],'.-')
# plt.plot(pos_array[1:], y1[1:], '.-')
# plt.plot(pos_axis[1:], y_interp[1:], '-o')
# plt.plot(pos_array*1e6,y1,'.-')
plt.plot(x[15000:],y1[15000:],'.-')
# plt.plot(pos_array[15000:],y1[15000:],'.-')
# plt.ylim(-5,5)
# plt.xlim(0,pos_array[-1])
plt.show()

#%% Wavenumber Spectrum

# ddelay = (pos_array[1] - pos_array[0])
# wavnum_vec = 2*np.pi/(2*ddelay)*np.linspace(-1,1,len(y1))
# dwave = 2*np.pi/(len(y1)*ddelay)
# dwavnum = wavnum_vec[1]-wavnum_vec[0]
# vw = np.fft.fftshift(np.fft.fft(np.fft.fftshift(y1)))

# plt.figure()
# plt.plot(wavnum_vec/10,np.abs(vw))
# plt.show()

#%% FFT

# #Time = np.linspace(0,12500,12500)
# Tim = np.linspace(0, (endpos - startpos)/(3*(10**8)), len(y1) )
# #d = 2*(endpos-startpos) / 1000
# #tao = d / 3e8
# #Tim = np.linspace(0,tao,tao)
# Nt = len(Tim)
# dt = Tim[1] - Tim[0]
# t1 = np.arange(-Nt/2*dt,Nt/2*dt,dt)


# dw = 2*np.pi/(Nt*dt)
# #w = np.arange(-(Nt-1)*dw/2,(Nt-0.9)*dw/2,dw)
# w = np.linspace(-(Nt-1)*dw/2,(Nt-1)*dw/2,Nt,endpoint=False) #you need to use False this if Nt is even, True if Nt is odd

# plt.figure()
# y2 = np.fft.fftshift(np.fft.fft(np.fft.fftshift(y11))) #takes the fft and shifts the data
# plt.semilogy(w/(2*np.pi),(np.abs(y2))**2)

#%% Bandstop filter for 60 Hz noise
#
#fig,(ax1,ax2) = plt.subplots(2,1,sharex=True)
#ax1.plot(Time,y11)
#ax1.set_title('Unfiltered Signal')
#
#sos = butter(10,(59,61),'bs', fs=scanRate, output='sos')
#filtered = sosfilt(sos,y11)
#ax2.plot(Time, filtered)
#ax2.set_title('Filtered Signal')
#ax2.set_xlabel('Time [s]')
#plt.tight_layout()
#plt.show()
#
##%% FFT
#
##Time = np.linspace(0,12500,12500)
#Nt = len(Time)
#dt = Time[1] - Time[0]
#
#dw = 2*np.pi/(Nt*dt)
##w = np.arange(-(Nt-1)*dw/2,(Nt-0.9)*dw/2,dw)
#w = np.linspace(-(Nt-1)*dw/2,(Nt-1)*dw/2,Nt,endpoint=False) #you need to use False this if Nt is even, True if Nt is odd
#
#plt.figure()
#filteredfft = np.fft.fftshift(np.fft.fft(np.fft.fftshift(filtered))) #takes the fft and shifts the data
#plt.semilogy(w/(2*np.pi),(np.abs(filteredfft))**2)