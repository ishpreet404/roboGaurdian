@echo off
echo 🤖 Robot Guardian - Enhanced Setup
echo ========================================
echo.
echo Installing required packages...
echo.

REM Install core packages first
pip install opencv-python ultralytics requests pillow numpy

REM Install new packages for enhanced features
pip install flask mediapipe sounddevice soundfile pygame scipy

REM Optional PyTorch for better AI performance
echo.
echo Installing PyTorch (optional, for better AI performance)...
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

echo.
echo ✅ Installation complete!
echo.
echo 📋 Features available:
echo   - YOLO AI person detection
echo   - Automatic robot following
echo   - 😢 Crying/Distress detection
echo   - 🌐 Internet video streaming
echo   - 🔊 Audio alerts
echo.
echo 🚀 Run with: python windows_ai_controller.py
echo.
pause