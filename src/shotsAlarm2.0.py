import asyncio
import sys

import src.Private as Private
import time
import threading
from gpiozero import Button
from src.util.ShotsAlarmSpotipy import ShotsAlarmSpotipy
from src.util.ShotsAlarmSerLCD import ShotsAlarmSerLCD
from src.util.ShotsAlarmHueControl import ShotsAlarmHueControl
from src.util.ShotsAlarmStrobe import ShotsAlarmStrobe
from src.util.ShotsNetworkController import ShotsNetworkController

import logging
from signal import pause

# set up logging
logger = logging.getLogger("Shots Alarm")
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

# globally init our pullstation and strobe
pullStation = Button(4)

logger.debug("GPIO initialized")

useHue = True
useDisplay = True
exitLock = threading.Lock()
logger.debug(f"Hue Integration: {useHue}")
logger.debug(f"Display Enabled: {useDisplay}")
'''
####################################
##            HUE                ##
####################################
'''
if useHue:
    hue = ShotsAlarmHueControl(Private.HUE_CONFIG)

'''
####################################
##            NETWORK             ##
####################################
'''
networkController = ShotsNetworkController()
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
    user=Private.USER,
    client_id=Private.CLIENT_ID,
    client_secret=Private.CLIENT_SECRET,
    redirect_uri=Private.REDIRECT_URI
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
        if useHue:
            hue.flashLights(hue.red, .75, Private.COUNTDOWN_LENGTH)
        logger.debug("hue_activate_thread RUNNING")
        logger.debug("hue_activate_thread FINISHED")
        time.sleep(1)


def hue_go_thread_call(event):
    while True:
        logger.debug("hue_go_thread WAITING")
        event.wait()
        if useHue:
            hue.flashLights(hue.green, .75, Private.GO_LENGTH)
        logger.debug("hue_go_thread RUNNING")
        logger.debug("hue_go_thread FINISHED")
        time.sleep(1)


def hue_play_thread_call(event):
    if useHue:
        hue.colorFade(True)
    while True:
        logger.debug("hue_play_thread WAITING")
        event.wait()
        if useHue:
            hue.colorFade(True)
        logger.debug("hue_play_thread RUNNING")
        logger.debug("hue_play_thread FINISHED")
        time.sleep(1)


def hue_cancel_thread_call(event):
    while True:
        logger.debug("hue_cancel_thread WAITING")
        event.wait()
        if useHue:
            hue.cancelFlash()
            hue.colorFade(True)
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
##            NETWORK             ##
####################################
'''


def network_thread_call():
    networkController.connect()
    while True:
        command = networkController.getData()
        if command == "ACTIVATE":
            alarm_activate()
        if command == "ABORT":
            alarm_cancel()


def display_activate_thread_call(event):
    while True:
        event.wait()
        lcd.shotsCountDown(Private.COUNTDOWN_LENGTH, Private.SONG)


def display_go_thread_call(event):
    while True:
        event.wait()
        lcd.shotsGo(Private.SONG)


def display_play_thread_call(event):
    while True:
        event.wait()
        lcd.playText(Private.SONG)


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

    currentStatus = 0

    while running:


        # get Spotify Status
        status['Spotify'] = mySpotipy.get_status()

        # get Hue Status
        if useHue:
            status['Hue'] = hue.getStatus()

        status["Network"] = networkController.getStatus()

        if not activated:
            line1 = ""
            currentStatusKey = list(status.keys())[currentStatus % len(list(status.keys()))]
            line2 = currentStatusKey + ": " + status.get(currentStatusKey)[0]
            currentStatus += 1

            for key in status.keys():
                if status.get(key)[1] != 0:
                    line1 += status.get(key)
            if line1 == "":
                line1 = "Ready"

            lcd.clear()
            lcd.write2Lines(line1, line2)

        # report status to logger
        logger.debug(status)

        # wait one minute before checking again
        time.sleep(10)


'''
####################################
##         ALARM HANDLING         ##
####################################
'''

activated = False
activated_lock = threading.Lock()
cdLength = Private.COUNTDOWN_LENGTH
goLength = Private.GO_LENGTH


def activate_thread_call(event):
    while True:

        logger.debug("activate_thread WAITING")
        event.wait()
        logger.debug("activate_thread RUNNING")

        # flags for keeping track of which events have been set
        cdFlag, goFlag, playFlag, endFlag, = False, False, False, False

        # make note of the starting time
        startTime = int(time.time())

        # while the alarm is activated
        logger.debug("Activated Lock Acquired")
        while event.isSet():

            # get the elapsed time from activation start
            timeElapsed = int(time.time()) - startTime
            logger.debug(f"Elapsed time: {timeElapsed} s")

            # Initiate the Countdown stage
            if timeElapsed < cdLength:
                # check event flag
                if not cdFlag:
                    cdFlag = True
                    logger.debug("Countdown Stage")
                    countDownEvent.set()
                    countDownEvent.clear()

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
    logger.debug("Alarm Activated")
    global activated
    if not activated:
        activated = True
        activateEvent.set()
    print("ActivateEvent: " + str(activateEvent.is_set()))


def alarm_cancel():
    logger.debug("Alarm Canceled")
    with activated_lock:
        logger.debug("Activated Lock Acquired")
        global activated
        if activated:
            activated = False
            activateEvent.clear()

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
countDownEvent = threading.Event()
shotsGoEvent = threading.Event()
shotsPlayEvent = threading.Event()
cancelEvent = threading.Event()



# initialize status thread (constantly runs)
status_thread = threading.Thread(target=status_thread_call)

# initialize all event-driven threads
activateThread = threading.Thread(target=activate_thread_call, args=[activateEvent])
spotipyActivateThread = threading.Thread(target=spotipy_activate_thread_call, args=[countDownEvent])
spotipyCancelThread = threading.Thread(target=spotipy_cancel_thread_call, args=[cancelEvent])
hueActivateThread = threading.Thread(target=hue_activate_thread_call, args=[countDownEvent])
hueGoThread = threading.Thread(target=hue_go_thread_call, args=[shotsGoEvent])
huePlayThread = threading.Thread(target=hue_play_thread_call, args=[shotsPlayEvent])
hueCancelThread = threading.Thread(target=hue_cancel_thread_call, args=[cancelEvent])
strobeGoThread = threading.Thread(target=strobe_go_thread_call, args=[shotsGoEvent])
strobePlayThread = threading.Thread(target=strobe_play_thread_call, args=[shotsPlayEvent])
strobeCancelThread = threading.Thread(target=strobe_cancel_thread_call, args=[cancelEvent])
display_activate_thread = threading.Thread(target=display_activate_thread_call, args=[countDownEvent])
display_go_thread = threading.Thread(target=display_go_thread_call, args=[shotsGoEvent])
display_play_thread = threading.Thread(target=display_play_thread_call, args=[shotsPlayEvent])
networkControllerThread = threading.Thread(target=network_thread_call)

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
display_play_thread.start()
display_go_thread.start()
display_activate_thread.start()
networkControllerThread.start()

# set up events for our pullstation
pullStation.when_pressed = alarm_activate
pullStation.when_released = alarm_cancel

try:
    pause()
except:
    networkController.close()
    lcd.shutdown()
    logger.info("Network Shutdown")
    sys.exit(0)
