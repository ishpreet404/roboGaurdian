# Chirpy – AI Powered Child/Pet Monitoring Robo

A comprehensive desktop GUI application for real-time person/animal detection and tracking, designed to prototype and test monitoring robot behavior before deploying to hardware. Uses computer vision to detect and follow children or pets, generating movement commands for autonomous robots.

## The Problem It Solves

Chirpy – AI Powered Child/Pet Monitoring Robo directly addresses the flaws in current monitoring solutions:

📹 **Eliminates Blind Spots** – Unlike static CCTV cameras with fixed views, Chirpy follows children or pets in real-time using AI vision, ensuring they are always in frame.

⏱️ **Proactive Safety** – Instead of only alerting after an incident, Chirpy actively prevents risks by maintaining a safe distance and avoiding obstacles.

🎮 **Interactive Engagement** – Goes beyond passive monitoring by offering interactive play features like a laser pointer, music playback, and a treat dispenser, keeping children and pets entertained.

📡 **Continuous Coverage** – Moves with the subject, providing complete monitoring across the home without gaps.

❤️ **Companionship & Well-being** – Acts as both a safety tool and a companion, reducing isolation for children and pets when parents or owners are busy.

## How It Makes Life Easier & Safer

Parents get peace of mind knowing their child is always supervised, even while they focus on work or chores.

Pet owners can monitor, interact, and even remotely reward their pets, reducing separation anxiety.

Smart homes gain a new dimension of safety and engagement, combining surveillance, companionship, and AI-driven intelligence in one device.

## System Architecture

### Robotics & Hardware

- **ESP32** – Handles motor control, ultrasonic sensors, and safe-distance obstacle detection for real-time collision prevention.
- **Raspberry Pi 4B** – Serves as the central hub for video feed management, AI processing coordination, and communication with the server.
- **Ultrasonic Sensors** – Provide real-time obstacle detection and collision prevention, integrated with ESP32.
- **Motors & Wheels** – Enable autonomous mobility for following the subject while maintaining safe distances.

### Artificial Intelligence

- **YOLOv8-lite** – Lightweight AI vision model optimized for edge devices, used for subject detection and tracking.
- **AI Processing Server (Laptop)** – Runs the full object detection pipeline, generates movement commands, and processes video feeds.

### Communication & Control

- **UART (Serial Communication)** – Reliable serial link between Raspberry Pi and ESP32 for transmitting movement commands and sensor data.
- **Wi-Fi Networking** – Streams live video to parents/pet owners, enables remote monitoring, and supports over-the-air updates.

### Software & Frameworks

- **Python** – Core language for AI model integration, video processing, server-side logic, and GUI development.
- **OpenCV** – Handles video frames, image processing, and computer vision tasks.
- **Arduino (ESP32 Programming)** – Firmware for hardware-level motor control, sensor reading, and low-level robotics logic.

### IoT & Cloud (Future Roadmap)

- **Cloud Storage** – For secure video feed archiving and AI model updates.
- **Mobile App Integration** – Remote control, real-time alerts, and live video streaming on smartphones.

## Features

- **Multi-Source Input**: Live webcam, prerecorded video files (e.g., Raspberry Pi captures), or simulated video for testing without hardware.
- **Detection Backends**: 
  - Haar cascades (classic, fast but less accurate)
  - MobileNet SSD (DNN-based, balanced performance)
  - YOLOv8n (modern, high accuracy, default)
- **Real-Time Visualization**: Live video feed with bounding boxes, target highlighting, FPS counter, and command overlays.
- **Command Synthesis**: Heuristic-based movement intent generation from subject position and size.
- **Robot Integration**: Optional HTTP-based command sending to robot endpoint (simulated by default).
- **Statistics & Logging**: Real-time metrics, command history, and source details.
- **Extensible Architecture**: Easy to add new detectors, smoothing, or networking protocols.

## Requirements

- **Python**: 3.8+
- **Dependencies**:
  - `opencv-python`
  - `Pillow`
  - `numpy`
  - `requests` (for SSD model download)
  - `ultralytics` (for YOLO backend; install separately if using YOLO)

