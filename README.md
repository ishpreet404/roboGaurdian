🤖 Chirpy – AI Powered Child & Pet Monitoring Robot

An AI-powered person & pet-tracking robot that uses computer vision, Raspberry Pi, ESP32, and a Windows PC to provide real-time safety, companionship, and entertainment.

Unlike static CCTV cameras that miss key moments, Chirpy actively follows your child or pet across the room, ensuring constant visibility and protection. With integrated voice communication, reminders, and interactive features, Chirpy is your Robot Guardian Companion.
✨ Features
🧠 AI & Tracking

    Real-time YOLOv8 person/pet detection and tracking
    Automatic robot following with obstacle avoidance
    Manual override controls via GUI
    Multi-source input: live webcam, prerecorded video, or simulated movement

🎤 Communication & Voice

    Two-way audio chat system (speak through Pi speaker)
    Multi-engine Text-to-Speech (TTS) (gTTS, pyttsx3, eSpeak)
    Smart Reminder system with voice playback
    Voice Assistant Dashboard (/assistant) for interactive commands

🤖 Robot Features

    ESP32-powered motor control (forward, back, left, right, stop)
    Safe-distance collision prevention with ultrasonic sensors
    Interactive play options: laser pointer, music playback, treat dispenser

💻 System Features

    Cross-platform Windows GUI with real-time visualization
    Web interface to control and test the Pi server
    Robust error handling, status logs, and system statistics
    Extensible modular architecture

🏗️ System Architecture

text

 ┌─────────────────┐    HTTP API    ┌─────────────────┐    UART     ┌─────────────────┐
 │   Windows PC    │◄──────────────►│  Raspberry Pi   │◄───────────►│     ESP32       │
 │ • YOLO AI       │                │ • Camera Stream │             │ • Motor Control │
 │ • GUI Interface │                │ • HTTP Server   │             │ • Obstacle Det. │
 │ • Person Track  │                │ • UART Bridge   │             │ • Status LEDs   │
 └─────────────────┘                └─────────────────┘             └─────────────────┘

    Windows PC → Runs AI detectors, GUI, and tracking logic
    Raspberry Pi → Streams camera, hosts Flask server, bridges commands
    ESP32 → Drives motors, uses ultrasonic sensors for collision detection

🔌 Hardware Components

    Raspberry Pi 4B + Camera
    ESP32 Development Board
    L298N Motor Driver
    HC-SR04 Ultrasonic Sensors
    Robot Chassis with Motors & Wheels
    Speaker for voice playback

⚙️ Software & Frameworks

    Python 3.8+ (OpenCV, Flask, Tkinter, NumPy, Pillow, Requests)
    YOLOv8-lite (Ultralytics for object detection)
    Arduino IDE (for ESP32 programming)
    UART & Wi-Fi networking (serial commands + video streaming)

🚀 Quick Start
1️⃣ Setup ESP32

bash

# Upload firmware
esp32_robot_pi_compatible.ino 

# Open Serial Monitor (115200 baud) to verify

2️⃣ Setup Raspberry Pi

bash

wget -O pi_camera_server.py https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/pi_camera_server.py
sudo apt update
sudo apt install python3-opencv python3-pip
pip3 install flask pyserial opencv-python psutil
python3 pi_camera_server.py

Enable UART:
sudo raspi-config → Interface Options → Serial Port → Enable
3️⃣ Setup Windows PC

bash

pip install opencv-python Pillow numpy requests ultralytics
python windows_ai_controller.py

4️⃣ Connect & Track

    Run ESP32 firmware
    Start Pi camera server (http://PI_IP:5000)
    Launch Windows AI controller and enter Pi IP
    Enable Auto Person Tracking
    Watch Chirpy follow your child/pet 🐾

🎮 GUI Overview

    Video Panel → Live tracking with bounding boxes & status overlays
    Controls Panel → Select detector (Haar / SSD / YOLO), set confidence
    Command Log → Real-time robot movement history
    Statistics → FPS, detection status, tracking info

📊 Key Benefits

✔️ Eliminates Blind Spots: Keeps subjects in frame, unlike static cameras
✔️ Proactive Safety: Maintains safe distances, avoids obstacles
✔️ Interactive Engagement: Entertainment features for pets/children
✔️ Continuous Coverage: Moves with subject across rooms
✔️ Companionship & Well-being: Acts as safety guard + companion
🛠️ Troubleshooting

    Robot not moving?
        Check ESP32 serial logs
        Verify Pi ↔ ESP32 wiring (TX14↔RX14 / RX15↔TX15 / GND↔GND)
        Run: python test_esp32.py PI_IP

    No video feed?
        Ensure Pi camera connected
        Check server (http://PI_IP:5000/video_feed)

    YOLO not detecting?
        Install: pip install ultralytics
        Lower confidence threshold
        Ensure lighting is sufficient

🔮 Roadmap

    📱 Mobile App Integration (notifications + remote control)
    ☁️ Cloud Storage (video archiving + AI model updates)
    👯 Multi-Subject Tracking (track multiple pets/children simultaneously)
    🧑‍🏫 Edumate Mode (interactive learning & storytelling)

📜 License

MIT License – Free to use and modify for personal & educational projects.
🤝 Contributing

We welcome PRs and issues!

    Add new detection models or play features
    Improve voice assistant
    Optimize for real-time edge computing
