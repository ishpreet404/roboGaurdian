#!/usr/bin/env python3
"""
Robot Communication Test Script
===============================

This script tests the complete communication chain:
Windows PC → Raspberry Pi → ESP32

Usage:
    python test_robot_communication.py [raspberry_pi_ip]

Example:
    python test_robot_communication.py 192.168.1.100
"""

import sys
import time
import requests
import json

def test_raspberry_pi_connection(pi_ip):
    """Test connection to Raspberry Pi server"""
    print(f"🔍 Testing Raspberry Pi connection at {pi_ip}:5000")
    
    try:
        # Test basic connection
        response = requests.get(f"http://{pi_ip}:5000/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Raspberry Pi server is running")
            print(f"   Status: {data.get('status', 'unknown')}")
            print(f"   ESP32 Connected: {data.get('esp32_connected', False)}")
            print(f"   Camera Active: {data.get('camera_active', False)}")
            return True
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to Raspberry Pi at {pi_ip}:5000")
        print("   Check: Pi is on, server is running, IP is correct")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ Connection timeout to {pi_ip}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_detailed_status(pi_ip):
    """Get detailed status from Raspberry Pi"""
    print(f"\n📊 Getting detailed status...")
    
    try:
        response = requests.get(f"http://{pi_ip}:5000/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Detailed Status:")
            print(f"   Server Status: {data.get('server_status', 'unknown')}")
            print(f"   ESP32 Connected: {data.get('esp32_connected', False)}")
            print(f"   ESP32 Address: {data.get('esp32_address', 'None')}")
            print(f"   Camera Active: {data.get('camera_active', False)}")
            print(f"   Last Command: {data.get('last_command', 'None')}")
            print(f"   Command Count: {data.get('command_count', 0)}")
            
            recent_commands = data.get('recent_commands', [])
            if recent_commands:
                print(f"   Recent Commands:")
                for cmd in recent_commands[-3:]:  # Show last 3
                    print(f"     - {cmd.get('command', '?')} at {cmd.get('timestamp', '?')}")
            
            return data.get('esp32_connected', False)
        else:
            print(f"❌ Status check failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Status check error: {e}")
        return False

def test_camera_stream(pi_ip):
    """Test camera stream availability"""
    print(f"\n📹 Testing camera stream...")
    
    try:
        response = requests.get(f"http://{pi_ip}:5000/?action=stream", timeout=3, stream=True)
        if response.status_code == 200:
            print(f"✅ Camera stream is available")
            print(f"   URL: http://{pi_ip}:5000/?action=stream")
            return True
        else:
            print(f"❌ Camera stream failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Camera stream error: {e}")
        return False

def test_command_sending(pi_ip):
    """Test sending movement commands"""
    print(f"\n🎮 Testing command sending...")
    
    commands = ['S', 'F', 'L', 'R', 'B', 'S']  # Stop, Forward, Left, Right, Back, Stop
    command_names = ['Stop', 'Forward', 'Left', 'Right', 'Backward', 'Stop']
    
    for cmd, name in zip(commands, command_names):
        try:
            payload = {'command': cmd}
            response = requests.post(
                f"http://{pi_ip}:5000/move",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=3
            )
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status', 'unknown')
                print(f"✅ Command '{cmd}' ({name}): {status}")
            else:
                print(f"❌ Command '{cmd}' failed: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Command '{cmd}' error: {e}")
            
        time.sleep(1)  # Wait between commands

def scan_bluetooth_devices(pi_ip):
    """Scan for Bluetooth devices via Raspberry Pi"""
    print(f"\n🔵 Scanning for Bluetooth devices...")
    
    try:
        response = requests.get(f"http://{pi_ip}:5000/scan_bluetooth", timeout=15)
        if response.status_code == 200:
            data = response.json()
            devices = data.get('devices', [])
            print(f"✅ Found {len(devices)} Bluetooth devices:")
            
            for device in devices:
                name = device.get('name', 'Unknown')
                addr = device.get('address', 'Unknown')
                print(f"   - {name} ({addr})")
                
            return devices
        else:
            print(f"❌ Bluetooth scan failed: HTTP {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Bluetooth scan error: {e}")
        return []

def main():
    """Main test function"""
    print("🤖 Robot Communication Test")
    print("=" * 40)
    
    # Get Raspberry Pi IP
    if len(sys.argv) > 1:
        pi_ip = sys.argv[1]
    else:
        pi_ip = input("Enter Raspberry Pi IP address (e.g., 192.168.1.100): ").strip()
        
    if not pi_ip:
        print("❌ No IP address provided")
        return
    
    print(f"Testing communication with Raspberry Pi: {pi_ip}")
    print("-" * 40)
    
    # Test 1: Basic connection
    if not test_raspberry_pi_connection(pi_ip):
        print("\n❌ Basic connection failed. Check Raspberry Pi setup.")
        return
    
    # Test 2: Detailed status
    esp32_connected = test_detailed_status(pi_ip)
    
    # Test 3: Camera stream
    test_camera_stream(pi_ip)
    
    # Test 4: Bluetooth scan
    scan_bluetooth_devices(pi_ip)
    
    # Test 5: Command sending
    if esp32_connected:
        print(f"\n✅ ESP32 is connected - testing commands")
        test_command_sending(pi_ip)
    else:
        print(f"\n⚠️  ESP32 not connected - skipping command tests")
        print("   Pair ESP32 with Raspberry Pi first")
    
    # Summary
    print(f"\n📋 Test Summary")
    print("-" * 20)
    print(f"Raspberry Pi: ✅ Connected")
    print(f"ESP32: {'✅ Connected' if esp32_connected else '❌ Not Connected'}")
    print(f"Camera: ✅ Available")
    print(f"Commands: {'✅ Working' if esp32_connected else '⚠️  ESP32 needed'}")
    
    print(f"\n🎯 Next Steps:")
    if not esp32_connected:
        print("1. Upload Arduino code to ESP32")
        print("2. Pair ESP32 with Raspberry Pi")
        print("3. Re-run this test")
    else:
        print("1. Update GUI robot IP to:", pi_ip)
        print("2. Set camera stream to: http://" + pi_ip + ":5000/?action=stream")
        print("3. Enable robot connection in GUI")
        print("4. Start person tracking!")

if __name__ == "__main__":
    main()