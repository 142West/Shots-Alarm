import os

import spotipy
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import cherrypy

binary_location = "/usr/bin/chromedriver"


def get_user_token(username, scope, client_id, client_secret, redirect_uri, cache_path,):
    """ prompts the user to login if necessary and returns
        the user token suitable for use with the spotipy.Spotify
        constructor
        Parameters:
         - username - the Spotify username
         - scope - the desired scope of the request
         - client_id - the client id of your app
         - client_secret - the client secret of your app
         - redirect_uri - the redirect URI of your app
         - cache_path - path to location to save tokens
    """

    if not client_id:
        client_id = os.getenv("SPOTIPY_CLIENT_ID")

    if not client_secret:
        client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")

    if not redirect_uri:
        redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI")

    if not client_id:
        raise spotipy.SpotifyException(550, -1, "no credentials set")

    cache_path = cache_path or ".cache-" + username
    sp_oauth = spotipy.oauth2.SpotifyOAuth(
        client_id, client_secret, redirect_uri, scope=scope, cache_path=cache_path
    )

    # try to get a valid token for this user, from the cache,
    # if not in the cache, the create a new (this will send
    # the user to a web page where they can authorize this app)

    token_info = sp_oauth.get_cached_token()

    if not token_info:
        auth_url = sp_oauth.get_authorize_url()
        try:
            visit_url(auth_url)
        except BaseException:
            print(f"Please navigate here: {auth_url}")

        response = wait_for_http_callback(5000)

        code = sp_oauth.parse_response_code(response)
        token_info = sp_oauth.get_access_token(code)
    if token_info:
        return token_info["access_token"]
    else:
        return None


def wait_for_http_callback(_port=9000, _host="127.0.0.1"):

    if _host == "localhost":
        _host = "127.0.0.1"

    cherrypy.config.update(
        {"server.socket_host": _host, "server.socket_port": _port, "log.screen": False}
    )

    class CallbackHandler(object):
        response = None

        @cherrypy.expose
        def index(self, code=None):
            request = cherrypy.serving.request
            self.response = cherrypy.url(qs=request.query_string)
            cherrypy.engine.exit()

    handle = CallbackHandler()
    cherrypy.quickstart(handle, "/callback", config={"/": {"log.screen": False}})
    return handle.response


def visit_url(_url, username, password):

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.binary_location = binary_location

    driver = webdriver.Chrome(executable_path=binary_location)
    driver.get(_url)
    driver.implicitly_wait(3)
    driver.find_element()
    return driver.current_url

