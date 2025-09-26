#!/bin/bash
# wget_pi_multimode.sh - Fetch the latest Raspberry Pi server + voice assistant bundle via wget
# Usage: bash wget_pi_multimode.sh [target-directory]
# Run this on the Raspberry Pi. It will create a folder (default: roboguardian-pi)
# containing the Flask server, voice assistant service, and helper assets.

set -euo pipefail

TARGET_DIR=${1:-roboguardian-pi}
BASE_URL="https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main"

mkdir -p "$TARGET_DIR/assistant"
mkdir -p "$TARGET_DIR/docs"

printf "\n📥 Downloading Robot Guardian Pi bundle into %s\n\n" "$TARGET_DIR"

wget -q --show-progress -O "$TARGET_DIR/pi_camera_server_fixed.py" \
  "$BASE_URL/pi_camera_server_fixed.py"

wget -q --show-progress -O "$TARGET_DIR/pi_camera_server.py" \
  "$BASE_URL/pi_camera_server.py"

wget -q --show-progress -O "$TARGET_DIR/assistant/pi_voice_chatbot_single.py" \
  "$BASE_URL/raspi-chatbot/pi_voice_chatbot_single.py"

wget -q --show-progress -O "$TARGET_DIR/requirements.txt" \
  "$BASE_URL/requirements.txt"

wget -q --show-progress -O "$TARGET_DIR/docs/SETUP_AND_USAGE.md" \
  "$BASE_URL/SETUP_AND_USAGE.md" || true

cat > "$TARGET_DIR/README_PI.md" <<'EOF'
# Robot Guardian – Raspberry Pi Bundle

## Quick start
1. Create and activate a virtual environment (recommended):
   ```bash
   cd roboguardian-pi
   python3 -m venv .venv
   source .venv/bin/activate
  pip install --upgrade pip
  sudo apt install -y python3-psutil python3-pyserial python3-opencv python3-flask python3-flask-cors ffmpeg mpv
   ```
2. Export your GitHub Models token for the voice assistant:
   ```bash
   export GITHUB_TOKEN="your_github_models_token"
   ```
3. Launch the Pi server:
   ```bash
  python3 pi_camera_server_fixed.py
   ```

## Files
- `pi_camera_server_fixed.py` – Primary Flask video/command server with voice-note queue
- `pi_camera_server.py` – Legacy server kept for compatibility
- `assistant/pi_voice_chatbot_single.py` – Chirpy voice assistant service
- `requirements.txt` – Shared dependency list
- `docs/` – Reference guides (SETUP_AND_USAGE, etc.) pulled from the repository

For optional YOLO model downloads, run `wget_download_pi.sh` or use the full repo clone.
EOF

cat <<'EOF'

✅ Download complete!

Next steps (on the Pi):
  cd "$TARGET_DIR"
  python3 -m venv .venv
  source .venv/bin/activate
  pip install --upgrade pip
  sudo apt install -y python3-psutil python3-pyserial python3-opencv python3-flask python3-flask-cors ffmpeg mpv
  export GITHUB_TOKEN="<github_token_with_models_access>"
  python3 pi_camera_server_fixed.py

Need YOLO weights or legacy scripts? Clone the repo for the full toolbox:
  git clone https://github.com/ishpreet404/roboGaurdian.git
EOF
