#!/usr/bin/env python3
"""
Audio Noise Diagnostic - Check what's causing noise in Bluetooth audio
"""

import subprocess
import tempfile
import os
import requests
from pathlib import Path

def test_bluetooth_audio_chain():
    """Test each step of the audio chain to isolate noise source"""
    print("🔍 AUDIO NOISE DIAGNOSTIC")
    print("=" * 40)
    
    # Step 1: Check what's actually being sent from laptop
    print("\n1️⃣ Testing laptop audio recording...")
    
    print("   📝 When you record in frontend, what format is being sent?")
    print("   💡 Check browser console for: 'Recording with format: ...'")
    
    # Step 2: Test Pi can play clean audio files
    print("\n2️⃣ Testing Pi can play clean audio...")
    
    test_commands = [
        "# Test 1: Can Pi play a simple test tone cleanly?",
        "speaker-test -t sine -f 440 -l 1 -s 1",
        "",
        "# Test 2: Can Pi play system sounds?", 
        "aplay /usr/share/sounds/alsa/Front_Left.wav 2>/dev/null || echo 'No system sounds'",
        "",
        "# Test 3: Create and play a clean test file",
        "ffmpeg -f lavfi -i 'sine=frequency=440:duration=2' -y /tmp/clean_test.wav 2>/dev/null",
        "aplay /tmp/clean_test.wav",
    ]
    
    for cmd in test_commands:
        if cmd.startswith("#") or cmd == "":
            print(f"   {cmd}")
        else:
            print(f"   Run on Pi: {cmd}")
    
    # Step 3: Check audio format conversion
    print(f"\n3️⃣ Checking audio format handling...")
    
    print("   🔍 The issue might be:")
    print("   • Frontend sending corrupted audio data")
    print("   • Audio format not compatible with Bluetooth")
    print("   • File corruption during transmission") 
    print("   • Bluetooth codec issues")
    
    # Step 4: Create a test file to send
    print(f"\n4️⃣ Creating test audio file...")
    
    return create_test_files()

def create_test_files():
    """Create various test audio files to isolate the issue"""
    test_files = {}
    
    try:
        # Create a simple WAV file (most compatible)
        print("   📁 Creating test WAV file...")
        wav_file = "test_clean_audio.wav"
        
        # Simple method - create a basic WAV header + sine wave data
        import wave
        import numpy as np
        
        # Generate 2 seconds of 440Hz sine wave
        sample_rate = 22050
        duration = 2
        frequency = 440
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        wave_data = np.sin(2 * np.pi * frequency * t)
        
        # Convert to 16-bit integers
        wave_data = (wave_data * 32767).astype(np.int16)
        
        # Write WAV file
        with wave.open(wav_file, 'w') as wav:
            wav.setnchannels(1)  # Mono
            wav.setsampwidth(2)  # 16-bit
            wav.setframerate(sample_rate)
            wav.writeframes(wave_data.tobytes())
        
        test_files['clean_wav'] = wav_file
        print(f"   ✅ Created clean WAV: {wav_file}")
        
        return test_files
        
    except ImportError:
        print("   ❌ numpy not available, creating simpler test")
        return create_simple_test()

def create_simple_test():
    """Create simple test without numpy"""
    print("   📁 Creating simple test file...")
    
    # Create a very basic text-to-speech test
    test_file = "simple_test.txt" 
    with open(test_file, 'w') as f:
        f.write("Testing audio transmission")
    
    print(f"   📝 Created: {test_file}")
    print(f"   💡 You can test this by sending it through the audio endpoint")
    
    return {'simple': test_file}

def test_pi_audio_directly(pi_ip="192.168.1.100"):
    """Test sending audio directly to Pi"""
    print(f"\n5️⃣ Testing direct Pi audio...")
    
    test_files = create_test_files()
    
    if 'clean_wav' in test_files:
        wav_file = test_files['clean_wav']
        print(f"   📤 Sending clean WAV to Pi: {wav_file}")
        
        try:
            with open(wav_file, 'rb') as f:
                files = {'file': ('clean_test.wav', f, 'audio/wav')}
                
                response = requests.post(
                    f"http://{pi_ip}:5000/assistant/audio_chat",
                    files=files,
                    timeout=10
                )
                
            if response.status_code == 200:
                print("   ✅ Clean WAV sent successfully!")
                print("   🎧 Did you hear a clean 440Hz tone or noise?")
                print("   💡 If noise: The issue is in Pi audio processing")
                print("   💡 If clean: The issue is in frontend audio recording")
            else:
                print(f"   ❌ Failed to send: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error sending: {e}")
        
        # Cleanup
        if os.path.exists(wav_file):
            os.remove(wav_file)

def main():
    """Run complete audio noise diagnostic"""
    test_bluetooth_audio_chain()
    
    print(f"\n💡 QUICK NOISE FIX ATTEMPTS:")
    print("=" * 35)
    
    print("\n🔧 Try these on Pi:")
    print("1. Check Bluetooth connection:")
    print("   bluetoothctl info [MAC_ADDRESS]")
    print("   # Look for 'Connected: yes' and audio codecs")
    
    print("\n2. Force audio quality settings:")
    print("   # Edit /etc/bluetooth/main.conf")  
    print("   # Add: Disable=Headset  (forces A2DP high quality)")
    print("   sudo systemctl restart bluetooth")
    
    print("\n3. Test with different audio players:")
    print("   echo 'Testing mpv...'")
    print("   mpv --audio-driver=pulse /path/to/audio/file")
    print("   echo 'Testing paplay...'") 
    print("   paplay /path/to/audio/file")
    
    print("\n4. Check for audio conflicts:")
    print("   sudo fuser -v /dev/snd/*  # See what's using audio")
    print("   pulseaudio --check -v     # Check PulseAudio status")
    
    print("\n🎯 MOST LIKELY CAUSES:")
    print("• Bluetooth codec mismatch (Pi trying to use low-quality codec)")
    print("• Audio format incompatibility (WebM/MP4 → Bluetooth issues)")
    print("• PulseAudio/ALSA conflict in audio routing")
    print("• Frontend sending corrupted audio data")
    
    print(f"\n📞 NEXT STEP:")
    print("Run this diagnostic script, then tell me:")
    print("1. Can Pi play clean tones (speaker-test)?") 
    print("2. Does the clean WAV test produce noise or clear audio?")
    print("3. What audio format does frontend show in browser console?")

if __name__ == "__main__":
    main()