# Requires installation of:
# adafruit-blinka
# sparkfun-circuitpython-serlcd

# +5v    -> PWR.RAW
# GND    -> PWR.GND
# GPI0 2 -> I2C.DA
# GPIO 3 -> I2C.CL

from time import sleep
import board
import busio
from sparkfun_serlcd import Sparkfun_SerLCD_I2C

i2c = busio.I2C(1, 0)
serlcd = Sparkfun_SerLCD_I2C(i2c)
sleep(1)

serlcd.set_fast_backlight_rgb(0, 0, 0)
serlcd.clear()
serlcd.write("Hello, world!")
sleep(0.5)

serlcd.set_fast_backlight_rgb(255, 0, 0) #bright red
sleep(0.5)

serlcd.set_fast_backlight(0xFF8C00) #orange
sleep(0.5)

serlcd.set_fast_backlight_rgb(255, 255, 0) #bright yellow
sleep(0.5)

serlcd.set_fast_backlight_rgb(0, 255, 0) #bright green
sleep(0.5)

serlcd.set_fast_backlight_rgb(0, 0, 255) #bright blue
sleep(0.5)

serlcd.set_fast_backlight(0x4B0082) #indigo, a kind of dark purplish blue
sleep(0.5)

serlcd.set_fast_backlight(0xA020F0) #violet
sleep(0.5)

serlcd.set_fast_backlight(0x808080) #grey
sleep(0.5)

serlcd.set_fast_backlight_rgb(255, 255, 255) #bright white
sleep(0.5)

serlcd.set_fast_backlight_rgb(0, 0, 0)