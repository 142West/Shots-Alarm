import sys
import time
from gpiozero import DigitalOutputDevice
from gpiozero import Button
import spotipy
import spotipy.util as util
import time
from threading import Timer, Thread, Event
from datetime import datetime, timedelta

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

# Setup GPIO
button = Button(25)
strobe = DigitalOutputDevice(19)
strobe.off()

# easy function for grabbing time
now = time.time

class ShotsAlarm:
    
    def __init__(self, user):
        self.USERNAME = user
        self.SCOPE0 = 'user-library-read'
        self.SCOPE1 = 'user-read-playback-state'
        self.SCOPE2 = 'user-modify-playback-state'
        self.TOTAL_SCOPE = self.SCOPE0 + ' ' + self.SCOPE1 + ' '+ self.SCOPE2
        self.CLIENT_ID='69e91797ca0143a3a51428e87685b6f0'
        self.CLIENT_SECRET='9d9cb5971edc422299042975ceb22ce2'
        self.REDIRECT_URI='http://localhost:8000'
        
        self.WhiteNoise = u'spotify:track:65rkHetZXO6DQmBh3C2YtW'
        self.RA = u'spotify:track:7GhIk7Il098yCjg4BQjzvb'
        self.likeAdream = u'spotify:track:2eJogHu4qygT1BDhAve9Us'
        self.SHOTS = u'spotify:track:1V4jC0vJ5525lEF1bFgPX2'

        #if we have a username, try logging in
        if self.checkUser():
            self.sp = self.spLogin()

    #make sure we have a username
    def checkUser(self):
        if self.USERNAME:
            return 1
        else:
            return 0

    #login to Spotify and get token (or refresh)
    def spLogin(self):
        # attempt to get an auth token
        token = util.prompt_for_user_token(
            username = self.USERNAME,
            scope = self.TOTAL_SCOPE,
            client_id = self.CLIENT_ID,
            client_secret = self.CLIENT_SECRET,
            redirect_uri = self.REDIRECT_URI)

        # if we succeded, return spotify object
        if token:
            sp = spotipy.Spotify(auth=token)
            return sp
        else:
            print("Can't get token for %s" % usr)
            return 0

    #take a song URI and return total seconds and
    #time-formatted minutes / seconds
    def getSongLength(self, songURI):
        trackData = self.sp.track(songURI)
        songLength= (trackData['duration_ms']) / 1000
        return songLength

    #return the user's currently playing track
    def getCurrentTrackData(self):
        trackData = self.sp.current_user_playing_track()
        return trackData

    #take currently playing track, return song progress in mills
    def getCurrentProgress(self, trackData):
        cProgress = trackData['progress_ms']
        return cProgress

    #take currently playing track, return track URI
    def getCurrentTrackURI(self, trackData):
        cTrackURI = trackData['item']['uri']
        return cTrackURI

    #take currently playing track, return context if available
    def getCurrentTrackContext(self, trackData):
        if trackData['context']:
            cContextURI = trackData['context']['uri']
            return cContextURI
        else:
            return 0

    #get all the info we need to save a snapshot of current song
    def saveSpot(self):
        theTrack = []
        trackData = self.getCurrentTrackData()
        theTrack.append(self.getCurrentProgress(trackData))
        theTrack.append(self.getCurrentTrackURI(trackData))
        theTrack.append(self.getCurrentTrackContext(trackData))
        return theTrack

    #Play a song from URI with no context.
    #This can be used for song injection
    def playNoContext(self, songURI):
        self.sp.start_playback(None, None, [songURI], None)

    #Play a song from URI with context.
    #This can be used to return to song
    #context = [progress, trackURI, trackContext]
    def playWithContext(self, context):
        #double check to make sure we have a context URI
        #if we do, go ahead and play with context
        if context[2]:
            self.sp.start_playback(None, context[2], None, {"uri": context[1]})
        #if we don't have a context URI, just go back to the song
        else:
            self.playNoContext(context[1])
        #we can then seek to song progress regardless of context URI
        self.sp.seek_track(context[0])

