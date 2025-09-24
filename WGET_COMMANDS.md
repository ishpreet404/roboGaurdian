# 🤖 Robot Guardian - Quick Download Commands for Raspberry Pi

## Method 1: One-Line Download & Setup
```bash
# Run this single command on your Raspberry Pi to download and setup everything:
curl -sSL https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/download_robot_files.sh | bash
```

## Method 2: Manual wget Commands
```bash
# Create directory
mkdir -p ~/robot-guardian && cd ~/robot-guardian

# Download main server file
wget https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/raspberry_pi_server_remote.py

# Download setup script
wget https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/setup_raspberry_pi.sh

# Download guides
wget https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/REMOTE_CONTROL_GUIDE.md

# Make executable
chmod +x *.py *.sh
```

## Method 3: Download Specific Files Only
```bash
cd ~/robot-guardian

# Just the server (if you have dependencies installed)
wget https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/raspberry_pi_server_remote.py
python3 raspberry_pi_server_remote.py

# Just the setup script
wget https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/setup_raspberry_pi.sh
chmod +x setup_raspberry_pi.sh
./setup_raspberry_pi.sh
```

## Method 4: Using Git Clone
```bash
# Clone entire repository (includes all files)
git clone https://github.com/ishpreet404/roboGaurdian.git
cd roboGaurdian
chmod +x *.sh
./setup_raspberry_pi.sh
```

## Quick Start Command (Copy & Paste)
```bash
# 🚀 Complete setup in one command:
curl -sSL https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/download_robot_files.sh | bash && cd ~/robot-guardian && ./setup_raspberry_pi.sh
```

## Files You'll Get:
- `raspberry_pi_server_remote.py` - Main robot server with web interface
- `setup_raspberry_pi.sh` - Complete setup script for dependencies  
- `REMOTE_CONTROL_GUIDE.md` - Full setup and usage guide
- Configuration files and startup scripts

## After Download:
1. **Install dependencies**: `./setup_raspberry_pi.sh`
2. **Connect ESP32** to Pi via USB
3. **Start server**: `python3 raspberry_pi_server_remote.py`
4. **Access locally**: http://your-pi-ip:5000
5. **Setup remote access**: Follow REMOTE_CONTROL_GUIDE.md

## Troubleshooting Downloads:
```bash
# If wget fails, try curl:
curl -O https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/raspberry_pi_server_remote.py

# Check internet connection:
ping -c 3 github.com

# Check downloaded files:
ls -la ~/robot-guardian/
```

That's it! Your robot will be ready for remote control from anywhere in the world! 🌍🤖