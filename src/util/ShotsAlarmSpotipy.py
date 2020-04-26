import spotipy
import src.util.shotsAlarmUtil as util


# simplify our tasks for interfacing with spotify via spotipy
class ShotsAlarmSpotipy:

    # dict of songs available for injection
    songs = {
        "Shots": u'spotify:track:1V4jC0vJ5525lEF1bFgPX2',
        "White Noise" : u'spotify:track:65rkHetZXO6DQmBh3C2YtW',
        "Never Gonna Give You Up" : u'spotify:track:7GhIk7Il098yCjg4BQjzvb',
        "Like A Dream" : u'spotify:track:2eJogHu4qygT1BDhAve9Us',
        "Hallelujah" : u'spotify:track:57suk8NVdGdoVON1CEbeSn'
    }

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
            print("Can't get token for %s" % self.USERNAME)
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

    # take song name string, return track URI from Dict
    def getTrackFromDict(self, songName):
        # if given song name is not in dict, return URI for Shots
        trackURI = self.songs.get(songName, self.songs.get("Shots"))
        return trackURI

    # take current track, return if playing or not
    def isPlaying(self, trackData):
        cTrackIsPlaying = trackData['is_playing']
        return cTrackIsPlaying

    # get all the info we need to save a snapshot of current song
    def saveSpot(self):
        # double check that we are logged in
        if self.spLogin():
            theTrack = []
            trackData = self.getCurrentTrackData()
            theTrack.append(self.getCurrentProgress(trackData))
            theTrack.append(self.getCurrentTrackURI(trackData))
            theTrack.append(self.getCurrentTrackContext(trackData))
            return theTrack
        else:
            return 0

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
