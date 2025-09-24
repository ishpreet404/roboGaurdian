#!/usr/bin/env python3
"""
🚨 EMERGENCY ROBOT TEST - Step by Step Debugging
=================================================

Tests each component individually to find the problem:
1. Pi server connection
2. Command sending
3. UART status
4. ESP32 response

Run this FIRST before anything else!
"""

import requests
import time
import json

def test_step_by_step():
    print("🚨 EMERGENCY ROBOT DEBUG")
    print("=" * 50)
    
    # Step 1: Get Pi IP from user
    print("📍 Step 1: Pi Connection")
    pi_ip = input("Enter Pi IP address (e.g., 192.168.1.2): ").strip()
    if not pi_ip:
        pi_ip = "192.168.1.2"
    
    base_url = f"http://{pi_ip}:5000"
    print(f"Testing: {base_url}")
    
    # Step 2: Test Pi server
    print("\n📡 Step 2: Testing Pi Server...")
    try:
        response = requests.get(f"{base_url}/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Pi server is running!")
            print(f"   Pi Status: {data.get('status')}")
            print(f"   UART Status: {data.get('uart_status')}")
            print(f"   Camera Status: {data.get('camera_status')}")
            print(f"   Commands Received: {data.get('commands_received')}")
        else:
            print(f"❌ Pi server error: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Pi: {e}")
        print(f"💡 Make sure Pi is running: python3 pi_camera_server.py")
        return False
    
    # Step 3: Test command sending
    print("\n🎮 Step 3: Testing Commands...")
    commands = ['S', 'F', 'B', 'L', 'R']
    
    for cmd in commands:
        print(f"\n   Testing command: {cmd}")
        try:
            cmd_data = {"direction": cmd}
            response = requests.post(f"{base_url}/move", json=cmd_data, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Command {cmd}: {result.get('status')}")
                print(f"      UART: {result.get('uart_status')}")
                print(f"      Message: {result.get('message')}")
            else:
                print(f"   ❌ Command {cmd} failed: HTTP {response.status_code}")
                try:
                    error = response.json()
                    print(f"      Error: {error.get('message')}")
                except:
                    print(f"      Raw error: {response.text}")
                    
        except Exception as e:
            print(f"   ❌ Command {cmd} error: {e}")
            
        time.sleep(1)  # Wait between commands
    
    # Step 4: Check current status
    print("\n📊 Step 4: Final Status Check...")
    try:
        response = requests.get(f"{base_url}/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Commands processed: {data.get('commands_received')}")
            print(f"   Last command: {data.get('last_command')}")
            print(f"   UART status: {data.get('uart_status')}")
    except Exception as e:
        print(f"❌ Status check failed: {e}")
    
    print("\n" + "=" * 50)
    print("🔍 DIAGNOSIS:")
    
    # Analyze results
    if data.get('uart_status') != 'connected':
        print("❌ UART PROBLEM DETECTED!")
        print("   Issue: Pi cannot communicate with ESP32")
        print("   Fix 1: Check ESP32 is powered and running")
        print("   Fix 2: Check GPIO wiring:")
        print("          Pi GPIO14 → ESP32 RX")  
        print("          Pi GPIO15 ← ESP32 TX")
        print("          Pi GND → ESP32 GND")
        print("   Fix 3: Enable Pi UART: sudo raspi-config")
        print("   Fix 4: Upload correct ESP32 code")
    elif data.get('commands_received', 0) == 0:
        print("❌ NO COMMANDS REACHING PI!")
        print("   Issue: Commands not getting through")
        print("   Check network connection")
    else:
        print("✅ Commands reaching Pi successfully")
        print("   If robot still not moving:")
        print("   - Check ESP32 Serial Monitor")
        print("   - Verify motor driver connections")
        print("   - Check motor power supply")

def quick_single_command():
    """Send one test command quickly"""
    pi_ip = input("Pi IP (or Enter for 192.168.1.2): ").strip() or "192.168.1.2"
    cmd = input("Command (F/B/L/R/S): ").upper().strip()
    
    if cmd not in ['F', 'B', 'L', 'R', 'S']:
        print("❌ Invalid command")
        return
    
    url = f"http://{pi_ip}:5000/move"
    data = {"direction": cmd}
    
    print(f"📤 Sending: {data} to {url}")
    
    try:
        response = requests.post(url, json=data, timeout=3)
        print(f"📥 Response: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    print("Choose test mode:")
    print("1. Full step-by-step diagnosis")
    print("2. Quick single command test")
    
    choice = input("Enter 1 or 2: ").strip()
    
    if choice == "1":
        test_step_by_step()
    else:
        quick_single_command()