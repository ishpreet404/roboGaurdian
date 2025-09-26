#!/bin/bash
# Fix Pi Speech Engine - Install missing TTS dependencies

echo "🔊 Installing Pi Text-to-Speech Dependencies..."

# Update package list
sudo apt update

# Install multiple TTS engines for better quality
echo "📦 Installing text-to-speech engines..."
sudo apt install -y espeak espeak-data festival festvox-hi-nsk
sudo apt install -y speech-dispatcher speech-dispatcher-festival

# Install alsa audio utilities (if not present)
echo "🔉 Installing audio utilities..."
sudo apt install -y alsa-utils

# Install Python TTS packages
echo "🐍 Installing Python TTS packages..."
pip3 install pyttsx3 gTTS pygame

# Test audio setup
echo "🧪 Testing audio setup..."
speaker-test -t wav -c 2 -l 1 || echo "⚠️ Audio test failed - check speaker/headphone connection"

# Test text-to-speech engines
echo "🗣️ Testing text-to-speech engines..."
echo "Hello from Pi robot" | espeak
echo "नमस्ते रोबोट" | espeak -v hi
echo "Testing Festival TTS" | festival --tts

echo "✅ Pi speech setup complete!"
echo ""
echo "🔄 Now restart your Pi camera server:"
echo "   python3 pi_camera_server_fixed.py"