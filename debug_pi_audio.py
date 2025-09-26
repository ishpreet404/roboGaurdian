#!/usr/bin/env python3
"""
Audio Noise Diagnostic Tool
Debug audio playback issues on Pi
"""

import subprocess
import tempfile
import os
import logging
from pathlib import Path

def test_audio_playback(file_path, method):
    """Test a specific audio playback method"""
    try:
        if method == 'aplay':
            result = subprocess.run(['aplay', '-v', file_path], 
                                  capture_output=True, text=True, timeout=10)
        elif method == 'ffplay':
            result = subprocess.run(['ffplay', '-nodisp', '-autoexit', '-v', 'info', file_path],
                                  capture_output=True, text=True, timeout=10)
        elif method == 'mpv':
            result = subprocess.run(['mpv', '--msg-level=all=info', file_path],
                                  capture_output=True, text=True, timeout=10)
        elif method == 'pygame':
            # Test pygame mixer
            import pygame
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=1024)
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            import time
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            pygame.mixer.quit()
            return True, "Pygame playback completed"
        
        return result.returncode == 0, f"stdout: {result.stdout[:200]}\nstderr: {result.stderr[:200]}"
    except Exception as e:
        return False, str(e)

def create_test_audio():
    """Create proper test audio files"""
    test_files = {}
    
    # Create a proper WAV file with sine wave
    try:
        # Generate 1 second of 1000Hz tone
        wav_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        subprocess.run([
            'ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=1000:duration=1',
            '-ar', '22050', '-ac', '1', '-y', wav_file.name
        ], check=True, capture_output=True)
        test_files['clean_wav'] = wav_file.name
        print(f"✅ Created clean WAV test file: {wav_file.name}")
    except Exception as e:
        print(f"❌ Could not create clean WAV: {e}")
    
    return test_files

def check_audio_system():
    """Check the audio system configuration"""
    print("🔊 Audio System Diagnostic")
    print("=" * 50)
    
    # Check audio cards
    try:
        result = subprocess.run(['aplay', '-l'], capture_output=True, text=True)
        if result.returncode == 0:
            print("📱 Audio devices:")
            for line in result.stdout.split('\n'):
                if 'card' in line.lower() or 'device' in line.lower():
                    print(f"   {line.strip()}")
        else:
            print("❌ No audio devices found")
    except Exception as e:
        print(f"❌ Error checking audio devices: {e}")
    
    # Check ALSA configuration
    print("\n🎛️ ALSA Configuration:")
    try:
        result = subprocess.run(['cat', '/proc/asound/cards'], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            print("   Cards in /proc/asound/cards:")
            for line in result.stdout.split('\n'):
                if line.strip():
                    print(f"   {line.strip()}")
        else:
            print("   ❌ No cards in /proc/asound/cards")
    except:
        print("   ❌ Could not read /proc/asound/cards")
    
    # Check volume levels
    try:
        result = subprocess.run(['amixer', 'get', 'Master'], capture_output=True, text=True)
        if result.returncode == 0:
            print("🔉 Volume levels:")
            for line in result.stdout.split('\n'):
                if '%' in line or 'Mono:' in line or 'Front Left:' in line:
                    print(f"   {line.strip()}")
    except Exception as e:
        print(f"❌ Could not check volume: {e}")

def main():
    print("🎤 Audio Noise Diagnostic Tool")
    print("=" * 40)
    
    # Check audio system
    check_audio_system()
    
    # Create test files
    print(f"\n🎵 Creating test audio files...")
    test_files = create_test_audio()
    
    if not test_files:
        print("❌ Could not create test files. Install ffmpeg first:")
        print("   sudo apt install -y ffmpeg")
        return
    
    # Test playback methods
    print(f"\n🔊 Testing playback methods...")
    
    methods = ['aplay', 'ffplay', 'mpv']
    
    for method in methods:
        print(f"\n🎶 Testing {method}:")
        for file_type, file_path in test_files.items():
            success, details = test_audio_playback(file_path, method)
            status = "✅" if success else "❌"
            print(f"   {status} {file_type}: {details[:100]}")
    
    # Test pygame separately
    try:
        print(f"\n🎮 Testing pygame mixer:")
        for file_type, file_path in test_files.items():
            success, details = test_audio_playback(file_path, 'pygame')
            status = "✅" if success else "❌"
            print(f"   {status} {file_type}: {details}")
    except ImportError:
        print("   ⚠️ pygame not available")
    
    # Cleanup
    for file_path in test_files.values():
        try:
            os.unlink(file_path)
        except:
            pass
    
    print(f"\n💡 Troubleshooting Audio Noise:")
    print("================================")
    print("1. Check if audio device supports the sample rate:")
    print("   aplay -D hw:0,0 --dump-hw-params /dev/null")
    print("")
    print("2. Force specific audio format:")
    print("   aplay -D hw:0,0 -r 22050 -f S16_LE -c 1 your_file.wav")
    print("")
    print("3. Check for audio conflicts:")
    print("   sudo lsof /dev/snd/*")
    print("")
    print("4. Test with minimal settings:")
    print("   pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)")
    print("")
    print("5. Enable ALSA debug:")
    print("   export ALSA_DEBUG=1")
    print("   aplay your_file.wav")

if __name__ == "__main__":
    main()