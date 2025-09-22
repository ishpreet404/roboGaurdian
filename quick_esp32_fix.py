#!/usr/bin/env python3
"""
Quick ESP32 Connection Test
==========================
Direct connection test for BT_CAR_32 with multiple methods.
"""

import subprocess
import time
import sys

BT_CAR_32_MAC = "1C:69:20:A4:30:2A"

def run_cmd(cmd):
    """Run shell command and return success"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stdout, result.stderr
    except:
        return False, "", "timeout"

def test_python_bluetooth():
    """Test Python Bluetooth connection"""
    print("🐍 Testing Python Bluetooth Connection")
    print("-" * 40)
    
    try:
        import bluetooth
        print("✅ Python bluetooth module loaded")
        
        # Test different channels
        for channel in [1, 0, 2, 3]:
            print(f"📞 Trying RFCOMM channel {channel}...")
            try:
                sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
                sock.settimeout(5)
                sock.connect((BT_CAR_32_MAC, channel))
                
                print(f"✅ SUCCESS! Connected on channel {channel}")
                
                # Send test command
                sock.send(b'S\n')
                print("📤 Sent STOP command")
                
                # Try to get response
                try:
                    sock.settimeout(2)
                    response = sock.recv(1024).decode().strip()
                    print(f"📥 ESP32 response: '{response}'")
                except:
                    print("📥 No response (normal for some ESP32s)")
                
                sock.close()
                print(f"🎉 Channel {channel} is working!")
                return True, channel
                
            except Exception as e:
                print(f"❌ Channel {channel} failed: {e}")
                continue
        
        print("❌ All channels failed")
        return False, None
        
    except ImportError:
        print("❌ Python bluetooth module not installed")
        print("💡 Install with: pip3 install pybluez")
        return False, None
    except Exception as e:
        print(f"❌ Bluetooth test failed: {e}")
        return False, None

def unpair_and_repair():
    """Unpair and repair the device"""
    print("\n🔄 Unpairing and Repairing Device")
    print("-" * 40)
    
    commands = [
        f"echo 'remove {BT_CAR_32_MAC}' | bluetoothctl",
        "sleep 2",
        "echo 'power on' | bluetoothctl", 
        "echo 'agent on' | bluetoothctl",
        f"echo 'pair {BT_CAR_32_MAC}' | bluetoothctl",
        f"echo 'trust {BT_CAR_32_MAC}' | bluetoothctl",
        "echo 'quit' | bluetoothctl"
    ]
    
    for cmd in commands:
        print(f"🔧 {cmd}")
        success, stdout, stderr = run_cmd(cmd)
        if "Failed" in stdout or "Failed" in stderr:
            print(f"⚠️ Command had issues")
        time.sleep(1)
    
    print("✅ Pairing attempt completed")

def restart_bluetooth():
    """Restart Bluetooth service"""
    print("\n🔄 Restarting Bluetooth")
    print("-" * 25)
    
    commands = [
        "sudo hciconfig hci0 down",
        "sleep 2", 
        "sudo hciconfig hci0 up",
        "sleep 2",
        "sudo systemctl restart bluetooth",
        "sleep 3"
    ]
    
    for cmd in commands:
        print(f"🔧 {cmd}")
        run_cmd(cmd)
    
    print("✅ Bluetooth restarted")

def main():
    """Main troubleshooting"""
    print("🛠️ Quick ESP32 Connection Fixer")
    print("=" * 40)
    print(f"🎯 Target: BT_CAR_32 ({BT_CAR_32_MAC})")
    print()
    
    # Test 1: Direct connection
    print("🚀 Test 1: Direct connection test")
    success, channel = test_python_bluetooth()
    
    if success:
        print(f"\n🎉 SUCCESS! Use channel {channel}")
        print("✅ Your ESP32 is working - try the server now!")
        return
    
    # Test 2: Restart Bluetooth
    print("\n🚀 Test 2: Restarting Bluetooth")
    restart_bluetooth()
    
    print("\n🔄 Retesting after restart...")
    success, channel = test_python_bluetooth()
    
    if success:
        print(f"\n🎉 SUCCESS after restart! Use channel {channel}")
        return
    
    # Test 3: Unpair and repair
    print("\n🚀 Test 3: Unpairing and repairing")
    unpair_and_repair()
    
    print("\n🔄 Final test after repair...")
    success, channel = test_python_bluetooth()
    
    if success:
        print(f"\n🎉 SUCCESS after repair! Use channel {channel}")
    else:
        print("\n❌ All fixes failed")
        print("\n🔧 Manual steps needed:")
        print("1. Power cycle ESP32 (unplug/replug)")
        print("2. Check ESP32 serial monitor for errors")
        print("3. Verify ESP32 code has SerialBT.begin('BT_CAR_32')")
        print("4. Try: sudo systemctl restart bluetooth")

if __name__ == "__main__":
    main()