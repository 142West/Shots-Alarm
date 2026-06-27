#!/usr/bin/env python3
"""
Wireless MQTT Button - Pi Zero W
================================
GPIO 17 - Status LED
  - Blinking : running but not connected to MQTT broker
  - Solid ON  : connected and ready

GPIO 27 - Trigger button (pull station)
  - Pull  : publishes PRESS   (HA sensor turns ON)
  - Reset : publishes RELEASE (HA sensor turns OFF)

GPIO 3  - Power button (handled by dtoverlay=gpio-shutdown in /boot/firmware/config.txt)
  - Press to shutdown, press again to wake -- no code needed
"""

import paho.mqtt.client as mqtt
from gpiozero import LED, Button
from dotenv import load_dotenv
import threading
import logging
import signal
import sys
import time
import os

# Load .env from same directory as this script
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ---------------------------------------------
#  CONFIG -- sensitive values come from .env,
#            the rest can be overridden there too
# ---------------------------------------------
MQTT_BROKER  = os.getenv("MQTT_BROKER",  "homeassistant.local")
MQTT_PORT    = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER    = os.getenv("MQTT_USER")     # required -- set in .env
MQTT_PASS    = os.getenv("MQTT_PASS")     # required -- set in .env
MQTT_TOPIC   = os.getenv("MQTT_TOPIC",   "home/shots-alarm-remote/trigger")

DEVICE_NAME  = os.getenv("DEVICE_NAME",  "shots-alarm-remote")
RECONNECT_S  = int(os.getenv("RECONNECT_S", "5"))
BLINK_HZ     = int(os.getenv("BLINK_HZ",   "2"))

STATUS_TOPIC = f"home/{DEVICE_NAME}/status"

# Fail fast if credentials are missing
if not MQTT_USER or not MQTT_PASS:
    sys.exit("ERROR: MQTT_USER and MQTT_PASS must be set in .env")

# ---------------------------------------------
#  LOGGING
# ---------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("/home/pi/wireless_button.log"),
    ],
)
log = logging.getLogger(__name__)

# ---------------------------------------------
#  GPIO SETUP
# ---------------------------------------------
led         = LED(17)
trigger_btn = Button(27, pull_up=True, bounce_time=0.05)

# ---------------------------------------------
#  STATE
# ---------------------------------------------
_connected    = False
_blink_thread = None
_shutdown_evt = threading.Event()

# ---------------------------------------------
#  LED CONTROL
# ---------------------------------------------
def _blink_loop():
    """Run in background thread -- blinks LED until stopped."""
    half = 1.0 / (BLINK_HZ * 2)
    while not _shutdown_evt.is_set() and not _connected:
        led.on()
        time.sleep(half)
        led.off()
        time.sleep(half)

def set_led_state(connected: bool):
    """Switch LED between blink (not ready) and solid (ready)."""
    global _connected, _blink_thread
    _connected = connected
    if connected:
        if _blink_thread and _blink_thread.is_alive():
            _blink_thread.join(timeout=1)
        led.on()
        log.info("LED -> SOLID (connected)")
    else:
        led.off()
        if _blink_thread is None or not _blink_thread.is_alive():
            _blink_thread = threading.Thread(target=_blink_loop, daemon=True)
            _blink_thread.start()
        log.info("LED -> BLINKING (not connected)")

# ---------------------------------------------
#  MQTT CALLBACKS
# ---------------------------------------------
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        log.info(f"MQTT connected to {MQTT_BROKER}")
        client.publish(STATUS_TOPIC, "online", qos=1, retain=True)
        log.info(f"Published 'online' -> {STATUS_TOPIC}")
        # Publish current physical state so HA doesn't show 'unknown' on startup
        initial = "PRESS" if trigger_btn.is_pressed else "RELEASE"
        client.publish(MQTT_TOPIC, initial, qos=1, retain=False)
        log.info(f"Published initial state '{initial}' -> {MQTT_TOPIC}")
        set_led_state(True)
    else:
        log.warning(f"MQTT connect failed, rc={rc}")
        set_led_state(False)

def on_disconnect(client, userdata, rc):
    log.warning(f"MQTT disconnected (rc={rc}), will retry in {RECONNECT_S}s")
    set_led_state(False)

# ---------------------------------------------
#  MQTT CLIENT
# ---------------------------------------------
client = mqtt.Client(client_id=DEVICE_NAME)
client.username_pw_set(MQTT_USER, MQTT_PASS)
client.on_connect    = on_connect
client.on_disconnect = on_disconnect

# Last Will -- broker sends this if the Pi drops unexpectedly
client.will_set(STATUS_TOPIC, "offline", qos=1, retain=True)

client.reconnect_delay_set(min_delay=RECONNECT_S, max_delay=60)

def mqtt_connect():
    """Initial blocking connect with retry loop."""
    while not _shutdown_evt.is_set():
        try:
            log.info(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}...")
            client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            client.loop_start()
            return
        except Exception as e:
            log.error(f"Connection error: {e}. Retrying in {RECONNECT_S}s...")
            time.sleep(RECONNECT_S)

# ---------------------------------------------
#  TRIGGER BUTTON HANDLERS
# ---------------------------------------------
def on_trigger_pressed():
    if _connected:
        result = client.publish(MQTT_TOPIC, "PRESS", qos=1, retain=False)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            log.info(f"Published 'PRESS' -> {MQTT_TOPIC}")
        else:
            log.warning(f"Publish failed, rc={result.rc}")
    else:
        log.warning("Trigger pulled but MQTT not connected -- ignored")
        threading.Thread(target=_error_flash, daemon=True).start()

def on_trigger_released():
    if _connected:
        result = client.publish(MQTT_TOPIC, "RELEASE", qos=1, retain=False)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            log.info(f"Published 'RELEASE' -> {MQTT_TOPIC}")
        else:
            log.warning(f"Publish failed, rc={result.rc}")
    else:
        log.warning("Trigger reset but MQTT not connected -- ignored")

def _error_flash():
    """3 rapid flashes to indicate a missed press."""
    for _ in range(3):
        led.on();  time.sleep(0.1)
        led.off(); time.sleep(0.1)
    if not _connected:
        set_led_state(False)

trigger_btn.when_pressed  = on_trigger_pressed
trigger_btn.when_released = on_trigger_released

# ---------------------------------------------
#  SIGNAL HANDLING (systemd stop / Ctrl-C)
# ---------------------------------------------
def handle_signal(sig, frame):
    log.info(f"Caught signal {sig}, shutting down cleanly...")
    _shutdown_evt.set()
    try:
        client.publish(STATUS_TOPIC, "offline", qos=1, retain=True)
        log.info(f"Published 'offline' -> {STATUS_TOPIC}")
        client.loop_stop()
        client.disconnect()
    except Exception:
        pass
    led.off()
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT,  handle_signal)

# ---------------------------------------------
#  MAIN
# ---------------------------------------------
if __name__ == "__main__":
    log.info(f"Starting {DEVICE_NAME}...")
    set_led_state(False)   # Start blinking -- not yet connected
    mqtt_connect()

    log.info("Running. Pull station to trigger, reset to release.")
    _shutdown_evt.wait()
