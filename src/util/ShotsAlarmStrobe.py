from gpiozero import DigitalOutputDevice

class ShotsAlarmStrobe:
    def __init__(self):
        self.strobe = DigitalOutputDevice(17)
        self.off()

    def on(self):
        self.strobe.on()

    def off(self):
        self.strobe.off()

    def alarm_activate(self, countdownLength, strobeLength):
        self.on()

    def alarm_cancel(self):
        self.off()


