#!/bin/bash
# wget_download_pi.sh - consolidated downloader for Raspberry Pi (run on Pi)
# Usage: bash wget_download_pi.sh
# This script downloads the core Raspberry Pi server files, helpers, and optional models.

set -euo pipefail

GITHUB_RAW="https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main"
OUT_DIR="pi_files"
mkdir -p "$OUT_DIR"

echo "Downloading robot Pi files into ./$OUT_DIR"

# Core Pi server files
wget -q --show-progress -O "$OUT_DIR/pi_camera_server.py" "$GITHUB_RAW/pi_camera_server.py"
wget -q --show-progress -O "$OUT_DIR/raspberry_pi_server.py" "$GITHUB_RAW/raspberry_pi_server.py" || true
wget -q --show-progress -O "$OUT_DIR/raspberry_pi_server_safe.py" "$GITHUB_RAW/raspberry_pi_server_safe.py" || true
wget -q --show-progress -O "$OUT_DIR/ultra_low_latency_pi_server.py" "$GITHUB_RAW/ultra_low_latency_pi_server.py" || true

# Setup and helper scripts
wget -q --show-progress -O "$OUT_DIR/setup_raspberry_pi.sh" "$GITHUB_RAW/setup_raspberry_pi.sh" || true
wget -q --show-progress -O "$OUT_DIR/setup_remote_access.sh" "$GITHUB_RAW/setup_remote_access.sh" || true
wget -q --show-progress -O "$OUT_DIR/setup_remote_access_fixed.sh" "$GITHUB_RAW/setup_remote_access_fixed.sh" || true

# Guides and docs
wget -q --show-progress -O "$OUT_DIR/PI_SETUP_COMMANDS.md" "$GITHUB_RAW/PI_SETUP_COMMANDS.md" || true
wget -q --show-progress -O "$OUT_DIR/REMOTE_CONTROL_GUIDE.md" "$GITHUB_RAW/REMOTE_CONTROL_GUIDE.md" || true
wget -q --show-progress -O "$OUT_DIR/REMOTE_ACCESS_GUIDE.md" "$GITHUB_RAW/REMOTE_ACCESS_GUIDE.md" || true
wget -q --show-progress -O "$OUT_DIR/UART_SETUP_GUIDE.md" "$GITHUB_RAW/UART_SETUP_GUIDE.md" || true

# ESP32 helper files
wget -q --show-progress -O "$OUT_DIR/esp32_robot_9600_baud.ino" "$GITHUB_RAW/esp32_robot_9600_baud.ino" || true
wget -q --show-progress -O "$OUT_DIR/ESP32_BT_CAR_Enhanced.ino" "$GITHUB_RAW/ESP32_BT_CAR_Enhanced.ino" || true
wget -q --show-progress -O "$OUT_DIR/esp32_connection_fixer.py" "$GITHUB_RAW/esp32_connection_fixer.py" || true

# Optional model files (large) - download only if user explicitly wants them
read -p "Download optional YOLO models? (y/N): " download_models
if [[ "$download_models" =~ ^[Yy]$ ]]; then
  mkdir -p "$OUT_DIR/models"
  echo "Downloading models (this may be large)..."
  wget -q --show-progress -O "$OUT_DIR/models/yolov8n.pt" "$GITHUB_RAW/yolov8n.pt" || true
  wget -q --show-progress -O "$OUT_DIR/models/yolov8m.pt" "$GITHUB_RAW/yolov8m.pt" || true
fi

# Post-download hints
cat <<EOF

Download complete. Files saved to ./$OUT_DIR

Next steps (on the Pi):
  1) Install dependencies:
     sudo apt update && sudo apt install -y python3-pip python3-opencv git
     pip3 install flask pyserial opencv-python psutil

  2) Enable serial/UART if needed:
     sudo raspi-config -> Interface Options -> Serial Port -> Enable

  3) Run the camera server:
     python3 $OUT_DIR/pi_camera_server.py

If you'd rather run a single one-liner, copy/paste this on your Pi:

  curl -fsSL https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/wget_download_pi.sh | bash -s --

EOF

exit 0
