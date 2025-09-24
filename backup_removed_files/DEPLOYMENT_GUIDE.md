# 🤖 Robot Guardian System - Complete Deployment Guide

## System Overview

```
┌─────────────────┐    HTTP API     ┌──────────────────┐    GPIO UART    ┌─────────────────┐
│                 │  (WiFi/LAN)     │                  │   (9600 baud)   │                 │
│   GUI Computer  ├────────────────►│  Raspberry Pi 4  ├────────────────►│     ESP32       │
│  (Windows/Mac)  │                 │  + Camera        │                 │  + Motor Driver │
│                 │                 │                  │                 │                 │
└─────────────────┘                 └──────────────────┘                 └─────────────────┘
   • Person tracking                   • Flask HTTP server                  • L298N motor driver
   • YOLO detection                    • Camera streaming                    • Obstacle avoidance
   • Remote control                    • GPIO UART (TX/RX)                   • Robot movement
   • Auto following                    • Command processing                  • Status feedback
```

## 📋 Hardware Requirements

### Raspberry Pi 4 Setup
- **Model**: Raspberry Pi 4 (4GB RAM recommended)
- **OS**: Raspberry Pi OS (Bullseye or newer)
- **Camera**: Pi Camera Module V2 or USB webcam
- **GPIO**: Pins 8 (TX), 10 (RX), 6 (GND) for UART

### ESP32 Robot Setup  
- **Board**: ESP32 DevKit V1 or similar
- **Motor Driver**: L298N or similar H-bridge
- **Motors**: DC geared motors with wheels
- **Power**: 7.4V Li-Po battery for motors, USB for ESP32
- **Connections**: UART2 (GPIO16=RX, GPIO17=TX)

### Network Setup
- **WiFi**: Both Pi and GUI computer on same network
- **Ports**: Port 5000 for Pi HTTP server
- **IP**: Static IP recommended for Pi

## 🔧 Hardware Wiring

### Pi to ESP32 UART Connection
```
Raspberry Pi 4          ESP32 DevKit V1
┌─────────────────┐     ┌─────────────────┐
│ GPIO14 (Pin 8)  │────►│ GPIO16 (RX2)    │
│ GPIO15 (Pin 10) │◄────│ GPIO17 (TX2)    │  
│ GND (Pin 6)     │─────│ GND             │
└─────────────────┘     └─────────────────┘
```

### ESP32 to L298N Motor Driver
```
ESP32 DevKit V1         L298N Motor Driver
┌─────────────────┐     ┌─────────────────┐
│ GPIO12          │────►│ IN1             │
│ GPIO13          │────►│ IN2             │
│ GPIO14          │────►│ IN3             │
│ GPIO27          │────►│ IN4             │
│ GPIO25          │────►│ ENA             │
│ GPIO26          │────►│ ENB             │
│ VIN (5V)        │────►│ +5V             │
│ GND             │─────│ GND             │
└─────────────────┘     └─────────────────┘
```

## 💾 Software Installation

### 1. Raspberry Pi Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python dependencies
sudo apt install python3-pip python3-opencv python3-serial -y

# Install Python packages
pip3 install flask opencv-python pyserial ultralytics

# Enable camera (if using Pi camera)
sudo raspi-config
# Navigate to: Interface Options → Camera → Enable

# Enable UART
sudo raspi-config  
# Navigate to: Interface Options → Serial Port
# "Would you like a login shell accessible over serial?" → No
# "Would you like the serial port hardware enabled?" → Yes

# Download Pi server code
cd ~
wget https://raw.githubusercontent.com/your-repo/raspberry_pi_gpio_uart_server.py
chmod +x raspberry_pi_gpio_uart_server.py

# Test UART (optional)
sudo apt install minicom -y
minicom -D /dev/serial0 -b 9600
```

### 2. ESP32 Setup

1. **Install Arduino IDE**
2. **Add ESP32 Board Support**:
   - File → Preferences
   - Add URL: `https://dl.espressif.com/dl/package_esp32_index.json`
   - Tools → Board → Boards Manager → Search "ESP32" → Install

3. **Upload ESP32 Code**:
   - Open `esp32_robot_9600_baud.ino`
   - Select Board: "ESP32 Dev Module"  
   - Select Port: Your ESP32 COM port
   - Upload code

### 3. GUI Computer Setup

```bash
# Install Python dependencies (Windows/Mac/Linux)
pip install opencv-python ultralytics requests tkinter pillow numpy

# Download GUI files
# - gui_tester.py (modified for Pi integration)
# - system_integration_test.py (testing tool)

# Update Pi IP address in code
# Edit both files and change: pi_server_url = "http://192.168.1.XXX:5000"
```

## 🚀 Deployment Steps

### Step 1: Configure Pi IP Address

```bash
# On Raspberry Pi - Find IP address
ip addr show wlan0

# Or use static IP (recommended)
sudo nano /etc/dhcpcd.conf
# Add these lines:
interface wlan0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1
```

### Step 2: Update Code with Pi IP

```python
# In gui_tester.py and system_integration_test.py
pi_server_url = "http://192.168.1.100:5000"  # Update this IP
```

### Step 3: Start Pi Server

```bash
# On Raspberry Pi
cd ~
python3 raspberry_pi_gpio_uart_server.py

# Expected output:
# 🤖 Robot Guardian Server Starting...
# UART initialized on /dev/serial0 at 9600 baud
# Camera initialized successfully  
# * Running on all addresses (0.0.0.0)
# * Running on http://127.0.0.1:5000
# * Running on http://192.168.1.100:5000
```

### Step 4: Test ESP32 Connection

