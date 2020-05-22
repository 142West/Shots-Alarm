# Requires installation of:
# adafruit-blinka
# sparkfun-circuitpython-serlcd

# +5v    -> PWR.RAW
# GND    -> PWR.GND
# GPI0 2 -> I2C.DA
# GPIO 3 -> I2C.CL

import board
import busio
from sparkfun_serlcd import Sparkfun_SerLCD_I2C

class ShotsAlarmSerLCD:

    def __init__(self):
        i2c = busio.I2C(1, 0)
        self.serlcd = Sparkfun_SerLCD_I2C(i2c)
        self.colors = {
            "Black" : [  0,   0,   0],
            "White" : [255, 255, 255],
            "Red"   : [255,   0,   0],
            "Orange": [255, 140,   0],
            "Yellow": [255, 255,   0],
            "Green" : [  0, 255,   0],
            "Teal"  : [  0, 255, 255],
            "Blue"  : [  0,   0, 255],
            "Indigo": [ 75,   0, 140],
            "Purple": [130,  32, 240],
            "Grey"  : [128, 128, 128]
        }
        self.countDownDigits = 0
        self.lcdRow = 2
        self.lcdCol = 16

    def clear(self):
        self.serlcd.clear()

    def setColorName(self,colorName):
        # check for color name in dictionary
        colorVal = self.colors.get(colorName)
        if colorVal:
            self.serlcd.set_fast_backlight_rgb(colorVal[0], colorVal[1], colorVal[2])
            return 0
        else: #color not in dictionary
            return 1

    def setColorRGB(self, R, G, B):
        # filter input to ensure 0 <= R,G,B <= 255
        colors = [R,G,B]
        for color in colors:
            if color < 0:
                color = 0
            if color > 255:
                color = 255
        self.serlcd.set_fast_backlight_rgb(R, G, B)

    def writeCenter(self, text):
        self.serlcd.write(self.strCenter(text))

    def writeColRow(self,text,col,row):
        self.serlcd.write(text)

    def shotsInit(self, time):
        self.clear()
        self.setColorName("White")

        #format "SHOTS IN:" string with correct spacing
        self.countDownDigits = len(str(time))
        shotsText = "SHOTS IN: " + (self.countDownDigits * " ")
        self.writeCenter(shotsText)

    def shotsCountDown(self, time):
        return 0


    def strCenter(self, text):
        # center string if <= 16 chars
        if len(text) <= 16:
            return text.center(16, " ")

