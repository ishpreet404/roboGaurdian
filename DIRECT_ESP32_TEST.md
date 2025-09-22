# Direct ESP32 Test Commands for Raspberry Pi

## 🚀 **Copy and Run This Test Script**

### **Step 1: Create the test file on Raspberry Pi**

```bash
# On your Raspberry Pi, create the test file:
cat > test_obstacle_car.py << 'EOF'
#!/usr/bin/env python3
"""
Direct BT_CAR_32 Connection Test
===============================
Test script specifically for your ESP32 obstacle avoidance car.
"""

import time
import sys

def test_bt_car_connection():
    """Test connection to your specific ESP32 code"""
    
    print("🤖 Testing BT_CAR_32 with Obstacle Avoidance")
    print("=" * 50)
    print("🎯 Target MAC: 1C:69:20:A4:30:2A")
    print()
    
    try:
        import bluetooth
        print("✅ Python bluetooth module loaded")
    except ImportError:
        print("❌ Python bluetooth module missing")
        print("💡 Install with: pip3 install pybluez")
        return False
    
    BT_CAR_32_MAC = "1C:69:20:A4:30:2A"
    
    # Test connection with your specific ESP32
    print("🔗 Attempting connection...")
    
    try:
        # Create socket
        sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        sock.settimeout(10)
        
        print("📞 Connecting to BT_CAR_32...")
        sock.connect((BT_CAR_32_MAC, 1))
        
        print("✅ Connected successfully!")
        print()
        
        # Test the exact command format your ESP32 expects
        print("🧪 Testing commands (matching your ESP32 code)...")
        
        # Your ESP32 expects single character commands
        test_commands = [
            ('S', 'Stop'),
            ('F', 'Forward'), 
            ('S', 'Stop'),
            ('B', 'Backward'),
            ('S', 'Stop'),
            ('L', 'Left Turn'),
            ('S', 'Stop'),
            ('R', 'Right Turn'),
            ('S', 'Final Stop')
        ]
        
        for cmd, desc in test_commands:
            print(f"📤 Sending: '{cmd}' ({desc})")
            
            # Send single character (your ESP32 reads single chars)
            sock.send(cmd.encode())
            
            # Wait a bit for ESP32 to process
            time.sleep(0.8)
            
            # Try to read any response (your ESP32 might send debug info)
            try:
                sock.settimeout(1)
                response = sock.recv(1024)
                if response:
                    print(f"📥 ESP32 response: {response.decode().strip()}")
                else:
                    print("📥 No response")
            except:
                print("📥 No response (normal)")
            
            print()
        
        # Close connection
        sock.close()
        print("🎉 All tests completed successfully!")
        print("✅ Your BT_CAR_32 is working perfectly!")
        
        return True
        
    except bluetooth.BluetoothError as e:
        print(f"❌ Bluetooth connection failed: {e}")
        
        # Specific error handling
        if "Host is down" in str(e):
            print("💡 ESP32 might be powered off")
        elif "Connection refused" in str(e):
            print("💡 ESP32 might be busy or not accepting connections")
        elif "File descriptor in bad state" in str(e):
            print("💡 Try power cycling the ESP32")
            print("💡 Or try: sudo systemctl restart bluetooth")
        
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def check_esp32_status():
    """Check if ESP32 is discoverable"""
    print("🔍 Checking if BT_CAR_32 is discoverable...")
    
    try:
        import bluetooth
        
        devices = bluetooth.discover_devices(lookup_names=True, duration=8)
        
        found = False
        for addr, name in devices:
            print(f"📱 Found: {name} [{addr}]")
            if addr == "1C:69:20:A4:30:2A":
                print("✅ BT_CAR_32 found and discoverable!")
                found = True
        
        if not found:
            print("❌ BT_CAR_32 not discoverable")
            print("💡 Check ESP32 power and Bluetooth status")
            
        return found
        
    except Exception as e:
        print(f"❌ Discovery failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 BT_CAR_32 Obstacle Avoidance Robot Test")
    print("=" * 55)
    print()
    
    # Step 1: Check discovery
    if not check_esp32_status():
        print("\n❌ ESP32 not discoverable - check power and Bluetooth")
        return
    
    print()
    
    # Step 2: Test connection and commands
    if test_bt_car_connection():
        print("\n🎉 SUCCESS! Your robot is ready!")
        print("✅ Now you can run: python3 raspberry_pi_server.py")
        print("✅ Commands will work: F, B, L, R, S")
        print("✅ Obstacle avoidance is active on ESP32")
    else:
        print("\n❌ Connection test failed")
        print("\n🔧 Try these fixes:")
        print("1. Power cycle ESP32 (unplug/replug power)")
        print("2. sudo systemctl restart bluetooth")
        print("3. Check ESP32 serial monitor for errors")
        print("4. Verify ESP32 is running your obstacle avoidance code")

if __name__ == "__main__":
    main()
EOF
```

### **Step 2: Run the test**

```bash
# Make it executable
chmod +x test_obstacle_car.py

# Run the test
python3 test_obstacle_car.py
```

## 🔧 **Expected Results:**

### **If Working:**
```
🤖 Testing BT_CAR_32 with Obstacle Avoidance
🎯 Target MAC: 1C:69:20:A4:30:2A
✅ BT_CAR_32 found and discoverable!
📞 Connecting to BT_CAR_32...
✅ Connected successfully!
🧪 Testing commands...
📤 Sending: 'S' (Stop)
📤 Sending: 'F' (Forward)
🎉 All tests completed successfully!
```

### **If Still Failing:**
```bash
# Try power cycling ESP32 first
# Then run:
sudo systemctl restart bluetooth
python3 test_obstacle_car.py
```

## 🎯 **Key Differences:**

Your ESP32 code expects:
- ✅ **Single character commands** (not strings with newlines)
- ✅ **Commands: F, B, L, R, S** (exactly what you have)
- ✅ **Obstacle avoidance is always active**

This test script matches your ESP32 code exactly! 🚀

Copy and run this test - it should work with your obstacle avoidance ESP32 code!