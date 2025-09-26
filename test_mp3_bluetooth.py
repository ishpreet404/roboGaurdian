#!/usr/bin/env python3
"""
Test MP3 audio sending to Pi Bluetooth speaker
"""

import requests
import tempfile
import subprocess
import os
from pathlib import Path

def create_test_mp3():
    """Create a test MP3 file"""
    mp3_file = "/tmp/test_bt_audio.mp3"
    
    print("🎵 Creating test MP3 file...")
    
    try:
        # Create a pleasant test tone (440Hz + 880Hz harmony)
        subprocess.run([
            'ffmpeg', '-f', 'lavfi', 
            '-i', 'sine=frequency=440:duration=2,sine=frequency=880:duration=2',
            '-filter_complex', '[0:a][1:a]amix=inputs=2:duration=first',
            '-acodec', 'mp3', '-ab', '128k', '-y', mp3_file
        ], check=True, capture_output=True)
        
        print(f"✅ Test MP3 created: {mp3_file}")
        return mp3_file
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create MP3: {e}")
        return None

def send_mp3_to_pi(mp3_file, pi_url="http://192.168.1.100:5000"):
    """Send MP3 file to Pi audio chat endpoint"""
    print(f"📤 Sending MP3 to Pi: {pi_url}/assistant/audio_chat")
    
    try:
        with open(mp3_file, 'rb') as f:
            files = {'audio': ('test.mp3', f, 'audio/mpeg')}
            
            response = requests.post(
                f"{pi_url}/assistant/audio_chat",
                files=files,
                timeout=10
            )
            
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS: {result.get('message', 'Audio sent')}")
            print(f"   File size: {result.get('file_size', 'unknown')} bytes")
            return True
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending MP3: {e}")
        return False

def test_local_windows_supervisor():
    """Test sending through Windows supervisor (like frontend does)"""
    print("🖥️ Testing via Windows supervisor...")
    
    mp3_file = create_test_mp3()
    if not mp3_file:
        return False
    
    try:
        with open(mp3_file, 'rb') as f:
            files = {'audio': ('test.mp3', f, 'audio/mpeg')}
            
            response = requests.post(
                "http://localhost:5050/api/assistant/audio-chat",  # Windows supervisor
                files=files,
                timeout=10
            )
            
        if response.status_code == 200:
            print("✅ Windows supervisor route works!")
            return True
        else:
            print(f"❌ Windows supervisor failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Windows supervisor error: {e}")
        return False
    finally:
        if os.path.exists(mp3_file):
            os.remove(mp3_file)

def main():
    print("🎧 Testing MP3 → Pi Bluetooth Audio")
    print("=" * 45)
    
    # Option 1: Test through Windows supervisor (matches frontend)
    print("\n1️⃣ Testing Windows Supervisor Route")
    if test_local_windows_supervisor():
        print("   This matches how the frontend sends audio!")
    
    print("\n2️⃣ Testing Direct Pi Route")
    pi_ip = input("Enter Pi IP address (or press Enter for 192.168.1.100): ").strip()
    if not pi_ip:
        pi_ip = "192.168.1.100"
    
    mp3_file = create_test_mp3()
    if mp3_file:
        success = send_mp3_to_pi(mp3_file, f"http://{pi_ip}:5000")
        
        # Cleanup
        if os.path.exists(mp3_file):
            os.remove(mp3_file)
            
        if success:
            print("\n🎯 RESULT: MP3 sent successfully!")
            print("   Did you hear clear audio from Bluetooth speaker?")
            print("   If yes: MP3 format works better than WAV conversion")
            print("   If no: May need PulseAudio configuration on Pi")
        else:
            print("\n❌ RESULT: MP3 sending failed")
            print("   Check Pi server is running and network connection")

if __name__ == "__main__":
    main()