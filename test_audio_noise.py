#!/usr/bin/env python3
"""
Quick Audio Noise Fix Test
Test different audio configurations to eliminate noise
"""

import subprocess
import tempfile
import os
import time

def test_audio_with_settings():
    """Test audio with different pygame/ALSA settings"""
    
    print("🎵 Testing Audio Noise Fixes")
    print("=" * 40)
    
    # First, let's test if the issue is with the audio system itself
    print("1️⃣ Testing system audio with clean tone...")
    
    try:
        # Generate a clean 1-second tone
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            test_wav = tmp.name
        
        # Create clean test tone
        subprocess.run([
            'ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=1',
            '-ar', '22050', '-ac', '1', '-sample_fmt', 's16', '-y', test_wav
        ], check=True, capture_output=True)
        
        print("   ✅ Clean test tone generated")
        
        # Test with aplay
        print("   🔊 Testing with aplay...")
        result = subprocess.run(['aplay', '-q', test_wav], capture_output=True)
        if result.returncode == 0:
            print("   ✅ aplay: Success (did you hear a clean tone?)")
        else:
            print("   ❌ aplay: Failed")
        
        # Test with pygame
        print("   🎮 Testing with pygame...")
        try:
            import pygame
            
            # Test with default settings
            pygame.mixer.init()
            pygame.mixer.music.load(test_wav)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            pygame.mixer.quit()
            print("   ❓ pygame (default): Played (was there noise?)")
            
            time.sleep(0.5)  # Brief pause
            
            # Test with optimized settings
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=1, buffer=1024)
            pygame.mixer.init()
            pygame.mixer.music.load(test_wav)
            pygame.mixer.music.set_volume(0.8)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            pygame.mixer.quit()
            print("   ✅ pygame (optimized): Played (less noise?)")
            
        except ImportError:
            print("   ❌ pygame not available")
        except Exception as e:
            print(f"   ❌ pygame error: {e}")
        
        # Cleanup
        os.unlink(test_wav)
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
    
    print("\n2️⃣ Audio system diagnosis...")
    
    # Check for common audio issues
    try:
        # Check if pulseaudio is running (can cause conflicts)
        result = subprocess.run(['pgrep', 'pulseaudio'], capture_output=True)
        if result.returncode == 0:
            print("   ⚠️ PulseAudio detected - may cause conflicts with direct ALSA")
            print("      Consider: pulseaudio --kill")
        else:
            print("   ✅ No PulseAudio conflicts")
    except:
        pass
    
    # Check audio card configuration
    try:
        result = subprocess.run(['cat', '/proc/asound/card0/pcm0p/info'], capture_output=True, text=True)
        if result.returncode == 0:
            print("   📱 Audio card info:")
            for line in result.stdout.split('\n')[:3]:
                if line.strip():
                    print(f"      {line.strip()}")
    except:
        pass
    
    print("\n💡 If you still hear noise, try these fixes on your Pi:")
    print("=" * 50)
    print("1. Force specific ALSA settings:")
    print("   sudo nano /etc/asound.conf")
    print("   Add:")
    print("   pcm.!default {")
    print("       type hw")
    print("       card 0")
    print("       device 0")
    print("       rate 22050")
    print("       format S16_LE")
    print("   }")
    print("")
    print("2. Disable PulseAudio (if present):")
    print("   pulseaudio --kill")
    print("   sudo systemctl --global disable pulseaudio.service")
    print("")
    print("3. Update Pi audio firmware:")
    print("   sudo rpi-update")
    print("")
    print("4. Test with volume adjustment:")
    print("   amixer set Master 70%")
    print("")
    print("5. Check for electromagnetic interference:")
    print("   - Move Pi away from power supplies/WiFi routers")
    print("   - Use shielded audio cables")
    print("   - Try a USB audio adapter instead of built-in audio")

def main():
    test_audio_with_settings()

if __name__ == "__main__":
    main()