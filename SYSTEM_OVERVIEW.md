# Robot Guardian System - Complete Setup Guide

## 🚀 System Overview

The Robot Guardian system creates an intelligent person-tracking robot using computer vision and wireless communication.

**System Architecture:**
```
┌─────────────────┐    HTTP     ┌─────────────────┐    Bluetooth    ┌─────────────────┐
│   Windows PC    │  Commands   │  Raspberry Pi   │   Commands      │     ESP32       │
│                 │ ─────────► │                 │ ─────────────► │     Robot       │
│ • Person Track  │            │ • Camera Stream │                │ • Motor Control │
│ • YOLO AI       │            │ • Command Relay │                │ • Movement      │
│ • GUI Control   │            │ • Web Server    │                │ • Bluetooth RX  │
└─────────────────┘            └─────────────────┘                └─────────────────┘
        ▲                               │
        │          Camera Stream        │
        └───────────────────────────────┘
```

## 📁 File Structure

```
d:\nexhack\
├── gui_tester.py              # Main Windows application
├── raspberry_pi_server.py     # Raspberry Pi server code
├── test_robot_communication.py # Communication test script
├── RASPBERRY_PI_SETUP.md      # Detailed Pi setup guide
├── README.md                   # Project documentation
└── requirements.txt            # Python dependencies
```

## 🛠️ Hardware Requirements

### Windows PC
- **OS:** Windows 10/11
- **RAM:** 8GB+ (16GB recommended for GPU)
- **GPU:** NVIDIA GPU with CUDA (optional, significant speedup)
- **Network:** WiFi connection to same network as Pi

### Raspberry Pi 4
- **Model:** Pi 4B (4GB+ RAM recommended)
- **Storage:** 32GB+ MicroSD card (Class 10)
- **Camera:** Pi Camera Module or USB webcam
- **Network:** WiFi connection
- **Bluetooth:** Built-in (Pi 3+ and newer)

### ESP32 Robot
- **MCU:** ESP32 DevKit (with Bluetooth)
- **Motors:** 2x DC geared motors
- **Driver:** L298N motor driver or similar
- **Power:** 7.4V-12V battery pack for motors
- **Chassis:** Robot chassis/frame

## ⚙️ Software Setup

### 1. Windows PC Setup

```bash
# Clone repository
git clone https://github.com/ishpreet404/roboGaurdian.git
cd roboGaurdian

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install opencv-python pillow numpy requests ultralytics tkinter

# For GPU acceleration (optional)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 2. Raspberry Pi Setup

Follow the detailed guide in `RASPBERRY_PI_SETUP.md`:

```bash
# Quick setup on Pi
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-opencv python3-flask bluetooth bluez libbluetooth-dev
pip3 install pybluez flask opencv-python requests

# Copy server file to Pi
scp raspberry_pi_server.py pi@[PI_IP]:/home/pi/

# Run server
python3 /home/pi/raspberry_pi_server.py
```

### 3. ESP32 Setup

Upload the Arduino code provided in `RASPBERRY_PI_SETUP.md` to your ESP32.

## 🚀 Quick Start Guide

### Step 1: Setup Raspberry Pi
1. Follow `RASPBERRY_PI_SETUP.md` instructions
2. Start the server: `python3 raspberry_pi_server.py`
3. Note the Pi's IP address (e.g., 192.168.1.100)

### Step 2: Setup ESP32
1. Upload Arduino code to ESP32
2. Power on ESP32 (should appear as "ESP32-Robot" in Bluetooth)
3. Pi server will auto-discover and connect

### Step 3: Configure Windows GUI
1. Run `python gui_tester.py`
2. Set Robot IP to Pi's IP address
3. Set Network Stream URL to: `http://192.168.1.100:5000/?action=stream`
4. Click "Test" to verify Pi connection
5. Enable "Connect to Robot" checkbox

### Step 4: Test Communication
```bash
# Test the complete chain
python test_robot_communication.py 192.168.1.100
```

### Step 5: Start Tracking
1. Select "Network Stream" as video source
2. Choose device (auto/cpu/cuda) for best performance
3. Adjust input size (640px for balanced, 832px for accuracy)
4. Click "▶ Start Tracking"

## 🎯 Configuration Options

