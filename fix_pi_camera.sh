#!/bin/bash
# 🔧 Pi Camera Fix Script
# Automatically fixes common Pi Camera issues

echo "🔧 Pi Camera Fix Script"
echo "======================"
echo

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ Don't run this script as root (no sudo needed)"
   echo "   Just run: ./fix_pi_camera.sh"
   exit 1
fi

echo "📋 Current camera status:"
vcgencmd get_camera 2>/dev/null || echo "   vcgencmd not available"
echo

# Step 1: Enable camera interface
echo "🔧 Step 1: Enabling camera interface..."
echo "   This will modify /boot/config.txt"
read -p "   Continue? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Enable camera in config.txt
    sudo sed -i 's/#camera_auto_detect=1/camera_auto_detect=1/' /boot/config.txt
    sudo sed -i 's/#dtoverlay=vc4-kms-v3d/dtoverlay=vc4-kms-v3d/' /boot/config.txt
    
    # Add camera settings if not present
    if ! grep -q "camera_auto_detect=1" /boot/config.txt; then
        echo "camera_auto_detect=1" | sudo tee -a /boot/config.txt
    fi
    
    if ! grep -q "dtoverlay=vc4-kms-v3d" /boot/config.txt; then
        echo "dtoverlay=vc4-kms-v3d" | sudo tee -a /boot/config.txt
    fi
    
    echo "   ✅ Camera interface enabled in config.txt"
else
    echo "   ⏭️ Skipped camera interface setup"
fi

# Step 2: Update system
echo
echo "🔧 Step 2: Updating system..."
read -p "   Update system? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo apt update
    sudo apt upgrade -y
    echo "   ✅ System updated"
else
    echo "   ⏭️ Skipped system update"
fi

# Step 3: Install camera packages
echo
echo "🔧 Step 3: Installing camera packages..."
sudo apt install -y python3-picamera2 python3-libcamera python3-opencv
pip3 install opencv-python --user
echo "   ✅ Camera packages installed"

# Step 4: Add user to video group
echo
echo "🔧 Step 4: Adding user to video group..."
sudo usermod -a -G video $USER
echo "   ✅ User $USER added to video group"

# Step 5: Check camera connection
echo
echo "🔧 Step 5: Camera connection check..."
echo "📸 Camera troubleshooting:"
echo "   1. Check ribbon cable connection (both Pi and camera end)"
echo "   2. Make sure camera is inserted correctly (contacts facing away from ethernet)"
echo "   3. Camera ribbon should be fully inserted and locked"
echo "   4. Try different camera if available"
echo

# Step 6: Reboot prompt
echo "🔄 Step 6: Reboot required"
echo "   A reboot is required to apply camera changes."
echo "   After reboot, test with: vcgencmd get_camera"
echo
read -p "   Reboot now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "   🔄 Rebooting in 5 seconds..."
    sleep 5
    sudo reboot
else
    echo "   ⚠️ Remember to reboot manually: sudo reboot"
fi

echo
echo "✅ Pi Camera fix script completed!"
echo "📖 Next steps after reboot:"
echo "   1. Test camera: vcgencmd get_camera"
echo "   2. Should show: supported=1 detected=1"
echo "   3. Test image: raspistill -o test.jpg"
echo "   4. Run camera diagnostic: python3 camera_diagnostic.py"