#!/bin/bash
"""
🔧 Camera Diagnostic and Fix Script for Raspberry Pi
===================================================

This script diagnoses and fixes common camera issues on Raspberry Pi.
Run this script when you get "Camera test failed - check camera permissions"

Usage: 
sudo bash camera_fix.sh

Author: Robot Guardian System
Date: September 2025
"""

echo "🔧 Robot Guardian - Camera Diagnostic & Fix Tool"
echo "================================================"
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root: sudo bash camera_fix.sh"
    exit 1
fi

echo "🔍 Running camera diagnostics..."
echo

# 1. Check camera hardware detection
echo "1️⃣ Checking camera hardware detection..."
if lsusb | grep -i camera > /dev/null; then
    echo "✅ USB camera detected"
elif vcgencmd get_camera | grep "detected=1" > /dev/null; then 
    echo "✅ Pi Camera detected"
else
    echo "❌ No camera detected in hardware"
    echo "   • Check camera cable connection"
    echo "   • Try a different camera"
fi
echo

# 2. Check camera interface enabled
echo "2️⃣ Checking camera interface status..."
if raspi-config nonint get_camera | grep -q "0"; then
    echo "✅ Camera interface is enabled"
else
    echo "❌ Camera interface is disabled"
    echo "🔧 Enabling camera interface..."
    raspi-config nonint do_camera 0
    echo "✅ Camera interface enabled (requires reboot)"
    NEED_REBOOT=1
fi
echo

# 3. Check video device permissions
echo "3️⃣ Checking video device permissions..."
if [ -c /dev/video0 ]; then
    echo "✅ /dev/video0 exists"
    ls -la /dev/video* | head -5
    
    # Add user to video group
    if groups $SUDO_USER | grep -q video; then
        echo "✅ User $SUDO_USER is in video group"
    else
        echo "🔧 Adding user $SUDO_USER to video group..."
        usermod -a -G video $SUDO_USER
        echo "✅ User added to video group (requires logout/login)"
        NEED_LOGOUT=1
    fi
else
    echo "❌ /dev/video0 not found"
    echo "🔧 Creating video device..."
    modprobe bcm2835-v4l2
    echo "bcm2835-v4l2" >> /etc/modules
    echo "✅ Video module loaded"
fi
echo

# 4. Check OpenCV camera access
echo "4️⃣ Testing OpenCV camera access..."
python3 -c "
import cv2
import sys

print('🔍 Testing camera backends...')
backends = [
    (cv2.CAP_V4L2, 'V4L2'),
    (cv2.CAP_GSTREAMER, 'GStreamer'), 
    (cv2.CAP_ANY, 'Auto')
]

camera_found = False
for backend, name in backends:
    for camera_id in [0, 1]:
        try:
            cap = cv2.VideoCapture(camera_id, backend)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    print(f'✅ Camera {camera_id} works with {name} backend')
                    print(f'   Frame shape: {frame.shape}')
                    camera_found = True
                else:
                    print(f'⚠️  Camera {camera_id} opens but cannot read with {name}')
                cap.release()
            else:
                print(f'❌ Camera {camera_id} failed to open with {name}')
        except Exception as e:
            print(f'❌ Camera {camera_id} error with {name}: {e}')

if not camera_found:
    print('❌ No working camera found with OpenCV')
    sys.exit(1)
else:
    print('✅ Camera is working with OpenCV')
" || {
    echo "❌ OpenCV camera test failed"
    echo "🔧 Installing/updating OpenCV..."
    pip3 install --upgrade opencv-python
}
echo

# 5. Check camera process conflicts
echo "5️⃣ Checking for camera process conflicts..."
CAMERA_PROCESSES=$(ps aux | grep -E "(camera|gstreamer|motion|mjpg)" | grep -v grep | grep -v "camera_fix")
if [ -n "$CAMERA_PROCESSES" ]; then
    echo "⚠️ Found processes using camera:"
    echo "$CAMERA_PROCESSES"
    echo
    read -p "Kill conflicting processes? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pkill -f "camera|gstreamer|motion|mjpg" 2>/dev/null || true
        echo "✅ Camera processes terminated"
    fi
else
    echo "✅ No conflicting camera processes found"
