"""
Created on Fri May 7 2021
@author: Nathan Drouillard, modified from BitScope_GUI_fast.py
A special thanks is owed to Aananth Kanagaraj (Codenio)
Notes: -use BL_STREAM mode in bitlib_read_data_for_GUI
       -the stage functions are from "micronix_functions(Feb21).py"
"""
from bitlib import *
import numba
import tkinter as tk
import tkinter.font as font #this is needed but unused?
from tkinter.filedialog import asksaveasfile
import time
from datetime import datetime
import os

# import matplotlib.pyplot as plt
import numpy as np
# import drawnow as drawnow

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

from pandas import DataFrame

#from feb26test import bitscope_setup, stream #this is a script I wrote from "bitlib-read-data.py"

import serial
#%%

root = tk.Tk()
root.geometry("1024x768")
root.title("FTIR GUI")

myFont = tk.font.Font(family='Helvetica', size=15, weight='bold')

#%% Major variables
global Nt, scanRate, now
scanRate = 20000000 #1000000 is the default sample rate of the BitScope, 20 MHz is the max
Nt = 100000#12228 #maximum is 12228 but 60,000 is much faster?
#bitscope_setup(scanRate,Nt)
myFont = ("Helvetica",12)
now = str(datetime.now()) #this is for naming the csv file by the date
#%%

#%% Micronix Stuff
c = 3e8
poslim = 1e-2 #1cm (these are the stage limits)
neglim = -1e-2
d = poslim + np.abs(neglim)
optical_t = np.linspace(0,d/c,Nt)

#%% Open the COM port
ser = serial.Serial('/dev/ttyUSB_MICRONIX',38400)

def bitscope_setup(rate,size):
    TRUE = 1
    FALSE = 0
    #Setup general parameters for the capture
    MY_RATE = rate # default sample rate in Hz we'll use for capture.
    MY_SIZE = size # number of samples we'll capture - 12288 is the maximum size

#     x = np.arange(MY_SIZE)/float(MY_RATE)

    print("Starting: Attempting to open one devices...")

    #Attempt to open 1 device at /dev/ttyUSBx
    #Make sure you run 'cd /dev/' followed by 'ls ' on terminal to see if the device is present.

    #See return value to see the number of successfully opened devices.
    if (BL_Open('USB:/dev/ttyUSB_BITSCOPE',1)==0):
    #if (BL_Open('USB:/dev/ttyUSB_BITSCOPE',1)==0):
        print("  FAILED: all devices not found (check your probe file)."    )
    else:
        #Successfully opened one device
        #Report the number of devices opened, and the library version used
        #print('\nNumber of devices opened: %s' ,BL_Count(BL_COUNT_DEVICE))
        print(" Library: %s (%s)\n\n" , (BL_Version(BL_VERSION_LIBRARY),BL_Version(BL_VERSION_BINDING)))

        #Select the first device opened, found at location 0 by default.
        BL_Select(BL_SELECT_DEVICE,0)

        #Setup acquisition in FAST mode, where the whole of the 12288 samples in
        #the buffer are used by one channel alone.
        BL_Mode(BL_MODE_FAST)
        #BL_Mode(BL_MODE_STREAM)

        #Report the capture details
        print(" Capture: %d @ %.0fHz = %fs" , (BL_Size(),BL_Rate(MY_RATE),BL_Time()))

        #Setup channel-nonspecific parameters for capture.
        BL_Intro(BL_ZERO); #How many seconds to capture before the trigger event- 0 by default
        BL_Delay(BL_ZERO); #How many seconds to capture after the trigger event- 0 by default
        BL_Rate(MY_RATE); # optional, default BL_MAX_RATE
        BL_Size(MY_SIZE); # optional default BL_MAX_SIZE

        #Set up channel A properties - A has channel index 0, B has 1.
        #All the subsequent properties belong to channel A until another is selected.
        BL_Select(BL_SELECT_CHANNEL,0);

        #Setup a falling-edge trigger at 0.999V.
        #Other options are BL_TRIG_RISE, BL_TRIG_HIGH, BL_TRIG_LOW.
        BL_Trigger(0.999,BL_TRIG_FALL); # This is optional when untriggered BL_Trace() is used
        #BL_Trigger(4)

        BL_Select(BL_SELECT_SOURCE,BL_SOURCE_POD); # use the POD input - the only one available
        BL_Range(BL_Count(BL_COUNT_RANGE)); # maximum range for y-axis - use this whenever possible
        BL_Offset(BL_ZERO); # Y-axis offset is set to zero as BL_ZERO

#%% Home the stage
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

