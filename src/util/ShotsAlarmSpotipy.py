import spotipy
import src.util.shotsAlarmUtil as util


# simplify our tasks for interfacing with spotify via spotipy
class ShotsAlarmSpotipy:

    # dict of tracks available for injection
    tracks = {
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

        # set default alarm track
        self.alarmTrackURI = self.tracks['Shots']

        # bookmark for place holding
        self.bookmark = None

        # keep track of if alarm has been activated
        self.shotsFired = False

        # keep track of token status for reporting out logged in, failed, or stuck
        self.haveToken = 1

        # if we have a username, try logging in
        if not self.checkUser():
            self.spLogin()

    def checkUser(self):
        """
        Verify that a non-empty username was provided at init
        :return: Username present (0) / absent (-1)
        """
        if self.USERNAME:
            return 0
        else:
            return -1

    def spLogin(self):
        """
        login to Spotify and get token (or refresh)
        :return: Login success (0) / fail (1)
        """
        # attempt to get an auth token
        self.haveToken = 1
        token = util.prompt_for_user_token(
            username=self.USERNAME,
            scope=self.TOTAL_SCOPE,
            client_id=self.CLIENT_ID,
            client_secret=self.CLIENT_SECRET,
            redirect_uri=self.REDIRECT_URI)

        # if we succeded, return spotify object
        if token:
            self.sp = spotipy.Spotify(auth=token)
            self.haveToken = 0
            return 0
        else:
            return 1

    def getTrackLength(self, trackURI):
        """
        Get the length of a track from a Spotify URI
        :param trackURI: Spotify track URI
        :return: Length of track in seconds
        """
        trackData = self.sp.track(trackURI)
        trackLength = (trackData['duration_ms']) / 1000
        return trackLength

    def getPlaybackData(self):
        """
        Get data regarding the user's currently playing track
        :return: Data regarding currently playing track
        """
        playbackData = self.sp.current_playback()
        return playbackData

    def getPlaybackTrackProgress(self, playbackData):
        """
        Extract track progress from track data
        :param playbackData:
        :return: 
        """
        trackProgress = playbackData['progress_ms']
        return trackProgress

    def getPlaybackTrackURI(self, playbackData):
        """
        Extract track URI from track data
        :param playbackData: Data regarding currently playing track
        :return: Spotify track URI
        """
        trackURI = playbackData['item']['uri']
        return trackURI

    def getPlaybackTrackContext(self, playbackData):
        """
        Extract context from track data, if available
        :param playbackData: Data regarding currently playing track
        :return: Spotify track context URI if available, else None
        """
        if playbackData['context']:
            contextURI = playbackData['context']['uri']
            return contextURI
        else:
            return None

    def getPlaybackVolume(self, playbackData):
        if playbackData['device']:
            playbackVolume = playbackData['device']['volume_percent']
            return playbackVolume
        else:
            return None

    def getTrackFromDict(self, trackName):
        """
        Lookup a track name from dictionary
        :param trackName: Name of track as a string
        :return: Spotify track URI
        """
        # if given track name is not in dict, return URI for Shots
        trackURI = self.tracks.get(trackName, self.tracks.get("Shots"))
        return trackURI

    def saveSpot(self):
        """
        Get all the info we need to save a snapshot of current track
        :return: array [track progress, track URI, track context, playback volume]
                 Will return empty array if no track is playing
        """
        theTrack = {}
        # get data for currently playing track
        playbackData = self.getPlaybackData()
        # catch if trackData is empty (nothing currently playing)
        if playbackData:
            theTrack['progress'] = (self.getPlaybackTrackProgress(playbackData))
            theTrack['track URI'] = (self.getPlaybackTrackURI(playbackData))
            theTrack['context URI'] = (self.getPlaybackTrackContext(playbackData))
            theTrack['volume'] = (self.getPlaybackVolume(playbackData))
        return theTrack

    def playNoContext(self, trackURI):
        """
        Play a track from URI with no context. This can be used for track injection
        :param trackURI: Spotify track URI with no context
        :return: None
        """
        self.sp.start_playback(device_id = None,
                               context_uri = None,
                               uris = [trackURI],
                               offset = None,
                               position_ms = None)

    def playWithContext(self, bookmark):
        """
        Play a track from URI with context (ie: progress, playlist, etc.)
        This can be used to return to a track after alarm track injection
        :param bookmark: dict of track data {track progress, track URI, context URI, volume}
        :return: None
        """
        # double check to make sure we have a context URI
        # if we do, go ahead and play with context
        if bookmark['context URI']:
            self.sp.start_playback(device_id = None,
                                   context_uri = bookmark['context URI'],
                                   uris = None,
                                   offset = None,
                                   position_ms = bookmark['progress'])

        # if we don't have a context URI, just go back to the track
        # and manually seek to position
        else:
            self.playNoContext(bookmark['track URI'])
            self.sp.seek_track(bookmark['progress'])

    def volumeUp(self, bookmark, percentIncrease):
        """
        Increase the playback volume by a percentage above the bookmarked playback volume
        :param bookmark: dict of track data {track progress, track URI, context URI, volume}
        :param percentIncrease: int 0-100 representing percent increase in volume above bookmark volume
        :return: Volume adjustment success (0) / fail (1)
        """
        # get volume from bookmark
        playbackVolume = bookmark['volume']
        # verify that we saved a playback volume
        if playbackVolume:
            # limit max volume to 100%
            if (playbackVolume + percentIncrease) > 100:
                setVolume = 100
            else:
                setVolume = playbackVolume + percentIncrease
            # increase the volume
            self.sp.volume(playbackVolume)
            return 0
        else:
            return 1

    def volumeDown(self, bookmark):
        """
        Decrease the playback volume back to the bookmark volume value
        :param bookmark: dict of track data {track progress, track URI, context URI, volume}
        :return: Volume adjustment success (0) / fail (1)
        """
        # get volume from bookmark
        playbackVolume = bookmark['volume']
        # verify that we saved a playback volume
        if playbackVolume:
            self.sp.volume(playbackVolume)
            return 0
        else:
            return 1

    def setAlarmTrack(self, trackName):
        """
        Set the track from a given list (will default to Shots)
        Returns the length of the selected track
        :param trackName: Name of track as a string
        :return: Length of alarm track in seconds
        """
        self.alarmTrackURI = self.getTrackFromDict(trackName)
        trackLength = self.getTrackLength(self.alarmTrackURI)
        return trackLength

    def alarmActivate(self):
        """
        Save the current play state if available then start playing alarm track
        :return: success (0) / fail (1)
        """
        # verify that the alarm has not already been activated
        if not self.shotsFired:
            # keep track of internal alarm state
            self.shotsFired = True

            # verify that we are logged in
            if not self.spLogin():
                # bookmark current spot (will be empty if no currently playing track)
                self.bookmark = self.saveSpot()
                # play the alarm track
                self.playNoContext(self.alarmTrackURI)
                # crank it up
                if self.bookmark:
                    self.volumeUp(self.bookmark, 10)
                return 0
            else:
                return 1
        else:
            return 1

    def alarmCancel(self):
        """
        Return to a previous play state via bookmark
        :return: success (0) / fail (1)
        """
        # verify that the alarm has not already been canceled
        if self.shotsFired:
            # keep track of internal alarm state
            self.shotsFired = False

            # verify that we are logged in
            if not self.spLogin():
                # verify that we have a bookmark
                if self.bookmark:
                    # return to our bookmark
                    self.playWithContext(self.bookmark)
                    # return to original volume
                    self.volumeDown(self.bookmark)
                    return 0
                else:
                    return 1
            else:
                return 1
        else:
            return 1

    def getShotsFired(self):
        return self.shotsFired

    def getStatus(self):
        return self.haveToken





