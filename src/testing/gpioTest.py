import time
from signal import pause

import gpiozero


def test():
    print("hi")


button = gpiozero.Button(4)
button.when_activated = test

pause()