#%% Setup for feedback loop
def params():
    min_pos = float(startpos.get())
    max_pos = float(stoppos.get())

    ser.write(b'1VEL5.0\r') #set velocity to 5 mm/s
    time.sleep(1)
    ser.flush()
    #velset = ser.readline()
    #print("velset")

    min_pos_str = "1TLN" + str(min_pos) + "\r"
    # ser.write(b'1POS?\r')
    # ser.write(b'1MVA0\r')
    min_pos_byt = str.encode(min_pos_str) #encode soft travel limit in the negative direction
    ser.write(min_pos_byt) #write it to the controller
    ser.flush()
    #neglim = ser.readline()
    time.sleep(1)
    #print("neglim")

    max_pos_str = "1TLP" + str(max_pos) + "\r"
    max_pos_byt = str.encode(max_pos_str)
    ser.write(max_pos_byt)
    ser.flush()
    #poslim = ser.readline()
    time.sleep(1)
    #print("poslim")

    ser.write(b'1EPL1\r') #ensure the correct encoder polarity for the feedback loop
    ser.flush()
    #polset = ser.readline()
    ser.write(b'1FBK3\r') #closed loop feedback mode
    ser.flush()
    #fbkset = ser.readline()
    ser.write(b'4DBD5,0\r') #set closed loop deadband parameters (0 means it will never timeout)
    ser.flush()
    time.sleep(1)
    print("Params set")
    #dbdset = ser.readline()

#%% Close COM port (important)
def close():

    ser.close()

#%% GUI functions
global t_vec, y, w_vec, yw_vec, all_t_vec, all_y, all_w_vec, all_yw_vec
tic = time.time()
t_vec = np.empty(1)
y = np.empty(1)
w_vec = np.empty(1)
yw_vec = np.empty(1)
all_t_vec = np.empty(1)
all_y = np.empty(1)
all_w_vec = np.empty(1)
all_yw_vec = np.empty(1)
old_time = 0
DATA1 = np.empty(1)
DATA2 = np.empty(1)

def record():

    global Nt, scanRate, old_time
    global t_vec, y, w_vec, yw_vec, tic, all_t_vec, all_y, all_w_vec, all_yw_vec
    TRUE = 1
    FALSE = 0
    params()
    bitscope_setup(scanRate,Nt)
    
    MY_RATE = 200000
    #Enable the currently selected channel, i.e. channel A
    #This ensures the recorded data goes into the memory-buffer in Bitscope device
    for i in range(0,4):
        BL_Enable(TRUE);

        print(" Bitscope Enabled")
        #Capture analog data synchronously to the Bitscope device's buffer.
        #If a trigger event is not received in 0.1sec, auto trigger happens.
        BL_Trace()#, when without any arguments, captures immediately, no trigger needed.
        print("trace {}",format(BL_Trace(0.01, BL_SYNCHRONOUS)))

        #Transfer the captured data to our PC's memory using the USB link
        DATA = BL_Acquire()
        x = np.arange(len(DATA))/float(MY_RATE)
        
        
        # ser.write(b'1PGL0\r') #loop program continuously
        ser.write(b'1MLN\r') #move to negative limit
        time.sleep(1)
        print("moved neg")
        # ser.write(b'1MVA-2\r')
        ser.flush()
        ser.write(b'1WST\r')
        time.sleep(1)
        ser.flush()
        BL_Enable(TRUE);

        print(" Bitscope Enabled")
        #Capture analog data synchronously to the Bitscope device's buffer.
        #If a trigger event is not received in 0.1sec, auto trigger happens.
        BL_Trace()#, when without any arguments, captures immediately, no trigger needed.
        print("trace {}",format(BL_Trace(0.01, BL_SYNCHRONOUS)))

        #Transfer the captured data to our PC's memory using the USB link
        DATA = BL_Acquire()
        x = np.arange(len(DATA))/float(MY_RATE)
        #movedneg = ser.readline()
        #ser.flush()
        #print(movedneg)
        # ser.write(b'1WTM5000\r') #wait for 5000 ms
        ser.write(b'1MLP\r') #move to positive limit
        # ser.write(b'1MVA2\r')
        time.sleep(1)
        ser.flush()
        ser.write(b'1WST\r')
        time.sleep(1)
        ser.flush()
        #movedpos = ser.readline()
        #ser.flush()
        print("movedpos")

        y = np.append(DATA1,DATA2)
        tmin = old_time
        tmax = time.perf_counter()
        old_time = tmax
        t_vec = np.linspace(tmin,tmax,len(y))
        dt = t_vec[1]-t_vec[0]
        w_vec = 2*np.pi/(2*dt)*np.linspace(-1,1,len(y))
        dw = w_vec[1]-w_vec[0]
        yw_vec = np.fft.fftshift(np.fft.fft(np.fft.fftshift(y)))

        all_y = np.append(all_y, y)
        all_t_vec = np.append(all_t_vec, t_vec)
        all_w_vec = np.append(all_w_vec, w_vec)
        all_yw_vec = np.append(all_yw_vec, yw_vec)

        count = len(all_yw_vec)
        data_count_disp.config(text=count)
        data_count_disp.after(int(1e-6),record)

    #return (t_vec, y, w_vec, yw_vec)

