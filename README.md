# shots-alarm

An MQTT pull station for Home Assistant built on a Raspberry Pi 4. A fire alarm style pull station on GPIO 17 triggers a Home Assistant automation when pulled and resets when released.

## Hardware

| Component | GPIO |
|---|---|
| Trigger input (pull station) | GPIO 17 |

---

## Requirements

- Raspberry Pi 4
- Raspberry Pi OS Trixie
- Home Assistant with Mosquitto MQTT broker add-on

---

## 1. Flash & Configure Pi OS

Flash Raspberry Pi OS Lite using Raspberry Pi Imager. In the imager settings:
- Set hostname (e.g. `shots-alarm`)
- Enable SSH

---

## 2. Install Dependencies

```bash
# System packages
sudo apt update
sudo apt install python3-full python3-rpi.gpio git -y

# Virtual environment
python3 -m venv /home/pi/venv --system-site-packages
/home/pi/venv/bin/pip install paho-mqtt gpiozero python-dotenv
```

---

## 3. Install the Script

```bash
# Clone the repo
git clone https://github.com/142West/Shots-Alarm.git
cd Shots-Alarm

# Copy files
cp .env.example .env
```

Edit `/home/pi/Shots-Alarm/.env` with your MQTT credentials:

```bash
nano /home/pi/Shots-Alarm/.env
```

Secure the file so credentials aren't world-readable:

```bash
chmod 600 /home/pi/Shots-Alarm/.env
```

---

## 4. Set Up Mosquitto on Home Assistant

In HA go to **Settings → Add-ons → Add-on Store** and install **Mosquitto broker**.

In the Mosquitto add-on **Configuration** tab, add a user:

```yaml
logins:
  - username: mqttuser
    password: yourpassword
```

Then go to **Settings → Devices & Services** and add the **MQTT integration** — it should auto-discover Mosquitto.

---

## 5. Configure Home Assistant

Add this to your `configuration.yaml`:

```yaml
mqtt:
  binary_sensor:
    - name: "Shots Alarm"
      unique_id: "shots_alarm"
      state_topic: "home/shots-alarm/trigger"
      payload_on: "PRESS"
      payload_off: "RELEASE"
      device_class: safety
      availability_topic: "home/shots-alarm/status"
      payload_available: "online"
      payload_not_available: "offline"
```

Reload YAML: **Developer Tools → YAML → Reload All**.

---

## 6. Install as a System Service

```bash
sudo cp shots-alarm.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable shots-alarm
sudo systemctl start shots-alarm
```

Check it's running:

```bash
sudo systemctl status shots-alarm
```

View live logs:

```bash
journalctl -u shots-alarm -f
```

---

## Configuration Reference

All config lives in `/home/pi/Shots-Alarm/.env`. Only `MQTT_USER` and `MQTT_PASS` are required — everything else has a sensible default.

| Variable | Default | Description |
|---|---|---|
| `MQTT_USER` | — | MQTT username (required) |
| `MQTT_PASS` | — | MQTT password (required) |
| `MQTT_BROKER` | `homeassistant.local` | HA IP or hostname |
| `MQTT_PORT` | `1883` | MQTT port |
| `MQTT_TOPIC` | `home/shots-alarm/trigger` | Topic for button state |
| `DEVICE_NAME` | `shots-alarm` | Used in MQTT topics and logs |
| `RECONNECT_S` | `5` | Seconds between reconnect attempts |
| `HEARTBEAT_S` | `30` | Seconds between state re-publishes (so HA recovers after restart) |
