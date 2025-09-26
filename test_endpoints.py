#!/usr/bin/env python3
"""Test script to check if the audio chat endpoint is working"""

import requests
import json

def test_endpoints():
    base_url = "http://localhost:5050"
    
    print("🧪 Testing Windows Robot Supervisor Endpoints")
    print("=" * 50)
    
    # Test 1: Check if supervisor is running
    try:
        response = requests.get(f"{base_url}/api/status", timeout=5)
        print(f"✅ Status endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Pi connected: {data.get('pi_connected', False)}")
            print(f"   Voice ready: {data.get('voice_ready', False)}")
    except Exception as e:
        print(f"❌ Status endpoint failed: {e}")
        return
    
    # Test 2: Check audio-chat endpoint with OPTIONS
    try:
        response = requests.options(f"{base_url}/api/assistant/audio-chat", timeout=5)
        print(f"✅ Audio-chat OPTIONS: {response.status_code}")
    except Exception as e:
        print(f"❌ Audio-chat OPTIONS failed: {e}")
    
    # Test 3: Try a POST without file (should return error but endpoint exists)
    try:
        response = requests.post(f"{base_url}/api/assistant/audio-chat", timeout=5)
        print(f"✅ Audio-chat POST (no file): {response.status_code}")
        if response.status_code != 200:
            try:
                error_data = response.json()
                print(f"   Expected error: {error_data.get('message', 'Unknown')}")
            except:
                print(f"   Response text: {response.text[:100]}...")
    except Exception as e:
        print(f"❌ Audio-chat POST failed: {e}")
    
    # Test 4: List available endpoints
    endpoints_to_test = [
        "/api/assistant/message",
        "/api/assistant/reminders", 
        "/api/assistant/voice-note"
    ]
    
    for endpoint in endpoints_to_test:
        try:
            response = requests.options(f"{base_url}{endpoint}", timeout=5)
            print(f"✅ {endpoint} OPTIONS: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint} failed: {e}")

if __name__ == "__main__":
    test_endpoints()