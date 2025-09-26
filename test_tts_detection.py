#!/usr/bin/env python3
"""
Test TTS detection and functionality on Pi
"""

import subprocess
import sys
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_tts_detection():
    """Test TTS engine detection like Pi server does"""
    print("🧪 TTS Detection Test")
    print("=" * 25)
    
    # Test 1: gTTS
    use_gtts = False
    try:
        import gtts
        use_gtts = True
        print("✅ gTTS: Available")
    except ImportError:
        print("❌ gTTS: Not installed")
    
    # Test 2: pyttsx3
    pyttsx3_engine = None
    try:
        import pyttsx3
        pyttsx3_engine = pyttsx3.init()
        print("✅ pyttsx3: Available")
    except ImportError:
        print("❌ pyttsx3: Not installed")
    except Exception as e:
        print(f"⚠️ pyttsx3: Error - {e}")
    
    # Test 3: espeak (like Pi server does)
    use_espeak = False
    try:
        result = subprocess.run(['espeak', '--version'], check=True, capture_output=True)
        use_espeak = True
        print("✅ espeak: Available")
        print(f"   Version: {result.stdout.decode().strip()}")
    except FileNotFoundError:
        print("❌ espeak: Command not found")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ espeak: Version check failed - {e}")
    except Exception as e:
        print(f"⚠️ espeak: Detection error - {e}")
    
    print(f"\n📊 Summary:")
    print(f"   gTTS: {use_gtts}")
    print(f"   pyttsx3: {pyttsx3_engine is not None}")
    print(f"   espeak: {use_espeak}")
    
    # Final check (Pi server logic)
    if pyttsx3_engine is None and not use_gtts and not use_espeak:
        print("\n🔇 Result: No TTS engines available (Pi server would show warning)")
        return False
    else:
        print("\n✅ Result: TTS engines available (Pi server should work)")
        return True

def test_speech_engines():
    """Test actual speech functionality"""
    print(f"\n🔊 Speech Functionality Test")
    print("=" * 35)
    
    test_text = "TTS test successful"
    
    # Test espeak directly
    print("1️⃣ Testing espeak...")
    try:
        subprocess.run(['espeak', test_text], check=True, timeout=5)
        print("   ✅ espeak speech worked")
    except Exception as e:
        print(f"   ❌ espeak failed: {e}")
    
    # Test pyttsx3
    print("2️⃣ Testing pyttsx3...")
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.say(test_text)
        engine.runAndWait()
        print("   ✅ pyttsx3 speech worked")
    except Exception as e:
        print(f"   ❌ pyttsx3 failed: {e}")
    
    # Test gTTS (creates file, doesn't play)
    print("3️⃣ Testing gTTS...")
    try:
        import gtts
        tts = gtts.gTTS(test_text, lang='en')
        tts.save('/tmp/tts_test.mp3')
        print("   ✅ gTTS file creation worked")
        
        # Try to play it
        try:
            subprocess.run(['mpv', '--really-quiet', '/tmp/tts_test.mp3'], 
                          timeout=5, check=True)
            print("   ✅ gTTS playback worked")
        except:
            print("   ⚠️ gTTS created file but playback failed")
            
        import os
        os.remove('/tmp/tts_test.mp3')
    except Exception as e:
        print(f"   ❌ gTTS failed: {e}")

def main():
    """Run all TTS tests"""
    print("🎤 Pi TTS Engine Diagnostic")
    print("=" * 40)
    print("This tests TTS detection exactly like the Pi server does")
    print()
    
    # Detection test
    tts_available = test_tts_detection()
    
    if tts_available:
        test_speech_engines()
        print(f"\n🎯 CONCLUSION:")
        print("TTS engines are available. If Pi server shows 'No speech engine'")
        print("warning, it might be a timing or initialization issue.")
        print()
        print("💡 Try restarting Pi server:")
        print("   pkill -f pi_camera_server")
        print("   python3 pi_camera_server_fixed.py")
    else:
        print(f"\n🔧 NEXT STEPS:")
        print("Install TTS engines:")
        print("   sudo apt install espeak")
        print("   pip3 install gtts pyttsx3")

if __name__ == "__main__":
    main()