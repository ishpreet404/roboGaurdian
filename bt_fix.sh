#!/bin/bash
# bt_fix.sh - Quick fix for Raspberry Pi Bluetooth issues

echo "🔧 BT_CAR_32 Bluetooth Quick Fix"
echo "=================================="

# BT_CAR_32 MAC address
BT_CAR_MAC="1C:69:20:A4:30:2A"

echo "🔄 Step 1: Restarting Bluetooth service..."
sudo systemctl stop bluetooth
sleep 2
sudo systemctl start bluetooth
sleep 2

echo "📡 Step 2: Unblocking Bluetooth..."
sudo rfkill unblock bluetooth

echo "🔌 Step 3: Bringing up Bluetooth adapter..."
sudo hciconfig hci0 up

echo "🧹 Step 4: Clearing Bluetooth cache..."
sudo rm -rf /var/lib/bluetooth/*/cache

echo "⚡ Step 5: Restarting Bluetooth again..."
sudo systemctl restart bluetooth
sleep 3

echo "🔍 Step 6: Checking Bluetooth status..."
if systemctl is-active --quiet bluetooth; then
    echo "✅ Bluetooth service is running"
else
    echo "❌ Bluetooth service failed to start"
    exit 1
fi

echo "📱 Step 7: Quick scan for BT_CAR_32..."
echo "Looking for $BT_CAR_MAC..."

# Scan for 10 seconds
timeout 10s hcitool scan | while read line; do
    if echo "$line" | grep -q "$BT_CAR_MAC"; then
        echo "✅ Found BT_CAR_32!"
        exit 0
    fi
done

scan_result=$?
if [ $scan_result -eq 0 ]; then
    echo "✅ BT_CAR_32 is discoverable"
else
    echo "⚠️ BT_CAR_32 not found in scan"
    echo "💡 Make sure ESP32 is powered on"
fi

echo ""
echo "🎯 Testing direct connection to BT_CAR_32..."

# Test with Python if available
if command -v python3 &> /dev/null; then
    python3 -c "
import sys
try:
    import bluetooth
    print('📞 Attempting connection...')
    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    sock.settimeout(5)
    sock.connect(('$BT_CAR_MAC', 1))
    print('✅ Connection successful!')
    sock.send(b'S\\n')
    sock.close()
    print('🎉 BT_CAR_32 is ready!')
except ImportError:
    print('❌ Python bluetooth module not installed')
    print('💡 Install with: pip3 install pybluez')
    sys.exit(1)
except Exception as e:
    print(f'❌ Connection failed: {e}')
    print('💡 Check ESP32 power and range')
    sys.exit(1)
"
else
    echo "❌ Python3 not available"
fi

echo ""
echo "🏁 Bluetooth fix completed!"
echo "💡 Now try: python3 raspberry_pi_server.py"