#!/bin/bash

echo "🎧 Bluetooth Audio Noise Fix"
echo "============================"

echo "🔍 Most likely issue: Pi is using low-quality Bluetooth codec (HSP/HFP instead of A2DP)"
echo ""

echo "1️⃣ Checking current Bluetooth audio setup..."

# Check if Bluetooth is working
if command -v bluetoothctl > /dev/null; then
    echo "✅ bluetoothctl available"
    
    # Show connected devices
    echo ""
    echo "📱 Connected Bluetooth devices:"
    bluetoothctl devices Connected 2>/dev/null || bluetoothctl devices
    
    echo ""
    echo "🔊 Current audio routing:"
    pactl list short sinks 2>/dev/null || echo "PulseAudio not running"
    
else
    echo "❌ bluetoothctl not found"
fi

echo ""
echo "2️⃣ Applying Bluetooth audio quality fixes..."

# Fix 1: Force A2DP high quality codec
echo "🔧 Forcing A2DP codec (high quality)..."

# Backup existing config
if [ -f /etc/bluetooth/main.conf ]; then
    sudo cp /etc/bluetooth/main.conf /etc/bluetooth/main.conf.backup
    echo "✅ Backed up bluetooth config"
fi

# Add A2DP settings
echo "📝 Updating Bluetooth configuration..."

# Create improved bluetooth config
sudo tee -a /etc/bluetooth/main.conf > /dev/null << 'EOF'

# Force high-quality A2DP audio codec
[General]
Class = 0x000100
DiscoverableTimeout = 0
Discoverable = yes
PairableTimeout = 0
Pairable = yes

# Disable low-quality headset profile (forces A2DP)
Disable = Headset

# Audio quality settings  
[A2DP]
SBCQualityMode = Bitpool
SBCMinimumBitpool = 53
SBCMaximumBitpool = 53
EOF

echo "✅ Bluetooth config updated"

# Fix 2: Restart Bluetooth with new settings
echo ""
echo "🔄 Restarting Bluetooth service..."
sudo systemctl restart bluetooth
sleep 2

# Fix 3: Configure PulseAudio for better Bluetooth
echo "🔊 Configuring PulseAudio for Bluetooth..."

# Create PulseAudio config for better Bluetooth
mkdir -p ~/.config/pulse

cat > ~/.config/pulse/default.pa << 'EOF'
# Load default PulseAudio configuration
.include /etc/pulse/default.pa

# Bluetooth A2DP optimizations
load-module module-bluetooth-policy auto_switch=2
load-module module-bluetooth-discover a2dp_config="ldac_eqmid=hq ldac_fmt=f32"

# Set default sample rate for better quality
default-sample-rate = 44100
alternate-sample-rate = 48000
default-sample-format = s16le

# Reduce latency
default-fragments = 4
default-fragment-size-msec = 25
EOF

echo "✅ PulseAudio configured for high-quality Bluetooth"

# Fix 4: Restart audio services
echo ""
echo "🔄 Restarting audio services..."
pulseaudio -k 2>/dev/null
sleep 1
pulseaudio --start 2>/dev/null
sleep 2

echo ""
echo "3️⃣ Testing Bluetooth audio quality..."

# Test system audio
if command -v speaker-test > /dev/null; then
    echo "🧪 Testing with clean tone (should be crystal clear)..."
    echo "   Playing 440Hz tone for 2 seconds..."
    speaker-test -t sine -f 440 -l 1 -s 1 2>/dev/null &
    sleep 2
    pkill speaker-test 2>/dev/null
    echo "   Did you hear a CLEAN tone or noise?"
else
    echo "⚠️ speaker-test not available"
fi

echo ""
echo "4️⃣ Verification commands..."
echo "Run these to verify the fix:"
echo ""
echo "# Check Bluetooth codec in use:"
echo "bluetoothctl info [YOUR_SPEAKER_MAC] | grep -i codec"
echo ""
echo "# Check PulseAudio Bluetooth module:"
echo "pactl list modules | grep bluetooth"
echo ""
echo "# Test high-quality audio:"
echo "paplay /usr/share/sounds/alsa/Front_Left.wav"

echo ""
echo "🎯 RESULTS:"
echo "=========="
echo "✅ If speaker-test played a CLEAN tone: Bluetooth is now fixed!"
echo "❌ If still noise: Run 'bluetoothctl info [MAC]' to check codec"
echo "🔄 If no change: Your speaker may need to be reconnected"
echo ""
echo "💡 To reconnect Bluetooth speaker:"
echo "   bluetoothctl disconnect [MAC]"
echo "   sleep 2" 
echo "   bluetoothctl connect [MAC]"

echo ""
echo "After this fix, restart your Pi camera server:"
echo "pkill -f pi_camera_server"
echo "python3 pi_camera_server_fixed.py"