import src.Private as Private
import sys
import time
import threading
import multiprocessing
import queue
from gpiozero import Button
from src.util.ShotsAlarmSpotipy import ShotsAlarmSpotipy
from src.util.ShotsAlarmSerLCD import ShotsAlarmSerLCD
from src.util.ShotsAlarmHueControl import ShotsAlarmHueControl
from datetime import datetime, timedelta
from phue import Bridge
from RPLCD.gpio import CharLCD
from RPi import GPIO

import logging
from enum import Enum

# set up logging
logger = logging.getLogger("Shots Alarm")
logger.setLevel(logging.DEBUG)

# globally init our pullstation and strobe
GPIO.setmode(GPIO.BCM)
pullStation = Button(4)

logger.debug("GPIO initialized")

useHue = False
useDisplay = True
logger.debug(f"Hue Integration: {useHue}")
logger.debug(f"Display Enabled: {useDisplay}")

# init display
lcd = ShotsAlarmSerLCD()

# init spotipy instance and log in
mySpotipy = ShotsAlarmSpotipy(
    user = Private.USER,
    client_id = Private.CLIENT_ID,
    client_secret = Private.CLIENT_SECRET,
    redirect_uri = Private.REDIRECT_URI
)
# select our desired alarm song and get its length
songLength = mySpotipy.setAlarmTrack(Private.SONG)
logger.debug(f"Selected '{Private.SONG}' with length {songLength}")

# init hue
# init network

# redneck thread management variable
running = True

# keep track of status of all utilities
status = {}

def statusThreadCall():
    """
    Get the status of all utilities once per minute
    :return: None
    """
    while running:

        # get Spotify Status
        status['spotify'] = mySpotipy.getStatus()

        # get Hue Status
        status['hue'] = None

        # get Network status
        status['network'] = None

        # report status to logger
        logger.debug(status)

        # wait one minute before checking again
        time.sleep(60)

def spotipyActivateThreadCall(event):
    """
    Wait for event then run the spotipy utility alarm activate function
    :param event: Threading event set at alarmActivate
    :return: None
    """
    event.wait()
    mySpotipy.alarmActivate()

def spotipyCancelThreadCall(event):
    """
    Wait for event then run the spotipy utility alarm cancel function
    :param event: Threading event set at alarmCancel
    :return: None
    """
    event.wait()
    mySpotipy.alarmCancel()

def hueActivateThreadCall(event):
    pass

def strobeActivateThreadCall(event):
    start = time.time()
    if

def alarmActivate():
    alarm.set()
    strobe.on()

def alarmCancel():
    alarm.clear()
    strobe.off()

activateEvent = threading.Event()
cancelEvent = threading.Event()

task1_thread = threading.Thread(target = task1, args = [event])

status_thread = threading.Thread(target = statusThreadCall)
spotipyActivate_thread = threading.Thread(target = spotipyActivateThreadCall, args = [event])

task1_thread.start()
task2_thread.start()
status_thread.start()

# set up events for our pullstation
pullStation.when_pressed = alarmActivate
pullStation.when_released = alarmCancel

while 1:
    time.sleep(0.5)

