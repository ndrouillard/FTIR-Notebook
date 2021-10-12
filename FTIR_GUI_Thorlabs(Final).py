# -*- coding: utf-8 -*-
"""
Created on Fri Aug  7 14:36:10 2020

@author: Nathan Drouillard, modified from FTIR_GUI_Micronix
"""

import tkinter as tk
import tkinter.font as font #this is needed but unused?
from tkinter.filedialog import asksaveasfile
import time
# import matplotlib.pyplot as plt
import numpy as np
# import drawnow as drawnow

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

import thorlabs_apt as apt
from labjack import ljm

from pandas import DataFrame

#%%

root = tk.Tk()
root.geometry("1024x768")

myFont = tk.font.Font(family='Helvetica', size=15, weight='bold')

#%% Major variables 

scanRate = 20000
myFont = ("Helvetica",12)

#%% Open Labjack T7 via USB
global handle
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

# Ensure triggered stream is disabled.
ljm.eWriteName(handle, "STREAM_TRIGGER_INDEX", 0)
# Enabling internally-clocked stream.
#ljm.eWriteName(handle, "STREAM_CLOCK_SOURCE", 0)

# All negative channels are single-ended, AIN0 and AIN1 ranges are
# +/-10 V, stream settling is 0 (default) and stream resolution index
# is 0 (default).
aNames = ["AIN_ALL_NEGATIVE_CH", "AIN0_RANGE", "AIN1_RANGE",
          "STREAM_SETTLING_US", "STREAM_RESOLUTION_INDEX"]
aValues = [ljm.constants.GND, 10.0, 10.0, 0, 0]

# Write the analog inputs' negative channels (when applicable), ranges,
# stream settling time and stream resolution configuration.
numFrames = len(aNames)
#ljm.eWriteNames(handle, numFrames, aNames, aValues)
#%% Setup for Thorlabs stage

serial_junk = apt.list_available_devices() #grabs all serial numbers from available devices
serial_no = serial_junk[0][1] #take first device
motor = apt.Motor(serial_no) #apply serial number as desired motor

#parameters for homing
acc_vel_parms = motor.get_velocity_parameter_limits()
max_acc = acc_vel_parms[0]#*0.9
max_vel = acc_vel_parms[1]#*0.9
motor.set_velocity_parameters(0,max_acc,max_vel)

#%% Functions for stage control

def home_stage():
    print('Homing')
    motor.move_home(True) #only need if kcube has been turned off

def start_stage():
    global totalscans, positions, startpos, stoppos
    global test_col_1, test_col_2, test_col_3, text_col_4
    # show_pos()
    # Export()
    start = float(startpos.get())
    stop = float(stoppos.get())
    print(start)
    
    motor.move_to(start-0.5) #-0.5 to cover the backlash
#            print("moving")
    while motor.is_in_motion:
        print(motor.position)
    acc_vel_parms = motor.get_velocity_parameter_limits()
    max_acc = acc_vel_parms[0]
#            stage_time = totalscans / scanRate
#            max_vel = (endpos-startpos)/stage_time
    max_vel = acc_vel_parms[1]*0.20
    
#            if max_vel >= acc_vel_parms[1]: #in the case that the calculated velocity exceeds the limit of the motor stage
#                max_vel = acc_vel_parms[1]*0.9/1.5
#                def_scan_time = (endpos - startpos) / max_vel*0.9
#                totalscans = int( scanRate * def_scan_time )
        
    motor.set_velocity_parameters(0,max_acc,max_vel)
    motor.move_to(stop)
    while motor.is_in_motion:
        print(motor.position)
#            plot()
    if motor.is_settled:
#                toc = time.time()
#            else:
        start_stage()
   
def stop_stage():
    motor.stop()
    
#%% Buttons for stage loop

button_open_stage = tk.Button(root,
                               text = "Open stage",
                               # command = ser.open(),
                               width = 10,
                               height = 1,
                               bg = "blue",
                               fg = "white",
                               font = myFont,
                               )
