#!/usr/bin/env python3
"""
🚀 Quick Robot Test
===================

Emergency test for robot commands
"""

import requests
import time

# Update with your Pi IP!
PI_IP = "192.168.1.2"
PI_URL = f"http://{PI_IP}:5000"

def test_robot():
    print("🚀 Quick Robot Test")
    print(f"Target: {PI_URL}")
    
    # Check connection
    try:
        response = requests.get(f"{PI_URL}/status", timeout=3)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Pi connected - UART: {data.get('uart_status')}")
        else:
            print("❌ Pi connection failed")
            return
    except:
        print("❌ Cannot reach Pi")
        return
    
    # Test commands
    commands = ['S', 'F', 'S']
    for cmd in commands:
        print(f"Sending: {cmd}")
        try:
            requests.post(f"{PI_URL}/move", json={"direction": cmd}, timeout=3)
        except:
            print(f"Failed: {cmd}")
        time.sleep(2)
    
    print("Done!")

if __name__ == "__main__":
    test_robot()