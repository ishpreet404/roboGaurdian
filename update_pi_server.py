#!/usr/bin/env python3
"""
Pi Server Update Script
This script helps you update the pi_camera_server.py on your Raspberry Pi
"""

import requests
import os
import sys

def create_update_commands():
    """Create the commands needed to update the Pi server"""
    
    # Commands to run on the Pi
    commands = [
        "# Stop the current Pi server (if running)",
        "pkill -f pi_camera_server || echo 'No server running'",
        "",
        "# Create backup of current server",
        "cp pi_camera_server.py pi_camera_server_backup_$(date +%Y%m%d_%H%M%S).py 2>/dev/null || echo 'No existing server file'",
        "",
        "# Download the updated server file",
        "wget -O pi_camera_server.py 'https://raw.githubusercontent.com/your-repo/main/pi_camera_server_fixed.py'",
        "",
        "# OR if you prefer, copy from your Windows machine:",
        "# scp user@windows-ip:/path/to/nexhack/pi_camera_server_fixed.py ./pi_camera_server.py",
        "",
        "# Install any missing Python packages",
        "pip3 install gtts pygame pyttsx3 --break-system-packages",
        "",
        "# Start the updated server",
        "python3 pi_camera_server.py"
    ]
    
    return commands

def check_pi_status(pi_ip="192.168.1.100"):
    """Check if we can reach the Pi server"""
    try:
        response = requests.get(f"http://{pi_ip}:5000/", timeout=3)
        print(f"✅ Pi server is reachable at {pi_ip}:5000")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot reach Pi server at {pi_ip}:5000: {e}")
        return False

def main():
    print("🤖 Pi Server Update Helper")
    print("=" * 50)
    
    # Check current Pi status
    pi_ip = input("Enter your Pi IP address (default: 192.168.1.100): ").strip()
    if not pi_ip:
        pi_ip = "192.168.1.100"
    
    print(f"\n📡 Checking Pi server at {pi_ip}...")
    check_pi_status(pi_ip)
    
    # Generate update commands
    print("\n📋 Commands to run on your Raspberry Pi:")
    print("=" * 50)
    
    commands = create_update_commands()
    for cmd in commands:
        print(cmd)
    
    # Create a shell script file
    script_content = "#!/bin/bash\n" + "\n".join([cmd for cmd in commands if not cmd.startswith("#") and cmd.strip()])
    
    with open("update_pi_server.sh", "w") as f:
        f.write(script_content)
    
    print(f"\n💾 Commands saved to: update_pi_server.sh")
    print("\n🔧 To update your Pi server:")
    print("1. Copy pi_camera_server_fixed.py to your Pi:")
    print(f"   scp pi_camera_server_fixed.py pi@{pi_ip}:~/pi_camera_server.py")
    print("\n2. SSH to your Pi and restart the server:")
    print(f"   ssh pi@{pi_ip}")
    print("   pkill -f pi_camera_server")
    print("   python3 pi_camera_server.py")
    
    print("\n✨ After updating, test the audio chat again!")

if __name__ == "__main__":
    main()