# Raspberry Pi Robot Command Server Setup Guide

## 📋 Overview

This guide helps you set up a Raspberry Pi as a bridge between your Windows PC (person tracking) and ESP32 robot via Bluetooth.

**Data Flow:**
```
Windows PC (GUI) → HTTP → Raspberry Pi → Bluetooth → ESP32 Robot
```

## 🛠️ Hardware Requirements

### Raspberry Pi Setup
- **Raspberry Pi 4** (recommended) or Pi 3B+
- **MicroSD Card** (32GB+ Class 10)
- **Camera Module** or USB webcam
- **Power Supply** (5V 3A for Pi 4)
- **Built-in Bluetooth** (Pi 3+ has this built-in)

### ESP32 Robot Setup
- **ESP32 Development Board**
- **Motor Driver** (L298N or similar)
- **Motors** and robot chassis
- **Power supply** for motors

## 🔧 Raspberry Pi Software Setup

### Step 1: Install Raspberry Pi OS

1. **Download Raspberry Pi Imager:**
   ```bash
   # Or download from: https://www.raspberrypi.org/software/
   ```

2. **Flash OS to SD Card:**
   - Use Raspberry Pi Imager
   - Choose "Raspberry Pi OS (64-bit)" with desktop
   - Enable SSH and set username/password
   - Configure WiFi settings

3. **First Boot:**
   ```bash
   # SSH into Pi (find IP from router or use: sudo nmap -sn 192.168.1.0/24)
   ssh pi@192.168.1.XXX
   
   # Update system
   sudo apt update && sudo apt upgrade -y
   ```

### Step 2: Install Dependencies

```bash
# Install Python dependencies
sudo apt install -y python3-pip python3-opencv python3-flask

# Install Bluetooth libraries
sudo apt install -y bluetooth bluez libbluetooth-dev

# Install Python packages
pip3 install pybluez flask opencv-python requests

# Enable camera (if using Pi camera)
sudo raspi-config
# Navigate to: Interface Options → Camera → Enable

# Reboot
sudo reboot
```

### Step 3: Setup Bluetooth

```bash
# Enable Bluetooth service
sudo systemctl enable bluetooth
sudo systemctl start bluetooth

# Add user to bluetooth group
sudo usermod -a -G bluetooth pi

# Configure Bluetooth for serial communication
sudo nano /etc/systemd/system/dbus-org.bluez.service
```

**Edit the ExecStart line to:**
```
ExecStart=/usr/lib/bluetooth/bluetoothd --experimental
```

**Restart Bluetooth:**
```bash
sudo systemctl daemon-reload
sudo systemctl restart bluetooth
```

### Step 4: Deploy Server Code

```bash
# Create project directory
mkdir -p /home/pi/robot_server
cd /home/pi/robot_server

# Copy the raspberry_pi_server.py file here
# You can use SCP: scp raspberry_pi_server.py pi@192.168.1.XXX:/home/pi/robot_server/

# Make executable
chmod +x raspberry_pi_server.py

# Test dependencies
python3 -c "import flask, cv2, bluetooth; print('All dependencies OK')"
```

### Step 5: Configure Auto-Start Service

```bash
# Create systemd service
sudo nano /etc/systemd/system/robot-server.service
```

**Service file content:**
```ini
[Unit]
Description=Robot Command Server
After=network.target bluetooth.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/robot_server
ExecStart=/usr/bin/python3 /home/pi/robot_server/raspberry_pi_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start service:**
```bash
# Enable service
sudo systemctl enable robot-server.service

# Start service
sudo systemctl start robot-server.service

# Check status
sudo systemctl status robot-server.service

# View logs
sudo journalctl -u robot-server.service -f
```

## 🔵 ESP32 Arduino Code

Create this code for your ESP32:

```cpp
// ESP32 Robot Controller
// Receives commands via Bluetooth and controls motors

#include "BluetoothSerial.h"

BluetoothSerial SerialBT;

// Motor pins (adjust for your motor driver)
#define MOTOR_LEFT_FORWARD   2
#define MOTOR_LEFT_BACKWARD  4
#define MOTOR_RIGHT_FORWARD  16
#define MOTOR_RIGHT_BACKWARD 17
#define LED_PIN 18

String lastCommand = "S";

