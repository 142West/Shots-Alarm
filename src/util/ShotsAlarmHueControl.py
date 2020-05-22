import json
import time
from phue import Bridge

# Hue Bridge IP address stored under "HUE_IP" in Private

class ShotsAlarmHueControl:
    def __init__(self, configFileName):
        f = open("config/"+configFileName)
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
    #
    # def updateLR(self, command):
    #     self.b.set_group(4, command)
    #     self.b.set
    #
    # def updateDoor(self, command):
    #     self.b.set_group(5, command)
    #
    # def updateHW(self, command):
    #     self.b.set_group(6, command)
    #
    # def updateKitchen(self, command):
    #     self.b.set_group(2, command)
    #
    def flashLights(self, color, delay, seconds):
        command = 0
        for i in range(1, round(seconds) + 1):
            for light in self.lights:
                if light["enabled"]:
                    if(light["type"] == "color"):
                        command = { 'xy': color, "alert": "select", 'bri': self.fIntensity}
                    else:
                        command = {"alert": "select", 'bri': self.fIntensity}
                    self.b.set_light(light["name"], command)

            time.sleep(delay)
    #
    def advanceAsOne(self, tTime):
        self.currentColor += 1;
        for light in self.lights:
            if light["enabled"] and light["type"] == "color":
                command = {'transitiontime': tTime, 'xy': self.colors[self.currentColor % len(self.colors)-1], 'bri': self.nIntensity}


    #     lrColor = self.b.get_light(10, 'xy')
    #
    #     if lrColor == self.red:
    #         lrCommand = {'transitiontime': tTime, 'xy': self.magenta, 'bri': self.nIntensity}
    #     elif lrColor == self.magenta:
    #         lrCommand = {'transitiontime': tTime, 'xy': self.blue, 'bri': self.nIntensity}
    #     elif lrColor == self.blue:
    #         lrCommand = {'transitiontime': tTime, 'xy': self.lblue, 'bri': self.nIntensity}
    #     elif lrColor == self.lblue:
    #         lrCommand = {'transitiontime': tTime, 'xy': self.green, 'bri': self.nIntensity}
    #     elif lrColor == self.green:
    #         lrCommand = {'transitiontime': tTime, 'xy': self.yellow, 'bri': self.nIntensity}
    #     elif lrColor == self.yellow:
    #         lrCommand = {'transitiontime': tTime, 'xy': self.orange, 'bri': self.nIntensity}
    #     else:
    #         lrCommand = {'transitiontime': tTime, 'xy': self.red, 'bri': self.nIntensity}
    #
    #     self.b.set_group(0, lrCommand)
    #
    # def advanceLights(self, tTime):
    #     lrColor = self.b.get_light(10, 'xy')
    #
    #     if lrColor == self.red:
    #         lrCommand = {'transitiontime': tTime, 'xy': self.magenta, 'bri': self.nIntensity}
    #         doorCommand = {'transitiontime': tTime, 'xy': self.blue, 'bri': self.nIntensity}
    #         hwCommand = {'transitiontime': tTime, 'xy': self.lblue, 'bri': self.nIntensity}
    #         kitchenCommand = {'transitiontime': tTime, 'xy': self.green, 'bri': self.nIntensity}
    #     elif lrColor == self.magenta:
    #         lrCommand = {'transitiontime': tTime, 'xy': self.blue, 'bri': self.nIntensity}
    #         doorCommand = {'transitiontime': tTime, 'xy': self.lblue, 'bri': self.nIntensity}
    #         hwCommand = {'transitiontime': tTime, 'xy': self.green, 'bri': self.nIntensity}
    #         kitchenCommand = {'transitiontime': tTime, 'xy': self.yellow, 'bri': self.nIntensity}
    #     elif lrColor == self.blue:
    #         lrCommand = {'transitiontime': tTime, 'xy': self.lblue, 'bri': self.nIntensity}
    #         doorCommand = {'transitiontime': tTime, 'xy': self.green, 'bri': self.nIntensity}
    #         hwCommand = {'transitiontime': tTime, 'xy': self.yellow, 'bri': self.nIntensity}
    #         kitchenCommand = {'transitiontime': tTime, 'xy': self.orange, 'bri': self.nIntensity}
    #     elif lrColor == self.lblue:
    #         lrCommand = {'transitiontime': tTime, 'xy': self.green, 'bri': self.nIntensity}
    #         doorCommand = {'transitiontime': tTime, 'xy': self.yellow, 'bri': self.nIntensity}
    #         hwCommand = {'transitiontime': tTime, 'xy': self.orange, 'bri': self.nIntensity}
    #         kitchenCommand = {'transitiontime': tTime, 'xy': self.red, 'bri': self.nIntensity}
    #     elif lrColor == self.green:
    #         lrCommand = {'transitiontime': tTime, 'xy': self.yellow, 'bri': self.nIntensity}
    #         doorCommand = {'transitiontime': tTime, 'xy': self.orange, 'bri': self.nIntensity}
    #         hwCommand = {'transitiontime': tTime, 'xy': self.red, 'bri': self.nIntensity}
    #         kitchenCommand = {'transitiontime': tTime, 'xy': self.magenta, 'bri': self.nIntensity}
    #     elif lrColor == self.yellow:
    #         lrCommand = {'transitiontime': tTime, 'xy': self.orange, 'bri': self.nIntensity}
    #         doorCommand = {'transitiontime': tTime, 'xy': self.red, 'bri': self.nIntensity}
    #         hwCommand = {'transitiontime': tTime, 'xy': self.magenta, 'bri': self.nIntensity}
    #         kitchenCommand = {'transitiontime': tTime, 'xy': self.blue, 'bri': self.nIntensity}
    #     else:
    #         lrCommand = {'transitiontime': tTime, 'xy': self.red, 'bri': self.nIntensity}
    #         doorCommand = {'transitiontime': tTime, 'xy': self.magenta, 'bri': self.nIntensity}
    #         hwCommand = {'transitiontime': tTime, 'xy': self.blue, 'bri': self.nIntensity}
    #         kitchenCommand = {'transitiontime': tTime, 'xy': self.lblue, 'bri': self.nIntensity}
    #
    #     self.updateLR(lrCommand)
    #     self.updateDoor(doorCommand)
    #     self.updateHW(hwCommand)
    #     self.updateKitchen(kitchenCommand)
