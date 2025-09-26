# 📸 Pi Camera Not Detected - Fix Guide

## Problem
Your Pi Camera shows: `supported=0 detected=0, libcamera interfaces=0`

This means:
- **supported=0**: Camera interface is disabled in firmware
- **detected=0**: No camera hardware detected  
- **libcamera interfaces=0**: Modern camera stack can't find camera

## Quick Fix Steps

### 1. 🔌 **Check Physical Connection**
```bash
# Power off Pi first
sudo shutdown -h now

# Check camera ribbon cable:
# - Remove and reinsert firmly
# - Contacts should face AWAY from ethernet port
# - Cable should be fully inserted and locked
# - Check both Pi end and camera end
```

### 2. ⚙️ **Enable Camera Interface**
```bash
# Method 1: Using raspi-config (easiest)
sudo raspi-config
# Navigate: Interface Options → Camera → Enable → Reboot

# Method 2: Edit config manually
sudo nano /boot/config.txt
# Add these lines:
camera_auto_detect=1
dtoverlay=vc4-kms-v3d

# Save and reboot
sudo reboot
```

### 3. 🔧 **Run Automatic Fix Script**
```bash
# Make script executable and run
chmod +x fix_pi_camera.sh
./fix_pi_camera.sh
```

### 4. 📦 **Install Required Packages**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install camera packages
sudo apt install -y python3-picamera2 python3-libcamera python3-opencv

# Install Python packages
pip3 install opencv-python picamera2
```

### 5. 👤 **Fix Permissions**
```bash
# Add user to video group
sudo usermod -a -G video $USER

# Logout and login again (or reboot)
sudo reboot
```

## Testing After Fix

### Test 1: Check Camera Detection
```bash
vcgencmd get_camera
# Should show: supported=1 detected=1
```

### Test 2: Take Test Photo
```bash
# For Pi Camera
raspistill -o test.jpg

# Or with libcamera (newer Pi OS)
libcamera-still -o test.jpg
```

### Test 3: Run Diagnostic
```bash
python3 camera_diagnostic.py
# Should find working cameras
```

## Alternative: Use USB Camera

If Pi Camera still doesn't work, try USB camera:

```bash
# Plug in USB webcam
lsusb
# Should see camera device

# Test with diagnostic
python3 camera_diagnostic.py
# Should detect USB camera at index 0 or 1
```

## Updated Pi Server Settings

For USB camera, update `pi_camera_server.py`:

```python
# If using USB camera, modify these settings:
self.frame_width = 1280    # USB cameras often support 720p better
self.frame_height = 720
self.fps = 30              # Conservative FPS for USB
```

## Troubleshooting Matrix

| Symptom | Cause | Fix |
|---------|-------|-----|
| `supported=0` | Camera interface disabled | Enable in raspi-config |
| `detected=0` | Hardware not connected | Check ribbon cable |
| `libcamera interfaces=0` | Driver issues | Update system, install packages |
| Permission denied | User not in video group | `sudo usermod -a -G video $USER` |
| Camera opens but no frames | Wrong device/driver | Try different camera index |

## Expected Results After Fix

✅ **Success indicators:**
```bash
vcgencmd get_camera
# Output: supported=1 detected=1, libcamera interfaces=1

python3 pi_camera_server.py
# Output: ✅ Camera ready: 1920x1080 @ 60fps
```

❌ **Still having issues?**
- Try USB webcam as alternative
- Check Pi Camera module compatibility  
- Verify Pi OS version (newer = better camera support)
- Consider hardware replacement if camera module is faulty