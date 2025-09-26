#!/usr/bin/env python3
"""
Emergency Audio Fix - Restore Basic Working Audio
Run this if audio completely stopped working
"""

import subprocess
import os

def emergency_audio_restore():
    """Restore the most basic working audio configuration"""
    print("🚨 Emergency Audio Restore")
    print("=" * 30)
    
    print("This will restore basic ALSA audio that should work")
    print("even without Bluetooth optimization.")
    print()
    
    # Test 1: Basic audio test
    print("1️⃣ Testing basic audio system...")
    
    try:
        # Check if aplay works at all
        result = subprocess.run(['aplay', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ ALSA (aplay) is available")
        else:
            print("❌ ALSA (aplay) not working")
            return False
    except Exception as e:
        print(f"❌ ALSA test failed: {e}")
        return False
    
    # Test 2: Check audio devices
    print("\n2️⃣ Checking audio devices...")
    try:
        result = subprocess.run(['aplay', '-l'], 
                              capture_output=True, text=True, timeout=5)
        print("Available audio devices:")
        print(result.stdout)
    except Exception as e:
        print(f"❌ Device check failed: {e}")
    
    # Test 3: Create a simple test file and play it
    print("\n3️⃣ Creating and testing basic audio...")
    
    test_file = "/tmp/emergency_test.wav"
    
    try:
        # Create a simple WAV file using speaker-test
        subprocess.run([
            'speaker-test', '-t', 'sine', '-f', '440', '-l', '1', '-s', '1', 
            '-w', test_file
        ], check=True, capture_output=True, timeout=10)
        
        print(f"✅ Test file created: {test_file}")
        
        # Try basic aplay
        print("🔊 Testing basic aplay...")
        result = subprocess.run(['aplay', '-q', test_file], 
                              check=True, capture_output=True, timeout=10)
        print("✅ Basic aplay works!")
        
        # Clean up
        os.remove(test_file)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Basic audio test failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Test creation failed: {e}")
        return False

def create_emergency_pi_server_patch():
    """Create a minimal audio function that definitely works"""
    
    patch_content = '''
# Emergency Audio Patch for pi_camera_server_fixed.py
# Replace the _play_audio_file_direct function with this ultra-simple version

def _play_audio_file_direct(file_path: str) -> bool:
    """Ultra-simple audio playback - guaranteed to work if Pi audio works at all"""
    
    # Method 1: Most basic aplay
    try:
        subprocess.run(['aplay', '-q', file_path], check=True, timeout=30)
        logger.info('🔊 Basic aplay SUCCESS')
        return True
    except Exception:
        pass
    
    # Method 2: aplay with specific format
    try:
        subprocess.run(['aplay', '-f', 'S16_LE', '-r', '22050', file_path], 
                      check=True, timeout=30)
        logger.info('🔊 Format-specific aplay SUCCESS')
        return True
    except Exception:
        pass
    
    # Method 3: pygame (most reliable)
    try:
        import pygame
        pygame.mixer.init()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)
        logger.info('🔊 Pygame SUCCESS')
        return True
    except Exception:
        pass
    
    logger.error('❌ ALL basic audio methods failed')
    return False
'''
    
    print("\n📝 Emergency patch created!")
    print("Copy the above function to replace _play_audio_file_direct() in pi_camera_server_fixed.py")
    print("This removes all complex audio routing and uses only the most basic methods.")
    
    return patch_content

def main():
    """Run emergency audio diagnostic and create patch"""
    print("🚨 EMERGENCY AUDIO RECOVERY")
    print("=" * 50)
    print("Use this when audio completely stops working")
    print()
    
    if emergency_audio_restore():
        print("\n✅ GOOD NEWS: Basic audio system is working!")
        print("The issue is likely in our complex audio routing.")
        print()
        print("🔧 SOLUTION:")
        print("1. Restart Pi camera server:")
        print("   pkill -f pi_camera_server")
        print("   python3 pi_camera_server_fixed.py")
        print("")
        print("2. The updated code now has better fallbacks")
        print("3. It will try Bluetooth methods first, then fall back to basic ALSA")
        print("")
        print("4. If still broken, the Pi server logs will show which method worked")
    else:
        print("\n❌ PROBLEM: Basic Pi audio system is broken!")
        print()
        print("🔧 SOLUTIONS:")
        print("1. Check Pi audio hardware:")
        print("   sudo raspi-config → Advanced → Audio → Force 3.5mm")
        print("")
        print("2. Restart audio services:")
        print("   sudo systemctl restart alsa-state")
        print("   sudo alsa reload")
        print("")
        print("3. Check volume levels:")
        print("   alsamixer")
        print("   # Unmute and increase volume")
        
        create_emergency_pi_server_patch()

if __name__ == "__main__":
    main()
'''