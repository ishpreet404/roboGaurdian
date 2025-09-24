# Quick Fix Guide for Raspberry Pi Bluetooth Issue

## 🚨 **Problem:**
```
ModuleNotFoundError: No module named 'bluetooth'
```

## ✅ **Solution Options:**

### **Option 1: Install Missing Dependencies (Recommended)**

Run this on your Raspberry Pi:

```bash
# Method 1: Use the installation script
wget https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/install_pi_dependencies.sh
bash install_pi_dependencies.sh

# Method 2: Manual installation
sudo apt update
sudo apt install -y python3-pip bluetooth bluez libbluetooth-dev build-essential
pip3 install pybluez flask opencv-python requests

# Method 3: If pybluez fails, try from source
sudo apt install -y git
cd /tmp
git clone https://github.com/pybluez/pybluez.git
cd pybluez
python3 setup.py build
python3 setup.py install --user
```

### **Option 2: Use Safe Mode Server (Quick Test)**

Use the new `raspberry_pi_server_safe.py` file which works without Bluetooth:

```bash
# Copy the safe version to your Pi
scp raspberry_pi_server_safe.py pi@[PI_IP]:/home/pi/

# Run it (works without Bluetooth)
python3 raspberry_pi_server_safe.py
```

## 🔧 **Step-by-Step Fix:**

### **1. Check Current Status**
```bash
# Check Python version
python3 --version

# Check if Bluetooth is working
bluetoothctl --version
sudo systemctl status bluetooth

# Check installed packages
pip3 list | grep -i blue
```

### **2. Install System Dependencies**
```bash
# Update package list
sudo apt update

# Install Bluetooth libraries
sudo apt install -y bluetooth bluez libbluetooth-dev

# Install build tools
sudo apt install -y build-essential python3-dev
```

### **3. Install Python Bluetooth**
```bash
# Try pip first
pip3 install --user pybluez

# If that fails, try system package
sudo apt install -y python3-bluetooth

# If still failing, compile from source
cd /tmp
git clone https://github.com/pybluez/pybluez.git
cd pybluez
python3 setup.py build
sudo python3 setup.py install
```

### **4. Test Installation**
```bash
python3 -c "
try:
    import bluetooth
    print('✅ Bluetooth module loaded successfully')
    print('Version:', bluetooth.__version__ if hasattr(bluetooth, '__version__') else 'Unknown')
except ImportError as e:
    print('❌ Failed to import bluetooth:', e)
"
```

### **5. Run Server**
```bash
# With Bluetooth support
python3 raspberry_pi_server.py

# Or safe mode (without Bluetooth)
python3 raspberry_pi_server_safe.py
```

## 🔍 **Troubleshooting:**

### **If pybluez still won't install:**
```bash
# Check Python headers
sudo apt install -y python3-dev python3-pip

# Check Bluetooth headers
sudo apt install -y libbluetooth-dev

# Try different installation method
sudo pip3 install pybluez
```

### **If Bluetooth service issues:**
```bash
# Restart Bluetooth service
sudo systemctl restart bluetooth

# Check Bluetooth adapter
hciconfig
sudo hciconfig hci0 up

# Check for conflicts
sudo systemctl stop bluetooth
sudo systemctl start bluetooth
```

### **Alternative: Skip Bluetooth for now**

The safe server version allows you to:
- ✅ Test HTTP communication from Windows
- ✅ Stream camera video
- ✅ Receive movement commands
- ⚠️ Commands logged but not sent to ESP32

This lets you test the Windows ↔ Pi communication while fixing Bluetooth separately.

## 🚀 **Quick Start Without Bluetooth:**

1. **Copy safe server to Pi:**
   ```bash
   scp raspberry_pi_server_safe.py pi@192.168.1.100:/home/pi/
   ```

2. **Run safe server:**
   ```bash
   ssh pi@192.168.1.100
   cd /home/pi
   python3 raspberry_pi_server_safe.py
   ```

3. **Test from Windows:**
   ```bash
   # Test connection
   curl http://192.168.1.100:5000/

   # Test command
   curl -X POST http://192.168.1.100:5000/move -H "Content-Type: application/json" -d '{"command": "F"}'
   ```

4. **Update Windows GUI:**
   - Set Robot IP: `192.168.1.100`
   - Set Stream URL: `http://192.168.1.100:5000/?action=stream`
   - Test connection and start tracking

This approach gets your system working immediately while you resolve the Bluetooth dependency separately!