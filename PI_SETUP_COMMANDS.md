# 🥧 Quick Pi Setup Commands

## One-liner wget (copy and paste on Pi):
```bash
wget -O pi_camera_server.py https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/pi_camera_server.py && python3 pi_camera_server.py
```

## Step-by-step setup:
```bash
# 1. Download server
wget -O pi_camera_server.py https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/pi_camera_server.py

# 2. Install dependencies
sudo apt update
sudo apt install python3-opencv python3-pip
pip3 install flask pyserial opencv-python psutil

# 3. Enable UART
sudo raspi-config
# → Interface Options → Serial Port → Enable

# 4. Run server
python3 pi_camera_server.py
```

## Alternative (using curl):
```bash
curl -o pi_camera_server.py https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/pi_camera_server.py
```

## Full automated setup script:
```bash
wget -O setup.sh https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/download_pi_server.sh
chmod +x setup.sh
./setup.sh
```