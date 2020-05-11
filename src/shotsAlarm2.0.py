import src.Private as Private
import sys
import time
import threading
import queue
from gpiozero import Button, DigitalOutputDevice
from src.util.ShotsAlarmSpotipy import ShotsAlarmSpotipy
from src.util.ShotsAlarmSerLCD import ShotsAlarmSerLCD
from src.util.ShotsAlarmHueControl import ShotsAlarmHueControl
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
useDisplay = True
logger.debug(f"Hue Integration: {useHue}")
logger.debug(f"Display Enabled: {useDisplay}")

#lcd = CharLCD(numbering_mode=GPIO.BCM, cols=16, rows=2, pin_rs=26, pin_e=19, pins_data=[21, 20, 16, 12, 13, 6, 5, 11])

class DisplayController:
    def __init__(self, queue):
        self.queue = queue
        self.lcd = ShotsAlarmSerLCD()

    def setMessage(self, value):
        logger.info(value)
        self.lcd.clear()
        self.lcd.setColorName("White")
        self.lcd.writeCenter(value)

    def processIncoming(self, cdLen, goHold, songLen):
        """Handle all messages currently in the queue, if any."""
        while self.queue.qsize():
            try:
                count = self.queue.get(0)

                # did we actually send something in the queue
                if not count == None:

                    # countdown stage
                    if (count < cdLen):
                        self.setMessage(f"SHOTS IN: {cdLen - count}")

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
        Start the asynchronous threads.
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
            self.myHue = ShotsAlarmHueControl(Private.HUE_IP)

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

        if not self.running:
            # This is the brutal stop of the system.
            # should do some cleanup before actually shutting it down.
            sys.exit(1)

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
        while self.running:
            self.display.processIncoming(self.cdLen, self.goHold, self.songLength)
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
                self.songLength = self.mySpotipy.getTrackLength(self.song)
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

cdLen = 5
goHold = 5

# initialize our main thread management and pass root
client = ThreadedClient(user, song, cdLen, goHold)

# set up events for our pullstation
pullStation.when_pressed = client.alarmActivate
pullStation.when_released = client.alarmCancel

