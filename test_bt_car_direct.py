#!/usr/bin/env python3
"""
Direct BT_CAR_32 Connection Test
===============================

Test script to verify direct connection to BT_CAR_32 
using hardcoded MAC address: 1C:69:20:A4:30:2A

Run this on Raspberry Pi to test ESP32 connection.
"""

import bluetooth
import time
import sys

# Hardcoded BT_CAR_32 MAC address
BT_CAR_32_MAC = "1C:69:20:A4:30:2A"

def test_direct_connection():
    """Test direct connection to BT_CAR_32"""
    print("🤖 BT_CAR_32 Direct Connection Test")
    print("=" * 40)
    print(f"📡 Target MAC: {BT_CAR_32_MAC}")
    print()
    
    try:
        print("🔗 Creating Bluetooth socket...")
        sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        sock.settimeout(10)
        
        print(f"📞 Connecting to BT_CAR_32 at {BT_CAR_32_MAC}...")
        sock.connect((BT_CAR_32_MAC, 1))
        
        print("✅ Connected successfully!")
        print()
        
        # Test movement commands
        test_sequence = [
            ('S', 'Stop'),
            ('F', 'Forward'),
            ('S', 'Stop'),
            ('B', 'Backward'), 
            ('S', 'Stop'),
            ('L', 'Turn Left'),
            ('S', 'Stop'),
            ('R', 'Turn Right'),
            ('S', 'Final Stop')
        ]
        
        print("🧪 Testing movement commands...")
        for cmd, description in test_sequence:
            print(f"📤 Sending: {cmd} ({description})")
            
            # Send command
            message = f"{cmd}\n"
            sock.send(message.encode())
            
            # Wait for response (if any)
            try:
                sock.settimeout(2)
                response = sock.recv(1024).decode().strip()
                print(f"📥 ESP32 Response: {response}")
            except bluetooth.BluetoothError:
                print("📥 No response (normal)")
            except Exception as e:
                print(f"📥 Response timeout: {e}")
            
            time.sleep(1)
            print()
        
        # Close connection
        sock.close()
        print("🎉 Test completed successfully!")
        print("✅ BT_CAR_32 is ready for robot control!")
        return True
        
    except bluetooth.BluetoothError as e:
        print(f"❌ Bluetooth connection failed: {e}")
        print()
        print("🔧 Troubleshooting:")
        print("   1. Make sure ESP32 is powered on")
        print("   2. Check if ESP32 is in range (~10 meters)")
        print("   3. Verify MAC address is correct")
        print("   4. Try: sudo systemctl restart bluetooth")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_bluetooth_status():
    """Check Bluetooth service status"""
    print("🔍 Checking Bluetooth status...")
    
    try:
        import subprocess
        
        # Check if bluetooth service is running
        result = subprocess.run(['systemctl', 'is-active', 'bluetooth'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Bluetooth service is active")
        else:
            print("❌ Bluetooth service is not active")
            print("💡 Try: sudo systemctl start bluetooth")
        
        # Check for blocked adapters
        result = subprocess.run(['rfkill', 'list', 'bluetooth'], 
                              capture_output=True, text=True)
        
        if 'blocked: yes' in result.stdout:
            print("❌ Bluetooth is blocked")
            print("💡 Try: sudo rfkill unblock bluetooth")
        else:
            print("✅ Bluetooth is unblocked")
            
    except Exception as e:
        print(f"⚠️ Could not check Bluetooth status: {e}")

def scan_for_bt_car():
    """Scan for BT_CAR_32 to verify it's discoverable"""
    print("🔍 Scanning for BT_CAR_32...")
    
    try:
        devices = bluetooth.discover_devices(lookup_names=True, duration=10)
        
        found_bt_car = False
        for addr, name in devices:
            print(f"📱 Found: {name} [{addr}]")
            
            if addr == BT_CAR_32_MAC:
                print(f"✅ Found BT_CAR_32 with correct MAC!")
                found_bt_car = True
            elif name and 'BT_CAR' in name.upper():
                print(f"⚠️ Found BT_CAR but different MAC: {addr}")
                found_bt_car = True
        
        if not found_bt_car:
            print("❌ BT_CAR_32 not found in scan")
            print("💡 Make sure ESP32 is powered on and broadcasting")
        
        return found_bt_car
        
    except Exception as e:
        print(f"❌ Scan failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting BT_CAR_32 diagnostics...")
    print()
    
    # Step 1: Check Bluetooth status
    check_bluetooth_status()
    print()
    
    # Step 2: Scan for device
    if scan_for_bt_car():
        print()
        # Step 3: Test direct connection
        if test_direct_connection():
            print("\n🎉 All tests passed! BT_CAR_32 is ready!")
            sys.exit(0)
        else:
            print("\n❌ Connection test failed!")
            sys.exit(1)
    else:
        print("\n❌ BT_CAR_32 not discoverable!")
        print("💡 Check ESP32 power and Bluetooth broadcasting")
        sys.exit(1)

if __name__ == "__main__":
    main()