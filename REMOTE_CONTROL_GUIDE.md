# 🤖 Robot Guardian - Remote Control Setup Guide

## Quick Start (5 Minutes)

### Step 1: Copy Files to Raspberry Pi
```bash
# On your computer, copy files to Pi
scp raspberry_pi_server_remote.py pi@your-pi-ip:~/
scp setup_raspberry_pi.sh pi@your-pi-ip:~/

# SSH into Raspberry Pi
ssh pi@your-pi-ip
```

### Step 2: Run Setup Script
```bash
# Make executable and run
chmod +x setup_raspberry_pi.sh
./setup_raspberry_pi.sh
```

### Step 3: Connect Hardware
- **USB Method**: Connect ESP32 to Pi via USB cable
- **GPIO Method**: Wire ESP32 TX/RX to Pi GPIO pins (see HARDWARE_SETUP.md)

### Step 4: Start Robot Server
```bash
cd robot-guardian
./start_robot_server.sh
```

### Step 5: Set Up Remote Access
```bash
# In another terminal
./setup_remote_access.sh
```

---

## 🌍 Remote Access Methods

### Method 1: ngrok (Recommended - Secure & Easy)

#### Install ngrok:
```bash
# Already done by setup script
ngrok --version
```

#### Get ngrok auth token:
1. Go to https://ngrok.com and sign up (free)
2. Copy your auth token from dashboard
3. Configure ngrok:
```bash
ngrok config add-authtoken YOUR_TOKEN_HERE
```

#### Start tunnel:
```bash
# Start robot server first
cd robot-guardian
python3 raspberry_pi_server_remote.py &

# In another terminal, create tunnel
ngrok http 5000
```

#### Access remotely:
- ngrok will show you a URL like: `https://abc123.ngrok.io`
- Share this URL to control your robot from anywhere! 🌍

---

### Method 2: Port Forwarding (Requires Router Access)

#### Router Setup:
1. Find your Pi's IP: `hostname -I`
2. Access router admin (usually 192.168.1.1)
3. Find "Port Forwarding" settings
4. Add rule:
   - **Internal IP**: Your Pi's IP
   - **Internal Port**: 5000
   - **External Port**: 5000
   - **Protocol**: TCP

#### Find Public IP:
- Visit: https://whatismyipaddress.com
- Your robot URL: `http://YOUR_PUBLIC_IP:5000`

⚠️ **Security**: Enable router firewall and consider changing default port

---

### Method 3: VPN Access (Most Secure)

#### Set up VPN server on Pi:
```bash
# Install PiVPN
curl -L https://install.pivpn.io | bash
```

#### Create client profile:
```bash
pivpn add
```

#### Access:
1. Connect to VPN from anywhere
2. Access robot at Pi's local IP: `http://192.168.1.x:5000`

---

## 📱 Web Interface Features

### Control Methods:
- **Web Browser**: Full-featured interface with video stream
- **Mobile**: Touch controls optimized for phones
- **Keyboard**: WASD or arrow keys + spacebar to stop

### Interface Elements:
- 📹 **Live Video Stream**: See what your robot sees
- 🎮 **Touch Controls**: Forward/Back/Left/Right/Stop buttons
- 📊 **Status Panel**: Connection status, command history
- ⌨️ **Keyboard Support**: Desktop control with keys

### Commands:
- **F**: Forward
- **B**: Backward  
- **L**: Left
- **R**: Right
- **S**: Stop

---

## 🔧 Troubleshooting

### Common Issues:

#### "No ESP32 devices found"
```bash
# Check serial ports
ls -la /dev/tty* | grep -E "(USB|ACM)"

# Test connection manually
screen /dev/ttyUSB0 115200
# Type commands: F, B, L, R, S
```

#### "Camera not available"
```bash
# Enable camera
sudo raspi-config
# Interface Options > Camera > Enable > Reboot

# Test camera
raspistill -o test.jpg
```

#### "Connection refused"
```bash
# Check if server is running
ps aux | grep python

# Check port usage
sudo netstat -tlnp | grep 5000

# Start server manually
cd robot-guardian
python3 raspberry_pi_server_remote.py
```

#### "Can't access remotely"
```bash
# Check firewall
sudo ufw status

# Allow port through firewall
sudo ufw allow 5000

# Check ngrok status
curl http://localhost:4040/api/tunnels
```

---

## 🚀 Advanced Features

### Auto-Start on Boot:
```bash
# Enable service
sudo systemctl enable robot-guardian
sudo systemctl start robot-guardian

# Check status
sudo systemctl status robot-guardian
```

### Custom Configuration:
Edit `config.py` to change:
- Serial port settings
- Camera resolution
- Server port
- Security settings

### API Access:
```bash
# Send commands via API
curl -X POST http://your-robot-url/move \
  -H "Content-Type: application/json" \
  -d '{"command": "F"}'

# Get status
curl http://your-robot-url/status
```

---

## 🔒 Security Best Practices

1. **Use ngrok**: Most secure option with HTTPS
2. **Change default ports**: Avoid port 5000 for public access
3. **Enable authentication**: Set `ENABLE_AUTH=true` in config
4. **Use VPN**: For maximum security
5. **Monitor access**: Check command history regularly

---

## 📞 Support

### Server URLs:
- **Local**: http://localhost:5000
- **Network**: http://YOUR_PI_IP:5000  
- **Remote**: Your ngrok URL or public IP

### Logs:
```bash
# Server logs
tail -f ~/robot_server.log

# System service logs
sudo journalctl -u robot-guardian -f
```

### Test Commands:
```bash
# Test ESP32 connection
echo "F" > /dev/ttyUSB0

# Test camera
python3 -c "import cv2; print(cv2.VideoCapture(0).isOpened())"

# Test web server
curl http://localhost:5000/status
```

---

## 🎉 You're Ready!

Your robot is now accessible from anywhere in the world! 🌍

- **Web Interface**: Full control with video stream
- **Mobile Friendly**: Works on phones and tablets  
- **Secure Access**: Multiple security options
- **Real-time Video**: See what your robot sees
- **Command History**: Track all movements

**Happy robot controlling!** 🤖🚀