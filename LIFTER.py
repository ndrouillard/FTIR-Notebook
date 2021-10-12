"""
Created on Sat Aug 24 07:42:08 2019

Title: Labjack-Thorlabs-FTIR (aka. LIFTER)

@author: Nathan Drouillard

Modified from stream_basic.py (from Labjack examples)
A combination of stream_correct_vals.py and Cluster_3.0.py

This program moves the motor stage continuously from startpos to endpos
and takes data through the Labjack ADC

THIS IS THE MOST UP TO DATE PROGRAM FOR THIS APPLICATION as of Oct.18th, 2019
"""
#%%
from datetime import datetime
import sys
from labjack import ljm
import numpy as np
import matplotlib.pyplot as plt
import thorlabs_apt as apt
import time
#from scipy.signal import butter, sosfilt #used in filter

#%%
# Major / "global" variables to change

MAX_REQUESTS = 5   # The number of eStreamRead calls that will be performed.
scanRate = 50000 # sampling rate of the ADC
startpos = 5 # start position of the stage in mm
endpos = 10 # stop position of the stage in mm

#%%
# Open Labjack T7 via USB
handle = ljm.openS("T7", "USB", "ANY")  # T7 device, Any connection, Any identifier

info = ljm.getHandleInfo(handle)
print("Opened a LabJack with Device type: %i, Connection type: %i,\n"
      "Serial number: %i, IP address: %s, Port: %i,\nMax bytes per MB: %i" %
      (info[0], info[1], info[2], ljm.numberToIP(info[3]), info[4], info[5]))

deviceType = info[0]

# Stream Configuration
ScanChannel = ["AIN0"]  # Scan list names to stream #can add channels here as needed
numAddresses = len(ScanChannel)
aScanList = ljm.namesToAddresses(numAddresses, ScanChannel)[0]
scansPerRead = int(scanRate / 2)
totalscans = scansPerRead * MAX_REQUESTS 
#creating array for corrected data
whole_set = np.empty(1)

#%% Setup for Thorlabs motor stage

serial_junk = apt.list_available_devices() #grabs all serial numbers from available devices
serial_no = serial_junk[0][1] #take first device
motor = apt.Motor(serial_no) #apply serial number as desired motor

#parameters for homing
acc_vel_parms = motor.get_velocity_parameter_limits()
max_acc = acc_vel_parms[0]#*0.9
max_vel = acc_vel_parms[1]#*0.9
motor.set_velocity_parameters(0,max_acc,max_vel)

posvec = np.zeros(10)

#%% HOME IF FIRST TIME RUNNING FOR THE DAY
print('HOMING')
motor.move_home(True) #only need if kcube has been turned off

#%%

motor.move_to(startpos-0.5) #-0.5 to cover the backlash
while motor.is_in_motion: #having this while statement makes it stop before it moves again
    toc = time.time()
time.sleep(0.5)
motor.move_to(startpos)
while motor.is_in_motion: #having this while statement makes it stop before it moves again
    toc = time.time()
time.sleep(0.5)

#parameters for collecting data
acc_vel_parms = motor.get_velocity_parameter_limits()
max_acc = acc_vel_parms[0]
#max_vel = acc_vel_parms[1]*0.9/703 

#my way
#scans_kept = totalscans - (scanRate/2) #to account for dropping the first stream read
stage_time = totalscans / scanRate
max_vel = (endpos-startpos)/stage_time

if max_vel >= acc_vel_parms[1]: #in the case that the calculated velocity exceeds the limit of the motor stage
    max_vel = acc_vel_parms[1]*0.9/1.5
    def_scan_time = (endpos - startpos) / max_vel*0.9
    totalscans = int( scanRate * def_scan_time )
    
#acc_vel_parms[1]*0.9/200 #/1000 is the slowest it can go, otherwise it's 0, at 60fps is 15 frames per wavelength at 633
motor.set_velocity_parameters(0,max_acc,max_vel)

tic = time.time()
motor.move_to(endpos)
startic = time.time()

#%%

try:
    
    if deviceType == ljm.constants.dtT4:
        # LabJack T4 configuration

        # AIN0 and AIN1 ranges are +/-10 V, stream settling is 0 (default) and
        # stream resolution index is 0 (default).
        aNames = ["AIN0_RANGE", "AIN1_RANGE", "STREAM_SETTLING_US",
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
        aNames = ["AIN_ALL_NEGATIVE_CH", "AIN0_RANGE", "AIN1_RANGE",
                  "STREAM_SETTLING_US", "STREAM_RESOLUTION_INDEX"]
        aValues = [ljm.constants.GND, 10.0, 10.0, 0, 0]
    # Write the analog inputs' negative channels (when applicable), ranges,
    # stream settling time and stream resolution configuration.
    numFrames = len(aNames)
    ljm.eWriteNames(handle, numFrames, aNames, aValues)

    # Configure and start stream
    scanRate = ljm.eStreamStart(handle, scansPerRead, numAddresses, aScanList, scanRate)
    print("\nStream started with a scan rate of %0.0f Hz." % scanRate)

    print("\nPerforming %i stream reads." % MAX_REQUESTS)
    totScans = 0
    totSkip = 0  # Total skipped samples

    i = 1
    timer_start = 0
    start = datetime.now()
    
    while i <= MAX_REQUESTS:
        
        ret = ljm.eStreamRead(handle) 
    
        aData = ret[0]
            
        scans = len(aData) / numAddresses #this is only necessary for more than one channel
        totScans += scans

        # Count the skipped samples which are indicated by -9999 values. Missed
        # samples occur after a device's stream buffer overflows and are
        # reported after auto-recover mode ends.
        curSkip = aData.count(-9999.0)
        totSkip += curSkip
    
        aData_array = np.asarray(aData)
        whole_set = np.append(whole_set,aData_array)
        i += 1
        
        if i==2:
            timer_start = datetime.now()
        
    end = datetime.now()
    timer_end = datetime.now()
    
    y = (whole_set * 10)
    y1 = y[int(scanRate/2):-1] #dropping the data from the first stream read
    y11 = y1 - np.mean(y1)
    
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

#%% Plot traces

Time = np.linspace(np.abs(tt - timer_len),timer_len ,len(y1))
#Time = np.linspace(0, (endpos - startpos)/(3*(10**8)), len(y1) )
plt.figure()
plt.plot(Time*1e3,y1,'.-')
plt.show()

#%% FFT

#Time = np.linspace(0,12500,12500)
Tim = np.linspace(0, (endpos - startpos)/(3*(10**8)), len(y1) )
#d = 2*(endpos-startpos) / 1000
#tao = d / 3e8
#Tim = np.linspace(0,tao,tao)
Nt = len(Tim)
dt = Tim[1] - Tim[0]
t1 = np.arange(-Nt/2*dt,Nt/2*dt,dt)


dw = 2*np.pi/(Nt*dt)
#w = np.arange(-(Nt-1)*dw/2,(Nt-0.9)*dw/2,dw)
w = np.linspace(-(Nt-1)*dw/2,(Nt-1)*dw/2,Nt,endpoint=False) #you need to use False this if Nt is even, True if Nt is odd

plt.figure()
y2 = np.fft.fftshift(np.fft.fft(np.fft.fftshift(y11))) #takes the fft and shifts the data
plt.semilogy(w/(2*np.pi),(np.abs(y2))**2)

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

