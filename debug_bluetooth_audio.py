#!/usr/bin/env python3
"""
Bluetooth Audio Diagnostic for Pi
Test if audio chat pipeline works properly with Bluetooth speakers
"""

import subprocess
import os
import tempfile
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_bluetooth_audio_setup():
    """Check Bluetooth audio configuration on Pi"""
    print("🔍 Checking Bluetooth Audio Setup")
    print("=" * 40)
    
    # Check if Bluetooth is active
    try:
        result = subprocess.run(['bluetoothctl', 'show'], 
                              capture_output=True, text=True, timeout=5)
        if 'Powered: yes' in result.stdout:
            print("✅ Bluetooth controller is powered on")
        else:
            print("❌ Bluetooth controller is off")
            return False
    except Exception as e:
        print(f"❌ Bluetooth check failed: {e}")
        return False
    
    # Check connected devices
    try:
        result = subprocess.run(['bluetoothctl', 'devices', 'Connected'], 
                              capture_output=True, text=True, timeout=5)
        if result.stdout.strip():
            print("✅ Bluetooth devices connected:")
            for line in result.stdout.strip().split('\n'):
                print(f"   {line}")
        else:
            print("⚠️ No Bluetooth devices connected")
            return False
    except Exception as e:
        print(f"❌ Connected devices check failed: {e}")
        return False
    
    return True

def check_audio_routing():
    """Check where audio is being routed"""
    print("\n🎵 Checking Audio Routing")
    print("=" * 30)
    
    # Check PulseAudio sinks (Bluetooth usually shows up here)
    try:
        result = subprocess.run(['pactl', 'list', 'short', 'sinks'], 
                              capture_output=True, text=True, timeout=5)
        print("Available audio outputs:")
        for line in result.stdout.strip().split('\n'):
            if line:
                print(f"   {line}")
                if 'bluez' in line.lower() or 'bluetooth' in line.lower():
                    print("   ✅ Bluetooth audio sink detected!")
    except Exception as e:
        print(f"❌ PulseAudio check failed: {e}")
        
        # Fallback: Check ALSA
        try:
            result = subprocess.run(['aplay', '-l'], 
                                  capture_output=True, text=True, timeout=5)
            print("ALSA devices:")
            print(result.stdout)
        except Exception as e2:
            print(f"❌ ALSA check also failed: {e2}")

def create_test_audio():
    """Create a simple test audio file"""
    print("\n🎧 Creating Test Audio File")
    print("=" * 35)
    
    test_file = "/tmp/bt_audio_test.wav"
    
    # Create a simple 440Hz tone using FFmpeg
    try:
        subprocess.run([
            'ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=2',
            '-ar', '44100', '-ac', '2', '-y', test_file
        ], check=True, capture_output=True)
        
        print(f"✅ Test audio created: {test_file}")
        return test_file
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create test audio: {e}")
        return None

def test_audio_playback_methods(test_file):
    """Test different audio playback methods with Bluetooth"""
    print("\n🔊 Testing Audio Playback Methods")
    print("=" * 40)
    
    methods = [
        # PulseAudio (most common for Bluetooth)
        ['paplay', test_file],
        
        # ALSA direct
        ['aplay', test_file],
        
        # FFplay
        ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet', test_file],
        
        # MPV
        ['mpv', '--really-quiet', test_file],
    ]
    
    working_methods = []
    
    for i, method in enumerate(methods, 1):
        try:
            print(f"\n🧪 Method {i}: {method[0]}")
            result = subprocess.run(method, check=True, timeout=10,
                                  capture_output=True)
            print(f"   ✅ SUCCESS - Did you hear the tone clearly?")
            working_methods.append(method[0])
        except FileNotFoundError:
            print(f"   ❌ {method[0]} not installed")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ {method[0]} failed: {e}")
        except subprocess.TimeoutExpired:
            print(f"   ⏱️ {method[0]} timed out")
    
    return working_methods

def simulate_audio_chat_pipeline():
    """Simulate the exact pipeline used in audio chat"""
    print("\n🎙️ Testing Audio Chat Pipeline")
    print("=" * 40)
    
    # Create a sample audio file similar to what laptop sends
    sample_file = "/tmp/chat_simulation.wav"
    
    try:
        # Create speech-like audio (multiple tones)
        subprocess.run([
            'ffmpeg', '-f', 'lavfi', 
            '-i', 'sine=frequency=200:duration=0.5,sine=frequency=400:duration=0.5,sine=frequency=600:duration=0.5',
            '-ar', '22050', '-ac', '1', '-y', sample_file
        ], check=True, capture_output=True)
        
        print(f"✅ Chat simulation audio created: {sample_file}")
        
        # Test with our Pi server's audio processing
        print("\n🔄 Testing Pi server audio processing...")
        
        # Method 1: Direct paplay (Bluetooth friendly)
        try:
            subprocess.run(['paplay', sample_file], check=True, timeout=5)
            print("✅ PulseAudio (paplay) - Should work best with Bluetooth")
        except Exception as e:
            print(f"❌ PulseAudio failed: {e}")
        
        # Method 2: ALSA (might not route to Bluetooth)  
        try:
            subprocess.run(['aplay', sample_file], check=True, timeout=5)
            print("⚠️ ALSA (aplay) - May not route to Bluetooth properly")
        except Exception as e:
            print(f"❌ ALSA failed: {e}")
            
        return sample_file
        
    except Exception as e:
        print(f"❌ Pipeline simulation failed: {e}")
        return None

def main():
    """Run complete Bluetooth audio diagnostic"""
    print("🎧 Pi Bluetooth Audio Diagnostic")
    print("=" * 50)
    print("This will help identify why audio chat has noise")
    print("while local Bluetooth audio works fine.")
    print()
    
    # Step 1: Check Bluetooth setup
    if not check_bluetooth_audio_setup():
        print("\n❌ Bluetooth setup issues detected!")
        print("   Make sure your Bluetooth speaker is connected")
        return
    
    # Step 2: Check audio routing
    check_audio_routing()
    
    # Step 3: Create and test with simple audio
    test_file = create_test_audio()
    if test_file:
        working_methods = test_audio_playback_methods(test_file)
        
        # Step 4: Test audio chat pipeline
        chat_file = simulate_audio_chat_pipeline()
        
        print("\n🎯 DIAGNOSIS RESULTS")
        print("=" * 30)
        
        if 'paplay' in working_methods:
            print("✅ PulseAudio works - This should be used for Bluetooth")
            print("   Recommendation: Update Pi server to use 'paplay' for Bluetooth")
        elif working_methods:
            print(f"⚠️ Working methods: {working_methods}")
            print("   May need audio routing configuration")
        else:
            print("❌ No working audio methods found")
            print("   Check Bluetooth speaker connection")
            
        print("\n💡 LIKELY ISSUE:")
        print("The Pi server is probably using ALSA (aplay) which")
        print("doesn't automatically route to Bluetooth speakers.")
        print("PulseAudio (paplay) handles Bluetooth routing properly.")
        
        # Cleanup
        for f in [test_file, chat_file]:
            if f and os.path.exists(f):
                os.remove(f)

if __name__ == "__main__":
    main()