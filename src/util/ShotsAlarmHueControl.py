import json
import time
import os

import phue
from phue import Bridge


# Hue Bridge IP address stored under "HUE_IP" in Private

class ShotsAlarmHueControl:
    def __init__(self, configFileName, logger):
        #print (os.path.abspath(os.curdir))
        f = open(configFileName)
        self.config = json.load(f)
        self.lights = self.config["lights"]
        self.groups = self.config["groups"]
        self.bridgeIP = self.config["bridgeIp"]

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

        self.colors = [
            self.red,
            self.magenta,
            self.blue,
            self.lblue,
            self.green,
            self.yellow,
            self.orange
        ]

        self.currentColor = 0;
        self.connected = False
        try:
            self.b = Bridge(self.bridgeIP)
            self.b.connect()
            self.b.get_api()
            self.status = ("Connected", 0)
            self.connected = True
        except phue.PhueRegistrationException:
            self.status = ("Hue Err: Push the bridge button", 1)
            self.connected = False

        self.flash = False
        self.fade = True

    def connect(self):
        if not self.connected:
            while not self.connected:
                try:
                    self.b = Bridge(self.bridgeIP)
                    self.b.connect()
                    self.b.get_api()
                    self.connected = True
                    self.status = ("Connected", 0)
                except phue.PhueRegistrationException or OSError as e:
                    print(e)
                    self.status = ("Hue Err: Push the bridge button", 1)
                    time.sleep(20)
                    self.connected = False

    def getStatus(self):
        return self.status

    def flashLights(self, color, delay, seconds, color2 = None, seconds2 = None):
        if self.connected:
            self.flash = True
            currentSeconds = 1
            while currentSeconds < seconds and self.flash:
                for light in self.lights:
                    if light["enabled"]:
                        if (light["type"] == "color"):
                            command = {'xy': color, "alert": "select", 'bri': self.fIntensity}
                        else:
                            command = {"alert": "select", 'bri': self.fIntensity}
                        self.b.set_light(light["name"], command)
                currentSeconds += 1
                time.sleep(delay)

            if color2:
                currentSeconds = 0
                while currentSeconds < seconds2 and self.flash:
                    for light in self.lights:
                        if light["enabled"]:
                            if (light["type"] == "color"):
                                command = {'xy': color2, "alert": "select", 'bri': self.fIntensity}
                            else:
                                command = {"alert": "select", 'bri': self.fIntensity}
                            self.b.set_light(light["name"], command)
                    currentSeconds += 1
                    time.sleep(delay)

            self.flash = False

    #
    def colorFade(self, enable):
        if self.connected:
            self.fade = enable
            while self.fade and not self.flash:
                self.advanceAsOne(5)
                time.sleep(6)

    def cancelFlash(self):
        self.flash = False

    def advanceAsOne(self, tTime):
        for light in self.lights:
            if light["enabled"] and light["type"] == "color":
                self.currentColor += 1;
                command = {'transitiontime': tTime, 'xy': self.colors[self.currentColor % len(self.colors) - 1],
                           'bri': self.nIntensity}
                self.b.set_light(light["name"], command)
            if light["enabled"] and light["type"] == "white":
                command = {'transitiontime': tTime, 'bri': self.nIntensity}
                self.b.set_light(light["name"], command)
