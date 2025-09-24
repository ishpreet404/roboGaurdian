#!/bin/bash
# 🚀 Robot Guardian System - Quick Download Commands
# ==================================================
# 
# Individual wget commands for downloading robot files
# Copy and paste these commands on your Raspberry Pi
#
# Author: Robot Guardian System
# Date: September 2025

echo "📥 Robot Guardian System - Download Commands"
echo "==========================================="
echo ""

# Create download directory
echo "🔧 Setup commands:"
echo "mkdir -p ~/robot_guardian && cd ~/robot_guardian"
echo ""

# Main Pi server file
echo "🥧 Pi Server (MAIN FILE - RUN THIS ON PI):"
echo "wget -O ultra_low_latency_pi_server.py https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/ultra_low_latency_pi_server.py"
echo ""

# Alternative Pi server
echo "🥧 Alternative Pi Server:"
echo "wget -O raspberry_pi_gpio_uart_server.py https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/raspberry_pi_gpio_uart_server.py"
echo ""

# ESP32 firmware
echo "🤖 ESP32 Firmware (UPLOAD TO ESP32):"
echo "wget -O esp32_robot_9600_baud.ino https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/esp32_robot_9600_baud.ino"
echo ""

# PC GUI application
echo "🖥️ PC GUI Application (RUN ON YOUR COMPUTER):"
echo "wget -O gui_tester.py https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/gui_tester.py"
echo ""

# Low latency client
echo "🚀 Low Latency Client (ALTERNATIVE FOR PC):"
echo "wget -O low_latency_client.py https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/low_latency_client.py"
echo ""

# Helper scripts
echo "⚙️ Helper Scripts:"
echo "wget -O start_pi_robot.sh https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/start_pi_robot.sh"
echo "wget -O setup_remote_access_fixed.sh https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/setup_remote_access_fixed.sh"
echo "chmod +x start_pi_robot.sh setup_remote_access_fixed.sh"
echo ""

# Documentation
echo "📖 Documentation:"
echo "wget -O WHAT_TO_RUN_WHERE.md https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/WHAT_TO_RUN_WHERE.md"
echo "wget -O DEPLOYMENT_GUIDE.md https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/DEPLOYMENT_GUIDE.md"
echo "wget -O LATENCY_OPTIMIZATION_GUIDE.md https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/LATENCY_OPTIMIZATION_GUIDE.md"
echo ""

# All-in-one command
echo "📦 Download Everything (ONE COMMAND):"
echo "----------------------------------------"
cat << 'EOF'
mkdir -p ~/robot_guardian && cd ~/robot_guardian && \
wget -O ultra_low_latency_pi_server.py https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/ultra_low_latency_pi_server.py && \
wget -O esp32_robot_9600_baud.ino https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/esp32_robot_9600_baud.ino && \
wget -O gui_tester.py https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/gui_tester.py && \
wget -O start_pi_robot.sh https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/start_pi_robot.sh && \
chmod +x start_pi_robot.sh && \
echo "✅ All files downloaded to ~/robot_guardian/"
EOF

echo ""
echo "🎯 Quick Start After Download:"
echo "=============================="
echo "1. On Pi: python3 ultra_low_latency_pi_server.py"
echo "2. On ESP32: Upload esp32_robot_9600_baud.ino"  
echo "3. On PC: python gui_tester.py"
echo ""
echo "🌐 Your Serveo URL is already configured in gui_tester.py!"
echo "   https://0eb12f6c4bd4153084c9ee30fac391ff.serveo.net"