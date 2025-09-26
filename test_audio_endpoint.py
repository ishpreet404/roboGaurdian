#!/usr/bin/env python3
"""Test audio chat endpoint with a simple audio file"""

import requests
import json

def test_audio_chat():
    print("🎤 Testing Audio Chat Endpoint")
    print("=" * 40)
    
    base_url = "http://localhost:5050"
    
    # Test 1: OPTIONS request
    try:
        response = requests.options(f"{base_url}/api/assistant/audio-chat", timeout=5)
        print(f"✅ OPTIONS /api/assistant/audio-chat: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
    except Exception as e:
        print(f"❌ OPTIONS failed: {e}")
        return
    
    # Test 2: POST without files (should return 400)
    try:
        response = requests.post(f"{base_url}/api/assistant/audio-chat", timeout=5)
        print(f"✅ POST (no file): {response.status_code}")
        if response.headers.get('content-type', '').startswith('application/json'):
            data = response.json()
            print(f"   Response: {data}")
        else:
            print(f"   Response (text): {response.text[:100]}...")
    except Exception as e:
        print(f"❌ POST (no file) failed: {e}")
    
    # Test 3: POST with dummy audio file
    try:
        # Create a dummy WAV file (minimal WAV header)
        wav_header = b'RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x22\x56\x00\x00\x44\xac\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
        
        files = {'file': ('test_audio.wav', wav_header, 'audio/wav')}
        
        response = requests.post(f"{base_url}/api/assistant/audio-chat", files=files, timeout=10)
        print(f"✅ POST (with file): {response.status_code}")
        
        if response.headers.get('content-type', '').startswith('application/json'):
            try:
                data = response.json()
                print(f"   Response: {data}")
            except:
                print(f"   Response (raw): {response.text}")
        else:
            print(f"   Response (text): {response.text[:200]}...")
            
    except Exception as e:
        print(f"❌ POST (with file) failed: {e}")

if __name__ == "__main__":
    test_audio_chat()