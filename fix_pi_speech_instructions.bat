@echo off
REM Quick Pi Speech Fix - Copy this script to your Pi and run it

echo 🔊 Pi Speech Engine Fix Script
echo.
echo Copy this file to your Raspberry Pi and run:
echo   chmod +x fix_pi_speech.sh
echo   ./fix_pi_speech.sh
echo.
echo Or run these commands manually on the Pi:
echo.
echo   sudo apt update
echo   # Install multiple TTS engines for better quality
echo   sudo apt install -y espeak espeak-data alsa-utils festival festvox-hi-nsk
echo   sudo apt install -y speech-dispatcher speech-dispatcher-festival
echo   pip3 install pyttsx3 gTTS pygame
echo.
echo   # Test Hindi speech engines:
echo   echo "नमस्ते रोबोट" ^| espeak -v hi
echo   echo "Hello robot" ^| festival --tts
echo.
echo   # Test Python TTS with Hindi:
echo   python3 -c "import pyttsx3; e=pyttsx3.init(); voices=e.getProperty('voices'); print([v.id for v in voices]); e.say('Robot speech test'); e.runAndWait()"
echo.
echo After fixing, restart your Pi server:
echo   python3 pi_camera_server_fixed.py
echo.
pause