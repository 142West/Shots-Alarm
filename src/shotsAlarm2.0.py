import src.Private as Private
import sys
import time
import threading
import queue
from gpiozero import Button, DigitalOutputDevice
from src.util.ShotsAlarmSpotipy import ShotsAlarmSpotipy
from src.util.ShotsAlarmSerLCD import ShotsAlarmSerLCD
from datetime import datetime, timedelta
from phue import Bridge
from RPLCD.gpio import CharLCD
from RPi import GPIO
import logging

# set up logging
logger = logging.getLogger("Shots Alarm")
logger.setLevel(logging.DEBUG)

# globally init our pullstation and strobe
GPIO.setmode(GPIO.BCM)
pullStation = Button(4)
strobe = DigitalOutputDevice(17)
strobe.off()
logger.debug("GPIO initialized")

useHue = False
logger.debug(f"Hue Integration: {useHue}")

lcd = CharLCD(numbering_mode=GPIO.BCM, cols=16, rows=2, pin_rs=26, pin_e=19, pins_data=[21, 20, 16, 12, 13, 6, 5, 11])

# fullscreen (0 for test, 1 for run)
fullscreen = False


class hueControl:
    def __init__(self):
        self.cIntensity = 175
        self.fIntensity = 254
        self.nIntensity = 128
        # self.tTime = 50
        self.nDelay = 5

        self.red = [0.6901, 0.3076]
        self.magenta = [0.4343, 0.1936]
        self.blue = [0.1541, 0.0836]
        self.lblue = [0.1695, 0.3364]
        self.green = [0.2073, 0.6531]
        self.yellow = [0.4898, 0.4761]
        self.orange = [0.5706, 0.4078]

        self.b = Bridge('10.142.1.114')
        self.b.connect()

        self.b.get_api()

    def updateLR(self, command):
        self.b.set_group(4, command)

    def updateDoor(self, command):
        self.b.set_group(5, command)

    def updateHW(self, command):
        self.b.set_group(6, command)

    def updateKitchen(self, command):
        self.b.set_group(2, command)

    def flashLights(self, color, delay, seconds):
        command = {'transitiontime': 1, 'xy': color, 'bri': self.fIntensity}
        self.b.set_group(0, command)

        for i in range(1, (seconds + 1)):
            command = {'transitiontime': 1, 'on': False}
            self.b.set_group(0, command)
            time.sleep(delay)

            command = {'transitiontime': 1, 'on': True, 'bri': self.fIntensity}
            self.b.set_group(0, command)
            time.sleep(delay)

    def advanceAsOne(self, tTime):
        lrColor = self.b.get_light(10, 'xy')

        if lrColor == self.red:
            lrCommand = {'transitiontime': tTime, 'xy': self.magenta, 'bri': self.nIntensity}
        elif lrColor == self.magenta:
            lrCommand = {'transitiontime': tTime, 'xy': self.blue, 'bri': self.nIntensity}
        elif lrColor == self.blue:
            lrCommand = {'transitiontime': tTime, 'xy': self.lblue, 'bri': self.nIntensity}
        elif lrColor == self.lblue:
            lrCommand = {'transitiontime': tTime, 'xy': self.green, 'bri': self.nIntensity}
        elif lrColor == self.green:
            lrCommand = {'transitiontime': tTime, 'xy': self.yellow, 'bri': self.nIntensity}
        elif lrColor == self.yellow:
            lrCommand = {'transitiontime': tTime, 'xy': self.orange, 'bri': self.nIntensity}
        else:
            lrCommand = {'transitiontime': tTime, 'xy': self.red, 'bri': self.nIntensity}

        self.b.set_group(0, lrCommand)

    def advanceLights(self, tTime):
        lrColor = self.b.get_light(10, 'xy')

        if lrColor == self.red:
            lrCommand = {'transitiontime': tTime, 'xy': self.magenta, 'bri': self.nIntensity}
            doorCommand = {'transitiontime': tTime, 'xy': self.blue, 'bri': self.nIntensity}
            hwCommand = {'transitiontime': tTime, 'xy': self.lblue, 'bri': self.nIntensity}
            kitchenCommand = {'transitiontime': tTime, 'xy': self.green, 'bri': self.nIntensity}
        elif lrColor == self.magenta:
            lrCommand = {'transitiontime': tTime, 'xy': self.blue, 'bri': self.nIntensity}
            doorCommand = {'transitiontime': tTime, 'xy': self.lblue, 'bri': self.nIntensity}
            hwCommand = {'transitiontime': tTime, 'xy': self.green, 'bri': self.nIntensity}
            kitchenCommand = {'transitiontime': tTime, 'xy': self.yellow, 'bri': self.nIntensity}
        elif lrColor == self.blue:
            lrCommand = {'transitiontime': tTime, 'xy': self.lblue, 'bri': self.nIntensity}
            doorCommand = {'transitiontime': tTime, 'xy': self.green, 'bri': self.nIntensity}
            hwCommand = {'transitiontime': tTime, 'xy': self.yellow, 'bri': self.nIntensity}
            kitchenCommand = {'transitiontime': tTime, 'xy': self.orange, 'bri': self.nIntensity}
        elif lrColor == self.lblue:
            lrCommand = {'transitiontime': tTime, 'xy': self.green, 'bri': self.nIntensity}
            doorCommand = {'transitiontime': tTime, 'xy': self.yellow, 'bri': self.nIntensity}
            hwCommand = {'transitiontime': tTime, 'xy': self.orange, 'bri': self.nIntensity}
            kitchenCommand = {'transitiontime': tTime, 'xy': self.red, 'bri': self.nIntensity}
        elif lrColor == self.green:
            lrCommand = {'transitiontime': tTime, 'xy': self.yellow, 'bri': self.nIntensity}
            doorCommand = {'transitiontime': tTime, 'xy': self.orange, 'bri': self.nIntensity}
            hwCommand = {'transitiontime': tTime, 'xy': self.red, 'bri': self.nIntensity}
            kitchenCommand = {'transitiontime': tTime, 'xy': self.magenta, 'bri': self.nIntensity}
        elif lrColor == self.yellow:
            lrCommand = {'transitiontime': tTime, 'xy': self.orange, 'bri': self.nIntensity}
            doorCommand = {'transitiontime': tTime, 'xy': self.red, 'bri': self.nIntensity}
            hwCommand = {'transitiontime': tTime, 'xy': self.magenta, 'bri': self.nIntensity}
            kitchenCommand = {'transitiontime': tTime, 'xy': self.blue, 'bri': self.nIntensity}
        else:
            lrCommand = {'transitiontime': tTime, 'xy': self.red, 'bri': self.nIntensity}
            doorCommand = {'transitiontime': tTime, 'xy': self.magenta, 'bri': self.nIntensity}
            hwCommand = {'transitiontime': tTime, 'xy': self.blue, 'bri': self.nIntensity}
            kitchenCommand = {'transitiontime': tTime, 'xy': self.lblue, 'bri': self.nIntensity}

        self.updateLR(lrCommand)
        self.updateDoor(doorCommand)
        self.updateHW(hwCommand)
        self.updateKitchen(kitchenCommand)


