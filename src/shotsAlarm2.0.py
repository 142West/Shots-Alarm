import Private
import sys
import time
import threading
import Queue
from gpiozero import Button, DigitalOutputDevice
import spotipy
import spotipy.util as util
from datetime import datetime, timedelta
from phue import Bridge
from RPLCD.gpio import CharLCD
from RPi import GPIO

# globally init our pullstation and strobe
print GPIO.getmode()
GPIO.setmode(GPIO.BCM)
pullStation = Button(4)
strobe = DigitalOutputDevice(17)
strobe.off()

lcd = CharLCD(numbering_mode=GPIO.BCM, cols=16, rows=2, pin_rs=26, pin_e=19, pins_data=[21, 20, 16, 12, 13, 6, 5, 11])

# fullscreen (0 for test, 1 for run)
fullscreen = False


# simplify our tasks for interfacing with spotify via spotipy
class ASpotipy:
    # class vars (our song lists so they are accessable)
    WhiteNoise = u'spotify:track:65rkHetZXO6DQmBh3C2YtW'
    RA = u'spotify:track:7GhIk7Il098yCjg4BQjzvb'
    ikeAdream = u'spotify:track:2eJogHu4qygT1BDhAve9Us'
    SHOTS = u'spotify:track:1V4jC0vJ5525lEF1bFgPX2'

    def __init__(self, user, client_id, client_secret, redirect_uri):
        self.USERNAME = user
        self.SCOPE0 = 'user-library-read'
        self.SCOPE1 = 'user-read-playback-state'
        self.SCOPE2 = 'user-modify-playback-state'
        self.TOTAL_SCOPE = self.SCOPE0 + ' ' + self.SCOPE1 + ' ' + self.SCOPE2
        self.CLIENT_ID = client_id
        self.CLIENT_SECRET = client_secret
        self.REDIRECT_URI = redirect_uri

        # if we have a username, try logging in
        if self.checkUser():
            self.sp = self.spLogin()

    # make sure we have a username
    def checkUser(self):
        if self.USERNAME:
            return 1
        else:
            return 0

    # login to Spotify and get token (or refresh)
    def spLogin(self):
        # attempt to get an auth token
        token = util.prompt_for_user_token(
            username=self.USERNAME,
            scope=self.TOTAL_SCOPE,
            client_id=self.CLIENT_ID,
            client_secret=self.CLIENT_SECRET,
            redirect_uri=self.REDIRECT_URI)

        # if we succeded, return spotify object
        if token:
            sp = spotipy.Spotify(auth=token)
            return sp
        else:
            print("Can't get token for %s" % user)
            return 0

    # take a song URI and return total seconds and
    # time-formatted minutes / seconds
    def getSongLength(self, songURI):
        trackData = self.sp.track(songURI)
        songLength = (trackData['duration_ms']) / 1000
        return songLength

    # return the user's currently playing track
    def getCurrentTrackData(self):
        # double check that we are logged in
        self.spLogin()
        trackData = self.sp.current_user_playing_track()

        return trackData

    # take currently playing track, return song progress in mills
    def getCurrentProgress(self, trackData):
        cProgress = trackData['progress_ms']
        return cProgress

    # take currently playing track, return track URI
    def getCurrentTrackURI(self, trackData):
        cTrackURI = trackData['item']['uri']
        return cTrackURI

    # take currently playing track, return context if available
    def getCurrentTrackContext(self, trackData):
        if trackData['context']:
            cContextURI = trackData['context']['uri']
            return cContextURI
        else:
            return 0

    # take current track, return if playing or not
    def isPlaying(self, trackData):
        cTrackIsPlaying = trackData['is_playing']
        return cTrackIsPlaying

    # get all the info we need to save a snapshot of current song
    def saveSpot(self):
        theTrack = []
        trackData = self.getCurrentTrackData()
        theTrack.append(self.getCurrentProgress(trackData))
        theTrack.append(self.getCurrentTrackURI(trackData))
        theTrack.append(self.getCurrentTrackContext(trackData))
        return theTrack

    # Play a song from URI with no context.
    # This can be used for song injection
    def playNoContext(self, songURI):
        # double check that we are logged in
        self.spLogin()
        self.sp.start_playback(None, None, [songURI], None)

    # Play a song from URI with context.
    # This can be used to return to song
    # context = [progress, trackURI, trackContext]
    def playWithContext(self, context):
        # double check that we are logged in
        self.spLogin()

        # double check to make sure we have a context URI
        # if we do, go ahead and play with context
        if context[2]:
            self.sp.start_playback(None, context[2], None, {"uri": context[1]})

        # if we don't have a context URI, just go back to the song
        else:
            self.playNoContext(context[1])

        # we can then seek to song progress regardless of context URI
        self.sp.seek_track(context[0])

    def volumeUp(self):
        self.spLogin()
        self.sp.volume(88)

    def volumeDown(self):
        self.spLogin()
        self.sp.volume(78)


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
    def __init__(self, queue, alarmCancelCommand):
        self.queue = queue
        self.alarmCancel = alarmCancelCommand

        # Set up the GUI

        '''
        self.frame = ttk.Frame(master, padding="5 5")
        if fullscreen:
            self.frame.master.attributes('-fullscreen', True)
        self.frame.master = master  # XXX
        ttk.Label(self.frame, textvariable=self.seconds_var, font=("Courier", 100, "bold")).grid(row=1, column=1)
        ttk.Button(self.frame, text='Cancel', command=self.cancel).grid(row=2, column=1, sticky="s")
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)
        self.frame.grid_rowconfigure(1, minsize=root.winfo_screenheight() / 2)
        self.frame.grid()
        self.frame.master.protocol("WM_DELETE_WINDOW", self.cancel)
        '''

    def setMessage(self, value):
        print value;
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

            except Queue.Empty:
                # just on general principles, although we don't
                # expect this branch to be taken in this case
                pass

    def cancel(self):
        """Cancel callback, hide."""
        self.alarmCancel()


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

        # What song are we going to play??
        self.song = song

        # keep track of length (sec) of selected song
        # this will be assigned at alarmActivate()
        self.songLength = 0

        # song countdown length
        # this is assigned by init call
        self.cdLen = cdLen

        # how long to display "GO!!"
        # this is assigned by init call
        self.goHold = goHold

        # Create the queue
        self.queue = Queue.Queue()

        # Create a lock to access shared resources amongst threads
        self.lock = threading.Lock()

        # Set up the GUIPart
        # we pass it the master (root), the queue, the endApplication function, and the hide / show functions
        self.gui = DisplayController(self.queue, self.alarmCancel)

        # Set up the Spotify instance
        self.mySpotipy = ASpotipy(user, Private.CLIENT_ID, Private.CLIENT_SECRET, Private.REDIRECT_URI)

        # setup hue
        self.myHue = hueControl()

        # Set up the thread to do asynchronous I/O
        self.running = 1
        self.thread1 = threading.Thread(target=self.workerThread1)
        self.thread1.start()

        self.thread2 = threading.Thread(target=self.workerThread2)
        self.thread2.start()

        self.thread3 = threading.Thread(target=self.workerThread3)
        self.thread3.start()

        self.thread4 = threading.Thread(target=self.workerThread4)
        self.thread4.start()

        # Start the periodic call in the GUI to check if the queue contains
        # anything
        self.periodicCall()

    ###########################################
    ## Periodic Update Function (root.after) ##
    ###########################################

    def periodicCall(self):
        """
        Check every 200 ms if there is something new in the queue.
        """
        self.gui.processIncoming(self.cdLen, self.goHold, self.songLength)
        if not self.running:
            # This is the brutal stop of the system.
            # should do some cleanup before actually shutting it down.
            sys.exit(1)

        threading.Timer(.2, self.periodicCall).start()

    ###########################################
    ## Worker Threads (for asynchronous I/O) ##
    ###########################################

    def workerThread1(self):  # ORIGINAL-WORKING
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
                # make sure shots is activated
                if self.shotsFired:
                    # make sure we haven't been counting longer than the song length
                    if (self.count <= self.songLength):
                        # update queue with count if countdown stage or go stage
                        if (self.count <= (self.cdLen + self.goHold)):
                            self.queue.put(self.count)
                            self.count += 1
                        else:  # not in countdown stage or go stage
                            self.queue.put(None)
                    else:  # song has ended
                        self.alarmCancel()
                else:  # shots not fired
                    pass
            time.sleep(1)

    # runs once an hour to make sure
    # count doesn't get too big
    def workerThread2(self):
        while self.running:
            time.sleep(3600)
            if self.count >= 3600:
                # make sure we have access to shared resource
                with self.lock:
                    self.count = 0

    def workerThread3(self):
        while self.running:
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

    def workerThread4(self):
        while self.running:
            if not self.shotsFired:
                self.myHue.advanceLights(50)
            time.sleep(10)


    ##########################
    ## PullStation Tracking ##
    ##########################

    def alarmActivate(self):
        print("alarm activated")

        # PULL SPOTIFY DATA
        # make sure we can get a token or refresh
        if self.mySpotipy.spLogin():

            # set hue flashed to 0
            self.flashed = 0
            self.flashed2 = 0

            # turn on strobe
            # strobe.on()

            # save our current spot
            self.mySpot = self.mySpotipy.saveSpot()
            print(self.mySpot)

            # get the length of the new song
            self.songLength = self.mySpotipy.getSongLength(self.song)
            print(self.seconds2string(self.songLength))

            # keep track of whether or not wer are running Shots
            self.shotsFired = 1

            # play our desired song
            self.mySpotipy.playNoContext(self.song)

            # CRANK IT UP
            self.mySpotipy.volumeUp()

        else:  # couldn't log in
            print("ERROR: CAN'T GET SPOTIFY TOKEN")

        # keep track of alarm activation
        self.shotsFired = 1

        # make sure we have access to shared resource
        with self.lock:
            self.count = 0

    def alarmCancel(self):
        # if we haven't already canceled
        if self.shotsFired:
            print("alarm canceled")

            # keep track of alarm activation
            self.shotsFired = 0

            self.flashed = 1
            self.flashed2 = 1

            # make sure we have access to shared resource
            with self.lock:
                self.count = 0

            # turn off strobe
            strobe.off()

            # return to previously playing song
            if self.mySpot:
                self.mySpotipy.playWithContext(self.mySpot)
                self.mySpotipy.volumeDown()


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
user = "59nmtms76slm25a959sz7kieb"
# song = ASpotipy.WhiteNoise
# song = ASpotipy.RA
song = ASpotipy.SHOTS
cdLen = 60
goHold = 15

# initialize our main thread management and pass root
client = ThreadedClient(user, song, cdLen, goHold)

# set up events for our pullstation
pullStation.when_pressed = client.alarmActivate
pullStation.when_released = client.alarmCancel

