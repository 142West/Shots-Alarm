# Requires installation of:
# adafruit-blinka
# sparkfun-circuitpython-serlcd

# +5v    -> PWR.RAW
# GND    -> PWR.GND
# GPI0 2 -> I2C.DA
# GPIO 3 -> I2C.CL

import board
import busio
import time
from sparkfun_serlcd import Sparkfun_SerLCD_I2C


class ShotsAlarmSerLCD:

    def __init__(self, logger):
        self.logger = logger
        i2c = busio.I2C(1, 0)
        self.serlcd = Sparkfun_SerLCD_I2C(i2c)
        self.colors = {
            "Black": [0, 0, 0],
            "White": [255, 255, 255],
            "Red": [255, 0, 0],
            "Orange": [255, 140, 0],
            "Yellow": [255, 255, 0],
            "Green": [0, 255, 0],
            "Teal": [0, 255, 255],
            "Blue": [0, 0, 255],
            "Indigo": [75, 0, 140],
            "Purple": [130, 32, 240],
            "Grey": [128, 128, 128]
        }
        self.countDownDigits = 0
        self.lcdRow = 2
        self.lcdCol = 16
        self.setColorName("White")
        self.writeCenter("Shots Alarm", " ")
        self.shots = False

    def clear(self):
        self.serlcd.clear()

    def setColorName(self, colorName):
        # check for color name in dictionary
        colorVal = self.colors.get(colorName)
        if colorVal:
            self.serlcd.set_fast_backlight_rgb(colorVal[0], colorVal[1], colorVal[2])
            return 0
        else:  # color not in dictionary
            return 1

    def setColorRGB(self, R, G, B):
        # filter input to ensure 0 <= R,G,B <= 255
        colors = [R, G, B]
        for color in colors:
            if color < 0:
                color = 0
            if color > 255:
                color = 255
        self.serlcd.set_fast_backlight_rgb(R, G, B)

    def writeCenter(self, line1, line2):
        self.clear()
        self.setColorName("White")
        line1 = self.strCenter(line1) + ((self.lcdCol + 2) * " ")
        line2 = self.strCenter(line2)
        finalString = line1[0:16] + line2[0:16]
        self.serlcd.write(finalString)

    def write2Lines(self, line1, line2):
        self.clear()
        self.setColorName("White")
        line1 = line1 + ((self.lcdCol + 2) * " ")
        finalString = line1[0:16] + line2[0:16]
        self.serlcd.write(finalString)

    def shotsCountDown(self, countDownTime, songName):
        self.shots = True
        self.clear()
        self.setColorName("White")
        startTime = int(time.time())
        currentElapsedTime = 0
        while currentElapsedTime < countDownTime and self.shots == True:
            currentElapsedTime = int(time.time()) - startTime
            shotsText = "SHOTS IN: " + str(round(countDownTime - currentElapsedTime))
            self.writeCenter(shotsText, songName)
            time.sleep(.5)

    def shotsGo(self, songName):
        self.clear()
        shotsText = "GO GO GO"
        self.writeCenter(shotsText, songName)
        self.setColorName("Green")

    def playText(self, line1):
        self.shots = False
        self.clear()
        self.setColorName("White")
        self.writeCenter(line1, " ")

    def strCenter(self, text):
        # center string if <= 16 chars
        if len(text) <= 16:
            return text.center(16, " ")
        return text[0, 15]

    def write32Chars(self, text):
        self.clear()
        print("Input text length = " + str(len(text)))
        writeString = text[0:31]
        print("Write text length = " + str(len(writeString)))
        print(text)
        self.serlcd.write(writeString)

    def shutdown(self):
        self.shots = False
        self.clear()
        self.setColorName("Black")
