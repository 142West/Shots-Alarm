import sys
import time
from gpiozero
import spotipy
import spotipy.util as util

version = sys.hexversion
if 0x03000000 <= version < 0x03010000 :
    import tkinter
    import ttk
elif version >= 0x03010000:
    import tkinter
    import tkinter.ttk as ttk
else: # version < 0x03000000
    import Tkinter as tkinter
    import ttk

class ShotsAlarm:
    def __init__(self, 
