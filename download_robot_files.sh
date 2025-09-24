#!/bin/bash
# Quick Download Script for Raspberry Pi Robot Files
# Run this directly on your Raspberry Pi

echo "🤖 Downloading Robot Guardian Files..."
echo "====================================="

# Create project directory
mkdir -p ~/robot-guardian
cd ~/robot-guardian

# GitHub repository raw file base URL
GITHUB_RAW="https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main"

# Download main files
echo "📥 Downloading main server file..."
wget "$GITHUB_RAW/raspberry_pi_server_remote.py" -O raspberry_pi_server_remote.py

echo "📥 Downloading setup script..."
wget "$GITHUB_RAW/setup_raspberry_pi.sh" -O setup_raspberry_pi.sh

echo "📥 Downloading guides..."
wget "$GITHUB_RAW/REMOTE_CONTROL_GUIDE.md" -O REMOTE_CONTROL_GUIDE.md
wget "$GITHUB_RAW/UART_SETUP_GUIDE.md" -O UART_SETUP_GUIDE.md 2>/dev/null || echo "UART guide not found (optional)"
wget "$GITHUB_RAW/REMOTE_ACCESS_GUIDE.md" -O REMOTE_ACCESS_GUIDE.md 2>/dev/null || echo "Remote access guide not found (optional)"

# Make scripts executable
chmod +x raspberry_pi_server_remote.py
chmod +x setup_raspberry_pi.sh

echo ""
echo "✅ Download complete!"
echo "Files saved to: ~/robot-guardian/"
echo ""
echo "Next steps:"
echo "1. Run setup: ./setup_raspberry_pi.sh"
echo "2. Or start directly: python3 raspberry_pi_server_remote.py"
echo ""
echo "🎉 Ready to control your robot remotely!"