## Installation

1. **Clone or Download**: Place `gui_tester.py` in your project directory (e.g., `d:\nexhack`).

2. **Set Up Virtual Environment** (recommended):
   ```powershell
   python -m venv venv
   venv\Scripts\activate  # On Windows
   ```

3. **Install Core Dependencies**:
   ```powershell
   pip install opencv-python Pillow numpy requests
   ```

4. **Install YOLO (Optional, but default)**:
   ```powershell
   pip install ultralytics
   ```
   - This enables the YOLO backend. If skipped, fall back to Haar or SSD.

5. **Download Models** (if using SSD):
   - Run the app and click "Download SSD Model" in Detector Settings, or manually download:
     - `MobileNetSSD_deploy.prototxt` (from repo or online)
     - `MobileNetSSD_deploy.caffemodel` (23MB from Google Drive)

## Usage

### Running the Application

```powershell
python gui_tester.py
```

Select an option:
- **1. Run GUI with real camera**: Uses webcam for live tracking.
- **2. Run GUI with simulated video (no camera needed)**: No camera needed; generates synthetic subject movement.
- **3. Run simple test**: Checks dependencies and camera access.

### GUI Overview

- **Left Panel**: Video display (640x480) with overlays.
- **Right Panel**:
  - Video Source: Select webcam or browse video file.
  - Robot Connection: Toggle and set IP for command sending.
  - Current Command: Visual display of movement intent.
  - Command History: Timestamped log (last 100 entries).
  - Statistics: FPS, subjects detected, tracking status, source info.
  - **Detector Settings**: Choose backend (Haar/SSD/YOLO), adjust confidence (0.1-0.9), download SSD model.

### Controls

- Click **"▶ Start Tracking"** to begin.
- Adjust **Confidence** slider for detection sensitivity (lower = more detections).
- Switch **Backend** for different detection methods.
- View real-time overlays: Green box = target subject, yellow line = center, red lines = movement thresholds.

### Command Logic

- **Lateral Movement**: Subject center offset > 100px from frame center → Left/Right.
- **Depth Movement**: Bounding box height < 150px → Forward (subject far); > 350px → Backward (too close); else Stop.
- Commands update only on change to avoid spam.

### Testing with Video Files

- Record video on Raspberry Pi:
  ```bash
  libcamera-vid -t 10000 -o test.h264 --width 640 --height 480 --framerate 30
  ffmpeg -i test.h264 -c copy test.mp4
  ```
- Transfer to Windows and select in GUI for repeatable testing.

## Configuration

- **Default Backend**: YOLO (yolov8n.pt) with confidence 0.1.
- **Frame Skipping**: Set `self.yolo_frame_skip = 2` in code for slower machines.
- **Robot Commands**: Uncomment `threading.Thread(target=simulate_send, daemon=True).start()` in `send_command_to_robot` for actual HTTP posts.
- **Performance Tuning**: Increase `self.ssd_frame_skip` or `self.yolo_frame_skip` to reduce CPU load.

## Troubleshooting

- **Camera Not Working**: Ensure no other apps use the webcam; try `cv2.CAP_DSHOW` in code.
- **YOLO Not Loading**: Run `pip install ultralytics`; check internet for model download.
- **Low FPS**: Switch to Haar backend or increase frame skip.
- **No Detections**: Lower confidence slider; ensure good lighting.
- **GUI Freezes**: Check queue size; reduce frame rate if needed.
- **Model Download Fails**: Manual download from Google Drive link in code.

## Architecture Notes

- **Threading**: Capture/inference in background thread; UI updates every 33ms.
- **Queue Management**: Bounded queue (size 2) with drop-old policy for freshness.
- **Detection Pipeline**: Original frame for inference, resized for display.
- **Safety**: Commands sent only if robot connected; no accidental hardware actuation.

## Contributing

- Fork and submit PRs for new features (e.g., temporal smoothing, multi-subject tracking).
- Report issues with logs and system specs.

## License

MIT License - Free for personal and educational use.

---

For questions or enhancements, refer to the code comments or open an issue. Enjoy prototyping your Chirpy robot! 🤖