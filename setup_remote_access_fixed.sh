#!/bin/bash
# Robot Guardian - Remote Access Setup Script (Fixed Order)
# Enables internet access for robot control

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_highlight() {
    echo -e "${CYAN}[HIGHLIGHT]${NC} $1"
}

# Function to get local IP
get_local_ip() {
    hostname -I | cut -d' ' -f1
}

# Function to check if server is running
check_server_running() {
    if pgrep -f "raspberry_pi_server" > /dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to start robot server
start_robot_server() {
    print_step "Starting robot server..."
    
    if check_server_running; then
        print_status "Robot server is already running"
        return 0
    fi
    
    # Check for server files
    if [[ -f "raspberry_pi_server_remote.py" ]]; then
        SERVER_FILE="raspberry_pi_server_remote.py"
    elif [[ -f "raspberry_pi_server.py" ]]; then
        SERVER_FILE="raspberry_pi_server.py"
    else
        print_error "No robot server file found!"
        echo "Please download the server file first:"
        echo "wget https://raw.githubusercontent.com/ishpreet404/roboGaurdian/main/raspberry_pi_server_remote.py"
        return 1
    fi
    
    print_status "Starting $SERVER_FILE..."
    python3 "$SERVER_FILE" &
    SERVER_PID=$!
    
    # Wait a moment for server to start
    sleep 3
    
    if check_server_running; then
        print_status "✅ Robot server started successfully (PID: $SERVER_PID)"
        return 0
    else
        print_error "❌ Failed to start robot server"
        return 1
    fi
}

# Function to setup Serveo SSH Tunnel (No signup required)
setup_serveo_tunnel() {
    print_step "Setting up Serveo SSH tunnel..."
    
    print_highlight "🔒 Serveo Tunnel (No signup required!):"
    echo "This creates a secure SSH tunnel through serveo.net"
    echo ""
    
    # Generate random subdomain
    SUBDOMAIN="robot$(date +%s)"
    
    print_step "Starting Serveo tunnel..."
    print_highlight "Creating tunnel: https://$SUBDOMAIN.serveo.net"
    
    # Start SSH tunnel
    ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -R $SUBDOMAIN:80:localhost:5000 serveo.net &
    SERVEO_PID=$!
    
    sleep 3
    
    echo ""
    print_status "🌍 Serveo tunnel started!"
    print_highlight "Your robot URL: https://$SUBDOMAIN.serveo.net"
    echo ""
    echo "✅ No signup required!"
    echo "✅ Unlimited requests!"
    echo "✅ HTTPS enabled!"
    echo "✅ 24/7 access!"
    echo ""
    print_status "Tunnel PID: $SERVEO_PID"
    echo "To stop tunnel: kill $SERVEO_PID"
}

# Function to setup Cloudflare Tunnel (Free & Unlimited)
setup_cloudflare_tunnel() {
    print_step "Setting up Cloudflare Tunnel..."
    
    # Check if cloudflared is installed
    if ! command -v cloudflared &> /dev/null; then
        print_warning "cloudflared not found. Installing..."
        
        # Download and install cloudflared for ARM
        cd /tmp
        wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64 -O cloudflared
        chmod +x cloudflared
        sudo mv cloudflared /usr/local/bin/
        
        print_status "cloudflared installed successfully"
    fi
    
    echo ""
    print_highlight "🌐 Cloudflare Tunnel Setup:"
    echo "1. Go to https://dash.cloudflare.com/"
    echo "2. Sign up/login (free account)"
    echo "3. Go to Zero Trust > Networks > Tunnels"
    echo "4. Create a tunnel and get your token"
    echo ""
    
    read -p "Have you created a tunnel and got the token? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Enter your tunnel token (starts with 'ey...'):"
        read -r TUNNEL_TOKEN
        
        if [[ -n "$TUNNEL_TOKEN" ]]; then
            print_step "Starting Cloudflare tunnel..."
            
            # Start tunnel
            cloudflared tunnel --url http://localhost:5000 --token "$TUNNEL_TOKEN" &
            TUNNEL_PID=$!
            
            echo ""
            print_status "🌍 Cloudflare tunnel started!"
            print_highlight "Your robot is now accessible via your Cloudflare domain!"
            echo ""
            echo "Check your Cloudflare dashboard for the tunnel URL"
            echo "To stop tunnel later: kill $TUNNEL_PID"
        else
            print_error "No token provided"
        fi
    else
        print_warning "Please create a Cloudflare tunnel first"
    fi
}

# Function to setup LocalTunnel (Free, simple)
setup_localtunnel() {
    print_step "Setting up LocalTunnel..."
    
    # Check if Node.js is installed
    if ! command -v node &> /dev/null; then
        print_warning "Node.js not found. Installing..."
        curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
        sudo apt-get install -y nodejs
    fi
    
    # Install localtunnel
    if ! command -v lt &> /dev/null; then
        print_status "Installing LocalTunnel..."
        sudo npm install -g localtunnel
    fi
    
    # Generate random subdomain
    SUBDOMAIN="robot$(date +%s)"
    
    print_step "Starting LocalTunnel..."
    print_highlight "Creating tunnel: https://$SUBDOMAIN.loca.lt"
    
    # Start tunnel
    lt --port 5000 --subdomain "$SUBDOMAIN" &
    LT_PID=$!
    
    sleep 3
    
    echo ""
    print_status "🌍 LocalTunnel started!"
    print_highlight "Your robot URL: https://$SUBDOMAIN.loca.lt"
    echo ""
    echo "✅ Free and unlimited!"
    echo "✅ Simple setup!"
    echo "⚠️  May show warning page on first visit"
    echo ""
    echo "To stop tunnel: kill $LT_PID"
}

# Function to setup ngrok (with warning)
setup_ngrok() {
    print_step "Setting up ngrok tunnel..."
    
    print_warning "⚠️  ngrok Free Tier Limitations:"
    echo "• Only 120 requests per month"
    echo "• Sessions timeout after 2 hours"
    echo "• Consider using Cloudflare Tunnel or Serveo instead"
    echo ""
    
    read -p "Continue with ngrok anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return
    fi
    
    # Check if ngrok is installed
    if ! command -v ngrok &> /dev/null; then
        print_warning "ngrok not found. Installing..."
        
        # Download and install ngrok
        cd /tmp
        wget -q https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-arm.tgz
        tar xzf ngrok-v3-stable-linux-arm.tgz
        sudo mv ngrok /usr/local/bin/
        
        print_status "ngrok installed successfully"
    fi
    
    echo ""
    print_highlight "🔐 ngrok Setup Instructions:"
    echo "1. Go to https://ngrok.com and sign up (free)"
    echo "2. Get your auth token from the dashboard"
    echo "3. Run: ngrok config add-authtoken YOUR_TOKEN"
    echo ""
    
    read -p "Have you configured your ngrok auth token? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_step "Starting ngrok tunnel..."
        
        # Start ngrok tunnel
        ngrok http 5000 --log=stdout &
        NGROK_PID=$!
        
        echo ""
        print_status "🌍 ngrok tunnel started!"
        print_highlight "Your robot is now accessible from anywhere!"
        echo ""
        echo "Check the ngrok output above for your public URL"
        echo "It will look like: https://abc123.ngrok.io"
        echo ""
        echo "To stop ngrok later: kill $NGROK_PID"
        
        # Wait for ngrok to establish tunnel
        sleep 5
        
        # Try to get ngrok URL from API
        if command -v curl &> /dev/null; then
            print_step "Getting ngrok tunnel URL..."
            NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o 'https://[^"]*\.ngrok\.io' | head -1)
            if [[ -n "$NGROK_URL" ]]; then
                echo ""
                print_highlight "🎉 Your robot URL: $NGROK_URL"
                echo "Share this URL to control your robot from anywhere!"
            fi
        fi
        
    else
        print_warning "Please configure ngrok first:"
        echo "1. Sign up at https://ngrok.com"
        echo "2. Get auth token from dashboard"
        echo "3. Run: ngrok config add-authtoken YOUR_TOKEN"
        echo "4. Then run this script again"
    fi
}

