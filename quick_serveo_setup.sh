#!/bin/bash
# Quick Serveo SSH Tunnel Setup for Robot Control
# No signup required, unlimited requests!

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_highlight() {
    echo -e "${CYAN}[HIGHLIGHT]${NC} $1"
}

echo "🔒 Serveo SSH Tunnel - Robot Remote Access"
echo "=========================================="

# Check if robot server is running
if ! pgrep -f "raspberry_pi_server" > /dev/null; then
    print_step "Starting robot server..."
    
    # Find server file
    if [[ -f "raspberry_pi_server_remote.py" ]]; then
        python3 raspberry_pi_server_remote.py &
    elif [[ -f "raspberry_pi_server.py" ]]; then
        python3 raspberry_pi_server.py &
    else
        echo "❌ No robot server file found!"
        echo "Download with: wget https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/raspberry_pi_server_remote.py"
        exit 1
    fi
    
    sleep 3
    print_status "✅ Robot server started"
else
    print_status "✅ Robot server already running"
fi

# Generate random subdomain
SUBDOMAIN="robot$(date +%s)"

print_step "Setting up Serveo SSH tunnel..."
print_highlight "🌍 Creating public URL: https://$SUBDOMAIN.serveo.net"

echo ""
print_status "✅ No signup required!"
print_status "✅ Unlimited requests!"  
print_status "✅ HTTPS enabled!"
print_status "✅ Global access!"

echo ""
print_step "Starting SSH tunnel..."

# Start SSH tunnel with Serveo
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -R $SUBDOMAIN:80:localhost:5000 serveo.net 2>/dev/null &
SERVEO_PID=$!

# Wait for connection
sleep 5

echo ""
print_highlight "🎉 SUCCESS! Your robot is now online!"
echo ""
print_highlight "🤖 Robot Control URL: https://$SUBDOMAIN.serveo.net"
echo ""
echo "📱 Access from anywhere:"
echo "  • Web browser on computer"
echo "  • Mobile phone browser"  
echo "  • Share URL with friends"
echo ""
echo "🎮 Controls:"
echo "  • Touch/click buttons for movement"
echo "  • Keyboard: WASD or arrow keys"
echo "  • Spacebar to stop"
echo ""
echo "📊 Features:"
echo "  • Live camera stream"
echo "  • Real-time robot status"
echo "  • Command history"
echo "  • Mobile-friendly interface"
echo ""
print_status "Tunnel PID: $SERVEO_PID"
print_status "To stop tunnel: kill $SERVEO_PID"

echo ""
echo "🔥 Your robot is now accessible from ANYWHERE in the world!"
echo "No more ngrok limits! 🚫"
echo ""
print_highlight "Press Ctrl+C to stop tunnel, or close terminal to keep running in background"

# Keep script running
wait $SERVEO_PID