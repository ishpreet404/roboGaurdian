#!/usr/bin/env python3
"""
ESP32 Connection Fixer
======================

Advanced connection troubleshooting for BT_CAR_32
Handles common ESP32 Bluetooth connection issues.
"""

import bluetooth
import time
import sys

BT_CAR_32_MAC = "1C:69:20:A4:30:2A"

def test_connection_methods():
    """Try different connection methods for ESP32"""
    
    print("🔧 Testing ESP32 Connection Methods")
    print("=" * 40)
    
    # Method 1: Standard RFCOMM Channel 1
    print("📞 Method 1: Standard RFCOMM Channel 1...")
    if test_rfcomm_connection(1):
        return True
    
    time.sleep(2)
    
    # Method 2: Try different channels
    for channel in [0, 2, 3, 4, 5]:
        print(f"📞 Method 2: Trying RFCOMM Channel {channel}...")
        if test_rfcomm_connection(channel):
            return True
        time.sleep(1)
    
    # Method 3: Service discovery
    print("📞 Method 3: Service discovery...")
    if test_service_discovery():
        return True
    
    print("❌ All connection methods failed")
    return False

def test_rfcomm_connection(channel):
    """Test RFCOMM connection on specific channel"""
    try:
        sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        sock.settimeout(8)
        
        print(f"   🔗 Connecting to channel {channel}...")
        sock.connect((BT_CAR_32_MAC, channel))
        
        print(f"   ✅ Connected on channel {channel}!")
        
        # Test communication
        sock.send(b'S\n')
        print("   📤 Sent STOP command")
        
        try:
            sock.settimeout(2)
            response = sock.recv(1024).decode().strip()
            print(f"   📥 Response: {response}")
        except:
            print("   📥 No response (might be normal)")
        
        sock.close()
        print(f"   🎉 Channel {channel} works!")
        return True
        
    except Exception as e:
        print(f"   ❌ Channel {channel} failed: {e}")
        return False

def test_service_discovery():
    """Discover available services on ESP32"""
    try:
        print("   🔍 Discovering services...")
        services = bluetooth.find_service(address=BT_CAR_32_MAC)
        
        if not services:
            print("   ❌ No services found")
            return False
        
        print(f"   📋 Found {len(services)} service(s):")
        
        for service in services:
            name = service.get('name', 'Unknown')
            port = service.get('port', 'Unknown')
            print(f"      • {name} on port {port}")
            
            # Try connecting to discovered service
            if port != 'Unknown':
                try:
                    sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
                    sock.settimeout(5)
                    sock.connect((BT_CAR_32_MAC, port))
                    
                    print(f"   ✅ Connected to service '{name}' on port {port}!")
                    sock.send(b'S\n')
                    sock.close()
                    return True
                    
                except Exception as e:
                    print(f"   ❌ Service '{name}' connection failed: {e}")
        
        return False
        
    except Exception as e:
        print(f"   ❌ Service discovery failed: {e}")
        return False

def pair_device():
    """Attempt to pair with ESP32"""
    print("🔗 Attempting to pair with BT_CAR_32...")
    
    try:
        import subprocess
        
        # Use bluetoothctl to pair
        commands = [
            "power on",
            "agent on",
            "pairable on",
            f"pair {BT_CAR_32_MAC}",
            f"trust {BT_CAR_32_MAC}",
            f"connect {BT_CAR_32_MAC}",
            "quit"
        ]
        
        for cmd in commands:
            print(f"   📞 Running: {cmd}")
            result = subprocess.run(['bluetoothctl'], 
                                  input=cmd + '\n', 
                                  text=True, 
                                  capture_output=True, 
                                  timeout=10)
            
            if "Failed" in result.stdout or "Failed" in result.stderr:
                print(f"   ⚠️ Command might have failed: {cmd}")
            else:
                print(f"   ✅ Command completed: {cmd}")
            
            time.sleep(1)
        
        return True
        
    except Exception as e:
        print(f"   ❌ Pairing failed: {e}")
        return False

def reset_bluetooth():
    """Reset Bluetooth adapter"""
    print("🔄 Resetting Bluetooth adapter...")
    
    try:
        import subprocess
        
        commands = [
            "sudo hciconfig hci0 down",
            "sleep 2",
            "sudo hciconfig hci0 up",
            "sleep 2",
            "sudo systemctl restart bluetooth",
            "sleep 3"
        ]
        
        for cmd in commands:
            print(f"   🔧 {cmd}")
            subprocess.run(cmd, shell=True, timeout=15)
        
        print("   ✅ Bluetooth reset completed")
        return True
        
    except Exception as e:
        print(f"   ❌ Reset failed: {e}")
        return False

def main():
    """Main troubleshooting function"""
    print("🛠️ ESP32 Advanced Connection Troubleshooter")
    print("=" * 50)
    print(f"🎯 Target: BT_CAR_32 ({BT_CAR_32_MAC})")
    print()
    
    # Step 1: Try direct connection
    print("🚀 Step 1: Testing connection methods...")
    if test_connection_methods():
        print("\n🎉 SUCCESS! Connection working!")
        print("✅ Your ESP32 is ready for the server")
        return
    
    print("\n❌ Direct connection failed. Trying advanced fixes...")
    
    # Step 2: Reset Bluetooth
    print("\n🚀 Step 2: Resetting Bluetooth...")
    reset_bluetooth()
    
    # Step 3: Try pairing
    print("\n🚀 Step 3: Attempting pairing...")
    pair_device()
    
    # Step 4: Test again
    print("\n🚀 Step 4: Testing connection after fixes...")
    if test_connection_methods():
        print("\n🎉 SUCCESS! Connection working after fixes!")
        print("✅ Your ESP32 is ready for the server")
    else:
        print("\n❌ CONNECTION STILL FAILING")
        print("\n🔧 Additional troubleshooting needed:")
        print("   1. Check ESP32 Arduino code - ensure Bluetooth is properly initialized")
        print("   2. Verify ESP32 is not paired with another device")
        print("   3. Try restarting ESP32 (power cycle)")
        print("   4. Check if ESP32 is in pairing mode")
        print("   5. Verify ESP32 Bluetooth name is 'BT_CAR_32'")
        
        print("\n📋 ESP32 Arduino Code Check:")
        print("   SerialBT.begin(\"BT_CAR_32\"); // Must match exactly")
        print("   // Should be in setup() function")

if __name__ == "__main__":
    main()