# Function to test local access
test_local_access() {
    LOCAL_IP=$(get_local_ip)
    
    print_step "Testing local access..."
    
    if command -v curl &> /dev/null; then
        if curl -s "http://localhost:5000/status" > /dev/null; then
            print_status "✅ Local server responding"
            echo "   Local URL: http://localhost:5000"
            echo "   Network URL: http://$LOCAL_IP:5000"
        else
            print_error "❌ Server not responding on localhost:5000"
            echo "Make sure the robot server is running"
        fi
    else
        print_warning "curl not available for testing"
        echo "Try accessing: http://$LOCAL_IP:5000"
    fi
}

# Check if script is run with parameters FIRST
if [[ $# -gt 0 ]]; then
    case $1 in
        --serveo)
            print_status "🔒 Starting Serveo SSH Tunnel..."
            start_robot_server
            setup_serveo_tunnel
            exit 0
            ;;
        --cloudflare)
            print_status "🌐 Starting Cloudflare Tunnel..."
            start_robot_server
            setup_cloudflare_tunnel
            exit 0
            ;;
        --localtunnel)
            print_status "🚀 Starting LocalTunnel..."
            start_robot_server
            setup_localtunnel
            exit 0
            ;;
        --ngrok)
            print_status "💰 Starting ngrok (Limited)..."
            start_robot_server
            setup_ngrok
            exit 0
            ;;
        --test)
            test_local_access
            exit 0
            ;;
        --start-server)
            start_robot_server
            exit 0
            ;;
        *)
            echo "🤖 Robot Guardian - Remote Access Setup"
            echo "Usage: $0 [OPTION]"
            echo ""
            echo "Available options:"
            echo "  --serveo        🔒 Serveo SSH tunnel (no signup, unlimited)"
            echo "  --cloudflare    🌐 Cloudflare tunnel (free, unlimited)"  
            echo "  --localtunnel   🚀 LocalTunnel (simple, unlimited)"
            echo "  --ngrok         💰 ngrok (120 req/month limit)"
            echo "  --test          🧪 Test local server connection"
            echo "  --start-server  🚀 Start robot server only"
            echo ""
            echo "Recommended: ./setup_remote_access.sh --serveo"
            exit 1
            ;;
    esac
