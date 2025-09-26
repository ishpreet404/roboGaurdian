# 🤖 Robot Guardian - AI Person Tracking Robot# Chirpy – AI Powered Child/Pet Monitoring Robo



A complete AI-powered person tracking robot system using Raspberry Pi, ESP32, and Windows PC.A comprehensive desktop GUI application for real-time person/animal detection and tracking, designed to prototype and test monitoring robot behavior before deploying to hardware. Uses computer vision to detect and follow children or pets, generating movement commands for autonomous robots.

## 🔔 Latest updates

### 🎤 NEW: Real-Time Audio Chat & Enhanced Voice Features
- **Audio Chat**: Record voice messages from your laptop microphone and send them directly to the Pi speaker for instant two-way communication
- **Multi-Engine Hindi TTS**: Enhanced text-to-speech system with gTTS for quality, pyttsx3 for offline use, and espeak as fallback
- **Smart Reminder System**: Schedule voice reminders with detailed logging and automatic delivery through the Pi speaker
- **Voice Assistant Dashboard**: New `/assistant` page in the frontend with comprehensive voice communication controls

### 🤖 Assistant & Communication Features  
- Dashboard now includes a **Chirpy assistant console** that lets you chat with the Pi voice agent directly from the browser. All requests are relayed over the new `/assistant/message` API.
- A **reminder scheduler with optional voice notes** is exposed at `/assistant/reminders`, allowing timed announcements that play automatically through the Pi speaker.
- Cross-origin requests are enabled on the Pi server so the Vite frontend can dispatch robot commands and assistant actions without extra proxies.
- Introduced **multi-mode behaviour**—including Care Companion, Watchdog, and Edumate—with synced alerts, dashboard controls to silence alarms, and automatic history summaries.

### 📋 Setup & Usage
- 📘 For fresh installs, follow the end-to-end [deployment & usage guide](./SETUP_AND_USAGE.md).
- 🛠️ Want a speaker-only Pi? Leave `PI_ASSISTANT_MODE` at the default `fallback` and skip the GitHub Models token—voice notes still play through the on-device TTS engine.
- 🎤 To use audio chat: Update Pi server with `wget -O pi_camera_server.py 'https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/pi_camera_server_fixed.py'`



## 📁 Project Structure## The Problem It Solves



```Chirpy – AI Powered Child/Pet Monitoring Robo directly addresses the flaws in current monitoring solutions:

roboGaurdian/

├── 🖥️  windows_ai_controller.py    # Windows AI control center (YOLO + GUI)📹 **Eliminates Blind Spots** – Unlike static CCTV cameras with fixed views, Chirpy follows children or pets in real-time using AI vision, ensuring they are always in frame.

├── 🥧  pi_camera_server.py         # Raspberry Pi camera server  

├── 🤖  esp32_robot_pi_compatible.ino # ESP32 robot firmware⏱️ **Proactive Safety** – Instead of only alerting after an incident, Chirpy actively prevents risks by maintaining a safe distance and avoiding obstacles.

├── 🔧  test_esp32.py               # ESP32 testing tool

├── 📥  download_pi_server.sh       # Pi setup script🎮 **Interactive Engagement** – Goes beyond passive monitoring by offering interactive play features like a laser pointer, music playback, and a treat dispenser, keeping children and pets entertained.

├── 🧠  yolov8n.pt                  # YOLO AI model (nano)

├── 🧠  yolov8m.pt                  # YOLO AI model (medium)📡 **Continuous Coverage** – Moves with the subject, providing complete monitoring across the home without gaps.

└── 📖  README.md                   # This file

```❤️ **Companionship & Well-being** – Acts as both a safety tool and a companion, reducing isolation for children and pets when parents or owners are busy.



## 🎯 System Overview## How It Makes Life Easier & Safer



**Three-tier architecture:**Parents get peace of mind knowing their child is always supervised, even while they focus on work or chores.

1. **Windows PC**: Runs YOLO AI model, GUI interface, sends robot commands

2. **Raspberry Pi**: Streams camera video, forwards commands via UART  Pet owners can monitor, interact, and even remotely reward their pets, reducing separation anxiety.

3. **ESP32**: Controls motors, handles obstacle avoidance, receives commands

Smart homes gain a new dimension of safety and engagement, combining surveillance, companionship, and AI-driven intelligence in one device.

## 🔌 Hardware Setup

## System Architecture

### **Connections:**

```### Robotics & Hardware

Pi GPIO14 (TX) ↔ ESP32 GPIO14 (RX2)  

Pi GPIO15 (RX) ↔ ESP32 GPIO15 (TX2)- **ESP32** – Handles motor control, ultrasonic sensors, and safe-distance obstacle detection for real-time collision prevention.

Pi GND ↔ ESP32 GND- **Raspberry Pi 4B** – Serves as the central hub for video feed management, AI processing coordination, and communication with the server.

```- **Ultrasonic Sensors** – Provide real-time obstacle detection and collision prevention, integrated with ESP32.

- **Motors & Wheels** – Enable autonomous mobility for following the subject while maintaining safe distances.

### **Components:**

