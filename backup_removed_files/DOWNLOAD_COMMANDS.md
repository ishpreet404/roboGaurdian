# Download Commands for Raspberry Pi Files (Updated with BT_CAR_32)

## 📥 **Download Updated Server with Hardcoded MAC**

```bash
# Download the updated Raspberry Pi server (with BT_CAR_32 MAC: 1C:69:20:A4:30:2A)
wget https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/raspberry_pi_server.py

# Make it executable
chmod +x raspberry_pi_server.py
```

## 🔧 **Download Bluetooth Diagnostic Tools**

```bash
# Download Bluetooth diagnostic script
wget https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/bt_diagnostic.py

# Download Bluetooth fix script
wget https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/bt_fix.sh

# Make them executable
chmod +x bt_diagnostic.py bt_fix.sh

# Run diagnostic first
python3 bt_diagnostic.py

# Or run quick fix
bash bt_fix.sh
```

## 🚀 **Troubleshooting Steps for "No ESP32 devices found"**

### **Step 1: Run Quick Fix**
```bash
wget https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/bt_fix.sh
bash bt_fix.sh
```

### **Step 2: Run Diagnostic**
```bash
wget https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/bt_diagnostic.py
python3 bt_diagnostic.py
```

### **Step 3: Manual Commands**
```bash
# Restart Bluetooth
sudo systemctl restart bluetooth
sudo rfkill unblock bluetooth
sudo hciconfig hci0 up

# Test scan
hcitool scan

# Look for: 1C:69:20:A4:30:2A BT_CAR_32
```

## 📥 **Download Safe Server File (Fallback)**

```bash
# Download the safe server (works without Bluetooth)
wget https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/raspberry_pi_server_safe.py

# Make it executable
chmod +x raspberry_pi_server_safe.py
```

## 📥 **Download Installation Script**

```bash
# Download the dependency installer
wget https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/install_pi_dependencies.sh

# Make it executable
chmod +x install_pi_dependencies.sh

# Run the installer
bash install_pi_dependencies.sh
```

## 📥 **Download All Files at Once**

```bash
# Create project directory
mkdir -p ~/robot_guardian
cd ~/robot_guardian

# Download all necessary files
wget https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/raspberry_pi_server.py
wget https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/raspberry_pi_server_safe.py
wget https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/install_pi_dependencies.sh
wget https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/RASPBERRY_PI_SETUP.md
wget https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/BLUETOOTH_FIX.md

# Make scripts executable
chmod +x *.py *.sh

# View downloaded files
ls -la
```

## 🚀 **Quick Setup Commands**

### **Option 1: Full Setup (with Bluetooth)**
```bash
# Download and install everything
wget https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/install_pi_dependencies.sh
bash install_pi_dependencies.sh

# Download and run main server
wget https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/raspberry_pi_server.py
python3 raspberry_pi_server.py
```

### **Option 2: Quick Test (no Bluetooth required)**
```bash
# Download and run safe server
wget https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/raspberry_pi_server_safe.py
python3 raspberry_pi_server_safe.py
```

## 📋 **Step-by-Step Raspberry Pi Setup**

1. **SSH into your Raspberry Pi:**
   ```bash
   ssh pi@192.168.1.100  # Replace with your Pi's IP
   ```

2. **Download files:**
   ```bash
   wget https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/raspberry_pi_server.py
   ```

3. **Install dependencies (if needed):**
   ```bash
   wget https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/install_pi_dependencies.sh
   bash install_pi_dependencies.sh
   ```

4. **Run the server:**
   ```bash
   python3 raspberry_pi_server.py
   ```

5. **Test from Windows:**
   ```bash
   # Test connection
   curl http://192.168.1.100:5000/

   # Test command
   curl -X POST http://192.168.1.100:5000/move -H "Content-Type: application/json" -d '{"command": "F"}'
   ```

## 🔗 **Direct File URLs**

- **Main Server:** `https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/raspberry_pi_server.py`
- **Safe Server:** `https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/raspberry_pi_server_safe.py`
- **Installer:** `https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/install_pi_dependencies.sh`
- **Setup Guide:** `https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/RASPBERRY_PI_SETUP.md`
- **Fix Guide:** `https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/BLUETOOTH_FIX.md`

## 💡 **Pro Tips**

- Use `raspberry_pi_server_safe.py` for immediate testing
- Use `raspberry_pi_server.py` for full Bluetooth functionality
- Run `install_pi_dependencies.sh` if you get import errors
- Check `BLUETOOTH_FIX.md` for troubleshooting