class DisplayController:
    def __init__(self, queue):
        self.queue = queue

    def setMessage(self, value):
        logger.info(value)
        lcd.clear()
        lcd.write_string(value)

    def processIncoming(self, cdLen, goHold, songLen):
        """Handle all messages currently in the queue, if any."""
        while self.queue.qsize():
            try:
                count = self.queue.get(0)

                # did we actually send something in the queue
                if not count == None:

                    # countdown stage
                    if (count < cdLen):
                        self.setMessage("SHOTS IN: {}".format(cdLen - count))

                    # GO!! stage
                    else:
                        # turn strobe on
                        strobe.on()
                        # alternate between GO and blank
                        if (count % 2):
                            self.setMessage("GO!! GO!! GO!!")
                        else:
                            self.setMessage("")

                else:  # count == None
                    # hide GUI
                    self.setMessage("")
                    # turn off strobe
                    strobe.off()

            except queue.Empty:
                # just on general principles, although we don't
                # expect this branch to be taken in this case
                pass



#######################
## Thread Management ##
#######################

class ThreadedClient:
    """
    Launch the main part of the GUI and the worker thread. periodicCall and
    endApplication could reside in the GUI part, but putting them here
    means that you have all the thread controls in a single place.
    """

    def __init__(self, user, song, cdLen, goHold):
        """
        Start the GUI and the asynchronous threads. We are in the main
        (original) thread of the application, which will later be used by
        the GUI as well. We spawn a new thread for the worker (I/O).
        """

        # GUI will be visible after tkinter.Tk()
        # hide the GUI window for now
        self.guiVisible = 1

        # keep track of whether alarm is active or not
        self.shotsFired = 0

        # keep track of whether we have flashed hue
        self.flashed = 0
        self.flashed2 = 0

        # keep track of seconds into a given track
        self.count = 0

        # keep track of length (sec) of selected song
        # this will be assigned at alarmActivate()
        self.songLength = 0

        # holding place for details of interrupted song
        # assigned at alarmActivate() and recalled in alarmCancel()
        self.bookmark = None

        # song countdown length
        # this is assigned by init call
        self.cdLen = cdLen

        # how long to display "GO!!"
        # this is assigned by init call
        self.goHold = goHold

        # Create the queue
        self.queue = queue.Queue()

        # Create a lock to access shared resources amongst threads
        self.lock = threading.RLock()

        # Set up the GUIPart
        self.display = DisplayController(self.queue)

        # Set up the Spotify instance
        self.mySpotipy = ShotsAlarmSpotipy(user, Private.CLIENT_ID, Private.CLIENT_SECRET, Private.REDIRECT_URI)

        # What song are we going to play??
        self.song = self.mySpotipy.getTrackFromDict(song)

        # setup hue
        if (useHue):
            self.myHue = hueControl()

        # Set up the thread to do asynchronous I/O
        self.running = 1
        self.timerThread = threading.Thread(target=self.timerThreadCall)
        self.timerThread.start()

        self.watchdogThread = threading.Thread(target=self.watchdogThreadCall)
        self.watchdogThread.start()

        self.hueThread = threading.Thread(target=self.hueThreadCall)
        self.hueThread.start()

        # eventually merge this into hueThread and remove
        self.hueThread2 = threading.Thread(target=self.hueThread2Call)
        self.hueThread2.start()

        self.networkThread = threading.Thread(target=self.networkThreadCall)
        self.networkThread.start()

        self.displayThread = threading.Thread(target=self.displayThreadCall)
        self.displayThread.start()

    ###########################################
    ## Worker Threads (for asynchronous I/O) ##
    ###########################################

    def timerThreadCall(self):  # ORIGINAL-WORKING
        """
        This is where we handle the asynchronous I/O. For example, it may be
        a 'select(  )'. One important thing to remember is that the thread has
        to yield control pretty regularly, by select or otherwise.
        """
        # make sure we have access to shared resource
        with self.lock:
            # set count to 0 if this is our first run through
            self.count = 0

        while self.running:
            # make sure we have access to shared resource
            with self.lock:
                logger.debug("timer acquired lock")
                # make sure shots is activated
                if self.shotsFired:
                    # make sure we haven't been counting longer than the song length
                    if (self.count <= self.songLength):
                        # update queue with count if countdown stage or go stage
                        if (self.count <= (self.cdLen + self.goHold)):
                            self.queue.put(self.count)
                        else:  # not in countdown stage or go stage
                            self.queue.put(None)
                        # increment counter
                        self.count += 1
                    else:  # song has ended
                        self.alarmCancel()

                else:  # shots not fired
                    pass
            logger.debug("timer released lock")
            time.sleep(1)

    # runs once an hour to make sure
    # count doesn't get too big
    def watchdogThreadCall(self):
        while self.running:
            time.sleep(3600)
            if self.count >= 3600:
                # make sure we have access to shared resource
                with self.lock:
                    logger.debug("watchdog acquired lock")
                    self.count = 0
                logger.debug("watchdog released lock")


    def hueThreadCall(self):
        while self.running:
            if useHue:
                if self.shotsFired and not self.flashed:
                    time.sleep(0.2)
                    self.flashed = 1
                    self.myHue.flashLights(self.myHue.red, 1, 5)
                elif self.shotsFired and self.flashed and self.count >= 6 and self.count <= self.cdLen:
                    # self.myHue.advanceLights(1)
                    self.myHue.advanceAsOne(1)
                    time.sleep(1)
                elif self.shotsFired and self.flashed and not self.flashed2 and self.count >= self.cdLen:
                    print("green")
                    self.flashed2 = 1
                    self.myHue.flashLights(self.myHue.green, 1, 5)
                else:
                    time.sleep(0.2)

    def hueThread2Call(self):
        while self.running:
            if not self.shotsFired and useHue == True:
                self.myHue.advanceLights(50)
            time.sleep(10)

    def networkThreadCall(self):
        while self.running:
            time.sleep(0.2)
            pass

    def displayThreadCall(self):
        """
        Check every 200 ms if there is something new in the queue.
        """
        self.display.processIncoming(self.cdLen, self.goHold, self.songLength)
        if not self.running:
            # This is the brutal stop of the system.
            # should do some cleanup before actually shutting it down.
            sys.exit(1)
        time.sleep(0.2)

    ##########################
    ## PullStation Tracking ##
    ##########################

    def alarmActivate(self):
        if not self.shotsFired:
            logger.info("Alarm Activated")

            # PULL SPOTIFY DATA
            # make sure we can get a spotify token or refresh
            if not self.mySpotipy.spLogin():

                if useHue == True:
                    # set hue flashed to 0
                    self.flashed = 0
                    self.flashed2 = 0

                # (this is now handled in ProcessIncoming)
                # turn on strobe
                # strobe.on()

                # save our current spot
                self.bookmark = self.mySpotipy.saveSpot()
                logger.debug(f"Saved bookmark {self.bookmark}")

                # get the length of the new song
                self.songLength = self.mySpotipy.getSongLength(self.song)
                logger.debug(f"Injected song length = {(self.seconds2string(self.songLength))}")

                # keep track of whether or not wer are running Shots
                self.shotsFired = 1

                # play our desired song
                self.mySpotipy.playNoContext(self.song)

                # CRANK IT UP
                #self.mySpotipy.volumeUp()

                # keep track of alarm activation
                self.shotsFired = 1

            else:  # couldn't get token or refresh
                logger.critical("Can't log in to spotify")
                pass

        else: #shots already fired
            logger.warning("Alarm already activated")
            pass

        # make sure we have access to shared resource
        with self.lock:
            logger.debug("alarmActivate acquired lock")
            self.count = 0
        logger.debug("alarmActivate released lock")

    def alarmCancel(self):
        # if we haven't already canceled
        if self.shotsFired:
            logger.info("Alarm Canceled")

            # keep track of alarm activation
            self.shotsFired = 0
            if useHue == True:
                self.flashed = 1
                self.flashed2 = 1

            # make sure we have access to shared resource
            with self.lock:
                logger.debug("alarmCancel acquired lock")
                self.count = 0
            logger.debug("alarmCancel released lock")

           # (this handled in ProcessIncoming, here for redundancy)
            # turn off strobe
            strobe.off()

            # make sure we can get a spotify token or refresh
            if not self.mySpotipy.spLogin():
                # return to previously playing song
                if self.bookmark:
                    self.mySpotipy.playWithContext(self.bookmark)
                    #self.mySpotipy.volumeDown()
                    logger.debug(f"Returned to bookmark {self.bookmark}")

            else:  # couldn't get token or refresh
                logger.critical("Can't log in to spotify")
                pass

        else: # alarm already canceled
            logger.warning("Alarm has already been canceled")
            pass

    ############################
    ## Time String Formatting ##
    ############################

    # convert seconds to minutes:seconds format, return in array.
    def seconds2time(self, secs):
        MinSec = datetime(1, 1, 1) + timedelta(seconds=secs)
        return [MinSec.minute, MinSec.second]

    # take minutes, seconds array and return as sting (MM:SS)
    def time2string(self, MinSec):
        timeStr = "%02d:%02d" % (MinSec[0], MinSec[1])
        return timeStr

    # take seconds, return as string (MM:SS)
    def seconds2string(self, secs):
        return self.time2string(self.seconds2time(secs))


# set ThreadedClient params
# user = "aflynn73"
user = "8w5yxlh9yqr8ooaizx3ca7grp" #moptechdev
# user = "59nmtms76slm25a959sz7kieb"
# user = "vollumd2"

# song = "Shots" # standard
# song = "White Noise" # for testing
# song = "Never Gonna Give You Up" for trolling
# song = "Like A Dream" # for testing without having to listen to "Shots" repeatedly
song = "Hallelujah" # short for testing song-end behavior

cdLen = 60
goHold = 15

# initialize our main thread management and pass root
client = ThreadedClient(user, song, cdLen, goHold)

# set up events for our pullstation
pullStation.when_pressed = client.alarmActivate
pullStation.when_released = client.alarmCancel
