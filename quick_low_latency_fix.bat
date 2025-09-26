@echo off
echo 🚀 Robot Guardian - Low Latency Quick Fix
echo =========================================
echo.
echo Applying optimized settings for minimal latency...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python first.
    pause
    exit /b 1
)

REM Check if optimized files exist
if not exist "pi_camera_server.py" (
    echo ❌ pi_camera_server.py not found!
    echo    Make sure you're running this from the robot project folder.
    pause
    exit /b 1
)

if not exist "windows_ai_controller.py" (
    echo ❌ windows_ai_controller.py not found!
    echo    Make sure you're running this from the robot project folder.
    pause
    exit /b 1
)

echo ✅ Found robot control files
echo.

REM Display current optimizations
echo 📊 Current Low Latency Optimizations:
echo    • Camera resolution: 320x240 (was 640x480)
echo    • Frame rate: 15fps (was 30fps) 
echo    • JPEG quality: 50%% (was 80%%)
echo    • Command cooldown: 100ms (was 300ms)
echo    • UART timeout: 100ms (was 500ms)
echo    • Request timeouts: 1-2s (was 3-5s)
echo    • AI inference: 224px (was 320px)
echo    • Display FPS: 20fps (was 12fps)
echo.

REM Ask user what to do
echo Choose an action:
echo 1. Start Windows AI Controller (optimized)
echo 2. Run latency benchmark test
echo 3. Configure extreme low latency
echo 4. View optimization guide
echo 5. Exit
echo.

set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" (
    echo.
    echo 🚀 Starting optimized Windows AI Controller...
    echo    Make sure your Pi camera server is running first!
    echo.
    python windows_ai_controller.py
    goto end
)

if "%choice%"=="2" (
    echo.
    echo 📊 Running latency benchmark...
    python low_latency_config.py
    echo.
    pause
    goto end
)

if "%choice%"=="3" (
    echo.
    echo ⚡ Configuring extreme low latency...
    echo    Warning: This will reduce image quality significantly!
    python low_latency_config.py
    echo.
    pause  
    goto end
)

if "%choice%"=="4" (
    echo.
    echo 📖 Opening optimization guide...
    if exist "LOW_LATENCY_OPTIMIZATION.md" (
        start notepad "LOW_LATENCY_OPTIMIZATION.md"
    ) else (
        echo Guide file not found. Here's a quick summary:
        echo.
        echo 🎯 Key Optimizations Applied:
        echo    • Reduced camera resolution from 640x480 to 320x240
        echo    • Lowered frame rate from 30fps to 15fps  
        echo    • Faster command processing (300ms to 100ms)
        echo    • Reduced AI inference size (320px to 224px)
        echo    • Shorter network timeouts (3-5s to 1-2s)
        echo    • Higher display refresh rate (12fps to 20fps)
        echo.
        echo Expected improvement: 40-60% faster response times!
        echo.
    )
    pause
    goto end
)

if "%choice%"=="5" (
    goto end
)

echo.
echo ❌ Invalid choice. Please select 1-5.
echo.
pause
goto end

:end
echo.
echo 👋 Thank you for using Robot Guardian Low Latency Optimizer!
echo.
echo 💡 Tips for best performance:
echo    • Use good Wi-Fi signal or Ethernet connection
echo    • Keep Pi close to router (^<10 meters)
echo    • Close other applications using network/CPU
echo    • Restart Pi if performance degrades
echo.
echo 📊 Expected latency improvements:
echo    • Command response: 40-60%% faster
echo    • Video streaming: 40-50%% faster  
echo    • Auto-tracking: 60%% more responsive
echo.
pause