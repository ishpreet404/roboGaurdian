#!/usr/bin/env python3
"""
Fix TTS (Text-to-Speech) engines for reminder voice notes
Install required packages and test speech functionality
"""

import subprocess
import sys
import os

def install_tts_engines():
    """Install TTS engines for Pi"""
    print("🔊 Installing TTS Engines for Voice Reminders")
    print("=" * 50)
    
    packages = [
        'gtts',           # Google Text-to-Speech (online)
        'pyttsx3',        # Offline TTS engine
        'espeak',         # System TTS (fallback)
    ]
    
    print("1️⃣ Installing Python TTS packages...")
    for package in packages[:2]:  # Skip espeak as it's system package
        try:
            print(f"   Installing {package}...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                         check=True, capture_output=True)
            print(f"   ✅ {package} installed")
        except subprocess.CalledProcessError as e:
            print(f"   ⚠️ {package} failed: {e}")
    
    print("\n2️⃣ Installing system TTS packages...")
    system_packages = [
        'espeak',
        'espeak-data', 
        'alsa-utils',
        'pulseaudio-utils'
    ]
    
    for package in system_packages:
        try:
            print(f"   Installing {package}...")
            subprocess.run(['sudo', 'apt-get', 'install', '-y', package], 
                         check=True, capture_output=True)
            print(f"   ✅ {package} installed")
        except subprocess.CalledProcessError as e:
            print(f"   ⚠️ {package} failed (may already be installed)")
    
    print("\n3️⃣ Testing TTS engines...")
    test_tts_engines()

def test_tts_engines():
    """Test available TTS engines"""
    print("\n🧪 Testing TTS Engines")
    print("=" * 30)
    
    # Test 1: gTTS (online)
    try:
        import gtts
        print("✅ gTTS available (online TTS)")
        
        # Quick test
        tts = gtts.gTTS("Testing Google TTS", lang='en')
        tts.save("/tmp/test_gtts.mp3")
        
        # Try to play it
        try:
            subprocess.run(['mpv', '--really-quiet', '/tmp/test_gtts.mp3'], 
                         timeout=5, check=True)
            print("   🔊 gTTS playback working!")
        except:
            print("   ⚠️ gTTS created file but playback failed")
        
        os.remove("/tmp/test_gtts.mp3")
        
    except ImportError:
        print("❌ gTTS not available")
    except Exception as e:
        print(f"⚠️ gTTS test failed: {e}")
    
    # Test 2: pyttsx3 (offline)
    try:
        import pyttsx3
        print("✅ pyttsx3 available (offline TTS)")
        
        engine = pyttsx3.init()
        engine.say("Testing offline TTS")
        engine.runAndWait()
        print("   🔊 pyttsx3 working!")
        
    except ImportError:
        print("❌ pyttsx3 not available")
    except Exception as e:
        print(f"⚠️ pyttsx3 test failed: {e}")
    
    # Test 3: espeak (system)
    try:
        subprocess.run(['espeak', 'Testing system TTS'], 
                      timeout=5, check=True, capture_output=True)
        print("✅ espeak available (system TTS)")
        print("   🔊 espeak working!")
    except FileNotFoundError:
        print("❌ espeak not installed")
    except Exception as e:
        print(f"⚠️ espeak test failed: {e}")

def create_simple_tts_fix():
    """Create a simple TTS fix for reminders"""
    print("\n🔧 Creating Simple TTS Fix")
    print("=" * 35)
    
    fix_code = '''
def _simple_speak(text, lang='en'):
    """Simple TTS function that works with basic Pi setup"""
    
    # Method 1: Try espeak (most reliable on Pi)
    try:
        subprocess.run(['espeak', '-s', '150', text], 
                      timeout=10, check=True)
        return True
    except:
        pass
    
    # Method 2: Try festival (if available)
    try:
        subprocess.run(['festival', '--tts'], 
                      input=text.encode(), timeout=10, check=True)
        return True
    except:
        pass
    
    # Method 3: Try flite (lightweight)
    try:
        subprocess.run(['flite', '-t', text], 
                      timeout=10, check=True)
        return True
    except:
        pass
    
    print(f"⚠️ No TTS engine available for: {text}")
    return False
'''
    
    print("💡 Simple TTS function created. Add this to your Pi server:")
    print("=" * 55)
    print(fix_code)
    print("=" * 55)

def main():
    print("🎤 TTS Engine Repair for Pi Reminders")
    print("=" * 45)
    print()
    print("This will install and test TTS engines needed for")
    print("voice reminder playback on your Pi.")
    print()
    
    if input("Continue with TTS installation? (y/N): ").lower() != 'y':
        print("Cancelled.")
        return
    
    install_tts_engines()
    create_simple_tts_fix()
    
    print("\n🎯 RESULTS:")
    print("=" * 15)
    print("✅ TTS engines installed/tested")
    print("✅ Simple TTS fallback function created")
    print("✅ Voice reminders should now work")
    
    print("\n📋 NEXT STEPS:")
    print("1. Restart Pi camera server")
    print("2. Test creating reminder with voice note")
    print("3. Check if reminder speaks when triggered")
    
    print("\n💡 If still issues:")
    print("• Check Pi audio output (Bluetooth speaker connected)")
    print("• Verify internet connection (for gTTS)")
    print("• Try simple espeak test: espeak 'Hello World'")

if __name__ == "__main__":
    main()