- Raspberry Pi 4 with camera### Artificial Intelligence

- ESP32 development board  

- L298N motor driver- **YOLOv8-lite** – Lightweight AI vision model optimized for edge devices, used for subject detection and tracking.

- HC-SR04 ultrasonic sensor- **AI Processing Server (Laptop)** – Runs the full object detection pipeline, generates movement commands, and processes video feeds.

- Robot chassis with motors

- Windows PC for AI processing### Communication & Control



## 🚀 Quick Start- **UART (Serial Communication)** – Reliable serial link between Raspberry Pi and ESP32 for transmitting movement commands and sensor data.

- **Wi-Fi Networking** – Streams live video to parents/pet owners, enables remote monitoring, and supports over-the-air updates.

### **1. ESP32 Setup**

```bash### Software & Frameworks

# Upload esp32_robot_pi_compatible.ino using Arduino IDE

# Serial monitor at 115200 baud for debugging- **Python** – Core language for AI model integration, video processing, server-side logic, and GUI development.

```- **OpenCV** – Handles video frames, image processing, and computer vision tasks.

- **Arduino (ESP32 Programming)** – Firmware for hardware-level motor control, sensor reading, and low-level robotics logic.

### **2. Raspberry Pi Setup**  

```bash### IoT & Cloud (Future Roadmap)

# Download and run Pi server

wget -O pi_camera_server.py https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/pi_camera_server.py- **Cloud Storage** – For secure video feed archiving and AI model updates.

- **Mobile App Integration** – Remote control, real-time alerts, and live video streaming on smartphones.

# Install dependencies

sudo apt update## Features

sudo apt install python3-opencv python3-pip

pip3 install flask pyserial opencv-python psutil- **Multi-Source Input**: Live webcam, prerecorded video files (e.g., Raspberry Pi captures), or simulated video for testing without hardware.

- **Detection Backends**: 

# Enable UART  - Haar cascades (classic, fast but less accurate)

sudo raspi-config  - MobileNet SSD (DNN-based, balanced performance)

# → Interface Options → Serial Port → Enable  - YOLOv8n (modern, high accuracy, default)

- **Real-Time Visualization**: Live video feed with bounding boxes, target highlighting, FPS counter, and command overlays.

# Run server- **Command Synthesis**: Heuristic-based movement intent generation from subject position and size.

python3 pi_camera_server.py- **Robot Integration**: Optional HTTP-based command sending to robot endpoint (simulated by default).

```- **Statistics & Logging**: Real-time metrics, command history, and source details.

- **Extensible Architecture**: Easy to add new detectors, smoothing, or networking protocols.

### **3. Windows Setup**

```bash## Requirements

# Install Python dependencies  

pip install opencv-python ultralytics requests tkinter pillow numpy- **Python**: 3.8+

- **Dependencies**:

# Run AI controller  - `opencv-python`

python windows_ai_controller.py  - `Pillow`

```  - `numpy`

  - `requests` (for SSD model download)

## 🎮 Usage  - `ultralytics` (for YOLO backend; install separately if using YOLO)



1. **Start ESP32**: Upload firmware, check serial monitor## Installation

2. **Start Pi server**: Run `python3 pi_camera_server.py`  

3. **Start Windows AI**: Run `python windows_ai_controller.py`1. **Clone or Download**: Place `gui_tester.py` in your project directory (e.g., `d:\nexhack`).

4. **Connect**: Enter Pi IP address in Windows app

5. **Enable tracking**: Toggle "Auto Person Tracking"2. **Set Up Virtual Environment** (recommended):

6. **Watch**: Robot follows people automatically!   ```powershell

   python -m venv venv

## 🔧 Testing & Debugging   venv\Scripts\activate  # On Windows

   ```

### **Test ESP32 Communication:**

```bash3. **Install Core Dependencies**:

python test_esp32.py 192.168.1.2   ```powershell

```   pip install opencv-python Pillow numpy requests

   ```

### **Pi Web Interface:**

```4. **Install YOLO (Optional, but default)**:

http://PI_IP:5000   ```powershell

```   pip install ultralytics

   ```

### **Check Status:**   - This enables the YOLO backend. If skipped, fall back to Haar or SSD.

- **ESP32**: Serial monitor shows command reception

- **Pi**: Web interface shows UART status  5. **Download Models** (if using SSD):

- **Windows**: Log shows command flow   - Run the app and click "Download SSD Model" in Detector Settings, or manually download:

     - `MobileNetSSD_deploy.prototxt` (from repo or online)

## 📊 Features     - `MobileNetSSD_deploy.caffemodel` (23MB from Google Drive)



### **AI Capabilities:**## Usage

- ✅ YOLO person detection

- ✅ Real-time tracking with bounding boxes### Running the Application

- ✅ Automatic robot following

- ✅ Manual override controls```powershell

python gui_tester.py

### **Robot Features:**  ```

- ✅ Obstacle avoidance (always active)

- ✅ Motor control (forward, backward, left, right)Select an option:

- ✅ Status LEDs for direction and activity- **1. Run GUI with real camera**: Uses webcam for live tracking.

