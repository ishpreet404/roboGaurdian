#!/bin/bash
# Robot Guardian - Remote Setup Script
# Run this on your Raspberry Pi to set up remote robot control

set -e

echo "🤖 Robot Guardian - Remote Setup"
echo "================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if running on Raspberry Pi
print_step "Checking system..."
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    print_warning "This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system
print_step "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python dependencies
print_step "Installing Python dependencies..."
sudo apt install -y python3 python3-pip python3-dev python3-opencv python3-flask

print_step "Installing Python packages..."
pip3 install --user pyserial flask opencv-python

# Install additional tools
print_step "Installing additional tools..."
sudo apt install -y curl wget git screen

# Download ngrok for remote access
print_step "Setting up ngrok for remote access..."
if ! command -v ngrok &> /dev/null; then
    print_status "Downloading ngrok..."
    cd /tmp
    wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-arm.tgz
    tar xvf ngrok-v3-stable-linux-arm.tgz
    sudo mv ngrok /usr/local/bin/
    print_status "ngrok installed successfully"
else
    print_status "ngrok already installed"
fi

# Create project directory
print_step "Creating project directory..."
PROJECT_DIR="$HOME/robot-guardian"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Create startup script
print_step "Creating startup scripts..."
cat > start_robot_server.sh << 'EOF'
#!/bin/bash
# Robot Guardian Startup Script

echo "🤖 Starting Robot Guardian Server..."

# Check for serial ports
echo "Available serial ports:"
ls -la /dev/tty* 2>/dev/null | grep -E "(USB|ACM)" || echo "No USB serial ports found"

# Start the server
cd "$(dirname "$0")"
python3 raspberry_pi_server_remote.py
EOF

chmod +x start_robot_server.sh

# Create remote access script
cat > setup_remote_access.sh << 'EOF'
#!/bin/bash
# Remote Access Setup Script

echo "🌍 Setting up remote access..."

# Function to get local IP
get_local_ip() {
    hostname -I | cut -d' ' -f1
}

LOCAL_IP=$(get_local_ip)
echo "Local IP: $LOCAL_IP"

echo ""
echo "Choose remote access method:"
echo "1) ngrok (Recommended - secure tunnel)"
echo "2) Show manual port forwarding instructions"
echo "3) Both"

read -p "Enter choice (1-3): " choice

case $choice in
    1|3)
        if command -v ngrok &> /dev/null; then
            echo ""
            echo "🔒 Setting up ngrok tunnel..."
            echo "1. First, sign up at https://ngrok.com and get your auth token"
            echo "2. Run: ngrok config add-authtoken YOUR_TOKEN"
            echo "3. Then run: ngrok http 5000"
            echo ""
            echo "Starting ngrok tunnel (requires auth token)..."
            ngrok http 5000 --log=stdout &
            NGROK_PID=$!
            echo "ngrok started with PID: $NGROK_PID"
            echo "Check the output above for your public URL"
        else
            echo "ngrok not found. Please install it first."
        fi
        ;;
esac

case $choice in
    2|3)
        echo ""
        echo "📋 Manual Port Forwarding Setup:"
        echo "================================="
        echo "1. Access your router admin panel (usually 192.168.1.1 or 192.168.0.1)"
        echo "2. Find 'Port Forwarding' or 'Virtual Server' settings"
        echo "3. Add new rule:"
        echo "   - Service Name: Robot Guardian"
        echo "   - Internal IP: $LOCAL_IP"
        echo "   - Internal Port: 5000"
        echo "   - External Port: 5000 (or any port you prefer)"
        echo "   - Protocol: TCP"
        echo "4. Save and apply settings"
        echo "5. Find your public IP at https://whatismyipaddress.com"
        echo "6. Access robot at: http://YOUR_PUBLIC_IP:5000"
        echo ""
        echo "⚠️  SECURITY WARNING: Enable your router's firewall!"
        ;;
esac

echo ""
echo "✅ Remote access setup complete!"
echo "Local access: http://$LOCAL_IP:5000"
EOF

chmod +x setup_remote_access.sh

# Create systemd service for auto-start
print_step "Creating systemd service..."
sudo tee /etc/systemd/system/robot-guardian.service > /dev/null << EOF
[Unit]
Description=Robot Guardian Remote Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/bin/python3 $PROJECT_DIR/raspberry_pi_server_remote.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create configuration file
print_step "Creating configuration..."
cat > config.py << 'EOF'
# Robot Guardian Configuration

# Serial settings
ESP32_PORT = "/dev/ttyUSB0"  # Change if your ESP32 is on different port
ESP32_BAUD = 115200

# Server settings
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5000

# Security settings (optional)
ENABLE_AUTH = False
API_KEY = "robot-guardian-2025"

# Camera settings
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30
EOF

# Create hardware connection guide
cat > HARDWARE_SETUP.md << 'EOF'
# Hardware Connection Guide

## ESP32 to Raspberry Pi Connection

### Option 1: USB Connection (Easiest)
1. Connect ESP32 to Raspberry Pi via USB cable
2. ESP32 will appear as `/dev/ttyUSB0` or `/dev/ttyACM0`

### Option 2: GPIO Connection (Advanced)
```
ESP32        Raspberry Pi
-----        ------------
GND    <-->  GND (Pin 6)
RX2    <-->  GPIO14 (Pin 8)  - TX
TX2    <-->  GPIO15 (Pin 10) - RX
```

## Testing Connection
```bash
# List serial ports
ls -la /dev/tty*

# Test communication
screen /dev/ttyUSB0 115200
```

## Camera Setup
1. Enable camera: `sudo raspi-config` > Interface Options > Camera > Enable
2. Reboot: `sudo reboot`
3. Test camera: `raspistill -o test.jpg`
EOF

print_step "Installation complete!"
print_status "Project directory: $PROJECT_DIR"
print_status "Files created:"
echo "  - raspberry_pi_server_remote.py (Enhanced server with web interface)"
echo "  - start_robot_server.sh (Startup script)"
echo "  - setup_remote_access.sh (Remote access helper)"
echo "  - config.py (Configuration)"
echo "  - HARDWARE_SETUP.md (Hardware guide)"

echo ""
print_step "Next Steps:"
echo "1. Copy your robot server code to: $PROJECT_DIR/raspberry_pi_server_remote.py"
echo "2. Connect ESP32 to Raspberry Pi (see HARDWARE_SETUP.md)"
echo "3. Run: cd $PROJECT_DIR && ./start_robot_server.sh"
echo "4. For remote access: ./setup_remote_access.sh"
echo ""
echo "🎉 Setup complete! Your robot is ready for remote control!"

# Final system check
echo ""
print_step "System check:"
python3 -c "
try:
    import serial
    print('✅ pyserial: OK')
except ImportError:
    print('❌ pyserial: Missing')

try:
    import cv2
    print('✅ opencv: OK')  
except ImportError:
    print('❌ opencv: Missing')

try:
    import flask
    print('✅ flask: OK')
except ImportError:
    print('❌ flask: Missing')
"

echo ""
echo "🤖 Robot Guardian setup completed successfully!"
echo "Happy robot controlling! 🚀"
EOF