# Disaster Rescue Rover System

A complete rescue rover stack that combines ESP32 firmware, a Raspberry Pi intelligence layer, a Go backend using Chi, and a React mission control dashboard. The rover explores, tracks its trail, detects victims, streams camera video, and reports real-time telemetry to a command center.

## Architecture

- ESP32 firmware: motor control (L298N), IMU fusion (MPU6050), ultrasonic obstacle avoidance, GPS parsing (NEO-6M), and telemetry output over UART.
- Raspberry Pi: serial bridge, path tracking with GPS drift correction, person detection, and data relay to the backend.
- Go backend (Chi): REST API, WebSocket hub, and MJPEG camera stream proxy.
- React frontend: mission control UI with live map, telemetry, logs, alerts, and manual controls.

## Data Flow

ESP32 -> Pi (serial)
Pi -> Go (HTTP + WebSocket)
Go -> React (WebSocket)
React -> Go -> Pi -> ESP32 (commands)

## Hardware (Strict)

- ESP32 DevKit V1
- L298N motor driver
- MPU6050 IMU
- HC-SR04 ultrasonic sensor
- NEO-6M GPS
- Raspberry Pi

## Repository Layout

- backend/
  - main.go
  - router.go
  - websocket.go
  - telemetry_handler.go
  - models.go
  - camera.go
- frontend/
  - src/components/MapView.jsx
  - src/components/CameraFeed.jsx
  - src/components/TelemetryPanel.jsx
  - src/components/AlertsBar.jsx
  - src/components/LogsPanel.jsx
  - src/components/Controls.jsx
  - src/App.jsx
- pi/
  - serial_reader.py
  - path_tracker.py
  - drift_correction.py
  - vision.py
  - api_client.py
- esp32/
  - gps.cpp
  - imu.cpp
  - odometry.cpp
  - motor.cpp
  - sonar.cpp
  - telemetry.cpp
  - main.ino

## Setup

### 1) ESP32 firmware

- Install Arduino IDE and ESP32 board support.
- Install library: TinyGPSPlus.
- Wiring defaults used in code:
  - Pi UART: RX=GPIO16, TX=GPIO17
  - GPS: RX=GPIO32, TX=GPIO4
  - Sonar: TRIG=GPIO5, ECHO=GPIO18
  - IMU: I2C SDA=GPIO21, SCL=GPIO22
  - L298N: IN1=GPIO27, IN2=GPIO26, IN3=GPIO25, IN4=GPIO33, ENA=GPIO14, ENB=GPIO12
- Flash esp32/main.ino

### 2) Raspberry Pi

```bash
sudo apt update
sudo apt install -y python3-pip python3-opencv
pip3 install pyserial requests websocket-client flask ultralytics
```

Run the bridge (includes MJPEG stream on port 8000):

```bash
python3 pi/serial_reader.py --port /dev/serial0 --backend http://<BACKEND_IP>:8080 --ws ws://<BACKEND_IP>:8080/ws --stream
```

### 3) Go backend

```bash
cd backend
go mod tidy
go run .
```

Environment options:

- PORT (default 8080)
- PI_CAMERA_STREAM_URL (default http://raspberrypi:8000/camera/stream)
- ALLOWED_ORIGINS (comma-separated, default *)

### 4) React dashboard

```bash
cd frontend
npm install
npm run dev
```

Optional environment overrides in frontend/.env:

```
VITE_BACKEND_HTTP_BASE=http://<BACKEND_IP>:8080
VITE_BACKEND_WS_URL=ws://<BACKEND_IP>:8080/ws
```

## Notes

- GPS fixes are fused with odometry to reduce drift; without GPS, the map shows local coordinates only.
- Victim detection uses OpenCV HOG by default and can optionally switch to YOLO if a model is provided.
- The MJPEG stream is proxied through the Go backend at /camera/stream.
