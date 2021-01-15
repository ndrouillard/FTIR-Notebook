"""
Created on Thurs Jan 7 2021

@author: Nathan Drouillard, modified from BitScope_GUI_v4.py, which comes from FTIR_GUI_Thorlabs(Final).py
A special thanks is owed to Aananth Kanagaraj (Codenio)

Note: use BL_STREAM mode in bitlib_read_data_for_GUI
"""
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

from bitlib_read_data_for_GUI import stream #this is a script I wrote from "bitlib-read-data.py"

#%%

root = tk.Tk()
root.geometry("1024x768")
root.title("FTIR GUI")

myFont = tk.font.Font(family='Helvetica', size=15, weight='bold')

#%% Major variables
global Nt, scanRate, now
scanRate = 20000000 #1000000 is the default sample rate of the BitScope, 20 MHz is the max
Nt = 60000#12228 #maximum is 12228 but 60,000 is much faster?
myFont = ("Helvetica",12)
now = str(datetime.now()) #this is for naming the csv file by the date
#%%

#%% For later
c = 3e8
poslim = 1e-2 #1cm (these are the stage limits)
neglim = -1e-2
d = poslim + np.abs(neglim)
optical_t = np.linspace(0,d/c,Nt)

#%% Functions
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

def record():

    global Nt, scanRate, old_time
    global t_vec, y, w_vec, yw_vec, tic, all_t_vec, all_y, all_w_vec, all_yw_vec

    y = stream(scanRate,Nt)

    tmin = old_time
    tmax = time.perf_counter()
    old_time = tmax
    t_vec = np.linspace(tmin,tmax,len(y))
    dt = t_vec[1]-t_vec[0]
    w_vec = 2*np.pi/(2*dt)*np.linspace(-1,1,len(y))
    dw = w_vec[1]-w_vec[0]
    yw_vec = np.fft.fftshift(np.fft.fft(np.fft.fftshift(y)))

    return (t_vec, y, w_vec, yw_vec)

dummy_button = tk.Button(root, text="Example")
dummy_button.after(int(1e-6), record)

def append_data():

    global t_vec, y, w_vec, yw_vec, all_t_vec, all_y, all_w_vec, all_yw_vec

    all_y = np.append(all_y, y)
    all_t_vec = np.append(all_t_vec, t_vec)
    all_w_vec = np.append(all_w_vec, w_vec)
    all_yw_vec = np.append(all_yw_vec, yw_vec)

    count = len(all_yw_vec)
    data_count_disp.config(text=count)
    data_count_disp.after(int(1e-6),append_data)

    return (all_t_vec, all_y, all_w_vec, all_yw_vec)

data_count_disp = tk.Label(root, font = myFont)
data_count_disp.place(x=750, y=600)

data_count_text = tk.Label(root, text = 'Data Points Processed', font = myFont)
data_count_text.place(x=575, y=600)

def write_to_file():

    (t,y,w,yw) = append_data()
    data = np.array([t[1:],y[1:],w[1:],yw[1:]])
    data = data.T
    df = DataFrame(data, columns = ['Time','Voltage','Wavelength', 'Intensity'])
    file = open("/home/pi/Documents/BitScope Data"+ now +"save_test.csv","a")
    df.to_csv (file, sep='\t', index = False, header=True)
    print("Data saved")

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

button_record = tk.Button(root, #this button is an edited version of the start_stage_button from FTIR_GUI_Thorlabs(Final).py
    text="Start recording",
    width = 15,
    height = 2,
    command = lambda: [append_data()],#, data_count()],
    bg = "blue",
    fg = "white",
    font = myFont,
    )
button_record.place(x=100, y=650)

button_save = tk.Button(root, text = 'Save data', width = 10, height = 2, bg = 'purple', fg = 'white', command = lambda : [write_to_file()])
button_save.place(x=850, y = 600)

button_quit = tk.Button(root,
    text="Quit",
    command = lambda: [root.destroy()],#, close_BitScope()],
    width = 10,
    height = 2,
    bg = "red",
    fg = "black",
    font = myFont,
    )
button_quit.place(x=850,y=650)

record()
root.mainloop()
