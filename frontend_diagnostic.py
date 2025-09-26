#!/usr/bin/env python3
"""
Frontend Diagnostic Tool
Test frontend connectivity and API endpoints
"""

import requests
import json

def test_endpoint(url, method='GET', data=None, files=None):
    """Test a single endpoint and return results"""
    try:
        if method == 'GET':
            response = requests.get(url, timeout=5)
        elif method == 'POST':
            if files:
                response = requests.post(url, files=files, timeout=10)
            else:
                response = requests.post(url, json=data, timeout=10)
        elif method == 'OPTIONS':
            response = requests.options(url, timeout=5)
        
        return {
            'status': response.status_code,
            'success': response.status_code < 400,
            'response': response.text[:500] if response.text else '',
            'headers': dict(response.headers)
        }
    except Exception as e:
        return {
            'status': 'ERROR',
            'success': False,
            'response': str(e),
            'headers': {}
        }

def main():
    print("🔍 Frontend API Diagnostic Tool")
    print("=" * 50)
    
    base_url = "http://localhost:5050"
    
    # Test basic connectivity
    print(f"\n📡 Testing Windows Supervisor at {base_url}")
    
    endpoints = [
        ("/api/status", "GET"),
        ("/api/assistant/status", "GET"),
        ("/api/assistant/message", "OPTIONS"),
        ("/api/assistant/message", "POST", {"text": "test", "speak": False}),
        ("/api/assistant/reminders", "GET"),
        ("/api/assistant/reminders", "OPTIONS"),
        ("/api/assistant/audio-chat", "OPTIONS"),
    ]
    
    for endpoint_data in endpoints:
        endpoint = endpoint_data[0]
        method = endpoint_data[1]
        data = endpoint_data[2] if len(endpoint_data) > 2 else None
        
        print(f"\n🔧 Testing {method} {endpoint}")
        result = test_endpoint(f"{base_url}{endpoint}", method, data)
        
        if result['success']:
            print(f"   ✅ {result['status']} - OK")
            if method == 'GET' and 'status' in endpoint:
                try:
                    parsed = json.loads(result['response'])
                    print(f"   📊 Pi Connected: {parsed.get('pi_connected', 'unknown')}")
                    print(f"   🎤 Voice Ready: {parsed.get('voice_ready', 'unknown')}")
                except:
                    pass
        else:
            print(f"   ❌ {result['status']} - {result['response'][:100]}")
    
    # Test audio chat with a dummy file
    print(f"\n🎤 Testing Audio Chat with dummy file")
    dummy_audio = b"fake audio data for testing"
    files = {'file': ('test.wav', dummy_audio, 'audio/wav')}
    
    result = test_endpoint(f"{base_url}/api/assistant/audio-chat", "POST", files=files)
    if result['success']:
        print(f"   ✅ {result['status']} - Audio endpoint working!")
    else:
        print(f"   ❌ {result['status']} - {result['response'][:200]}")
    
    # Check frontend dev server
    print(f"\n🌐 Testing Frontend Dev Server at http://localhost:5173")
    try:
        response = requests.get("http://localhost:5173", timeout=3)
        if response.status_code == 200:
            print("   ✅ Frontend dev server is running")
        else:
            print(f"   ⚠️ Frontend returned {response.status_code}")
    except Exception as e:
        print(f"   ❌ Frontend dev server not accessible: {e}")
        print("   💡 Run 'cd frontend && npm run dev' to start it")
    
    print(f"\n🎯 Summary:")
    print("   1. Make sure Windows supervisor is running: python windows_robot_supervisor.py")
    print("   2. Make sure frontend is running: cd frontend && npm run dev")
    print("   3. Frontend should connect to http://localhost:5050 (Windows API)")
    print("   4. Audio chat endpoint should be available at /api/assistant/audio-chat")

if __name__ == "__main__":
    main()