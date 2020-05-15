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
from src.util.ShotsAlarmStrobe import ShotsAlarmStrobe
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
'''
####################################
##            NETWORK             ##
####################################
'''
# init network
'''
####################################
##           DISPLAY              ##
####################################
'''
lcd = ShotsAlarmSerLCD()

'''
####################################
##           SPOTIPY              ##
####################################
'''
# init spotipy instance and log in
mySpotipy = ShotsAlarmSpotipy(
    user = Private.USER,
    client_id = Private.CLIENT_ID,
    client_secret = Private.CLIENT_SECRET,
    redirect_uri = Private.REDIRECT_URI
)
# select our desired alarm song and get its length
songLength = mySpotipy.set_alarm_track(Private.SONG)
logger.debug(f"Selected '{Private.SONG}' with length {songLength}")

# set up alarm activate and cancel thread calls

def spotipy_activate_thread_call(event):
    """
    Wait for event then run the spotipy utility alarm activate function
    :param event: Threading event set at alarmActivate
    :return: None
    """
    while True:
        logger.debug("spotipy_activate_thread WAITING")
        event.wait()
        logger.debug("spotipy_activate_thread RUNNING")
        mySpotipy.alarm_activate()
        logger.debug("spotipy_activate_thread FINISHED")
        time.sleep(1)

def spotipy_cancel_thread_call(event):
    """
    Wait for event then run the spotipy utility alarm cancel function
    :param event: Threading event set at alarmCancel
    :return: None
    """
    while True:
        logger.debug("spotipy_cancel_thread WAITING")
        event.wait()
        logger.debug("spotipy_cancel_thread RUNNING")
        mySpotipy.alarm_cancel()
        logger.debug("spotipy_cancel_thread FINISHED")
        time.sleep(1)

'''
####################################
##             HUE                ##
####################################
'''
def hue_activate_thread_call(event):
    while True:
        logger.debug("hue_activate_thread WAITING")
        event.wait()
        logger.debug("hue_activate_thread RUNNING")
        logger.debug("hue_activate_thread FINISHED")
        time.sleep(1)

def hue_go_thread_call(event):
    while True:
        logger.debug("hue_go_thread WAITING")
        event.wait()
        logger.debug("hue_go_thread RUNNING")
        logger.debug("hue_go_thread FINISHED")
        time.sleep(1)

def hue_play_thread_call(event):
    while True:
        logger.debug("hue_play_thread WAITING")
        event.wait()
        logger.debug("hue_play_thread RUNNING")
        logger.debug("hue_play_thread FINISHED")
        time.sleep(1)

def hue_cancel_thread_call(event):
    while True:
        logger.debug("hue_cancel_thread WAITING")
        event.wait()
        logger.debug("hue_cancel_thread RUNNING")
        logger.debug("hue_cancel_thread FINISHED")
        time.sleep(1)

'''
####################################
##            STROBE              ##
####################################
'''
myStrobe = ShotsAlarmStrobe()

def strobe_go_thread_call(event):
    while True:
        logger.debug("strobe_go_thread WAITING")
        event.wait()
        logger.debug("strobe_go_thread RUNNING")
        myStrobe.on()
        logger.debug("strobe_go_thread FINISHED")
        time.sleep(1)

def strobe_play_thread_call(event):
    while True:
        logger.debug("strobe_play_thread WAITING")
        event.wait()
        logger.debug("strobe_play_thread RUNNING")
        myStrobe.off()
        logger.debug("strobe_play_thread FINISHED")
        time.sleep(1)

def strobe_cancel_thread_call(event):
    while True:
        logger.debug("strobe_cancel_thread WAITING")
        event.wait()
        logger.debug("strobe_cancel_thread RUNNING")
        myStrobe.off()
        logger.debug("strobe_cancel_thread FINISHED")
        time.sleep(1)

'''
####################################
##         UTILITY STATUS         ##
####################################
'''

# redneck thread management variable
running = True

# keep track of status of all utilities
status = {}

def status_thread_call():
    """
    Get the status of all utilities once per minute
    :return: None
    """
    while running:

        # get Spotify Status
        status['spotify'] = mySpotipy.get_status()

        # get Hue Status
        status['hue'] = None

        # get Network status
        status['network'] = None

        # report status to logger
        logger.debug(status)

        # wait one minute before checking again
        time.sleep(60)

