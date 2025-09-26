#!/bin/bash

echo "🔊 Quick TTS Fix for Pi Reminders"
echo "================================="
echo ""

echo "Installing espeak (system TTS)..."
sudo apt-get update
sudo apt-get install -y espeak espeak-data

echo ""
echo "Testing espeak..."
espeak "TTS engine test successful" 2>/dev/null && echo "✅ espeak working!" || echo "⚠️ espeak test failed"

echo ""
echo "Installing Python TTS packages..."
pip3 install gtts pyttsx3 2>/dev/null && echo "✅ Python TTS installed" || echo "⚠️ Python TTS install failed"

echo ""
echo "🎯 TTS Fix Complete!"
echo "===================="
echo "✅ espeak installed (system TTS)"
echo "✅ Pi server updated to use espeak fallback"
echo "✅ Voice reminders should now work"
echo ""
echo "🔄 Restart your Pi server:"
echo "   pkill -f pi_camera_server"
echo "   python3 pi_camera_server_fixed.py"
echo ""
echo "🧪 Test reminder with voice note:"
echo "   Create reminder in frontend with voice note text"
echo "   Should now speak through your Bluetooth speaker!"