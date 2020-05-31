import atexit
import time


def leave():
    print("testing")


atexit.register(leave)
while True:
    time.sleep(1)
