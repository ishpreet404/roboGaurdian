#!/bin/bash
#
# Raspberry Pi Robot Server Installation Script
# =============================================
#
# This script installs all dependencies needed for the robot server
# Run with: bash install_pi_dependencies.sh
#

echo "🤖 Robot Guardian - Raspberry Pi Setup"
echo "======================================"
echo

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi"
    echo "   Continue anyway? (y/N)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "❌ Installation cancelled"
        exit 1
    fi
fi

echo "📋 Step 1: Updating system packages..."
sudo apt update
if [ $? -ne 0 ]; then
    echo "❌ Failed to update package list"
    exit 1
fi

echo "📦 Step 2: Installing system dependencies..."
sudo apt install -y \
    python3-pip \
    python3-dev \
    python3-opencv \
    bluetooth \
    bluez \
    libbluetooth-dev \
    build-essential

if [ $? -ne 0 ]; then
    echo "❌ Failed to install system packages"
    exit 1
fi

echo "🐍 Step 3: Installing Python packages..."

# Install basic packages first
pip3 install --user flask requests opencv-python

# Install pybluez (this often has issues, so we handle it specially)
echo "🔵 Installing Bluetooth support..."
pip3 install --user pybluez

if [ $? -ne 0 ]; then
    echo "⚠️  pybluez installation failed, trying alternative method..."
    
    # Try installing from source
    cd /tmp
    git clone https://github.com/pybluez/pybluez.git
    cd pybluez
    python3 setup.py build
    python3 setup.py install --user
    
    if [ $? -ne 0 ]; then
        echo "❌ Could not install pybluez"
        echo "   The server will run in HTTP-only mode"
        echo "   Bluetooth functionality will be disabled"
    else
        echo "✅ pybluez installed from source"
    fi
fi

echo "🔧 Step 4: Configuring Bluetooth..."
sudo systemctl enable bluetooth
sudo systemctl start bluetooth

# Add user to bluetooth group
sudo usermod -a -G bluetooth $USER

echo "📹 Step 5: Configuring camera..."
# Enable camera interface if not already enabled
if ! grep -q "^camera_auto_detect=1" /boot/config.txt; then
    echo "Enabling camera interface..."
    echo "camera_auto_detect=1" | sudo tee -a /boot/config.txt
fi

# Add user to video group for camera access
sudo usermod -a -G video $USER

echo "🔥 Step 6: Configuring firewall..."
# Install and configure UFW if not present
if ! command -v ufw &> /dev/null; then
    sudo apt install -y ufw
fi

# Allow the robot server port
sudo ufw allow 5000/tcp
sudo ufw --force enable

echo "📁 Step 7: Creating service directory..."
mkdir -p /home/$USER/robot_server
cd /home/$USER/robot_server

echo "🔧 Step 8: Testing installation..."
echo "Testing Python imports..."

python3 -c "
try:
    import flask
    print('✅ Flask: OK')
except ImportError:
    print('❌ Flask: FAILED')

try:
    import cv2
    print('✅ OpenCV: OK')
except ImportError:
    print('❌ OpenCV: FAILED')

try:
    import bluetooth
    print('✅ Bluetooth: OK')
except ImportError:
    print('⚠️  Bluetooth: FAILED (HTTP-only mode)')

try:
    import requests
    print('✅ Requests: OK')
except ImportError:
    print('❌ Requests: FAILED')
"

echo
echo "🎉 Installation Complete!"
echo "========================"
echo
echo "📋 Next Steps:"
echo "1. Copy raspberry_pi_server.py to /home/$USER/robot_server/"
echo "2. Run: cd /home/$USER/robot_server && python3 raspberry_pi_server.py"
echo "3. Test with: curl http://localhost:5000/"
echo
echo "📌 Important Notes:"
echo "• You may need to reboot for camera changes to take effect"
echo "• If Bluetooth failed, the server will run in HTTP-only mode"
echo "• Your Pi's IP address is: $(hostname -I | awk '{print $1}')"
echo

# Check if reboot is needed
if [[ -f /var/run/reboot-required ]]; then
    echo "⚠️  System reboot required for some changes to take effect"
    echo "   Reboot now? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        sudo reboot
    fi
fi