@echo off
echo 🤖 Pi Server Update Script
echo ========================

REM Get Pi IP address
set /p PI_IP="Enter Pi IP address (default: 192.168.1.100): "
if "%PI_IP%"=="" set PI_IP=192.168.1.100

echo.
echo 📡 Updating Pi server at %PI_IP%...

REM Check if we have the fixed file
if not exist "pi_camera_server_fixed.py" (
    echo ❌ Error: pi_camera_server_fixed.py not found in current directory
    echo Make sure you're running this from the nexhack folder
    pause
    exit /b 1
)

echo ✅ Found pi_camera_server_fixed.py

REM Copy the file to Pi (requires SSH/SCP setup)
echo.
echo 📋 To update your Pi server manually:
echo 1. Copy the file to your Pi:
echo    scp pi_camera_server_fixed.py pi@%PI_IP%:~/pi_camera_server.py
echo.
echo 2. SSH to your Pi and restart:
echo    ssh pi@%PI_IP%
echo    pkill -f pi_camera_server
echo    python3 pi_camera_server.py
echo.
echo OR use the automatic method below...
echo.

REM Attempt automatic copy (if SSH is set up)
set /p COPY_AUTO="Try automatic copy? (y/n): "
if /i "%COPY_AUTO%"=="y" (
    echo.
    echo 🚀 Attempting automatic copy...
    scp pi_camera_server_fixed.py pi@%PI_IP%:~/pi_camera_server.py
    
    if %ERRORLEVEL% EQU 0 (
        echo ✅ File copied successfully!
        echo.
        echo 🔄 Now restart the Pi server:
        echo ssh pi@%PI_IP% "pkill -f pi_camera_server && python3 pi_camera_server.py"
    ) else (
        echo ❌ Copy failed. Please copy manually using the commands above.
    )
)

echo.
echo ✨ After updating, test the audio chat feature again!
pause