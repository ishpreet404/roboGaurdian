#!/usr/bin/env python3
"""
Emergency Audio Restore - Simple Working Version
This restores the most basic audio playback that should definitely work
"""

import os
import sys

def create_simple_audio_function():
    """Create the simplest possible working audio function"""
    
    simple_function = '''
def _play_audio_file_direct(file_path: str) -> bool:
    """EMERGENCY: Ultra-simple audio playback"""
    import subprocess
    import logging
    from pathlib import Path
    
    logger = logging.getLogger(__name__)
    extension = Path(file_path).suffix.lower()
    
    # Just try the most basic methods that definitely work
    commands = [
        # Method 1: Basic aplay (should work for WAV)
        ['aplay', file_path],
        
        # Method 2: MPV (most reliable)
        ['mpv', '--really-quiet', '--no-video', file_path],
        
        # Method 3: FFplay (very reliable)
        ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet', file_path],
        
        # Method 4: Python pygame as last resort
        ['python3', '-c', f"""
import pygame, time
pygame.mixer.init()
pygame.mixer.music.load('{file_path}')
pygame.mixer.music.play()
while pygame.mixer.music.get_busy(): time.sleep(0.1)
"""],
    ]
    
    for i, cmd in enumerate(commands, 1):
        try:
            logger.info(f'🎵 Trying method {i}: {cmd[0]}')
            subprocess.run(cmd, check=True, timeout=30, 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logger.info(f'✅ Audio SUCCESS with {cmd[0]}')
            return True
        except Exception as e:
            logger.debug(f'Method {i} failed: {e}')
            continue
    
    logger.error('❌ All simple audio methods failed')
    return False
'''
    
    return simple_function

def main():
    print("🚨 EMERGENCY AUDIO RESTORE")
    print("=" * 30)
    print()
    print("Creating ultra-simple audio function...")
    print()
    
    simple_func = create_simple_audio_function()
    print("📋 EMERGENCY FIX:")
    print("Replace the _play_audio_file_direct function in pi_camera_server_fixed.py")
    print("with this ultra-simple version:")
    print()
    print("=" * 50)
    print(simple_func)
    print("=" * 50)
    print()
    print("🔧 QUICK MANUAL FIX:")
    print("1. Edit pi_camera_server_fixed.py")
    print("2. Find the _play_audio_file_direct function")
    print("3. Replace it with the simple version above")
    print("4. Restart Pi server: python3 pi_camera_server_fixed.py")
    print()
    print("This removes all the complex Bluetooth logic and uses")
    print("just the most basic audio methods that should work.")

if __name__ == "__main__":
    main()