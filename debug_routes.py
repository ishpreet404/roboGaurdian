#!/usr/bin/env python3
"""Debug script to check registered Flask routes"""

import sys
from pathlib import Path

# Add current directory to Python path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from windows_robot_supervisor import WindowsRobotSupervisor

def debug_routes():
    print("🔍 Checking registered Flask routes...")
    print("=" * 50)
    
    supervisor = WindowsRobotSupervisor()
    
    print("📋 Registered routes:")
    for rule in supervisor.app.url_map.iter_rules():
        methods = ', '.join(rule.methods - {'HEAD', 'OPTIONS'})
        print(f"  {rule.rule:<40} [{methods}]")
    
    print()
    print("🎯 Looking for audio-chat route:")
    audio_routes = [rule for rule in supervisor.app.url_map.iter_rules() 
                   if 'audio-chat' in rule.rule]
    
    if audio_routes:
        for route in audio_routes:
            print(f"  ✅ Found: {route.rule} {route.methods}")
    else:
        print("  ❌ No audio-chat route found!")
    
    print()
    print("🧪 Testing route resolution:")
    
    test_paths = [
        "/api/assistant/audio-chat",
        "/api/assistant/message", 
        "/api/assistant/reminders"
    ]
    
    for path in test_paths:
        try:
            endpoint, values = supervisor.app.url_map.bind('localhost').match(path, 'POST')
            print(f"  ✅ {path:<35} -> {endpoint}")
        except Exception as e:
            print(f"  ❌ {path:<35} -> {type(e).__name__}: {e}")

if __name__ == "__main__":
    debug_routes()