fi

# If no parameters, show interactive menu
echo "🤖 Robot Guardian - Remote Access Setup"
echo "========================================"
echo ""
print_status "✅ Interactive mode - choose your tunneling method"
echo ""

LOCAL_IP=$(get_local_ip)
print_status "Current system info:"
echo "  Local IP: $LOCAL_IP"
echo "  Server status: $(check_server_running && echo "Running ✅" || echo "Stopped ❌")"
echo ""

echo "Choose remote access method:"
echo ""
echo "1) 🔒 Serveo SSH Tunnel (Recommended - No signup, unlimited)"
echo "2) 🌐 Cloudflare Tunnel (Professional - Free, unlimited)"
echo "3) 🚀 LocalTunnel (Simple - Free, unlimited)"
echo "4) 💰 ngrok (Limited - 120 req/month)"
echo "5) 🧪 Test local access"
echo "6) 🚀 Start robot server"
echo "7) 🚪 Exit"
echo ""

read -p "Enter choice (1-7): " choice

case $choice in
    1)
        if ! check_server_running; then
            start_robot_server
        fi
        setup_serveo_tunnel
        ;;
    2)
        if ! check_server_running; then
            start_robot_server
        fi
        setup_cloudflare_tunnel
        ;;
    3)
        if ! check_server_running; then
            start_robot_server
        fi
        setup_localtunnel
        ;;
    4)
        if ! check_server_running; then
            start_robot_server
        fi
        setup_ngrok
        ;;
    5)
        test_local_access
        ;;
    6)
        start_robot_server
        ;;
    7)
        print_status "Goodbye! 🤖"
        exit 0
        ;;
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

echo ""
print_highlight "🎉 Setup complete! Your robot is now accessible remotely!"