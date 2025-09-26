#!/bin/bash

echo "🔧 Pi Audio Setup Script"
echo "========================"
echo ""

echo "📋 Checking audio tools..."

# Check for ffmpeg
if command -v ffmpeg &> /dev/null; then
    echo "✅ FFmpeg is installed"
    ffmpeg_version=$(ffmpeg -version 2>/dev/null | head -n1)
    echo "   Version: $ffmpeg_version"
else
    echo "❌ FFmpeg not found"
    echo "   Installing FFmpeg..."
    sudo apt update -qq
    sudo apt install -y ffmpeg
    if command -v ffmpeg &> /dev/null; then
        echo "✅ FFmpeg installed successfully"
    else
        echo "❌ FFmpeg installation failed"
    fi
fi

# Check for alsa-utils (aplay)
if command -v aplay &> /dev/null; then
    echo "✅ ALSA (aplay) is installed"
else
    echo "❌ ALSA (aplay) not found"
    echo "   Installing ALSA utilities..."
    sudo apt install -y alsa-utils
    if command -v aplay &> /dev/null; then
        echo "✅ ALSA installed successfully"
    else
        echo "❌ ALSA installation failed"
    fi
fi

# Check for mpv (optional)
if command -v mpv &> /dev/null; then
    echo "✅ MPV player is installed"
else
    echo "⚠️ MPV player not found (optional)"
    echo "   To install: sudo apt install -y mpv"
fi

echo ""
echo "🔊 Testing audio output..."

# Test if audio device is available
if aplay -l &> /dev/null; then
    echo "✅ Audio devices found:"
    aplay -l | grep "card\|device" | head -3
    
    # Test audio output with a beep
    echo ""
    echo "🎵 Testing speaker output (you should hear a beep)..."
    speaker-test -t sine -f 1000 -l 1 -s 1 &> /dev/null
    if [ $? -eq 0 ]; then
        echo "✅ Audio output test successful!"
    else
        echo "⚠️ Audio output test failed - check speaker connection"
    fi
else
    echo "❌ No audio devices found"
    echo "   Check if speakers are connected and enabled"
fi

echo ""
echo "📁 Audio format compatibility test..."

# Create temporary test files
temp_dir=$(mktemp -d)

# Test WAV support
echo "RIFF....WAVEfmt ................data...." > "$temp_dir/test.wav"
if aplay -q "$temp_dir/test.wav" 2>/dev/null; then
    echo "✅ WAV format: Supported by aplay"
else
    echo "⚠️ WAV format: Issues with aplay"
fi

# Test ffmpeg format support
if command -v ffmpeg &> /dev/null; then
    echo "✅ WebM/MP4 formats: Supported via FFmpeg"
else
    echo "❌ WebM/MP4 formats: FFmpeg required"
fi

# Cleanup
rm -rf "$temp_dir"

echo ""
echo "🎯 Audio Chat Setup Status:"
echo "=========================="

all_good=true

if ! command -v ffmpeg &> /dev/null; then
    echo "❌ FFmpeg missing - WebM/MP4 audio won't work"
    all_good=false
fi

if ! command -v aplay &> /dev/null; then
    echo "❌ ALSA missing - WAV audio won't work"
    all_good=false
fi

if ! aplay -l &> /dev/null; then
    echo "❌ No audio devices - check speaker connection"
    all_good=false
fi

if [ "$all_good" = true ]; then
    echo "✅ Audio chat should work perfectly!"
    echo ""
    echo "💡 Usage tips:"
    echo "   • Record audio in the web interface"
    echo "   • Audio will be auto-converted to WAV format"
    echo "   • FFmpeg handles WebM/MP4, aplay handles WAV"
    echo "   • Check Pi server logs if audio has issues"
else
    echo "⚠️ Some issues found - audio chat may not work properly"
    echo ""
    echo "🔧 To fix:"
    echo "   sudo apt update"
    echo "   sudo apt install -y ffmpeg alsa-utils"
    echo "   # Then test: speaker-test -t sine -f 1000 -l 1"
fi

echo ""
echo "🔄 After fixing issues, restart the Pi server:"
echo "   pkill -f pi_camera_server"
echo "   python3 pi_camera_server.py"