fi
echo

# 6. Test camera with v4l2-utils
echo "6️⃣ Testing camera with v4l2-utils..."
if ! command -v v4l2-ctl &> /dev/null; then
    echo "🔧 Installing v4l2-utils..."
    apt update && apt install -y v4l2-utils
fi

if [ -c /dev/video0 ]; then
    echo "📷 Camera device info:"
    v4l2-ctl --device=/dev/video0 --info 2>/dev/null || echo "Could not get camera info"
    
    echo "📐 Supported formats:"
    v4l2-ctl --device=/dev/video0 --list-formats-ext 2>/dev/null | head -10 || echo "Could not list formats"
else
    echo "❌ No video device available for testing"
fi
echo

# 7. Set optimal camera parameters
echo "7️⃣ Optimizing camera parameters..."
if [ -c /dev/video0 ]; then
    echo "🔧 Setting low-latency camera parameters..."
    v4l2-ctl --device=/dev/video0 --set-ctrl=rotate=0 2>/dev/null || true
    v4l2-ctl --device=/dev/video0 --set-parm=30 2>/dev/null || true
    echo "✅ Camera parameters optimized"
else
    echo "⚠️ No video device to optimize"
fi
echo

# 8. Create camera test script
echo "8️⃣ Creating camera test script..."
cat > /home/$SUDO_USER/test_camera.py << 'EOF'
#!/usr/bin/env python3
"""
Quick camera test script
Usage: python3 test_camera.py
"""

import cv2
import time

print("🔍 Quick Camera Test")
print("==================")

# Test different backends
backends = [
    (cv2.CAP_V4L2, "V4L2 (Linux)"),
    (cv2.CAP_GSTREAMER, "GStreamer"),
    (cv2.CAP_ANY, "Auto-detect")
]

for backend, name in backends:
    print(f"\n📹 Testing {name}...")
    
    for camera_id in [0, 1, -1]:
        try:
            cap = cv2.VideoCapture(camera_id, backend)
            
            if cap.isOpened():
                # Try to read a few frames
                success_count = 0
                for i in range(5):
                    ret, frame = cap.read()
                    if ret:
                        success_count += 1
                    time.sleep(0.1)
                
                if success_count >= 3:
                    print(f"✅ Camera {camera_id}: {success_count}/5 frames captured")
                    print(f"   Resolution: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
                    print(f"   FPS: {cap.get(cv2.CAP_PROP_FPS):.1f}")
                else:
                    print(f"⚠️  Camera {camera_id}: Only {success_count}/5 frames captured")
            else:
                print(f"❌ Camera {camera_id}: Failed to open")
                
            cap.release()
            
        except Exception as e:
            print(f"❌ Camera {camera_id}: Exception - {e}")

print(f"\n🏁 Camera test completed!")
print(f"If any camera showed ✅, your camera is working!")
EOF

chown $SUDO_USER:$SUDO_USER /home/$SUDO_USER/test_camera.py
chmod +x /home/$SUDO_USER/test_camera.py
echo "✅ Camera test script created: /home/$SUDO_USER/test_camera.py"
echo

# Summary and recommendations
echo "📋 DIAGNOSTIC SUMMARY"
echo "===================="

if [ "$NEED_REBOOT" = "1" ]; then
    echo "🔄 REBOOT REQUIRED: Camera interface was enabled"
    echo "   Run: sudo reboot"
    echo
fi

if [ "$NEED_LOGOUT" = "1" ]; then
    echo "🔄 LOGOUT REQUIRED: User added to video group"  
    echo "   Log out and log back in, or run: newgrp video"
    echo
fi

echo "🧪 TESTING RECOMMENDATIONS:"
echo "1. Run camera test: python3 /home/$SUDO_USER/test_camera.py"
echo "2. Test robot server: python3 pi_camera_server.py"
echo "3. Check camera physically connected and not covered"
echo "4. Try different USB port if using USB camera"
echo

echo "🔧 IF PROBLEMS PERSIST:"
echo "• Check camera cable connection"
echo "• Try a different camera"  
echo "• Update system: sudo apt update && sudo apt upgrade"
echo "• Check power supply (cameras need good power)"
echo

echo "✅ Camera diagnostic completed!"