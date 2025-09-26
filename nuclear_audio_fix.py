#!/usr/bin/env python3
"""
Nuclear Audio Fix for Pi
Completely bypass problematic audio systems and force clean playback
"""

import subprocess
import os
import tempfile
import logging

logger = logging.getLogger(__name__)

def nuclear_audio_fix():
    """Apply aggressive fixes for Pi audio noise issues"""
    
    print("💥 Nuclear Audio Fix for Pi")
    print("=" * 40)
    
    fixes_applied = []
    
    # 1. Kill all conflicting audio processes
    print("1️⃣ Killing conflicting audio processes...")
    try:
        subprocess.run(['sudo', 'pkill', '-f', 'pulseaudio'], capture_output=True)
        subprocess.run(['sudo', 'pkill', '-f', 'pipewire'], capture_output=True)
        fixes_applied.append("✅ Killed conflicting audio daemons")
    except:
        fixes_applied.append("⚠️ Could not kill audio processes")
    
    # 2. Force ALSA to use specific settings
    print("2️⃣ Configuring ALSA for Pi...")
    alsa_config = """
pcm.!default {
    type hw
    card 0
    device 0
    rate 22050
    format S16_LE
    channels 1
}

ctl.!default {
    type hw
    card 0
}
"""
    
    try:
        with open('/tmp/asound.conf', 'w') as f:
            f.write(alsa_config)
        subprocess.run(['sudo', 'cp', '/tmp/asound.conf', '/etc/asound.conf'], check=True)
        fixes_applied.append("✅ Applied ALSA configuration")
    except Exception as e:
        fixes_applied.append(f"❌ ALSA config failed: {e}")
    
    # 3. Set optimal audio levels
    print("3️⃣ Setting optimal audio levels...")
    try:
        # Set master volume to 70% to avoid clipping
        subprocess.run(['amixer', 'set', 'Master', '70%'], check=True, capture_output=True)
        
        # Disable auto-mute if it exists
        subprocess.run(['amixer', 'set', 'Auto-Mute', 'Disabled'], capture_output=True)
        
        fixes_applied.append("✅ Set optimal volume levels")
    except Exception as e:
        fixes_applied.append(f"⚠️ Volume adjustment: {e}")
    
    # 4. Create a test conversion script
    print("4️⃣ Creating ultra-clean audio conversion...")
    
    conversion_script = '''#!/bin/bash
# Ultra-clean audio conversion for Pi
input_file="$1"
output_file="$2"

ffmpeg -i "$input_file" \\
    -acodec pcm_s16le \\
    -ar 22050 \\
    -ac 1 \\
    -af "highpass=f=100,lowpass=f=3000,volume=0.8,dynaudnorm" \\
    -sample_fmt s16 \\
    -y "$output_file" \\
    -loglevel error

# Test the output
if [ -f "$output_file" ]; then
    echo "Conversion successful"
    exit 0
else
    echo "Conversion failed"
    exit 1
fi
'''
    
    try:
        with open('/tmp/clean_audio_convert.sh', 'w') as f:
            f.write(conversion_script)
        subprocess.run(['chmod', '+x', '/tmp/clean_audio_convert.sh'], check=True)
        fixes_applied.append("✅ Created clean conversion script")
    except Exception as e:
        fixes_applied.append(f"❌ Conversion script failed: {e}")
    
    # 5. Test with the cleanest possible audio
    print("5️⃣ Testing with ultra-clean audio...")
    
    try:
        # Create the cleanest possible test tone
        test_file = '/tmp/ultra_clean_test.wav'
        subprocess.run([
            'ffmpeg', '-f', 'lavfi', 
            '-i', 'sine=frequency=440:duration=0.5',
            '-acodec', 'pcm_s16le',
            '-ar', '22050',
            '-ac', '1',
            '-af', 'volume=0.6',  # Very conservative volume
            '-y', test_file
        ], check=True, capture_output=True)
        
        # Test playback
        result = subprocess.run(['aplay', test_file], capture_output=True)
        if result.returncode == 0:
            fixes_applied.append("✅ Clean audio test successful")
        else:
            fixes_applied.append("❌ Clean audio test failed")
        
        os.unlink(test_file)
        
    except Exception as e:
        fixes_applied.append(f"❌ Audio test failed: {e}")
    
    # 6. Hardware-level fixes
    print("6️⃣ Applying hardware-level fixes...")
    
    # Check if we're on a Pi and apply Pi-specific fixes
    try:
        with open('/proc/cpuinfo', 'r') as f:
            if 'Raspberry Pi' in f.read():
                # Pi-specific audio fixes
                config_lines = [
                    'audio_pwm_mode=2',          # Use PWM audio mode 2
                    'disable_audio_dither=1',    # Disable audio dither
                    'audio_pwm_chan=1',          # Use single channel PWM
                ]
                
                # Check if config.txt exists and add lines
                config_path = '/boot/config.txt'
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        existing_config = f.read()
                    
                    new_lines = []
                    for line in config_lines:
                        if line.split('=')[0] not in existing_config:
                            new_lines.append(line)
                    
                    if new_lines:
                        with open('/tmp/config_addition.txt', 'w') as f:
                            f.write('\n# Audio noise fixes\n')
                            f.write('\n'.join(new_lines) + '\n')
                        
                        print("   Pi-specific config lines to add to /boot/config.txt:")
                        for line in new_lines:
                            print(f"     {line}")
                        
                        fixes_applied.append(f"✅ Pi hardware config ready ({len(new_lines)} lines)")
                    else:
                        fixes_applied.append("✅ Pi hardware already configured")
                
    except Exception as e:
        fixes_applied.append(f"⚠️ Hardware fixes: {e}")
    
    # Print results
    print("\n🎯 Nuclear Fix Results:")
    print("=" * 30)
    for fix in fixes_applied:
        print(f"   {fix}")
    
    # Final recommendations
    print(f"\n💣 If noise STILL persists:")
    print("=" * 35)
    print("1. USB Audio Adapter (Hardware solution):")
    print("   - Buy a cheap USB audio dongle (~$5)")
    print("   - Connect speakers to USB dongle instead of 3.5mm jack")
    print("   - USB audio bypasses Pi's noisy built-in DAC")
    print("")
    print("2. Disable Pi audio entirely and use USB:")
    print("   sudo nano /boot/config.txt")
    print("   # Comment out: dtparam=audio=on")
    print("   # Add: dtoverlay=disable-audio")
    print("")
    print("3. Use network audio streaming:")
    print("   - Install 'mpd' + 'mpc' for network audio")
    print("   - Stream audio over network instead of local playback")
    print("")
    print("4. The Pi 3.5mm audio jack is notoriously noisy!")
    print("   - This is a known hardware limitation")
    print("   - USB audio adapters are the definitive solution")

if __name__ == "__main__":
    nuclear_audio_fix()