- ✅ UART communication with acknowledgments- **2. Run GUI with simulated video (no camera needed)**: No camera needed; generates synthetic subject movement.

- **3. Run simple test**: Checks dependencies and camera access.

### **System Features:**

- ✅ Low-latency video streaming### GUI Overview

- ✅ Web interface for manual control

- ✅ Comprehensive logging and diagnostics- **Left Panel**: Video display (640x480) with overlays.

- ✅ Robust error handling- **Right Panel**:

  - Video Source: Select webcam or browse video file.

## 🛠️ Troubleshooting  - Robot Connection: Toggle and set IP for command sending.

  - Current Command: Visual display of movement intent.

### **Robot Not Moving:**  - Command History: Timestamped log (last 100 entries).

1. Check ESP32 serial monitor for command reception  - Statistics: FPS, subjects detected, tracking status, source info.

2. Verify GPIO1/3 wiring Pi ↔ ESP32  - **Detector Settings**: Choose backend (Haar/SSD/YOLO), adjust confidence (0.1-0.9), download SSD model.

3. Test UART: `python test_esp32.py`

4. Check Pi server UART status at `/status`### Controls



### **No Video Stream:**- Click **"▶ Start Tracking"** to begin.

1. Check camera connection on Pi- Adjust **Confidence** slider for detection sensitivity (lower = more detections).

2. Verify Pi server running on port 5000- Switch **Backend** for different detection methods.

3. Test URL: `http://PI_IP:5000/video_feed`- View real-time overlays: Green box = target subject, yellow line = center, red lines = movement thresholds.



### **AI Not Detecting:**### Command Logic

1. Check YOLO model download in Windows app

2. Verify camera stream quality- **Lateral Movement**: Subject center offset > 100px from frame center → Left/Right.

3. Adjust confidence threshold in GUI- **Depth Movement**: Bounding box height < 150px → Forward (subject far); > 350px → Backward (too close); else Stop.

- Commands update only on change to avoid spam.

## 📚 Technical Details

### Testing with Video Files

### **Communication Protocol:**

- Windows ↔ Pi: HTTP API (JSON)- Record video on Raspberry Pi:

- Pi ↔ ESP32: UART 9600 baud (/dev/ttyS0)  ```bash

- Commands: F, B, L, R, S (Forward, Back, Left, Right, Stop)  libcamera-vid -t 10000 -o test.h264 --width 640 --height 480 --framerate 30

  ffmpeg -i test.h264 -c copy test.mp4

### **Performance:**  ```

- Video: 640x480 @ 30fps MJPEG- Transfer to Windows and select in GUI for repeatable testing.

- AI: YOLOv8n for speed, YOLOv8m for accuracy  

- Latency: <200ms end-to-end## Configuration

- Command rate: Max 10 Hz

- **Default Backend**: YOLO (yolov8n.pt) with confidence 0.1.

## 🔄 System Architecture- **Frame Skipping**: Set `self.yolo_frame_skip = 2` in code for slower machines.

- **Robot Commands**: Uncomment `threading.Thread(target=simulate_send, daemon=True).start()` in `send_command_to_robot` for actual HTTP posts.

```- **Performance Tuning**: Increase `self.ssd_frame_skip` or `self.yolo_frame_skip` to reduce CPU load.

┌─────────────────┐    HTTP API    ┌─────────────────┐    UART     ┌─────────────────┐

│   Windows PC    │◄──────────────►│  Raspberry Pi   │◄───────────►│     ESP32       │## Troubleshooting

│                 │                │                 │             │                 │

│ • YOLO AI       │                │ • Camera Stream │             │ • Motor Control │  - **Camera Not Working**: Ensure no other apps use the webcam; try `cv2.CAP_DSHOW` in code.

│ • GUI Interface │                │ • HTTP Server   │             │ • Obstacle Det. │- **YOLO Not Loading**: Run `pip install ultralytics`; check internet for model download.

│ • Person Track  │                │ • UART Bridge   │             │ • Status LEDs   │- **Low FPS**: Switch to Haar backend or increase frame skip.

└─────────────────┘                └─────────────────┘             └─────────────────┘- **No Detections**: Lower confidence slider; ensure good lighting.

```- **GUI Freezes**: Check queue size; reduce frame rate if needed.

- **Model Download Fails**: Manual download from Google Drive link in code.

## 📄 License

## Architecture Notes

MIT License - Feel free to use and modify for your projects!

- **Threading**: Capture/inference in background thread; UI updates every 33ms.

## 🤝 Contributing- **Queue Management**: Bounded queue (size 2) with drop-old policy for freshness.

- **Detection Pipeline**: Original frame for inference, resized for display.

Issues and pull requests welcome! This is an active robotics project.- **Safety**: Commands sent only if robot connected; no accidental hardware actuation.



---## Contributing



**🎯 Ready to track some humans? Let's go!** 🚀- Fork and submit PRs for new features (e.g., temporal smoothing, multi-subject tracking).
- Report issues with logs and system specs.

## License

MIT License - Free for personal and educational use.

---

For questions or enhancements, refer to the code comments or open an issue. Enjoy prototyping your Chirpy robot! 🤖