```bash
# On ESP32 Serial Monitor (115200 baud):
# Expected output:
# 🤖 ESP32 Robot Controller Started
# ================================
# UART: 9600 baud on Serial2
# Commands: F=Forward, B=Backward, L=Left, R=Right, S=Stop
# Motor Driver: L298N  
# Ready for commands...
```

### Step 5: Run GUI Application

```bash
# On GUI computer
python gui_tester.py

# Or run the integration tester
python system_integration_test.py
```

## 🧪 Testing Procedures

### 1. Basic Connectivity Test

```bash
# Test Pi HTTP server
curl http://192.168.1.100:5000/status

# Expected response:
{
  "status": "running",
  "uart_status": "connected", 
  "baud_rate": 9600,
  "camera_status": "active"
}
```

### 2. UART Communication Test

```bash
# On Pi terminal
echo "F" > /dev/serial0  # Should move robot forward
echo "S" > /dev/serial0  # Should stop robot
```

### 3. Camera Stream Test

```bash
# In web browser
http://192.168.1.100:5000/video_feed
# Should show live camera feed
```

### 4. Full System Test

1. **Start all components**:
   - Pi server running
   - ESP32 connected and powered
   - GUI application open

2. **Test manual controls**:
   - Click direction buttons in GUI
   - Verify robot movement
   - Check ESP32 serial output

3. **Test person tracking**:
   - Enable "Auto Person Tracking"
   - Stand in front of camera
   - Verify robot follows movement

## 🔍 Troubleshooting

### Pi Server Issues

```bash
# Check UART permissions
ls -l /dev/serial0
sudo usermod -a -G dialout pi

# Check GPIO permissions  
sudo usermod -a -G gpio pi

# Test camera
libcamera-hello -t 5000

# Check port availability
sudo netstat -tulpn | grep 5000
```

### ESP32 Issues

```bash
# Check UART wiring
# Verify GPIO16/17 are not used by other functions
# Test with multimeter for continuity

# Monitor ESP32 serial output
# Arduino IDE → Tools → Serial Monitor → 115200 baud

# Check motor driver power
# Ensure 7.4V battery connected to L298N
# Verify 5V supply to ESP32
```

### Network Issues

```bash
# Test network connectivity
ping 192.168.1.100

# Check firewall (Pi)
sudo ufw status
sudo ufw allow 5000

# Check Python requests
python -c "import requests; print(requests.get('http://192.168.1.100:5000/status').json())"
```

### YOLO Model Issues

```bash
# Download YOLO model manually
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

# Check CUDA/GPU (optional)
python -c "import torch; print(torch.cuda.is_available())"
```

## ⚡ Performance Optimization

### Pi Performance

```bash
# Increase GPU memory split
sudo raspi-config
# Advanced Options → Memory Split → 128

# Overclock (if needed)
sudo raspi-config  
# Advanced Options → Overclock → Modest

# Disable unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable cups
```

### Network Optimization

```python
# In Pi server code - adjust these values:
FRAME_WIDTH = 640        # Lower for better performance
FRAME_HEIGHT = 480       # Lower for better performance  
JPEG_QUALITY = 70        # Lower for smaller files
DETECTION_COOLDOWN = 0.3 # Adjust command frequency
```

### ESP32 Optimization

```cpp
// In ESP32 code - adjust these values:
const int motorSpeed = 200;      // Adjust robot speed
const int commandTimeout = 1000; // Safety timeout
const int pwmFreq = 1000;        // PWM frequency
```

## 📊 Monitoring & Logs

### Pi Server Logs

```bash
# View server logs
python3 raspberry_pi_gpio_uart_server.py > server.log 2>&1

# Monitor in real-time
tail -f server.log
```

### ESP32 Logs  

```bash
# Arduino IDE Serial Monitor
# Or use PlatformIO monitor
pio device monitor --port /dev/ttyUSB0 --baud 115200
```

### System Status Dashboard

Access Pi web interface:
- **Status**: http://192.168.1.100:5000/status
- **Camera**: http://192.168.1.100:5000/video_feed  
- **Web Control**: http://192.168.1.100:5000/

## 🛡️ Safety Features

### Automatic Safety Stops

1. **Command Timeout**: Robot stops if no command for 1 second
2. **Connection Loss**: Robot stops if Pi loses connection
3. **Emergency Stop**: Manual stop button always available
4. **Low Battery**: ESP32 monitors voltage (optional)

### Error Handling

1. **UART Errors**: Automatic retry with exponential backoff
2. **Camera Errors**: Graceful degradation to manual mode
3. **Network Errors**: Local operation continues
4. **YOLO Errors**: Fallback to basic tracking

## 📈 Future Enhancements

### Planned Features
- [ ] Voice control integration
- [ ] Mobile app interface  
- [ ] Multiple robot support
- [ ] Advanced obstacle avoidance
- [ ] GPS navigation (outdoor)
- [ ] Machine learning improvements
- [ ] Real-time performance metrics
- [ ] Remote internet access (ngrok alternatives)

### Hardware Upgrades
- [ ] Lidar sensor integration
- [ ] IMU for better navigation
- [ ] Servo camera gimbal
- [ ] Ultrasonic sensors
- [ ] LED status indicators
- [ ] Speaker for audio feedback

---

## 📞 Support & Documentation

- **GitHub Issues**: Report bugs and feature requests
- **Wiki**: Detailed technical documentation  
- **Examples**: Additional code samples
- **Community**: Discord/Telegram support groups

**System Version**: 2.0.0  
**Last Updated**: September 2025  
**Compatibility**: Pi 4, ESP32, YOLOv8

---

🤖 **Robot Guardian System** - Bringing AI vision to robotic movement! 🎯