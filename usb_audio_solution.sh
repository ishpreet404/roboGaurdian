#!/bin/bash

echo "🎧 USB Audio Adapter Solution for Pi"
echo "===================================="
echo ""

echo "The Pi's built-in 3.5mm audio jack is notoriously noisy due to:"
echo "• Poor analog-to-digital converter (ADC)"
echo "• Electrical interference from other Pi components" 
echo "• Inadequate power supply filtering"
echo "• Cheap onboard audio hardware"
echo ""

echo "🔍 Checking for USB audio devices..."

# Check for USB audio devices
usb_audio_found=false

if lsusb | grep -i audio > /dev/null; then
    echo "✅ USB audio device detected:"
    lsusb | grep -i audio
    usb_audio_found=true
else
    echo "❌ No USB audio device found"
fi

echo ""
echo "🎵 Available audio devices:"
aplay -l 2>/dev/null

echo ""
echo "💡 USB Audio Adapter Solution:"
echo "=============================="

if [ "$usb_audio_found" = true ]; then
    echo "✅ You have a USB audio device! Let's configure it:"
    echo ""
    
    # Get the USB audio card number
    usb_card=$(aplay -l | grep "USB" | head -1 | grep -o "card [0-9]" | grep -o "[0-9]")
    
    if [ -n "$usb_card" ]; then
        echo "🎯 Found USB audio at card $usb_card"
        echo ""
        
        # Create ALSA config for USB audio
        echo "Creating ALSA configuration for USB audio..."
        
        cat > /tmp/usb_asound.conf << EOF
# USB Audio Configuration for Pi
pcm.!default {
    type hw
    card $usb_card
    device 0
    rate 44100
    format S16_LE
}

ctl.!default {
    type hw
    card $usb_card
}
EOF
        
        echo "✅ USB audio config created. To apply:"
        echo "   sudo cp /tmp/usb_asound.conf /etc/asound.conf"
        echo ""
        
        # Test USB audio
        echo "🧪 Testing USB audio (you should hear a clean tone)..."
        
        # Create test tone for USB audio
        if command -v speaker-test > /dev/null; then
            speaker-test -D hw:$usb_card,0 -t sine -f 440 -l 1 -s 1 2>/dev/null
            if [ $? -eq 0 ]; then
                echo "✅ USB audio test successful!"
            else
                echo "⚠️ USB audio test failed - check connections"
            fi
        fi
        
    else
        echo "⚠️ Could not determine USB audio card number"
    fi
    
else
    echo "❌ No USB audio device detected."
    echo ""
    echo "🛒 Recommended USB Audio Adapters (~$5-15):"
    echo "• Generic USB Audio Adapter (CM108/CM109 chipset)"
    echo "• Sabrent USB External Stereo Sound Adapter"  
    echo "• UGREEN USB Audio Adapter"
    echo "• Any USB-C to 3.5mm adapter with DAC"
    echo ""
    echo "📦 After getting a USB audio adapter:"
    echo "1. Plug into Pi USB port"
    echo "2. Connect speakers to USB adapter (NOT Pi 3.5mm jack)"
    echo "3. Run this script again"
    echo "4. Restart Pi camera server"
fi

echo ""
echo "🔧 Alternative: Disable Pi built-in audio entirely"
echo "================================================="
echo "If you get a USB adapter, disable Pi audio to avoid conflicts:"
echo ""
echo "sudo nano /boot/config.txt"
echo "# Comment out or remove: dtparam=audio=on"
echo "# Add: dtoverlay=disable-audio"
echo ""
echo "Then reboot and Pi will only use USB audio (much cleaner!)"

echo ""
echo "🎯 Why USB Audio Fixes Noise:"
echo "=============================="
echo "• USB audio adapters have dedicated DACs"
echo "• Isolated from Pi's electrical noise"  
echo "• Better power supply filtering"
echo "• Higher quality audio components"
echo "• No interference from Pi CPU/GPU/WiFi"

echo ""
echo "After setup, restart the Pi server:"
echo "pkill -f pi_camera_server"
echo "python3 pi_camera_server.py"