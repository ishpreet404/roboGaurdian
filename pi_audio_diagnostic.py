#!/usr/bin/env python3
"""
Audio Format Diagnostic for Pi Server
Test different audio formats and players on the Pi
"""

import subprocess
import tempfile
import os
from pathlib import Path

def test_audio_player(command, file_path):
    """Test if an audio player can handle a file"""
    try:
        result = subprocess.run(command + [file_path], 
                               capture_output=True, 
                               text=True, 
                               timeout=5,
                               check=True)
        return True, "OK"
    except FileNotFoundError:
        return False, "Player not found"
    except subprocess.CalledProcessError as e:
        return False, f"Player error: {e.stderr[:100]}"
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, f"Other error: {e}"

def main():
    print("🔊 Audio Format Diagnostic for Pi Server")
    print("=" * 50)
    
    # Test available audio players
    players = [
        (['aplay', '--version'], "ALSA aplay"),
        (['ffplay', '-version'], "FFmpeg ffplay"), 
        (['mpv', '--version'], "MPV player"),
        (['which', 'ffmpeg'], "FFmpeg converter"),
    ]
    
    print("\n📋 Available Audio Tools:")
    available_tools = {}
    for cmd, name in players:
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=3)
            if result.returncode == 0:
                print(f"   ✅ {name}: Available")
                available_tools[name] = True
            else:
                print(f"   ❌ {name}: Not working")
                available_tools[name] = False
        except:
            print(f"   ❌ {name}: Not found") 
            available_tools[name] = False
    
    # Create test audio files (fake data for format testing)
    print(f"\n🎵 Testing Audio Format Support:")
    
    test_formats = [
        ('test.wav', b'RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00'),  # Fake WAV header
        ('test.mp3', b'\xff\xfb\x90\x00'),  # Fake MP3 header  
        ('test.webm', b'\x1a\x45\xdf\xa3'),  # Fake WebM header
        ('test.ogg', b'OggS'),  # Fake OGG header
    ]
    
    for filename, fake_data in test_formats:
        print(f"\n🎶 Format: {Path(filename).suffix}")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix, delete=False) as tmp:
            tmp.write(fake_data + b'\x00' * 1000)  # Add some data
            tmp_path = tmp.name
        
        try:
            # Test different players
            test_commands = [
                (['aplay', '-q'], "aplay"),
                (['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet'], "ffplay"),  
                (['mpv', '--really-quiet'], "mpv"),
            ]
            
            for cmd_base, player_name in test_commands:
                if available_tools.get(f"FFmpeg {player_name}" if player_name == "ffplay" else player_name.upper() + " " + player_name if player_name == "aplay" else "MPV player", False):
                    success, message = test_audio_player(cmd_base, tmp_path)
                    status = "✅" if success else "❌"
                    print(f"   {status} {player_name}: {message}")
                else:
                    print(f"   ⏸️ {player_name}: Not available")
        
        finally:
            os.unlink(tmp_path)
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    if available_tools.get("FFmpeg ffplay", False):
        print("   ✅ FFmpeg available - should handle WebM, MP4, MP3, WAV")
    else:
        print("   ⚠️ FFmpeg not available - install with: sudo apt install ffmpeg")
    
    if available_tools.get("ALSA aplay", False):
        print("   ✅ ALSA available - handles WAV files well")
    else:
        print("   ⚠️ ALSA not available - install with: sudo apt install alsa-utils")
    
    print(f"\n🔧 Quick fixes:")
    print("   1. Install FFmpeg: sudo apt update && sudo apt install -y ffmpeg")
    print("   2. Install ALSA: sudo apt install -y alsa-utils")  
    print("   3. Test audio: speaker-test -t sine -f 1000 -l 1")
    print("   4. For WebM support, prefer FFmpeg over pygame")

if __name__ == "__main__":
    main()