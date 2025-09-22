#!/usr/bin/env python3
"""
BT_CAR_32 Bluetooth Diagnostic Tool
==================================

Quick diagnostic to troubleshoot Bluetooth connection to BT_CAR_32
Run this on Raspberry Pi before starting the main server.

Usage: python3 bt_diagnostic.py
"""

import subprocess
import sys
import time

# BT_CAR_32 MAC address
BT_CAR_32_MAC = "1C:69:20:A4:30:2A"

def run_command(cmd, description):
    """Run a system command and return result"""
    print(f"🔍 {description}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✅ Success")
            if result.stdout.strip():
                print(f"📄 Output: {result.stdout.strip()}")
        else:
            print(f"❌ Failed (exit code: {result.returncode})")
            if result.stderr.strip():
                print(f"📄 Error: {result.stderr.strip()}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"⏱️ Timeout (30s)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_bluetooth_service():
    """Check Bluetooth service status"""
    print("\n🔧 CHECKING BLUETOOTH SERVICE")
    print("=" * 40)
    
    # Check if bluetooth service is running
    if run_command("systemctl is-active bluetooth", "Checking Bluetooth service"):
        print("✅ Bluetooth service is running")
    else:
        print("❌ Bluetooth service not running")
        print("💡 Try: sudo systemctl start bluetooth")
        return False
    
    # Check if bluetooth is enabled
    run_command("systemctl is-enabled bluetooth", "Checking if Bluetooth is enabled")
    
    # Check rfkill status
    if run_command("rfkill list bluetooth", "Checking rfkill status"):
        print("✅ Bluetooth adapter status checked")
    
    return True

def check_bluetooth_adapter():
    """Check Bluetooth adapter"""
    print("\n📡 CHECKING BLUETOOTH ADAPTER")
    print("=" * 40)
    
    # Check hci devices
    if run_command("hciconfig", "Checking HCI devices"):
        print("✅ Bluetooth adapter detected")
    else:
        print("❌ No Bluetooth adapter found")
        return False
    
    # Check if adapter is up
    if run_command("hciconfig hci0", "Checking hci0 status"):
        print("✅ hci0 adapter accessible")
    else:
        print("❌ hci0 adapter not accessible")
        print("💡 Try: sudo hciconfig hci0 up")
        return False
    
    return True

def scan_for_bt_car():
    """Scan for BT_CAR_32"""
    print("\n🔍 SCANNING FOR BT_CAR_32")
    print("=" * 40)
    print(f"🎯 Looking for MAC: {BT_CAR_32_MAC}")
    
    # Quick scan with hcitool
    print("📡 Running 10-second scan...")
    if run_command(f"timeout 10s hcitool scan", "Quick Bluetooth scan"):
        print("✅ Scan completed")
    else:
        print("❌ Scan failed")
        return False
    
    # Check if BT_CAR_32 is in scan results
    result = subprocess.run(f"hcitool scan | grep -i {BT_CAR_32_MAC}", 
                          shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ Found BT_CAR_32 at {BT_CAR_32_MAC}")
        return True
    else:
        print(f"❌ BT_CAR_32 not found in scan")
        print("💡 Make sure ESP32 is powered on and in pairing mode")
        return False

def test_python_bluetooth():
    """Test Python bluetooth module"""
    print("\n🐍 TESTING PYTHON BLUETOOTH")
    print("=" * 40)
    
    try:
        import bluetooth
        print("✅ Python bluetooth module imported successfully")
        
        # Test device discovery
        print("📡 Testing Python device discovery...")
        devices = bluetooth.discover_devices(duration=8, lookup_names=True)
        
        print(f"📱 Found {len(devices)} devices:")
        bt_car_found = False
        
        for addr, name in devices:
            print(f"   {name} [{addr}]")
            if addr.upper() == BT_CAR_32_MAC.upper():
                bt_car_found = True
                print(f"✅ Found BT_CAR_32!")
        
        if not bt_car_found:
            print(f"❌ BT_CAR_32 ({BT_CAR_32_MAC}) not found")
        
        return bt_car_found
        
    except ImportError:
        print("❌ Python bluetooth module not installed")
        print("💡 Install with: pip3 install pybluez")
        return False
    except Exception as e:
        print(f"❌ Python bluetooth test failed: {e}")
        return False

def attempt_connection():
    """Attempt direct connection to BT_CAR_32"""
    print("\n🔗 TESTING DIRECT CONNECTION")
    print("=" * 40)
    
    try:
        import bluetooth
        
        print(f"📞 Attempting connection to {BT_CAR_32_MAC}...")
        sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        sock.settimeout(10)
        
        sock.connect((BT_CAR_32_MAC, 1))
        print("✅ Connection successful!")
        
        # Send test command
        print("📤 Sending test command 'S'...")
        sock.send(b'S\n')
        
        # Try to receive response
        try:
            sock.settimeout(3)
            response = sock.recv(1024).decode().strip()
            print(f"📥 ESP32 response: {response}")
        except:
            print("📥 No response (might be normal)")
        
        sock.close()
        print("🎉 Connection test passed!")
        return True
        
    except ImportError:
        print("❌ Python bluetooth module not available")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("💡 Check if ESP32 is powered on and accepting connections")
        return False

def main():
    """Main diagnostic function"""
    print("🤖 BT_CAR_32 Bluetooth Diagnostic Tool")
    print("=" * 50)
    print(f"🎯 Target ESP32: BT_CAR_32 ({BT_CAR_32_MAC})")
    print()
    
    # Run all diagnostic checks
    checks = [
        ("Bluetooth Service", check_bluetooth_service),
        ("Bluetooth Adapter", check_bluetooth_adapter),
        ("Device Scan", scan_for_bt_car),
        ("Python Bluetooth", test_python_bluetooth),
        ("Direct Connection", attempt_connection)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except KeyboardInterrupt:
            print("\n⏹️ Diagnostic interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"❌ {name} check failed with error: {e}")
            results.append((name, False))
    
    # Summary
    print("\n📋 DIAGNOSTIC SUMMARY")
    print("=" * 30)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:.<20} {status}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 All checks passed! BT_CAR_32 should work with the server.")
        print("✅ You can now run: python3 raspberry_pi_server.py")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("💡 Common fixes:")
        print("   • sudo systemctl start bluetooth")
        print("   • sudo rfkill unblock bluetooth")
        print("   • sudo hciconfig hci0 up")
        print("   • pip3 install pybluez")
        print("   • Power cycle the ESP32")

if __name__ == "__main__":
    main()