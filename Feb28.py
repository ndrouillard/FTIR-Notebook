"""
Created on Mon May 17 2021
@author: Nathan Drouillard, modified from BitScope_GUI_fast.py
A special thanks is owed to Aananth Kanagaraj (Codenio)
Notes: -use BL_STREAM mode in bitlib_read_data_for_GUI
       -the stage functions are from "micronix_functions(Feb21).py"
"""
from bitlib import *
from bitscope import *
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
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure
from pandas import DataFrame
import serial
import threading
from threading import Thread
#%%

root = tk.Tk()
root.geometry("1024x768")
root.title("FTIR GUI")

myFont = tk.font.Font(family='Helvetica', size=15, weight='bold')

#%% Major variables
global MY_SIZE, MY_RATE, now, TRUE, FALSE
MY_RATE = 20000000 #1000000 is the default sample rate of the BitScope, 20 MHz is the max
MY_SIZE = 12228#12228 #maximum is 12228 but 60,000 is much faster?
TRUE = 1
FALSE = 0
#bitscope_setup(scanRate,Nt)
myFont = ("Helvetica",12)
now = str(datetime.now()) #this is for naming the csv file by the date
#%%

#%% Micronix Stuff
c = 3e8
poslim = 1e-2 #1cm (these are the stage limits)
neglim = -1e-2
d = poslim + np.abs(neglim)
#optical_t = np.linspace(0,d/c,Nt)

#Variables for data collection
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

#Plotting stuff
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

#%% Open the BitScope
ser = serial.Serial('/dev/ttyUSB_MICRONIX',38400)
#%% Setup the Bitscope
#def bitscope_setup():

 #   global MY_SIZE, MY_RATE, TRUE, FALSE
    #Setup general parameters for the capture

print("Starting: Attempting to open one devices...")

#Attempt to open 1 device at /dev/ttyUSBx
#Make sure you run 'cd /dev/' followed by 'ls ' on terminal to see if the device is present.

# initialisation of scope collects all the device data and stores them in scope.devices list
# and closes open devices on object termination
scope = Scope('USB:/dev/ttyUSB1',1)

#See return value to see the number of successfully opened devices.
if (scope.device_count==0):
    print("  FAILED: all devices not found (check your probe file).")
else:
    #Successfully opened one device
    #Report the number of devices opened, and the library version used
    print('\nNumber of devices opened: %s' %scope.device_count)
    print(" Library: %s (%s)\n\n" %(scope.version(VERSION.LIBRARY),scope.version(VERSION.BINDING)))

    # collect the list of devices
    devices = scope.devices

    #Select the first device opened, found at location 0 by default.
    #Setup acquisition in FAST mode, where the whole of the 12288 samples in
    #the buffer are used by one channel alone.
    devices[0].mode(MODE.FAST)
    #devices[0].mode(MODE.STREAM) #when this is used, it defaults to ~4kHz for some reason

    #Report the capture details
    print(" Capture: %d @ %.0fHz = %fs" % (scope.tracer.size(),scope.tracer.rate(MY_RATE),scope.tracer.time()))

    #Setup channel-nonspecific parameters for capture.
    scope.tracer.configure(
        rate=MY_RATE, # optional, default BL_MAX_RATE
        size=MY_SIZE, # optional default BL_MAX_SIZE
        pre_capture=ZERO, #How many seconds to capture before the trigger event- 0 by default
        post_capture=ZERO, #How many seconds to capture after the trigger event- 0 by default
    )

    #Set up channel A properties - A has channel index 0, B has 1.
    #All the subsequent properties belong to channel A until another is selected.

    #Setup a falling-edge trigger at 0.999V.
    #Other options are BL_TRIG_RISE, BL_TRIG_HIGH, BL_TRIG_LOW.
    scope.tracer.trigger(0.999,TRIGGER.FALL)

    # select channel 0 form device 0 and configure
    devices[0].channels[0].configure(
        source=SOURCE.BNC, # use the POD input - the only one available (I tried putting BNC here, to no avail)
        offset=ZERO, # Y-axis offset is set to zero as BL_ZERO
        range=devices[0].channels[0].analog_range_count, # maximum range for y-axis - use this whenever possible
        coupling=COUPLING.DC
    )

    #Enable the currently selected channel, i.e. channel A
    #This ensures the recorded data goes into the memory-buffer in Bitscope device
    devices[0].channels[0].enable()

    #Capture analog data synchronously to the Bitscope device's buffer.
    #If a trigger event is not received in 0.1sec, auto trigger happens.
    #BL_Trace(), when without any arguments, captures immediately, no trigger needed.
    print("trace {}".format(scope.tracer.trace(0.01,TRACE.SYNCHRONOUS)))

#%% Functions
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

#%% Setup stage parameters for scanning
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

