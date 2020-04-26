# Requires installation of:
# adafruit-blinka
# sparkfun-circuitpython-serlcd

# +5v    -> PWR.RAW
# GND    -> PWR.GND
# GPI0 2 -> I2C.DA
# GPIO 3 -> I2C.CL

# run once to save splash screen for LCD
import board
import busio
from sparkfun_serlcd import Sparkfun_SerLCD_I2C

i2c = busio.I2C(board.SCL, board.SDA)
serlcd = Sparkfun_SerLCD_I2C(i2c)

serlcd.set_fast_backlight_rgb(255, 255, 255)
serlcd.write('  SHOTS ALARM   ')

serlcd.save_splash_screen()
serlcd.splash_screen(True)