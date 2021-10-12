# -*- coding: utf-8 -*-
"""
Created on Fri Jul 17 14:52:44 2020

@author: Nathan Drouillard

Run this program to close a stream from the Labjack. 
This is helpful if your code throws an error before it has a chance to close the handle.
"""
from labjack import ljm

handle = ljm.openS("T7", "USB", "ANY")
ljm.eStreamStop(handle)
ljm.close(handle)

print("Labjack closed, ready to start a new stream.")