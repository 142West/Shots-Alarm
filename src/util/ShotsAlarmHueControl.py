import json
import time
from phue import Bridge


# Hue Bridge IP address stored under "HUE_IP" in Private

class ShotsAlarmHueControl:
    def __init__(self, configFileName):
        f = open("config/" + configFileName)
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

        self.b = Bridge(self.bridgeIP)
        self.b.connect()
        self.b.get_api()

        self.flash = False
        self.fade = True

    def getStatus(self):
        if self.b.get_api():
            return ("Connected", 0)
        return ("Not Connected", 1)

    def flashLights(self, color, delay, seconds):
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

        self.flash = False

    #
    def colorFade(self, enable):
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
