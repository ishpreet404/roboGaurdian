#!/usr/bin/env python3
"""
Simple test for audio chat - run this while Windows supervisor is running
"""

import requests
import time

def quick_test():
    """Quick test that runs while supervisor is active"""
    print("🎤 Quick Audio Chat Test")
    print("=" * 30)
    
    url = "http://localhost:5050/api/assistant/audio-chat"
    
    # Test OPTIONS first
    try:
        response = requests.options(url, timeout=3)
        print(f"OPTIONS: {response.status_code} ✅")
    except Exception as e:
        print(f"OPTIONS: ❌ {e}")
        return False
    
    # Test POST without file (should return 400)
    try:
        response = requests.post(url, timeout=3)
        print(f"POST (no file): {response.status_code}")
        if response.status_code == 400:
            data = response.json()
            print(f"Expected error: {data.get('message', 'No message')}")
        print("✅ Endpoint is working!")
        return True
    except Exception as e:
        print(f"POST: ❌ {e}")
        return False

if __name__ == "__main__":
    print("⚠️  Make sure Windows supervisor is running!")
    print("   Run: .\\venv\\Scripts\\Activate.ps1; python .\\windows_robot_supervisor.py")
    print()
    input("Press Enter when supervisor is ready...")
    
    if quick_test():
        print("\n✅ Audio chat endpoint is working correctly!")
        print("   The issue might be with your Pi server not responding to audio requests.")
        print("   Make sure your Pi is running: python3 pi_camera_server_fixed.py")
    else:
        print("\n❌ Audio chat endpoint is not working.")