'''
####################################
##         ALARM HANDLING         ##
####################################
'''

activated = False
cdLength = Private.COUNTDOWN_LENGTH
goLength = Private.GO_LENGTH

def activate_thread_call(event):
    global activated

    logger.debug("activate_thread WAITING")
    event.wait()
    logger.debug("activate_thread RUNNING")

    # flags for keeping track of which events have been set
    cdFlag, goFlag, playFlag, endFlag, = False, False, False, False

    # make note of the starting time
    startTime = int(time.time())

    # while the alarm is activated
    while activated:

        # get the elapsed time from activation start
        timeElapsed = int(time.time()) - startTime
        logger.debug(f"Elapsed time: {timeElapsed} s")

        # Initiate the Countdown stage
        if timeElapsed < cdLength:
            # check event flag
            if not cdFlag:
                cdFlag = True
                logger.debug("Countdown Stage")
                # for reference only
                # activate event already set in alarm_activate()

        # Initiate "GO" stage
        elif cdLength <= timeElapsed < cdLength + goLength:
            # check event flag
            if not goFlag:
                goFlag = True
                logger.debug("GO Stage")
                shotsGoEvent.set()
                shotsGoEvent.clear()

        # Initiate Play stage
        elif cdLength + goLength <= timeElapsed < songLength:
            # check event flag
            if not playFlag:
                playFlag = True
                logger.debug("Play Stage")
                shotsPlayEvent.set()
                shotsPlayEvent.clear()

        # Initiate End stage
        elif songLength < timeElapsed:
            # check event flag
            if not endFlag:
                endFlag = True
                logger.debug("End Stage")
                alarm_cancel()

        # A place we hope to never arrive at
        else:
            logger.debug("Please check space-time continuum")

        # attempt to keep time
        time.sleep(1)

    logger.debug("activate_thread FINISHED")

def alarm_activate():
    global activated
    logger.debug("Alarm Activated")
    if not activated:
        activated = True
        activateEvent.set()
        activateEvent.clear()


def alarm_cancel():
    logger.debug("Alarm Canceled")
    global activated
    if activated:
        activated = False
        cancelEvent.set()
        cancelEvent.clear()

        # allow cancel threads to complete
        logger.debug("Clearing all events...")
        time.sleep(2)
        # then reset all events
        activateEvent.clear()
        shotsGoEvent.clear()
        shotsPlayEvent.clear()
        cancelEvent.clear()
        logger.debug("All events have been cleared")

'''
####################################
##       THREAD MANAGEMENT        ##
####################################
'''
# init events
activateEvent = threading.Event()
shotsGoEvent = threading.Event()
shotsPlayEvent = threading.Event()
cancelEvent = threading.Event()

# initialize status thread (constantly runs)
status_thread = threading.Thread(target = status_thread_call)

# initialize all event-driven threads
activateThread = threading.Thread(target = activate_thread_call, args = [activateEvent])
spotipyActivateThread = threading.Thread(target = spotipy_activate_thread_call, args = [activateEvent])
spotipyCancelThread = threading.Thread(target = spotipy_cancel_thread_call, args = [cancelEvent])
hueActivateThread = threading.Thread(target = hue_activate_thread_call, args = [activateEvent])
hueGoThread = threading.Thread(target = hue_go_thread_call, args = [shotsGoEvent])
huePlayThread = threading.Thread(target = hue_play_thread_call, args = [shotsPlayEvent])
hueCancelThread = threading.Thread(target = hue_cancel_thread_call, args = [cancelEvent])
strobeGoThread = threading.Thread(target = strobe_go_thread_call, args = [shotsGoEvent])
strobePlayThread = threading.Thread(target = strobe_play_thread_call, args = [shotsPlayEvent])
strobeCancelThread = threading.Thread(target = strobe_cancel_thread_call, args = [cancelEvent])

# start all threads
status_thread.start()
activateThread.start()
spotipyActivateThread.start()
spotipyCancelThread.start()
hueActivateThread.start()
hueGoThread.start()
huePlayThread.start()
hueCancelThread.start()
strobeGoThread.start()
strobePlayThread.start()
strobeCancelThread.start()

# set up events for our pullstation
pullStation.when_pressed = alarm_activate
pullStation.when_released = alarm_cancel

while 1:
    time.sleep(0.5)

