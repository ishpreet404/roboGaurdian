#!/bin/bash
# 🚀 Pi Robot Server Startup Script
# =================================
# 
# This script starts the Pi camera server and creates a tunnel for remote access.
# Run this on your Raspberry Pi to enable remote robot control.
#
# Usage: ./start_pi_robot.sh
#
# Author: Robot Guardian System
# Date: September 2025

echo "🤖 Starting Robot Guardian Pi Server..."
echo "======================================="

# Check if running as pi user
if [ "$USER" != "pi" ]; then
    echo "⚠️  Warning: Not running as 'pi' user. GPIO permissions may be limited."
fi

# Check Python dependencies
echo "📋 Checking dependencies..."

python3 -c "import cv2" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ OpenCV not found. Installing..."
    sudo apt update && sudo apt install -y python3-opencv
fi

python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Flask not found. Installing..."
    pip3 install flask
fi

python3 -c "import serial" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ PySerial not found. Installing..."
    pip3 install pyserial
fi

# Check UART permissions
if [ ! -c "/dev/serial0" ]; then
    echo "⚠️  UART not found. Make sure it's enabled in raspi-config"
    echo "   Run: sudo raspi-config → Interface Options → Serial Port"
else
    echo "✅ UART found at /dev/serial0"
fi

# Check camera
if [ ! -e "/dev/video0" ] && [ ! -e "/dev/video1" ]; then
    echo "⚠️  No camera found. Please connect camera and enable it."
else
    echo "✅ Camera detected"
fi

# Create logs directory
mkdir -p ~/robot_logs

# Function to start server
start_server() {
    echo ""
    echo "🚀 Starting Ultra Low-Latency Pi Server..."
    
    # Kill any existing server
    pkill -f "ultra_low_latency_pi_server.py" 2>/dev/null
    
    # Start server with logging
    python3 ~/ultra_low_latency_pi_server.py 2>&1 | tee ~/robot_logs/server_$(date +%Y%m%d_%H%M%S).log &
    SERVER_PID=$!
    
    # Wait for server to start
    sleep 3
    
    # Check if server started successfully
    if ps -p $SERVER_PID > /dev/null; then
        echo "✅ Server started successfully (PID: $SERVER_PID)"
        
        # Get local IP
        LOCAL_IP=$(hostname -I | awk '{print $1}')
        echo "🌐 Local access: http://$LOCAL_IP:5000"
        
        return 0
    else
        echo "❌ Failed to start server"
        return 1
    fi
}

# Function to create tunnel
create_tunnel() {
    echo ""
    echo "🌐 Creating internet tunnel..."
    
    # Kill any existing tunnels
    pkill -f "serveo.net" 2>/dev/null
    pkill -f "cloudflared" 2>/dev/null
    pkill -f "localtunnel" 2>/dev/null
    
    # Try different tunnel options
    echo "Choose tunnel service:"
    echo "1) Serveo (SSH tunnel - reliable)"
    echo "2) Cloudflare (often fastest)" 
    echo "3) LocalTunnel (alternative)"
    echo "4) Skip tunnel (local only)"
    
    read -p "Enter choice (1-4): " tunnel_choice
    
    case $tunnel_choice in
        1)
            echo "🚀 Starting Serveo tunnel..."
            ssh -o StrictHostKeyChecking=no -R 80:localhost:5000 serveo.net &
            TUNNEL_PID=$!
            sleep 5
            echo "✅ Serveo tunnel started"
            echo "📱 Access from anywhere: Check SSH output for URL"
            ;;
        2)
            if command -v cloudflared &> /dev/null; then
                echo "🚀 Starting Cloudflare tunnel..."
                cloudflared tunnel --url http://localhost:5000 &
                TUNNEL_PID=$!
                sleep 3
                echo "✅ Cloudflare tunnel started"
            else
                echo "❌ Cloudflared not installed. Install with:"
                echo "   wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb"
                echo "   sudo dpkg -i cloudflared-linux-arm64.deb"
            fi
            ;;
        3)
            if command -v npm &> /dev/null; then
                echo "🚀 Starting LocalTunnel..."
                npx localtunnel --port 5000 &
                TUNNEL_PID=$!
                sleep 3
                echo "✅ LocalTunnel started"
            else
                echo "❌ Node.js/npm not installed for LocalTunnel"
            fi
            ;;
        4)
            echo "⚠️  Skipping tunnel - local access only"
            TUNNEL_PID=""
            ;;
        *)
            echo "❌ Invalid choice. Skipping tunnel."
            TUNNEL_PID=""
            ;;
    esac
}

# Function to show status
show_status() {
    echo ""
    echo "📊 System Status:"
    echo "================"
    
    if ps -p $SERVER_PID > /dev/null 2>&1; then
        echo "✅ Pi Server: Running (PID: $SERVER_PID)"
    else
        echo "❌ Pi Server: Stopped"
    fi
    
    if [ -n "$TUNNEL_PID" ] && ps -p $TUNNEL_PID > /dev/null 2>&1; then
        echo "✅ Tunnel: Running (PID: $TUNNEL_PID)"
    elif [ -n "$TUNNEL_PID" ]; then
        echo "❌ Tunnel: Stopped"
    else
        echo "⚠️  Tunnel: Not started"
    fi
    
    # Show recent logs
    echo ""
    echo "📋 Recent server logs:"
    tail -5 ~/robot_logs/server_*.log 2>/dev/null | tail -5
}

# Main execution
main() {
    # Start server
    if start_server; then
        echo ""
        
        # Ask about tunnel
        read -p "🌐 Create internet tunnel for remote access? (y/n): " create_tunnel_choice
        
        if [[ $create_tunnel_choice =~ ^[Yy] ]]; then
            create_tunnel
        fi
        
        # Show final status
        show_status
        
        echo ""
        echo "🎉 Robot Guardian Pi Server is ready!"
        echo ""
        echo "📖 Next steps:"
        echo "  1. Note the tunnel URL from above output"
        echo "  2. Update gui_tester.py with your tunnel URL"
        echo "  3. Run gui_tester.py on your PC"
        echo "  4. Start person tracking!"
        echo ""
        echo "🔍 Monitor logs: tail -f ~/robot_logs/server_*.log"
        echo "🛑 Stop server: pkill -f ultra_low_latency_pi_server.py"
        echo ""
        
        # Keep script running to monitor
        echo "Press Ctrl+C to stop all services..."
        
        # Monitor processes
        while true; do
            sleep 10
            
            # Check if server died
            if ! ps -p $SERVER_PID > /dev/null 2>&1; then
                echo "⚠️  Server process died! Check logs."
                break
            fi
        done
        
    else
        echo "❌ Failed to start server. Check the logs for errors."
        exit 1
    fi
}

# Handle Ctrl+C
cleanup() {
    echo ""
    echo "🛑 Shutting down Robot Guardian Pi Server..."
    
    if [ -n "$SERVER_PID" ]; then
        kill $SERVER_PID 2>/dev/null
        echo "✅ Server stopped"
    fi
    
    if [ -n "$TUNNEL_PID" ]; then
        kill $TUNNEL_PID 2>/dev/null
        echo "✅ Tunnel stopped"
    fi
    
    echo "👋 Goodbye!"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Run main function
main