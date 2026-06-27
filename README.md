# shots-alarm-remote

A wireless MQTT button for Home Assistant built on a Raspberry Pi Zero W. Designed to be wired to a pull station (fire alarm style) that triggers a Home Assistant automation when pulled and resets when released.

## Hardware

| Component | GPIO |
|---|---|
| Status LED | GPIO 17 |
| Trigger input (pull station) | GPIO 27 |
| Power button | GPIO 3 (handled by device tree overlay — no code needed) |

**Status LED behaviour:**
- Blinking — running but not connected to MQTT broker
- Solid — connected and ready
- 3 rapid flashes — trigger pulled while disconnected (press ignored)

---

## Requirements

- Raspberry Pi Zero W
- Raspberry Pi OS Trixie
- Home Assistant with Mosquitto MQTT broker add-on

---

## 1. Flash & Configure Pi OS

Flash Raspberry Pi OS Lite (32-bit) using Raspberry Pi Imager. In the imager settings:
- Set hostname (e.g. `shots-alarm-remote`)
- Enable SSH
- Configure WiFi

---

## 2. Set Up the Power Button (GPIO 3)

GPIO 3 has a hardware feature that wakes the Pi from halt when pulled low — no code needed. Add the shutdown overlay so pressing the button also gracefully shuts down a running Pi:

```bash
echo "dtoverlay=gpio-shutdown,gpio_pin=3" | sudo tee -a /boot/firmware/config.txt
sudo reboot
```

After this, one button on GPIO 3 gives you full on/off control:
- **Pi running** → press to shut down gracefully
- **Pi halted** → press to boot

---

## 3. Install Dependencies

```bash
# System packages
sudo apt update
sudo apt install python3-full python3-rpi.gpio git -y

# Virtual environment
python3 -m venv /home/pi/venv --system-site-packages
/home/pi/venv/bin/pip install paho-mqtt gpiozero python-dotenv
```

---

## 4. Install the Script

```bash
# Clone the repo
git clone https://github.com/142West/Shots-Alarm-Remote.git
cd Shots-Alarm-Remote

# Copy files
cp .env.example .env
```

Edit `/home/pi/Shots-Alarm-Remote/.env` with your MQTT credentials:

```bash
nano /home/pi/Shots-Alarm-Remote/.env
```

Secure the file so credentials aren't world-readable:

```bash
chmod 600 /home/pi/Shots-Alarm-Remote/.env
```

---

## 5. Set Up Mosquitto on Home Assistant

In HA go to **Settings → Add-ons → Add-on Store** and install **Mosquitto broker**.

In the Mosquitto add-on **Configuration** tab, add a user:

```yaml
logins:
  - username: mqttuser
    password: yourpassword
```

Then go to **Settings → Devices & Services** and add the **MQTT integration** — it should auto-discover Mosquitto.

---

## 6. Configure Home Assistant

Add this to your `configuration.yaml`:

```yaml
mqtt:
  binary_sensor:
    - name: "Shots Alarm Remote"
      unique_id: "shots_alarm_remote"
      state_topic: "home/shots-alarm-remote/trigger"
      payload_on: "PRESS"
      payload_off: "RELEASE"
      device_class: safety
      availability_topic: "home/shots-alarm-remote/status"
      payload_available: "online"
      payload_not_available: "offline"
```

Reload YAML: **Developer Tools → YAML → Reload All**.

---

## 7. Install as a System Service

```bash
sudo cp shots-alarm-remote.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable shots-alarm-remote
sudo systemctl start shots-alarm-remote
```

Check it's running:

```bash
sudo systemctl status shots-alarm-remote
```

View live logs:

```bash
journalctl -u shots-alarm-remote -f
```

---

## Configuration Reference

All config lives in `/home/pi/Shots-Alarm-Remote/.env`. Only `MQTT_USER` and `MQTT_PASS` are required — everything else has a sensible default.

| Variable | Default | Description |
|---|---|---|
| `MQTT_USER` | — | MQTT username (required) |
| `MQTT_PASS` | — | MQTT password (required) |
| `MQTT_BROKER` | `homeassistant.local` | HA IP or hostname |
| `MQTT_PORT` | `1883` | MQTT port |
| `MQTT_TOPIC` | `home/shots-alarm-remote/trigger` | Topic for button state |
| `DEVICE_NAME` | `shots-alarm-remote` | Used in MQTT topics and logs |
| `RECONNECT_S` | `5` | Seconds between reconnect attempts |
| `BLINK_HZ` | `2` | LED blink speed when not connected |