button_open_stage.place(x=600, y=625)

start_stage_text = tk.Label(root, text = 'Start Position', font = myFont)
start_stage_text.place(x=100, y=520)
global startpos
startpos = tk.StringVar(root)
startpos.set("1")
start_stage_spin = tk.Spinbox(root, 
                        from_ = -6, to = 6, 
                        width = 5,
                        textvariable = startpos, 
                        font = myFont)
start_stage_spin.place(x=125, y=550)

stop_stage_text = tk.Label(root, text = 'Stop Position', font = myFont)
stop_stage_text.place(x=250, y=520)
global stoppos
stoppos = tk.StringVar(root)
stoppos.set("2")
stop_stage_spin = tk.Spinbox(root, 
                        from_ = -6, to = 6, 
                        width = 5,
                        textvariable = stoppos, 
                        font = myFont)
stop_stage_spin.place(x=275, y=550)

button_home_stage = tk.Button(root,
    # command =                               
    text="Home",
    width = 7,
    height = 1,
    command = home_stage,
    bg = "green",
    fg = "white",
    font = myFont,
    )
button_home_stage.place(x=350,y=600)

button_start_stage = tk.Button(root,
    text="Start stage",
    width = 15,
    height = 2,
    command = lambda: [start_stage(), act_pos_val(), append_data()],
    bg = "blue",
    fg = "white",
    font = myFont,
    )
button_start_stage.place(x=100, y=650)

button_stop_stage = tk.Button(root,
    text="Stop Stage",
    width = 15,
    height = 2,
    command = stop_stage,
    bg = "red",
    fg = "white",
    font = myFont,
    )
button_stop_stage.place(x=300,y=650)

checkvar1 = tk.IntVar()
checkvar1.set(1) #make default on
check_feedback = tk.Checkbutton(text = "Feedback on",
                 variable = checkvar1,
                 # onvalue = 1, 
                 # offvalue = 0, 
                 height=1, 
                 width = 20,
                 font = myFont)
check_feedback.place(x=50,y=600)

#%% Buttons for relative move

des_pos = tk.IntVar()
des_pos_text = tk.Label(root, text = 'Desired Position', font = myFont)
des_pos_text.place(x=630, y=525)

def des_pos_val_add():
    cur_pos = int(des_pos.get())
    move_by = int(moverel_spin.get())
    new_des_pos = cur_pos + move_by
    des_pos.set(new_des_pos)
    des_pos_disp.config(textvariable = des_pos)
    
def des_pos_val_sub():
    cur_pos = int(des_pos.get())
    move_by = int(moverel_spin.get())
    new_des_pos = cur_pos - move_by
    des_pos.set(new_des_pos)
    des_pos_disp.config(textvariable = des_pos)

des_pos_disp = tk.Label(root, font = myFont)

moverel_stage_text = tk.Label(root, text = 'Move rel', font = myFont)
moverel_stage_text.place(x=450, y=520)
moverelval = tk.StringVar(root)
moverelval.set("1")
moverel_spin = tk.Spinbox(root, 
                        from_ = 0, to = 6, 
                        width = 5,
                        textvariable = moverelval, 
                        font = myFont)
moverel_spin.place(x=460, y=550)

button_moveup = tk.Button(root,
    command = des_pos_val_add,                      
    text="^",
    width = 3,
    height = 1,
    bg = "green",
    fg = "white",
    font = myFont,
    )
button_moveup.place(x=560, y=520)

des_pos_disp = tk.Label(root, font = myFont)
des_pos_disp.place(x=850, y=525)

button_movedown = tk.Button(root,
    command = des_pos_val_sub,                            
    text="v",
    width = 3,
    height = 1,
    bg = "green",
    fg = "white",
    font = myFont,
    )
button_movedown.place(x=560,y=570)

#%% For actual position

act_pos_text = tk.Label(root, text = 'Actual Position', font = myFont)
act_pos_text.place(x=630, y=575)