def move():

    for i in range(0,4):
        # ser.write(b'1PGL0\r') #loop program continuously
        ser.write(b'1MLN\r') #move to negative limit
        time.sleep(1)
        #print("moved neg")
        # ser.write(b'1MVA-2\r')
        ser.flush()
        ser.write(b'1WST\r')
        time.sleep(1)
        ser.flush()
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
        run_Fourier() #take FFT
        #movedpos = ser.readline()
        #ser.flush()
        #print("movedpos")

        ser.write(b'1MLN\r') #move to negative limit
        time.sleep(1)
        #print("moved neg")
        # ser.write(b'1MVA-2\r')
        ser.flush()
        ser.write(b'1WST\r')
        time.sleep(1)
        ser.flush()

        run_Fourier() #take FFT
        #movedneg = ser

#Record data from Bitscope and move stage
def record():
    global DATA, DATA1
    global MY_RATE, MY_SIZE, TRUE, FALSE, old_time
    global t_vec, y, w_vec, yw_vec, tic, all_t_vec, all_y, all_w_vec, all_yw_vec

    #bitscope_setup()

    while True:
    #Transfer the captured data to our PC's memory using the USB link
        DATA1 = np.empty(1)
        DATA = devices[0].channels[1].acquire()
        data = np.array(DATA)

        y = np.append(DATA1[1:],data)
        tmin = old_time
        tmax = time.perf_counter()
        old_time = tmax
        t_vec = np.linspace(tmin,tmax,len(y))

        all_y = np.append(all_y, y)
        all_t_vec = np.append(all_t_vec, t_vec)
        all_w_vec = np.append(all_w_vec, w_vec)
        all_yw_vec = np.append(all_yw_vec, yw_vec)

        count = len(all_yw_vec)
        data_count_disp.config(text=count)
        #data_count_disp.after(int(1e-6),record)

data_count_disp = tk.Label(root, font = myFont)
data_count_disp.place(x=750, y=600)

data_count_text = tk.Label(root, text = 'Data Points Processed', font = myFont)
data_count_text.place(x=575, y=600)

def Fourier():
    global DATA, DATA1
    global MY_RATE, MY_SIZE, TRUE, FALSE, old_time
    global t_vec, y, w_vec, yw_vec, tic, all_t_vec, all_y, all_w_vec, all_yw_vec

    dt = t_vec[1]-t_vec[0]
    w_vec = 2*np.pi/(2*dt)*np.linspace(-1,1,len(y))
    dw = w_vec[1]-w_vec[0]
    yw_vec = np.fft.fftshift(np.fft.fft(np.fft.fftshift(y)))

    all_w_vec = np.append(all_w_vec, w_vec)
    all_yw_vec = np.append(all_yw_vec, yw_vec)

#%% Threads
def run_record():
    params()
    t1 = threading.Thread(target = record)
    t1.start()
    t0 = threading.Thread(target = move)
    t0.start()

def run_Fourier():
    t3 = threading.Thread(target = Fourier)
    t3.start()

#Write data to file
def write_to_file():

    global all_t_vec, all_y, all_w_vec, all_yw_vec
    #(t,y,w,yw) = append_data()
    data = np.array([all_t_vec[1:],all_y[1:],all_w_vec[1:],all_yw_vec[1:]])
    data = data.T
    df = DataFrame(data, columns = ['Time','Voltage','Frequency', 'Intensity'])
    #df = DataFrame(zip(),columns = ['Time','Voltage','Frequency', 'Intensity'])
    file = open("/home/pi/Documents/BitScope Data"+ now +"save_test.csv","a")
    df.to_csv (file, sep=',', index = False, header=True)

    print("Data saved")
    print(len(all_t_vec))
    print(len(all_y))
    print(len(all_w_vec))
    print(len(all_yw_vec))

#%% Plotting stuff


#Plot data
def plot():

    global t_vec, y, w_vec, yw_vec

    a.cla()
    a.plot(y,'.-')
    a.set_xlabel('Time (s)')
    a.set_ylabel('Voltage (V)')
    a.set_ylim([0,2])

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

button_record = tk.Button(root, #this button is an edited version of the start_stage_button from FTIR_GUI_Thorlabs(Final).py
    text="Start Scan",
    width = 10,
    height = 2,
    command = lambda: [run_record()],#, data_count()],
    bg = "blue",
    fg = "white",
    font = myFont,
    )
button_record.place(x=250, y=580)

button_save = tk.Button(root,
    text = 'Save & Close',
    width = 10, height = 2,
    bg = 'purple', fg = 'white',
    command = lambda : [write_to_file(), root.destroy()])
button_save.place(x=850, y = 580)

button_quit = tk.Button(root,
    text="Quit",
    command = lambda: [root.destroy(), scope.close()],
    width = 10,
    height = 2,
    bg = "red",
    fg = "black",
    font = myFont,
    )
button_quit.place(x=850,y=630)

root.mainloop()
