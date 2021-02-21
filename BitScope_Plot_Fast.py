#/usr/bin/pypy

"""
Created on Sun Feb 21 2021

For fast plotting of the BitScope signal, no FFT or stage movement

@author: Nathan Drouillard, modified from FTIR_GUI_Thorlabs(Final).py
A special thanks is owed to Aananth Kanagaraj (Codenio)
"""
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

from bitlib_read_data_for_GUI import stream #this is a script I wrote from "bitlib-read-data.py"

#%%

root = tk.Tk()
root.geometry("1024x768")
root.title("FTIR GUI")

myFont = tk.font.Font(family='Helvetica', size=15, weight='bold')

#%% Major variables
scanRate = 20000000 #1000000 is the default sample rate of the BitScope
global Nt, now
Nt = 5000 #maximum number of points from BitScope
myFont = ("Helvetica",12)
now = str(datetime.now())

#%% Plotting stuff

fig_time = Figure(figsize=(5,4))
ax_time = fig_time.add_subplot(111)
canvas_time = FigureCanvasTkAgg(fig_time, master=root)

f = Figure(figsize=(5,5),dpi=100)#, tight_layout=True)
#f3 = Figure(figsize=(5,5),dpi=100)
#d = f3.add_subplot(111)
a = f.add_subplot(111)

canvas = FigureCanvasTkAgg(f, root)

global k, t_vec, y, yw_vec#, w_vec, all_t_vec, all_y, all_w_vec, all_yw_vec
k = 0
tic = time.time()
all_t_vec = np.empty(1)
all_y = np.empty(1)
all_w_vec = np.empty(1)
all_yw_vec = np.empty(1)

old_time = 0
def plot():
    global Nt, scanRate, old_time
    global t_vec, y, yw_vec, w_vec, tic

    y = stream(scanRate,Nt) #call the scope_stream function from the BitScope_stream code. These parameters are sampling rate and array size

    tmin = old_time
    tmax = time.perf_counter()
    old_time = tmax
    t_vec = np.linspace(tmin,tmax,len(y))

    a.cla()
    a.plot(t_vec,y,'.-')
    a.set_xlabel('Time (s)')
    a.set_ylabel('Voltage (V)')

    canvas.draw()
    canvas.get_tk_widget().place(x=250, y=25)
    fig_plot.after(1,plot)

fig_plot = tk.Frame(root)
tk.Frame(plot()).pack()

global df

def append_data():
    global t_vec, y, w_vec, all_t_vec, all_y, all_w_vec, all_yw_vec

    all_y = np.append(all_y, y)
    all_t_vec = np.append(all_t_vec, t_vec)
    all_w_vec = np.append(all_w_vec, w_vec)
    all_yw_vec = np.append(all_yw_vec, yw_vec)

    return (all_t_vec, all_y, all_w_vec, all_yw_vec)

def save():
#    global df, all_t_vec, all_y, all_w_vec, all_yw_vec
    (t,y,w,yw) = append_data()
    data = np.array([t,y,w,yw])
    data = data.T
    df = DataFrame(data, columns = ['Time','Voltage','Wavelength', 'Intensity'])
    file = open("/home/pi/Documents/BitScope Data"+ now +"save_test.csv","a")
    df.to_csv (file, sep='\t', index = False, header=True)
    print("Data saved")

button_record = tk.Button(root, #this button is an edited version of the start_stage_button from FTIR_GUI_Thorlabs(Final).py
    text="Start recording",
    width = 15,
    height = 2,
    command = lambda: [append_data()],
    bg = "blue",
    fg = "white",
    font = myFont,
    )
button_record.place(x=100, y=650)

button_save = tk.Button(root, text = 'Save data', width = 10, height = 2, bg = 'purple', fg = 'white', command = lambda : [save()])
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
button_quit.place(x=850,y=640)

root.mainloop()
