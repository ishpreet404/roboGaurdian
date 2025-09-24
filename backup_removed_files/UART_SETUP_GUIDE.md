# ESP32 UART Connection Setup Guide

## 🔌 **Hardware Connection**

### **ESP32 to Raspberry Pi UART Connection:**

```
ESP32          USB-to-Serial      Raspberry Pi
=====          =============      ============
GND     -----> GND         -----> GND (Pin 6)
TX (GPIO1) ---> RX          -----> GPIO 14 (Pin 8) TXD
RX (GPIO3) ---> TX          -----> GPIO 15 (Pin 10) RXD
5V      -----> VCC         -----> 5V (Pin 2)
```

### **Option 1: USB-to-Serial Adapter (Recommended)**

**Hardware needed:**
- USB-to-Serial adapter (CP2102, CH340, FTDI)
- Jumper wires

**Connections:**
```
ESP32 → USB-to-Serial Adapter → Raspberry Pi (USB)
```

**Advantages:**
- ✅ Easy to set up
- ✅ Reliable connection
- ✅ No pin conflicts
- ✅ Galvanic isolation

### **Option 2: Direct GPIO Connection**

**Pi GPIO Pins:**
```
Pin 6  (GND) ← ESP32 GND
Pin 8  (TXD) ← ESP32 RX (GPIO3)  
Pin 10 (RXD) ← ESP32 TX (GPIO1)
Pin 2  (5V)  ← ESP32 VIN
```

⚠️ **Note:** Disable Raspberry Pi serial console first!

## 🛠️ **Software Setup**

### **Step 1: Install Dependencies on Raspberry Pi**

```bash
# Update system
sudo apt update

# Install Python serial library
pip3 install pyserial flask opencv-python

# Install other tools
sudo apt install -y python3-dev python3-pip
```

### **Step 2: Configure Raspberry Pi Serial (if using GPIO)**

```bash
# Disable serial console (if using direct GPIO connection)
sudo raspi-config
# Navigate to: Interface Options → Serial Port
# "Login shell over serial?" → No
# "Serial port hardware enabled?" → Yes

# Reboot
sudo reboot
```

### **Step 3: Check Serial Ports**

```bash
# List available serial ports
ls /dev/tty*

# Common ESP32 ports:
# /dev/ttyUSB0  (USB-to-Serial adapter)
# /dev/ttyACM0  (Direct USB connection)
# /dev/serial0  (Pi GPIO serial)
```

### **Step 4: Test Serial Connection**

```bash
# Install screen for testing
sudo apt install screen

# Test connection (replace with your port)
screen /dev/ttyUSB0 115200

# You should see ESP32 debug output
# Press Ctrl+A then K to exit
```

## 🤖 **ESP32 Code Modifications**

Your existing ESP32 code is already perfect! It uses:
- ✅ `Serial.begin(115200)` - Matches Pi baud rate
- ✅ Single character commands (F, B, L, R, S)
- ✅ Serial debugging output

**No changes needed to your ESP32 code!**

## 📥 **Download Updated Server**

### **Get UART-enabled Raspberry Pi Server:**

```bash
# Download the updated server
wget https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/raspberry_pi_server.py

# Or copy from your Windows machine
scp raspberry_pi_server.py pi@10.214.108.26:/home/pi/
```

## 🚀 **Running the Server**

### **Start the UART Server:**

```bash
# Run the server
python3 raspberry_pi_server.py

# Expected output:
# 🤖 Robot Guardian - Raspberry Pi Command Server (UART Mode)
# 📋 Available serial ports:
#    /dev/ttyUSB0 - USB-to-Serial
# 🔍 Scanning for ESP32 on serial ports...
# 📞 Trying port: /dev/ttyUSB0
# ✅ Successfully connected to ESP32 via /dev/ttyUSB0
# 🎉 Successfully connected to ESP32 on /dev/ttyUSB0!
```

## 🔧 **Troubleshooting**

### **Permission Denied Error:**
```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER

# Logout and login again, or:
sudo reboot
```

### **Port Not Found:**
```bash
# Check USB devices
lsusb

# Check serial ports
dmesg | grep tty

# Try different ports
ls /dev/ttyUSB* /dev/ttyACM*
```

### **Connection Failed:**
```bash
# Check ESP32 power
# Check cable connections
# Try different baud rates: 9600, 115200
# Check ESP32 serial monitor for errors
```

## 🧪 **Testing Commands**

### **From Windows (same as before):**

```powershell
# Test connection
Invoke-RestMethod -Uri "http://10.214.108.26:5000/"

# Test command
Invoke-RestMethod -Uri "http://10.214.108.26:5000/move" -Method POST -Headers @{"Content-Type"="application/json"} -Body '{"command": "F"}'
```

### **Check Serial Ports via API:**

```bash
# Scan available ports
curl http://10.214.108.26:5000/scan_serial

# Manual connection
curl -X POST http://10.214.108.26:5000/connect_esp32 \
  -H "Content-Type: application/json" \
  -d '{"port": "/dev/ttyUSB0", "baud_rate": 115200}'
```

## ✅ **Advantages of UART vs Bluetooth**

- 🚀 **Faster**: Direct serial communication
- 🔒 **Reliable**: No pairing or connection drops  
- 🐛 **Easier Debug**: Direct access to ESP32 serial output
- ⚡ **Lower Latency**: No Bluetooth protocol overhead
- 🔧 **Simpler Setup**: No Bluetooth configuration needed
- 💰 **Cheaper**: No need for ESP32 Bluetooth module

Your robot will now have a much more reliable connection! 🎉