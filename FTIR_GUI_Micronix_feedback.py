# -*- coding: utf-8 -*-
"""
Created on Mon Jun  1 12:36:30 2020

@author: TJ Hammond, edited by Nathan Drouillard
"""

import tkinter as tk
import tkinter.font as font #this is needed but unused?
from tkinter.filedialog import asksaveasfile
import time
# import matplotlib.pyplot as plt
import numpy as np
# import drawnow as drawnow

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

import serial


#%%

root = tk.Tk()
root.geometry("1024x768")

myFont = tk.font.Font(family='Helvetica', size=15, weight='bold')

#%% Functions for stage control

def home_stage():
    global ser
    # ser = serial.Serial('COM3',38400)
    ser.write(b'1ZRO\r') #zero the stage
    ser.write(b'1HOM\r') #home the stage
    ser.write(b'1WST\r') #wait for the stage to stop
    ser.flush()
    # ser.close()

def start_stage():
    global ser, startpos, stoppos
    min_pos = startpos.get()
    max_pos = stoppos.get()
    # abspos = -8
    # ser.write(b'1FBK3\r') #set to closed-loop feedback mode
    # ser.write(b'1PGL0\r') #loops the function continuously
    # ser.write(b'1WST\r')
    # move_start_str = "1MVA"+ str(start) + "\r" #move to start position
    # # ser.write(b'1MVA0\r')
    # move_start_byt = str.encode(move_start_str)
    # ser.write(move_start_byt)
    # ser.write(b'1WST\r')
    # move_stop_str = "1MVA"+ str(stop) + "\r" #move to stop position
    # # ser.write(b'1MVA0\r')
    # move_stop_byt = str.encode(move_stop_str)
    # ser.write(move_stop_byt)
    # ser.write(b'1WST\r')
    
    ser.write(b'1VEL5.0\r') #set velocity to 5 mm/s
    
    min_pos_str = "1MLN" + str(min_pos) + "\r"
    ser.write(b'1POS?\r')
    # ser.write(b'1MVA0\r')
    min_pos_byt = str.encode(min_pos_str) #encode soft travel limit in the negative direction
    ser.write(min_pos_byt) #write it to the controller
    
    max_pos_str = "1MLP" + str(max_pos) + "\r"
    max_pos_byt = str.encode(max_pos_str)
    ser.write(max_pos_byt)
    
    ser.write(b'1EPL1\r') #ensure the correct encoder polarity for the feedback loop
    ser.write(b'1FBK3\r') #closed loop feedback mode
    ser.write(b'4DBD5,0\r') #set closed loop deadband parameters (0 means it will never timeout)
    j = 0
    # timeout = 100
    global i
    i = 1
    
    # for i in range(0,timeout):
    while i == 1:
        if j == 0:
            ser.write(b'1MLN\r') #move to negative limit
            ser.write(b'1WST\r')
            ser.flush()
            j = 1
        else: #j ==1:
            ser.write(b'1MLP\r') #move to positive limit
            ser.write(b'1WST\r')
            ser.flush()
            j = 0
    
def stop_stage():
    global ser, i
    
    i = 2 
    ser.write(b'1STP\r')
    
#%% Buttons for stage loop

global ser
ser = serial.Serial('COM3',38400,timeout=10)
# print('Port opened')

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
startpos.set("0")
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
stoppos.set("1")
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
    command = lambda: [start_stage(), act_pos_val()],
    bg = "blue",
    fg = "white",
    font = myFont,
    )
button_start_stage.place(x=100, y=650)

button_stop_stage = tk.Button(root,
    text="Stop Stage",
    width = 15,
    height = 2,
    command = lambda: [stop_stage(),"break"],
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
    global ser
    # ser = serial.Serial('COM3',38400)
    # time2 = time.time()
    # timer = round(time2-time1,5)
    # ser.open()
    ser.write(b'1FBK?\r')
    ser.write(b'1POS?\r')
    ser.flush()
    pos1 = ser.readline()[-9:]
    # print(pos1)
    act_pos_disp.config(text=pos1)
    act_pos_disp.after(50,act_pos_val)

act_pos_disp = tk.Label(root, font = myFont)
act_pos_disp.place(x=850, y=575)
# act_pos_val()

#%% Plotting stuff

fig_time = Figure(figsize=(5,4))
ax_time = fig_time.add_subplot(111)       
canvas_time = FigureCanvasTkAgg(fig_time, master=root)

Nt = 100
t_vec = np.linspace(0,100,Nt)
dt = t_vec[1]-t_vec[0]
w_vec = 2*np.pi/(2*dt)*np.linspace(-1,1,Nt)
dw = w_vec[1]-w_vec[0]

tic = time.time()
def live_plotter_time():
    toc = time.time()
    timer = toc-tic
    yt_vec = np.sin(timer*10 + t_vec) + np.random.rand(Nt)
    ax_time.cla()
    ax_time.plot(t_vec,yt_vec)
    canvas_time.draw()
    canvas_time.get_tk_widget().place(x=25, y=25)
    fig_time_plot.after(50,live_plotter_time)

fig_time_plot = tk.Frame(root)
tk.Frame(live_plotter_time()).pack()


fig_freq = Figure(figsize=(5,4))
ax_freq = fig_freq.add_subplot(111)       
canvas_freq = FigureCanvasTkAgg(fig_freq, master=root)

def live_plotter_freq():
    toc = time.time()
    timer = toc-tic
    yt_vec = np.sin(timer*10 + t_vec) + np.random.rand(Nt)
    yw_vec = np.fft.fftshift(np.fft.fft(np.fft.fftshift(yt_vec)))
    ax_freq.cla()
    ax_freq.semilogy(w_vec,np.abs(yw_vec))
    ax_freq.set_xlim((0,w_vec[-1]))
    canvas_freq.draw()
    canvas_freq.get_tk_widget().place(x=525, y=25)
    fig_freq_plot.after(50,live_plotter_freq)

fig_freq_plot = tk.Frame(root)
tk.Frame(live_plotter_freq()).pack()

def save(): 
    files = [('All Files', '*.*'),  
             ('Python Files', '*.py'), 
             ('Text Document', '*.txt')] 
    file = asksaveasfile(filetypes = files, defaultextension = files) 
  
button_save = tk.Button(root, text = 'Save data', width = 10, height = 2, bg = 'purple', fg = 'white', command = lambda : save()) 
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
    command = lambda: [root.destroy(),ser.close()],
    width = 10,
    height = 2,
    bg = "red",
    fg = "black",
    font = myFont,
    )
button_quit.place(x=850,y=650)

root.mainloop()