time1 = time.time()
def act_pos_val():
    
    curr_pos = motor.position
    act_pos_disp.config(text=curr_pos)
    act_pos_disp.after(50,act_pos_val)

act_pos_disp = tk.Label(root, font = myFont)
act_pos_disp.place(x=850, y=575)
# act_pos_val()

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

global k, t_vec, y, yw_vec#, w_vec, all_t_vec, all_y, all_w_vec, all_yw_vec
Nt = scanRate / 2
t_vec = np.linspace(0,Nt,Nt)
dt = t_vec[1]-t_vec[0]
w_vec = 2*np.pi/(2*dt)*np.linspace(-1,1,Nt)
dw = w_vec[1]-w_vec[0]
k = 0
tic = time.time()
all_t_vec = np.empty(1)
all_y = np.empty(1)
all_w_vec = np.empty(1)
all_yw_vec = np.empty(1)

def plot():
    global handle, scansPerRead, numAddresses, aScanList, scanRate, k, positions
    j = k
    global y, yw_vec
    
    if j == 0:
        scanRate1 = ljm.eStreamStart(handle, scansPerRead, numAddresses, aScanList, scanRate)
        ret = ljm.eStreamRead(handle) 
        aData = ret[0]
        aData_array = np.asarray(aData)
        y = (aData_array*10)
        yw_vec = np.fft.fftshift(np.fft.fft(np.fft.fftshift(y)))
        k = k + 1
    else:  
        ret = ljm.eStreamRead(handle) 
        aData = ret[0]
        aData_array = np.asarray(aData)
        y = (aData_array*10)
        yw_vec = np.fft.fftshift(np.fft.fft(np.fft.fftshift(y)))
    
    a.cla()
    a.plot(t_vec,y*1000,'.-')
    a.set_xlabel('Time (ms)')
    a.set_ylabel('Voltage (mV)')

    b.cla()
    b.plot(w_vec,np.abs(yw_vec))
    b.set_xlabel('Frequency (Hz)')
    b.set_ylabel('Intensity (a.u.)')

    canvas.draw()
    canvas2.draw()
    canvas.get_tk_widget().place(x=25, y=25)
    canvas2.get_tk_widget().place(x=525, y=25)
    fig_plot.after(50,plot)
        
fig_plot = tk.Frame(root)
tk.Frame(plot()).pack()

global df

def append_data():
    global all_t_vec, all_y, all_w_vec, all_yw_vec
    
    all_y = np.append(all_y, y)
    all_t_vec = np.append(all_t_vec, t_vec)
    all_w_vec = np.append(all_w_vec, w_vec)
    all_yw_vec = np.append(all_yw_vec, yw_vec)
    
    return (all_y, all_t_vec, all_w_vec, all_yw_vec)
    
def save(): 
#    global df, all_t_vec, all_y, all_w_vec, all_yw_vec
    (t,y,w,yw) = append_data()
    data = np.array([t,y,w,yw])
    data = data.T
    df = DataFrame(data, columns = ['Time','Voltage','Wavelength', 'Intensity'])
    files = [('All Files', '*.*'),  
             ('Python Files', '*.py'), 
             ('Text Document', '*.txt'),('CSV File','*.csv')] 
    file = asksaveasfile(filetypes = files, defaultextension = files) 
    df.to_csv (file, index = False, header=True)
  
button_save = tk.Button(root, text = 'Save data', width = 10, height = 2, bg = 'purple', fg = 'white', command = lambda : [save()]) 
button_save.place(x=850, y = 600)     

#%%

button_close_stage = tk.Button(root,
                               text = "Close stage",
                               # command = ser.close(),
                               width = 10,
                               height = 1,
                               bg = "blue",
                               fg = "white",
                               font = myFont,
                               )
button_close_stage.place(x=600, y=675)

button_quit = tk.Button(root,
    text="Quit",
    command = lambda: [root.destroy(),ljm.close(handle)],
    width = 10,
    height = 2,
    bg = "red",
    fg = "black",
    font = myFont,
    )
button_quit.place(x=850,y=650)

root.mainloop()


