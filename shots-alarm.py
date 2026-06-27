#!/usr/bin/env python3
"""
Shots Alarm - MQTT Pull Station - Pi 4
=======================================
GPIO 17 - Trigger button (pull station)
  - Pull  : publishes PRESS   (HA sensor turns ON)
  - Reset : publishes RELEASE (HA sensor turns OFF)
"""

import paho.mqtt.client as mqtt
from gpiozero import Button
from dotenv import load_dotenv
import threading
import logging
import signal
import sys
import time
import os

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ---------------------------------------------
#  CONFIG
# ---------------------------------------------
MQTT_BROKER  = os.getenv("MQTT_BROKER",  "homeassistant.local")
MQTT_PORT    = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER    = os.getenv("MQTT_USER")
MQTT_PASS    = os.getenv("MQTT_PASS")
MQTT_TOPIC   = os.getenv("MQTT_TOPIC",   "home/shots-alarm/trigger")

DEVICE_NAME  = os.getenv("DEVICE_NAME",  "shots-alarm")
RECONNECT_S  = int(os.getenv("RECONNECT_S", "5"))
HEARTBEAT_S  = int(os.getenv("HEARTBEAT_S", "30"))

STATUS_TOPIC = f"home/{DEVICE_NAME}/status"

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
        logging.FileHandler("/home/pi/shots-alarm.log"),
    ],
)
log = logging.getLogger(__name__)

# ---------------------------------------------
#  GPIO SETUP
# ---------------------------------------------
trigger_btn = Button(17, pull_up=True, bounce_time=0.05)

# ---------------------------------------------
#  STATE
# ---------------------------------------------
_connected    = False
_shutdown_evt = threading.Event()

# ---------------------------------------------
#  MQTT CALLBACKS
# ---------------------------------------------
def on_connect(client, userdata, flags, rc):
    global _connected
    if rc == 0:
        log.info(f"MQTT connected to {MQTT_BROKER}")
        client.publish(STATUS_TOPIC, "online", qos=1, retain=True)
        log.info(f"Published 'online' -> {STATUS_TOPIC}")
        initial = "PRESS" if trigger_btn.is_pressed else "RELEASE"
        client.publish(MQTT_TOPIC, initial, qos=1, retain=False)
        log.info(f"Published initial state '{initial}' -> {MQTT_TOPIC}")
        _connected = True
    else:
        log.warning(f"MQTT connect failed, rc={rc}")
        _connected = False

def on_disconnect(client, userdata, rc):
    global _connected
    log.warning(f"MQTT disconnected (rc={rc}), will retry in {RECONNECT_S}s")
    _connected = False

# ---------------------------------------------
#  MQTT CLIENT
# ---------------------------------------------
client = mqtt.Client(client_id=DEVICE_NAME)
client.username_pw_set(MQTT_USER, MQTT_PASS)
client.on_connect    = on_connect
client.on_disconnect = on_disconnect

client.will_set(STATUS_TOPIC, "offline", qos=1, retain=True)

client.reconnect_delay_set(min_delay=RECONNECT_S, max_delay=60)

def mqtt_connect():
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

def on_trigger_released():
    if _connected:
        result = client.publish(MQTT_TOPIC, "RELEASE", qos=1, retain=False)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            log.info(f"Published 'RELEASE' -> {MQTT_TOPIC}")
        else:
            log.warning(f"Publish failed, rc={result.rc}")
    else:
        log.warning("Trigger reset but MQTT not connected -- ignored")

trigger_btn.when_pressed  = on_trigger_pressed
trigger_btn.when_released = on_trigger_released

# ---------------------------------------------
#  HEARTBEAT — re-publish current state so HA
#  recovers after a restart
# ---------------------------------------------
def _heartbeat_loop():
    while not _shutdown_evt.is_set():
        _shutdown_evt.wait(HEARTBEAT_S)
        if _shutdown_evt.is_set():
            break
        if _connected:
            state = "PRESS" if trigger_btn.is_pressed else "RELEASE"
            client.publish(MQTT_TOPIC, state, qos=1, retain=False)
            log.debug(f"Heartbeat '{state}' -> {MQTT_TOPIC}")

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
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_signal)
signal.signal(signal.SIGINT,  handle_signal)

# ---------------------------------------------
#  MAIN
# ---------------------------------------------
if __name__ == "__main__":
    log.info(f"Starting {DEVICE_NAME}...")
    mqtt_connect()

    threading.Thread(target=_heartbeat_loop, daemon=True).start()
    log.info("Running. Pull station to trigger, reset to release.")
    _shutdown_evt.wait()
