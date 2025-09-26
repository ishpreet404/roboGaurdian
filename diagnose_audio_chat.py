#!/usr/bin/env python3
"""
Step-by-step audio chat debugging guide
"""

import requests
import time

def test_windows_supervisor():
    """Test if Windows supervisor is responding"""
    print("1️⃣  Testing Windows Supervisor...")
    try:
        response = requests.get("http://localhost:5050/api/status", timeout=3)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Windows supervisor running")
            print(f"   📡 Pi URL: {data.get('pi_base_url', 'Unknown')}")
            print(f"   🔗 Pi connected: {data.get('pi_connected', False)}")
            return True, data.get('pi_base_url')
        else:
            print(f"   ❌ Windows supervisor error: {response.status_code}")
            return False, None
    except Exception as e:
        print(f"   ❌ Windows supervisor not running: {e}")
        print(f"   💡 Start it with: .\\venv\\Scripts\\Activate.ps1; python .\\windows_robot_supervisor.py")
        return False, None

def test_pi_connection(pi_url):
    """Test if Pi server is responding"""
    if not pi_url:
        print("2️⃣  Skipping Pi test - no Pi URL available")
        return False
        
    print(f"2️⃣  Testing Pi Server at {pi_url}...")
    try:
        response = requests.get(f"{pi_url}/assistant/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Pi server responding")
            print(f"   🔊 Voice ready: {data.get('voice_ready', False)}")
            return True
        else:
            print(f"   ❌ Pi server error: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Pi server not reachable: {e}")
        print(f"   💡 Check if Pi is running: python3 pi_camera_server_fixed.py")
        return False

def test_audio_endpoint():
    """Test the audio chat endpoint"""
    print("3️⃣  Testing Audio Chat Endpoint...")
    
    url = "http://localhost:5050/api/assistant/audio-chat"
    
    # Test OPTIONS
    try:
        response = requests.options(url, timeout=3)
        print(f"   ✅ OPTIONS: {response.status_code}")
    except Exception as e:
        print(f"   ❌ OPTIONS failed: {e}")
        return False
    
    # Test POST without file
    try:
        response = requests.post(url, timeout=3)
        print(f"   ✅ POST (no file): {response.status_code}")
        if response.status_code == 400:
            data = response.json()
            print(f"   📝 Expected error: {data.get('message')}")
        return True
    except Exception as e:
        print(f"   ❌ POST failed: {e}")
        return False

def test_with_audio():
    """Test with actual audio file"""
    print("4️⃣  Testing with Audio File...")
    
    # Create minimal WAV file
    wav_header = b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00"V\x00\x00D\xac\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
    files = {'file': ('test.wav', wav_header, 'audio/wav')}
    
    try:
        response = requests.post("http://localhost:5050/api/assistant/audio-chat", files=files, timeout=10)
        print(f"   📡 Response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: {data.get('message')}")
            return True
        else:
            try:
                data = response.json()
                print(f"   ❌ Error: {data.get('message')}")
            except:
                print(f"   ❌ Error: {response.text[:100]}")
            return False
    except Exception as e:
        print(f"   ❌ Request failed: {e}")
        return False

def main():
    print("🔧 Audio Chat Debugging Tool")
    print("=" * 40)
    
    # Test Windows supervisor
    windows_ok, pi_url = test_windows_supervisor()
    if not windows_ok:
        print("\n❌ Cannot continue - Windows supervisor not running")
        return
    
    # Test Pi connection
    pi_ok = test_pi_connection(pi_url)
    
    # Test audio endpoint
    endpoint_ok = test_audio_endpoint()
    if not endpoint_ok:
        print("\n❌ Audio endpoint not working")
        return
    
    # Test with actual audio
    audio_ok = test_with_audio()
    
    print("\n" + "=" * 40)
    if windows_ok and pi_ok and endpoint_ok and audio_ok:
        print("🎉 All tests passed! Audio chat should work.")
    else:
        print("🔧 Issues found:")
        if not windows_ok:
            print("   • Windows supervisor not running")
        if not pi_ok:
            print("   • Pi server not responding")
        if not endpoint_ok:
            print("   • Audio endpoint not working")
        if not audio_ok:
            print("   • Audio upload failed")

if __name__ == "__main__":
    main()