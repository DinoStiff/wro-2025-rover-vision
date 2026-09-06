# WRO 2025 Rover Vision and MQTT Tools

Hardware-side code snapshot from a WRO robotics project. It contains an OpenMV color/blob detector, a Matrix Mini R4 scanning sketch, and small Python MQTT tools for controlling the test loop and viewing the published map.

This is a historical hardware snapshot, not a complete competition-ready robot. The older rover and “icetaker” experiments are intentionally not included because their final role was not confirmed.

## Included components

| Path | Purpose |
| --- | --- |
| `camera/main.py` | OpenMV image capture and color/blob detection |
| `camera/matrix_mini.py` | OpenMV UART packet helper |
| `camera/fill_light.py` | OpenMV fill-light helper |
| `scanning/scanning.ino` | Matrix Mini R4 map integration and MQTT publishing |
| `tools/mqtt_control_console.py` | Interactive MQTT test/control console (renamed from `test.py`) |
| `tools/mqtt_map_viewer.py` | Read-only MQTT map viewer (renamed from `getmap.py`) |

## Data flow

```text
OpenMV camera ──UART──> Matrix Mini / scanner ──MQTT──> map viewer or control console
```

The OpenMV script sends a compact binary UART packet containing detected color classes, positions, and areas. The scanning sketch publishes maps as `MAP rows,cols;...` messages on the configured MQTT topic.

The source files were developed around the same 8-row scan setting, but the OpenMV UART packet path and `MiniR4.Vision.SmartCamReader()` path should be validated on the actual hardware before being described as one fully integrated runtime pipeline.

## Python tools

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
set -a; source .env; set +a
python tools/mqtt_map_viewer.py
```

In another terminal, run `python tools/mqtt_control_console.py` to send test messages such as `start`, `hello`, or a raw MQTT payload. Both tools use `MQTT_BROKER_HOST`, `MQTT_BROKER_PORT`, and `MQTT_TOPIC`; they default to a local broker and contain no network credentials.

## OpenMV and Arduino setup

1. Open `camera/main.py` in the OpenMV IDE and upload it with `matrix_mini.py` and `fill_light.py` available on the camera filesystem.
2. Open `scanning/scanning.ino` in Arduino IDE with the Matrix Mini R4 and its library installed.
3. Fill the Wi-Fi and MQTT placeholders in the Arduino sketch locally before flashing. Keep those values out of GitHub.
4. Use the same broker host, port, and topic for the scanner and Python tools.

The stock OpenMV documentation file and temporary editor backup were not copied into this public snapshot.

## Safety and scope

The original local sketches contained Wi-Fi credentials and private broker addresses. This repository replaces them with placeholders and environment variables. Do not reuse credentials that appeared in the original files; rotate them if they are still active. No rover movement firmware is included because the final rover version was not confirmed.

## Validation

```bash
python3 -m py_compile tools/mqtt_control_console.py tools/mqtt_map_viewer.py camera/matrix_mini.py camera/fill_light.py
```

The OpenMV and Arduino files require their respective hardware runtimes and cannot be executed by normal desktop Python.
