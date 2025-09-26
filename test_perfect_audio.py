#!/usr/bin/env python3
"""
Test clean audio file transmission to isolate noise source
"""

import requests
import wave
import numpy as np
import tempfile
import os

def create_perfect_test_audio():
    """Create a mathematically perfect test audio file"""
    print("🎵 Creating perfect test audio...")
    
    # Parameters for clean audio
    sample_rate = 22050  # Pi-friendly sample rate
    duration = 3  # 3 seconds
    frequency = 440  # A4 note (clear, recognizable frequency)
    
    # Generate perfect sine wave
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # Create a pleasant chord (440Hz + 880Hz)
    wave_440 = 0.3 * np.sin(2 * np.pi * frequency * t)
    wave_880 = 0.2 * np.sin(2 * np.pi * frequency * 2 * t)
    wave_data = wave_440 + wave_880
    
    # Apply smooth fade in/out to avoid clicks
    fade_samples = int(0.1 * sample_rate)  # 0.1 second fade
    fade_in = np.linspace(0, 1, fade_samples)
    fade_out = np.linspace(1, 0, fade_samples)
    
    wave_data[:fade_samples] *= fade_in
    wave_data[-fade_samples:] *= fade_out
    
    # Convert to 16-bit integers (standard format)
    wave_data = (wave_data * 32767 * 0.8).astype(np.int16)  # 80% volume to avoid clipping
    
    # Save as WAV
    temp_file = "perfect_test_audio.wav"
    with wave.open(temp_file, 'w') as wav:
        wav.setnchannels(1)  # Mono
        wav.setsampwidth(2)  # 16-bit
        wav.setframerate(sample_rate)
        wav.writeframes(wave_data.tobytes())
    
    print(f"✅ Created perfect audio: {temp_file}")
    print(f"   📊 Format: 16-bit mono WAV, {sample_rate}Hz")
    print(f"   🎼 Content: 440Hz + 880Hz chord with smooth fades")
    
    return temp_file

def test_perfect_audio_to_pi(pi_ip="192.168.1.100"):
    """Send mathematically perfect audio to Pi"""
    print(f"\n📡 Testing perfect audio → Pi Bluetooth")
    print("=" * 45)
    
    try:
        # Create perfect test file
        test_file = create_perfect_test_audio()
        
        # Send via Windows supervisor (matching frontend path)
        print("\n1️⃣ Testing via Windows supervisor...")
        try:
            with open(test_file, 'rb') as f:
                files = {'audio': ('perfect_test.wav', f, 'audio/wav')}
                
                response = requests.post(
                    "http://localhost:5050/api/assistant/audio-chat",
                    files=files,
                    timeout=10
                )
                
            if response.status_code == 200:
                print("✅ Perfect audio sent via supervisor!")
                result = response.json()
                print(f"   📦 Sent {result.get('file_size', 'unknown')} bytes")
            else:
                print(f"❌ Supervisor failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Supervisor error: {e}")
        
        # Send directly to Pi
        print(f"\n2️⃣ Testing direct to Pi ({pi_ip})...")
        try:
            with open(test_file, 'rb') as f:
                files = {'file': ('perfect_test.wav', f, 'audio/wav')}
                
                response = requests.post(
                    f"http://{pi_ip}:5000/assistant/audio_chat",
                    files=files,
                    timeout=10
                )
                
            if response.status_code == 200:
                print("✅ Perfect audio sent directly to Pi!")
                result = response.json()
                print(f"   📦 Sent {result.get('file_size', 'unknown')} bytes")
            else:
                print(f"❌ Direct Pi failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Direct Pi error: {e}")
        
        print(f"\n🎧 LISTEN CAREFULLY:")
        print("=" * 25)
        print("You should hear a pleasant, clean musical chord (440Hz + 880Hz)")
        print("with smooth fade in/out - NO noise, clicks, or distortion")
        print("")
        print("📊 DIAGNOSIS:")
        print("✅ If you hear CLEAN audio: The issue is frontend recording")
        print("❌ If you hear NOISE: The issue is Pi → Bluetooth pipeline")
        print("🔇 If you hear NOTHING: Check Bluetooth connection")
        
    except ImportError:
        print("❌ numpy not available, using simpler test")
        test_simple_audio_to_pi(pi_ip)
    
    finally:
        # Cleanup
        if 'test_file' in locals() and os.path.exists(test_file):
            os.remove(test_file)

def test_simple_audio_to_pi(pi_ip):
    """Fallback test without numpy"""
    print("🔊 Creating simple beep test...")
    
    # Use system tools to create test audio
    try:
        import subprocess
        
        # Create simple test tone
        subprocess.run([
            'ffmpeg', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=2',
            '-ar', '22050', '-ac', '1', '-y', 'simple_test.wav'
        ], check=True, capture_output=True)
        
        print("✅ Created simple test tone")
        
        # Send to Pi
        with open('simple_test.wav', 'rb') as f:
            files = {'file': ('simple_test.wav', f, 'audio/wav')}
            response = requests.post(f"http://{pi_ip}:5000/assistant/audio_chat", files=files, timeout=10)
        
        if response.status_code == 200:
            print("✅ Simple test sent to Pi")
        else:
            print(f"❌ Failed: {response.status_code}")
            
        os.remove('simple_test.wav')
        
    except Exception as e:
        print(f"❌ Simple test failed: {e}")

def main():
    print("🧪 PERFECT AUDIO TEST - Isolate Noise Source")
    print("=" * 50)
    
    print("This sends mathematically perfect, clean audio to your Pi.")
    print("It will help us determine if noise comes from:")
    print("• Frontend audio recording (microphone/browser issues)")  
    print("• Pi → Bluetooth pipeline (codec/routing issues)")
    print()
    
    pi_ip = input("Enter Pi IP (or press Enter for 192.168.1.100): ").strip()
    if not pi_ip:
        pi_ip = "192.168.1.100"
    
    test_perfect_audio_to_pi(pi_ip)
    
    print(f"\n💡 NEXT STEPS based on what you heard:")
    print("=" * 45)
    print("🔵 CLEAN AUDIO heard:")
    print("   → Problem is frontend recording (mic/browser)")
    print("   → Need to fix audio recording in browser")
    print("")
    print("🔴 NOISE/DISTORTION heard:")
    print("   → Problem is Pi → Bluetooth pipeline")  
    print("   → Run: chmod +x fix_bluetooth_codec.sh && ./fix_bluetooth_codec.sh")
    print("")
    print("⚫ NO AUDIO heard:")
    print("   → Bluetooth connection or Pi audio routing issue")
    print("   → Check: bluetoothctl info [MAC_ADDRESS]")

if __name__ == "__main__":
    main()