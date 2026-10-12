# LED strip controller

Control an RGB LED strip from a Raspberry Pi, with a mobile-friendly web UI.

- Color wheel, brightness, on/off with smooth fades
- Two-color fades and a rainbow cycle
- Saved favorite colors
- Remembers its state across restarts
- A small CLI and a JSON API

## Hardware

An RGB strip driven through MOSFETs (or a driver board) from three GPIO pins.
Default pins (BCM numbering): red **17**, green **22**, blue **24**. Override with `LED_PINS=17,22,24`.

## Setup (on the Pi)

```sh
sudo apt install git python3-venv
```

Install the pigpio daemon. On Raspberry Pi OS Bookworm or older: `sudo apt install pigpio`.
On Trixie (Debian 13) the package was removed, so build it from source:

```sh
sudo apt install -y python3-setuptools python3-full make gcc wget
wget https://github.com/joan2937/pigpio/archive/refs/tags/v79.tar.gz
tar zxf v79.tar.gz && cd pigpio-79
make && sudo make install && sudo ldconfig
cd ..
```

Note that pigpio does not support the Pi 5.

```sh
sudo systemctl daemon-reload
sudo systemctl enable --now pigpiod

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m ledctl
```

Open `http://<pi-address>:5000`.

To start on boot, edit paths/user in `deploy/led.service`, then:

```sh
sudo cp deploy/led.service /etc/systemd/system/
sudo systemctl enable --now led
```

## Developing without a Pi

```sh
python3 -m venv .venv && .venv/bin/pip install flask pytest
LED_MOCK=1 .venv/bin/python -m ledctl
.venv/bin/pytest
```

Open `http://127.0.0.1:5000`. On macOS, port 5000 is used by AirPlay Receiver, so run with `LED_PORT=5001` instead (or disable AirPlay Receiver in System Settings). In mock mode the page shows a virtual LED strip at the top that mirrors exactly what the real strip would show, including fades and the rainbow.

The UI is plain HTML/CSS/JS in `web/`, so there is no build step.

## Configuration (environment variables)

| Variable       | Default      | Description                              |
| -------------- | ------------ | ---------------------------------------- |
| `LED_PINS`     | `17,22,24`   | GPIO pins for R, G, B                    |
| `LED_GAMMA`    | `2.8`        | Gamma correction                         |
| `LED_PORT`     | `5000`       | HTTP port                                |
| `LED_HOST`     | `0.0.0.0`    | Bind address                             |
| `LED_DATA_DIR` | `./data`     | Where state and favorites are stored     |
| `LED_MOCK`     | unset        | Set to `1` to run without hardware       |

There is no authentication, so only expose it on a trusted network.

## CLI

```sh
python -m ledctl.cli color '#ff00aa'
python -m ledctl.cli fade '#ff00aa' '#00ffee' --period 4
python -m ledctl.cli rainbow --period 20
python -m ledctl.cli off        # also: on, status
```

Use `--url` or `LED_URL` to target another host.

## API

All bodies are JSON; every endpoint returns the new state `{on, mode, color}` or an `{error}` with status 400.

| Method | Path                      | Body                                  |
| ------ | ------------------------- | ------------------------------------- |
| GET    | `/api/state`              |                                       |
| POST   | `/api/color`              | `{"color": "#rrggbb"}`                |
| POST   | `/api/power`              | `{"on": true}`                        |
| POST   | `/api/fade`               | `{"start": "#..", "end": "#..", "period": 4}` (seconds one way) |
| POST   | `/api/rainbow`            | `{"period": 20}` (seconds per cycle)  |
| GET    | `/api/favorites`          |                                       |
| POST   | `/api/favorites`          | `{"color": "#rrggbb"}`                |
| DELETE | `/api/favorites/<rrggbb>` |                                       |
