# Shots Alarm Windows Test Code
# Andrew Flynn
# 12-05-2018
#
# Requires installation of "Spotipy" and "Six"

import sys
import spotipy
import spotipy.util as util

USERNAME = 'aflynn73'
SCOPE0 = 'user-library-read'
SCOPE1 = 'user-read-playback-state'
SCOPE2 = 'user-modify-playback-state'
TOTAL_SCOPE = SCOPE0 + ' ' + SCOPE1 + ' '+ SCOPE2
CLIENT_ID='69e91797ca0143a3a51428e87685b6f0'
CLIENT_SECRET='9d9cb5971edc422299042975ceb22ce2'
REDIRECT_URI='http://localhost:8000'

RA = u'spotify:track:7GhIk7Il098yCjg4BQjzvb'
SHOTS = u'spotify:track:1V4jC0vJ5525lEF1bFgPX2'
SHOTS_DURATION = 222133

if len(sys.argv) > 1:
    USERNAME = sys.argv[1]
else:
    USERNAME = 'aflynn73'
##    print "Usage: %s username" % (sys.argv[0],)
##    sys.exit()

#get token for access to user info
#will need user to login with browser
token = util.prompt_for_user_token(
        username=USERNAME,
        scope=TOTAL_SCOPE,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI)

sp = spotipy.Spotify(auth=token)

input("Press Enter to Change \n")

##
if token:
    sp = spotipy.Spotify(auth=token)
    c_track = sp.current_user_playing_track()
    c_progress = c_track['progress_ms']
    c_track_uri = c_track['item']['uri']
    c_duration = c_track['item']['duration_ms']
    
    if c_track['context']:
        c_context_uri = c_track['context']['uri']

    sp.start_playback(None, None, [RA], None)

    input("Press Enter to Go Back")
    sp.start_playback(None, c_context_uri, None, {"uri": c_track_uri})
    sp.seek_track(c_progress)
    
else:
    print ("Can't get token for", USERNAME)
