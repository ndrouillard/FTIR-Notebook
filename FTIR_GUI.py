# -*- coding: utf-8 -*-
"""
Created on Tue Jul  7 13:54:35 2020

@author: TJ Hammond
"""

import tkinter as tk
import tkinter.font as font #this is needed but unused?
import time
import numpy as np
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

#%%
root = tk.Tk()
root.geometry("1024x768")

myFont = tk.font.Font(family='Helvetica', size=15, weight='bold')


#%% Buttons for stage loop

start_stage_text = tk.Label(root, text = 'Start Position', font = myFont)
start_stage_text.place(x=100, y=520)
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
stoppos = tk.StringVar(root)
stoppos.set("1")
start_spin = tk.Spinbox(root, 
                        from_ = -6, to = 6, 
                        width = 5,
                        textvariable = stoppos, 
                        font = myFont)
start_spin.place(x=275, y=550)

button_start_stage = tk.Button(root,
    text="Start stage",
    width = 15,
    height = 2,
    bg = "blue",
    fg = "white",
    font = myFont,
    )
button_start_stage.place(x=100, y=650)

button_stop_stage = tk.Button(root,
    text="Stop Stage",
    width = 15,
    height = 2,
    bg = "red",
    fg = "white",
    font = myFont,
    )
button_stop_stage.place(x=300,y=650)

checkvar1 = tk.IntVar()
checkvar1.set(1) #make default on
check_feedback = tk.Checkbutton(text = "Feedback on",
                  variable = checkvar1, 
                  onvalue = 1, 
                  offvalue = 0, 
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
    time2 = time.time()
    timer = round(time2-time1,5)
    act_pos_disp.config(text=timer)
    act_pos_disp.after(50,act_pos_val)

act_pos_disp = tk.Label(root, font = myFont)
act_pos_disp.place(x=850, y=575)
act_pos_val()


#%% Plotting stuff

fig_time = Figure(figsize=(5,4))
ax_time = fig_time.add_subplot(111)       
canvas_time = FigureCanvasTkAgg(fig_time, master=root)

Nt = 1000
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


#%%
button_quit = tk.Button(root,
    text="Quit",
    command = root.destroy,
    width = 10,
    height = 2,
    bg = "red",
    fg = "black",
    font = myFont,
    )
button_quit.place(x=850,y=650)

root.mainloop()