data_count_disp = tk.Label(root, font = myFont)
data_count_disp.place(x=750, y=600)

data_count_text = tk.Label(root, text = 'Data Points Processed', font = myFont)
data_count_text.place(x=575, y=600)

global z
z = 0

def write_to_file():

        global all_t_vec, all_y, all_w_vec, all_yw_vec
        #(t,y,w,yw) = append_data()
        data = np.array([all_t_vec[1:],all_y[1:],all_w_vec[1:],all_yw_vec[1:]])
        data = data.T
        df = DataFrame(data, columns = ['Time','Voltage','Wavelength', 'Intensity'])
        file = open("/home/pi/Documents/BitScope Data"+ now +"save_test.csv","a")
        df.to_csv (file, sep='\t', index = False, header=True)

    #print("Data saved")

#%% Plotting stuff

fig_time = Figure(figsize=(5,4))
ax_time = fig_time.add_subplot(111)
canvas_time = FigureCanvasTkAgg(fig_time, master=root)

f = Figure(figsize=(5,5),dpi=100)#, tight_layout=True)
f2 = Figure(figsize=(5,5),dpi=100)
#f3 = Figure(figsize=(5,5),dpi=100)
#d = f3.add_subplot(111)
a = f.add_subplot(111)
b = f2.add_subplot(111)
g = Figure(figsize=(5,5),dpi=100)
c = g.add_subplot(111)

canvas = FigureCanvasTkAgg(f, root)
canvas2 = FigureCanvasTkAgg(f2, root)

def plot():

    global t_vec, y, w_vec, yw_vec

    a.cla()
    a.plot(t_vec,y,'.-')
    a.set_xlabel('Time (s)')
    a.set_ylabel('Voltage (V)')

    b.cla()
    b.plot(w_vec,np.abs(yw_vec))
    b.set_xlabel('Frequency (Hz)')
    b.set_ylabel('Intensity (a.u.)')

    canvas.draw()
    canvas2.draw()
    canvas.get_tk_widget().place(x=25, y=25)
    canvas2.get_tk_widget().place(x=525, y=25)
    fig_plot.after(1,plot)

fig_plot = tk.Frame(root)
tk.Frame(plot()).pack()

#%% Buttons

start_stage_text = tk.Label(root, text = 'Start Position', font = myFont)
start_stage_text.place(x=100, y=530)
startpos = tk.StringVar(root)
startpos.set("0")
start_stage_spin = tk.Spinbox(root,
                        from_ = -6, to = 6,
                        width = 5,
                        textvariable = startpos,
                        font = myFont)
start_stage_spin.place(x=125, y=550)

stop_stage_text = tk.Label(root, text = 'Stop Position', font = myFont)
stop_stage_text.place(x=250, y=530)
stoppos = tk.StringVar(root)
stoppos.set("1")
start_spin = tk.Spinbox(root,
                        from_ = -6, to = 6,
                        width = 5,
                        textvariable = stoppos,
                        font = myFont)
start_spin.place(x=275, y=550)

button_home_stage = tk.Button(root,
    # command =
    text="Home",
    width = 10,
    height = 2,
    command = lambda: [home()],
    bg = "green",
    fg = "white",
    font = myFont,
    )
button_home_stage.place(x=100,y=580)

button_move = tk.Button(root, #this button is an edited version of the start_stage_button from FTIR_GUI_Thorlabs(Final).py
    text="Move Stage",
    width = 10,
    height = 2,
    command = lambda: [record()],#, data_count()],
    bg = "blue",
    fg = "white",
    font = myFont,
    )
button_move.place(x=250, y=580)

button_save = tk.Button(root,
    text = 'Save & Close',
    width = 10, height = 2,
    bg = 'purple', fg = 'white',
    command = lambda : [write_to_file(), root.destroy()])
button_save.place(x=850, y = 580)

button_quit = tk.Button(root,
    text="Quit",
    command = lambda: [root.destroy()],#, close_BitScope()],
    width = 10,
    height = 2,
    bg = "red",
    fg = "black",
    font = myFont,
    )
#button_quit.place(x=850,y=640)

#params()
root.mainloop()
