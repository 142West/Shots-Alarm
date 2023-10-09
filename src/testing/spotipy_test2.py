import sys
import time
import gpiozero
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

# Setup GPIO
button = gpiozero.Button(18)
rlyOn = gpiozero.DigitalOutputDevice(17)
rlyOff = gpiozero.DigitalOutputDevice(16)

#blink(onTime, offTime, nTimes, background)
#rlyOn.blink(1, 1, 1, True)

# Setup variables for the spotify API
USERNAME = 'aflynn73'
SCOPE0 = 'user-library-read'
SCOPE1 = 'user-read-playback-state'
SCOPE2 = 'user-modify-playback-state'
TOTAL_SCOPE = SCOPE0 + ' ' + SCOPE1 + ' '+ SCOPE2
CLIENT_ID=''
CLIENT_SECRET=''
REDIRECT_URI='http://localhost:8000'

# Spotify URIs to songs of interest
RA = u'spotify:track:7GhIk7Il098yCjg4BQjzvb'
SHOTS = u'spotify:track:1V4jC0vJ5525lEF1bFgPX2'

# Make sure we have a username to give to Spotify
if len(sys.argv) > 1:
    USERNAME = sys.argv[1]
else:
    USERNAME = raw_input("Spotify Username: ")
    if not USERNAME:
        sys.exit()

def spLogin(usr, scope, clientId, clientSecret, redirectUri):
    # attempt to get an auth token
    token = util.prompt_for_user_token(
        username=usr,
        scope=scope,
        client_id=cleintId,
        client_secret=clientSecret,
        redirect_uri=redirectUri)

    # if we succeded, return spotify object
    if token:
        sp = spotipy.Spotify(auth=token)
        return spObj
    else:
        print("Can't get token for %s" % usr)
        return 0

def changeSong(sp, songUri):
    # find out what user is currently listening to
    # as well as its context so we can go back
    cTrack = sp.current_user_playing_track()
    cProgress = cTrack['progress_ms']
    cTrack_uri = cTrack['item']['uri']
    cDuration = cTrack['item']['duration_ms']
    if cTrack['context']:
        cContext_uri = cTrack['context']['uri']

    # change songs
    sp.start_playback(None, None, [songUri], None)

    # get current system time and start a counter
    startTime = time.time()
    time.clock()
    elapsedTime = 0
    
    # get length of song in ms
    cTrack = sp.current_user_playing_track()
    cDuration = cTrack['item']['duration_ms']
    
    

def dispSong(sp, progress, length):
    return 0
    
spObj = spLogin(USERNAME, TOTAL_SCOPE, CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)