### GUI Settings
- **Backend:** YOLO (recommended), SSD, or Haar
- **Device:** Auto (uses GPU if available), CPU, or CUDA
- **Input Size:** 320-1024px (higher = more accurate, slower)
- **Confidence:** 0.1-0.9 (lower = more detections)

### Performance Tuning
| Setting | Fast | Balanced | Accurate |
|---------|------|----------|----------|
| Input Size | 320px | 640px | 832px |
| Confidence | 0.3 | 0.1 | 0.05 |
| Device | CPU | Auto | CUDA |

## 📊 Monitoring & Debugging

### Real-time Monitoring
- **GUI Stats:** Shows FPS, device, processing info
- **Video Overlay:** Device status, commands, frame skip
- **Status Bar:** Connection status, error messages

### Log Files
```bash
# Raspberry Pi logs
tail -f /home/pi/robot_server.log
sudo journalctl -u robot-server.service -f

# Windows console output
# Check terminal where gui_tester.py is running
```

### API Endpoints
```bash
# Check Pi server status
curl http://192.168.1.100:5000/

# Send manual command
curl -X POST http://192.168.1.100:5000/move \
  -H "Content-Type: application/json" \
  -d '{"command": "F"}'

# Scan Bluetooth devices
curl http://192.168.1.100:5000/scan_bluetooth
```

## 🐛 Troubleshooting

### Common Issues

**1. "Cannot connect to Pi"**
- Check Pi IP address is correct
- Verify Pi server is running: `sudo systemctl status robot-server.service`
- Test with: `ping [PI_IP]`

**2. "ESP32 not connected"**
- Check ESP32 is powered and running
- Verify Bluetooth pairing on Pi: `sudo bluetoothctl devices`
- Check ESP32 code uploaded correctly

**3. "Camera stream not working"**
- Test Pi camera: `raspistill -o test.jpg`
- Check camera permissions: `sudo usermod -a -G video pi`
- Verify stream URL: `http://[PI_IP]:5000/?action=stream`

**4. "Low FPS/High latency"**
- Reduce input size (640px → 320px)
- Enable GPU acceleration
- Check network bandwidth
- Adjust confidence threshold

**5. "Commands not reaching robot"**
- Test communication chain with `test_robot_communication.py`
- Check ESP32 serial monitor for received commands
- Verify Bluetooth connection status

### Performance Optimization

**For CPU-only systems:**
- Use input size 320-640px
- Set confidence to 0.2-0.3
- Enable adaptive frame skipping

**For GPU systems:**
- Install CUDA-enabled PyTorch
- Use input size 640-832px
- Enable half precision
- Set confidence to 0.1

## 🔧 Advanced Configuration

### Static IP for Pi
```bash
# Edit network config
sudo nano /etc/dhcpcd.conf

# Add lines:
interface wlan0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
```

### Auto-start Services
```bash
# Enable Pi server auto-start
sudo systemctl enable robot-server.service

# Start on boot
sudo systemctl start robot-server.service
```

### Firewall Rules
```bash
# Allow HTTP port on Pi
sudo ufw allow 5000
sudo ufw enable
```

## 📈 System Performance

**Expected Performance:**
- **Detection Rate:** 15-30 FPS (depending on hardware)
- **Command Latency:** <100ms (local network)
- **Accuracy:** 90%+ person detection (YOLO)
- **Range:** WiFi range (typically 30-50m indoors)

**Hardware Recommendations:**
- **Budget:** Pi 4B 4GB + basic ESP32 + CPU inference
- **Performance:** Pi 4B 8GB + ESP32-CAM + GPU inference
- **Professional:** Pi 5 + ESP32-S3 + RTX GPU

## 🎓 Learning Resources

### Understanding the Code
- `gui_tester.py`: Main UI and computer vision pipeline
- `raspberry_pi_server.py`: HTTP server and Bluetooth communication
- `RASPBERRY_PI_SETUP.md`: Hardware setup and configuration

### Extending the System
- Add more robots (multiple ESP32s)
- Implement path planning
- Add obstacle avoidance sensors
- Create mobile app interface
- Add cloud logging/monitoring

This system provides a complete foundation for intelligent robot control using modern computer vision and wireless communication technologies!