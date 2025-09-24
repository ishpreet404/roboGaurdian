# 🎯 QUICK START - What to Run Where

## 📍 **EXACTLY WHAT FILES TO RUN**

### 🖥️ **ON YOUR PC (Windows)**

**File:** `gui_tester.py` ⭐ **MAIN APPLICATION**

```bash
# Install dependencies first:
pip install opencv-python ultralytics requests tkinter pillow numpy

# Then run:
python gui_tester.py
```

**What it does:**
- 🧠 Runs YOLO AI model for person detection  
- 📺 Shows Pi camera stream in GUI window
- 🎮 Sends movement commands to robot
- 🎯 Automatically follows detected person

---

### 🥧 **ON RASPBERRY PI**

**File:** `ultra_low_latency_pi_server.py` ⭐ **MAIN PI SERVER**

```bash
# Method 1: Easy startup (recommended)
chmod +x start_pi_robot.sh
./start_pi_robot.sh

# Method 2: Manual startup
python3 ultra_low_latency_pi_server.py
```

**What it does:**
- 📹 Captures camera video and streams it
- 🌐 Creates HTTP API server on port 5000
- 📡 Sends commands to ESP32 via UART
- ⚡ Optimized for low latency streaming

---

### 🤖 **ON ESP32**

**File:** `esp32_robot_9600_baud.ino` ⭐ **ROBOT FIRMWARE**

```bash
# Upload via Arduino IDE:
1. Open Arduino IDE
2. Load esp32_robot_9600_baud.ino
3. Select "ESP32 Dev Module" board
4. Upload to ESP32
```

**What it does:**
- 🚗 Controls robot motors (forward, back, left, right, stop)
- 📶 Receives commands via UART at 9600 baud  
- 💡 Status LED indicates connection/movement
- 🔒 Safety timeout stops robot if no commands

---

## 🚀 **STARTUP SEQUENCE**

### **1. ESP32 First** 🤖
- Power on ESP32
- Check Serial Monitor shows: "Ready for commands..."

### **2. Pi Server** 🥧  
- Run: `./start_pi_robot.sh` or `python3 ultra_low_latency_pi_server.py`
- Create tunnel (Serveo/Cloudflare) when prompted
- Note the tunnel URL (e.g., `https://abc123.serveo.net`)

### **3. PC GUI** 🖥️
- Your Serveo URL is already configured in `gui_tester.py`
- Run: `python gui_tester.py`
- Click "🔍 Test" to verify connection
- Click "Start Tracking" to begin

---

## ✅ **VERIFICATION CHECKLIST**

### **ESP32 Working:**
- [ ] Serial Monitor shows "🤖 ESP32 Robot Controller Started"
- [ ] LED blinks every second (heartbeat)
- [ ] Responds to manual commands in Serial Monitor

### **Pi Server Working:**  
- [ ] Terminal shows "✅ Camera initialized" 
- [ ] Can access `http://PI_IP:5000` in browser
- [ ] Camera stream visible at `/video_feed`
- [ ] Tunnel URL accessible from internet

### **PC GUI Working:**
- [ ] Stream appears in GUI window
- [ ] "🔍 Test" button shows "✅ Pi Connected"
- [ ] Manual arrow buttons move robot
- [ ] Person detection shows green boxes

### **Full System Working:**
- [ ] Person appears in camera → Green box drawn around them
- [ ] Robot automatically moves to follow person
- [ ] Commands visible in ESP32 Serial Monitor
- [ ] Low latency (under 1 second response time)

---

## 📁 **FILE SUMMARY**

| Location | File | Status |
|----------|------|--------|
| **PC** | `gui_tester.py` | ⭐ **RUN THIS** - AI + Control GUI |
| **Pi** | `ultra_low_latency_pi_server.py` | ⭐ **RUN THIS** - Camera + API Server |
| **Pi** | `start_pi_robot.sh` | 🔧 Helper script (optional) |
| **ESP32** | `esp32_robot_9600_baud.ino` | ⭐ **UPLOAD THIS** - Robot firmware |
| **PC** | `low_latency_client.py` | 🧪 Alternative test client |
| **Reference** | `REMOTE_AI_DEPLOYMENT.md` | 📖 Detailed setup guide |

---

## 🎮 **HOW TO USE**

1. **Start everything** (ESP32 → Pi → PC GUI)
2. **Check connections** (Test buttons in GUI)
3. **Enable tracking** ("Track Person" checkbox)
4. **Stand in front of Pi camera** 
5. **Watch robot follow you!** 🤖

**The AI runs on your PC, camera on Pi, robot controlled by ESP32!**

---

## 🔧 **QUICK TROUBLESHOOTING**

**No video in GUI?** 
- Check Pi server running: `ps aux | grep python3`
- Test stream in browser: `https://your-tunnel-url/video_feed`

**Robot not moving?**
- Check ESP32 Serial Monitor for incoming commands
- Test UART on Pi: `echo "F" > /dev/serial0`

**High latency?**
- Try Cloudflare tunnel instead of Serveo
- Lower video quality in Pi server settings

**Connection failed?**
- Click "🔄 Sync URLs" in GUI
- Use "🚀 Use Serveo Tunnel" button for auto-config

---

## 🎯 **YOU'RE READY!**

**Just run these 3 main files and you'll have a working AI robot!** 

1. `esp32_robot_9600_baud.ino` → ESP32 ⚡
2. `ultra_low_latency_pi_server.py` → Pi 🥧  
3. `gui_tester.py` → PC 🖥️

**AI person tracking with remote robot control over the internet!** 🚀🤖🎯