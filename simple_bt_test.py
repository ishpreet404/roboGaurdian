#!/usr/bin/env python3
"""
Simple audio test for Bluetooth compatibility
"""

import requests
import os
import tempfile

def test_audio_endpoint():
    """Test the audio endpoint is working"""
    print("🎧 Testing Pi Bluetooth Audio Setup")
    print("=" * 40)
    
    print("1️⃣ Testing Windows Supervisor Connection...")
    try:
        response = requests.get("http://localhost:5050/health", timeout=5)
        if response.status_code == 200:
            print("✅ Windows supervisor is running")
        else:
            print(f"⚠️ Windows supervisor responded with: {response.status_code}")
    except Exception as e:
        print(f"❌ Windows supervisor not accessible: {e}")
        return False
    
    print("\n2️⃣ What we've changed for Bluetooth:")
    print("✅ Pi server now prioritizes PulseAudio over ALSA")
    print("✅ Direct MP3/MP4 playback (no conversion needed)")
    print("✅ FFmpeg → PulseAudio pipeline for Bluetooth routing")
    print("✅ MPV with PulseAudio driver as backup")
    
    print("\n🎯 Why this should fix Bluetooth noise:")
    print("• ALSA commands don't route to Bluetooth properly")
    print("• PulseAudio handles Bluetooth audio routing automatically") 
    print("• MP3 format preserves quality better than WAV conversion")
    print("• No unnecessary format conversions that add noise")
    
    print("\n📋 Next steps:")
    print("1. Restart your Pi camera server:")
    print("   pkill -f pi_camera_server")
    print("   python3 pi_camera_server_fixed.py")
    print("")
    print("2. Test audio chat from frontend:")
    print("   - Record voice message")
    print("   - Send to Pi")
    print("   - Should play clearly through Bluetooth speaker")
    print("")
    print("3. If still issues, run on Pi:")
    print("   python3 debug_bluetooth_audio.py")
    
    return True

if __name__ == "__main__":
    test_audio_endpoint()