class Countdown:
    #Show countdown and call `callback` in `delay` seconds unless cancelled
    def __init__(self, root, delay):
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)
        self.frame = ttk.Frame(root, padding="5 5")
        self.frame.master.attributes('-fullscreen',True)
        self.frame.master = root #XXX
        self.seconds_var = tkinter.StringVar()
        self.update_id = None
        
        ttk.Label(self.frame, textvariable=self.seconds_var, font=("Courier", 100, "bold")).grid(row=1, column=1)
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)
        self.frame.grid_rowconfigure(1, minsize=700)
        self.frame.grid()
        self.frame.master.protocol("WM_DELETE_WINDOW", self.cancel)
        #self.update(now() + delay)
        self.isCanceled = False

        print(self.frame.grid_size())

    #we are going to use this and do our countdown updates in our main loop
    def update2(self, delay, elapsed):
        self.seconds_var.set('SHOTS IN: %.0f' % (delay - elapsed))

    def update3(self, visible):
        if not (visible % 2):
            self.seconds_var.set("GO!! GO!! GO!!")
        else:
            self.seconds_var.set(" ")

    #Unused, but here for refenence
    #the last line frame.after is what runs the update
    #in this case every 100ms
    def update(self, end_time):
        #Update countdown or call the callback and exit
        if end_time <= now():
            print("END COUNTDOWN")
            self.frame.master.destroy()
        else:
            self.seconds_var.set('SHOTS IN: %.2f' % (end_time - now()))
            self.update_id = self.frame.after(100, self.update, end_time)

    def cancel(self):
        #Cancel callback, exit.
        if self.update_id is not None:
            self.frame.after_cancel(self.update_id)
        self.frame.master.destroy()
        self.isCanceled = True

#thread for scheduling counter updates
class myThread(Thread):
    def __init__(self, event, cntr):
        Thread.__init__(self)
        self.stopped = event
        self.count = cntr

    def run(self):
        while not self.stopped.wait(1.0):
            self.count.increment()
            
#counter... because keeping track of time is hard
class Counter:
    def __init__(self):
        self.count = 0
        self.update = 1

    def increment(self):
        self.count +=1
        self.update = 1

#convert seconds to minutes:seconds format, return in array.
def seconds2time(secs):
    MinSec = datetime(1, 1, 1) + timedelta(seconds = secs)
    return [MinSec.minute, MinSec.second]

def time2string(MinSec):
    timeStr = "%02d:%02d" % (MinSec[0], MinSec[1])
    return timeStr

#you know what this one does ;)
#thought it was going to be simple, eh?
def SHOTS(song, cdLen, myCount, thread, stopFlag):
    
    #turn on strobe
    strobe.on()
    
    #refresh spotify token
    myShotsAlarm.spLogin()
    
    #save our current spot
    mySpot = myShotsAlarm.saveSpot()
    
    #play our desired song
    myShotsAlarm.playNoContext(song)
    
    #start counter thread
    thread.start()
    
    #start UI
    root = tkinter.Tk()
    mycd = Countdown(root, 59)
    mycd.update2(cdLen, 0)
    mycd.frame.update()

    #get the length of the new song
    songLength = myShotsAlarm.getSongLength(song)
    
    #keep track of how much time has elapsed
    while myCount.count <= songLength:
        
        #make sure we only check update once a second
        if myCount.update:
            
            #if we canceled, then pack it up and get out
            if not button.is_pressed:
                break;

            #string formatting for song timestamp
            print(time2string(seconds2time(myCount.count)))

            #counting down
            if myCount.count < cdLen and not mycd.isCanceled:
                mycd.update2(cdLen, myCount.count)
                mycd.frame.update()
                
            #It's go time (for 30 seconds at least if we haven't canceled)
            elif myCount.count >= cdLen and myCount.count <= cdLen + 10 and not mycd.isCanceled:
                mycd.update3(myCount.count)
                mycd.frame.update()

            #Go time is over. Time to pack it up and get out
            elif myCount.count > cdLen + 10 and not mycd.isCanceled:
                mycd.cancel()
                
            myCount.update = 0
        
    #turn off strobe
    strobe.off()

    #stop the counter thread
    thread.stopped.set()
    
    #return to previously playing song
    myShotsAlarm.playWithContext(mySpot)
    
    #clear our display if it isn't clear already
    if not mycd.isCanceled:
        mycd.cancel()

    
#init a shots alarm object
myShotsAlarm = ShotsAlarm("aflynn73")

#set up our super janky timer stuff
stopFlag = Event()
myCount = Counter()
thread = myThread(stopFlag, myCount)

#run SHOTS when switch activated
#note, need "lambda" to assign to function with args
#SHOTS(Track_URI, Countdown_seconds, Counter_obj, thread_obj, Event)
button.when_pressed = lambda : SHOTS(myShotsAlarm.SHOTS, 60, myCount, thread, stopFlag)