void setup() {
  Serial.begin(115200);
  SerialBT.begin("ESP32-Robot"); // Bluetooth device name
  
  // Configure motor pins
  pinMode(MOTOR_LEFT_FORWARD, OUTPUT);
  pinMode(MOTOR_LEFT_BACKWARD, OUTPUT);
  pinMode(MOTOR_RIGHT_FORWARD, OUTPUT);
  pinMode(MOTOR_RIGHT_BACKWARD, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  
  // Stop all motors initially
  stopMotors();
  
  Serial.println("ESP32 Robot ready for Bluetooth commands");
  digitalWrite(LED_PIN, HIGH); // Ready indicator
}

void loop() {
  if (SerialBT.available()) {
    String command = SerialBT.readStringUntil('\n');
    command.trim();
    command.toUpperCase();
    
    Serial.println("Received: " + command);
    
    executeCommand(command);
    lastCommand = command;
    
    // Send acknowledgment
    SerialBT.println("ACK:" + command);
  }
  
  delay(50);
}

void executeCommand(String cmd) {
  if (cmd == "F") {
    moveForward();
  } else if (cmd == "B") {
    moveBackward();
  } else if (cmd == "L") {
    turnLeft();
  } else if (cmd == "R") {
    turnRight();
  } else if (cmd == "S") {
    stopMotors();
  } else {
    Serial.println("Unknown command: " + cmd);
  }
}

void moveForward() {
  Serial.println("Moving Forward");
  digitalWrite(MOTOR_LEFT_FORWARD, HIGH);
  digitalWrite(MOTOR_LEFT_BACKWARD, LOW);
  digitalWrite(MOTOR_RIGHT_FORWARD, HIGH);
  digitalWrite(MOTOR_RIGHT_BACKWARD, LOW);
}

void moveBackward() {
  Serial.println("Moving Backward");
  digitalWrite(MOTOR_LEFT_FORWARD, LOW);
  digitalWrite(MOTOR_LEFT_BACKWARD, HIGH);
  digitalWrite(MOTOR_RIGHT_FORWARD, LOW);
  digitalWrite(MOTOR_RIGHT_BACKWARD, HIGH);
}

void turnLeft() {
  Serial.println("Turning Left");
  digitalWrite(MOTOR_LEFT_FORWARD, LOW);
  digitalWrite(MOTOR_LEFT_BACKWARD, HIGH);
  digitalWrite(MOTOR_RIGHT_FORWARD, HIGH);
  digitalWrite(MOTOR_RIGHT_BACKWARD, LOW);
}

void turnRight() {
  Serial.println("Turning Right");
  digitalWrite(MOTOR_LEFT_FORWARD, HIGH);
  digitalWrite(MOTOR_LEFT_BACKWARD, LOW);
  digitalWrite(MOTOR_RIGHT_FORWARD, LOW);
  digitalWrite(MOTOR_RIGHT_BACKWARD, HIGH);
}

void stopMotors() {
  Serial.println("Stopping Motors");
  digitalWrite(MOTOR_LEFT_FORWARD, LOW);
  digitalWrite(MOTOR_LEFT_BACKWARD, LOW);
  digitalWrite(MOTOR_RIGHT_FORWARD, LOW);
  digitalWrite(MOTOR_RIGHT_BACKWARD, LOW);
}
```

## 🔗 Pairing ESP32 with Raspberry Pi

### Method 1: Automatic Discovery
The server will automatically scan for ESP32 devices named "ESP32-Robot".

### Method 2: Manual Pairing

```bash
# On Raspberry Pi, scan for devices
sudo bluetoothctl
scan on
# Wait for ESP32-Robot to appear
pair XX:XX:XX:XX:XX:XX  # ESP32 MAC address
trust XX:XX:XX:XX:XX:XX
connect XX:XX:XX:XX:XX:XX
exit
```

### Method 3: Via API
```bash
# Get ESP32 MAC address first
curl http://192.168.1.XXX:5000/scan_bluetooth

# Connect to specific device
curl -X POST http://192.168.1.XXX:5000/connect_esp32 \
  -H "Content-Type: application/json" \
  -d '{"address": "XX:XX:XX:XX:XX:XX"}'
```

## 🌐 Server API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Server status and info |
| `/move` | POST | Send robot command |
| `/status` | GET | Detailed server status |
| `/scan_bluetooth` | GET | Scan for Bluetooth devices |
| `/connect_esp32` | POST | Connect to specific ESP32 |
| `/?action=stream` | GET | Camera stream |

### Example Commands

```bash
# Server status
curl http://192.168.1.XXX:5000/

# Send movement command
curl -X POST http://192.168.1.XXX:5000/move \
  -H "Content-Type: application/json" \
  -d '{"command": "F"}'

# Check detailed status
curl http://192.168.1.XXX:5000/status
```

## 🚀 Starting Everything

### 1. Start ESP32
- Upload Arduino code to ESP32
- Power on ESP32
- Verify "ESP32-Robot" appears in Bluetooth scan

### 2. Start Raspberry Pi Server
```bash
# Manual start
cd /home/pi/robot_server
python3 raspberry_pi_server.py

# Or via service
sudo systemctl start robot-server.service
```

### 3. Start Windows GUI
- Update robot IP to Raspberry Pi's IP
- Set video source to: `http://192.168.1.XXX:5000/?action=stream`
- Enable robot connection
- Start tracking

## 🐛 Troubleshooting

### Common Issues

**1. Bluetooth Connection Failed:**
```bash
# Restart Bluetooth
sudo systemctl restart bluetooth
sudo hciconfig hci0 down
sudo hciconfig hci0 up
```

**2. Camera Not Working:**
```bash
# Check camera
vcgencmd get_camera
# Should show: supported=1 detected=1

# Test camera
raspistill -o test.jpg
```

**3. Server Won't Start:**
```bash
# Check logs
sudo journalctl -u robot-server.service -f

# Check port
sudo netstat -tlnp | grep :5000
```

**4. ESP32 Not Found:**
```bash
# Manual Bluetooth scan
sudo bluetoothctl
scan on
devices
```

## 📊 Monitoring

### View Live Logs
```bash
# Server logs
tail -f /home/pi/robot_server.log

# System service logs
sudo journalctl -u robot-server.service -f
```

### Check Performance
```bash
# CPU usage
htop

# Memory usage
free -h

# Bluetooth status
sudo systemctl status bluetooth
```

## 🔧 Configuration Files

### Network Configuration
```bash
# Static IP (optional)
sudo nano /etc/dhcpcd.conf
# Add:
# interface wlan0
# static ip_address=192.168.1.100/24
# static routers=192.168.1.1
# static domain_name_servers=8.8.8.8
```

### Firewall Setup
```bash
# Allow HTTP port
sudo ufw allow 5000

# Enable firewall
sudo ufw enable
```

This setup creates a complete bridge system between your Windows person tracking application and the ESP32 robot via Raspberry Pi!