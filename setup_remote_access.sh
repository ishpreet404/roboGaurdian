#!/bin/bash
# Robot Guardian - Remote Access Setup Script
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

# Function to setup ngrok
setup_ngrok() {
    print_step "Setting up ngrok tunnel..."
    
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

# Function to show port forwarding instructions
show_port_forwarding() {
    LOCAL_IP=$(get_local_ip)
    
    echo ""
    print_highlight "📋 Router Port Forwarding Setup:"
    echo "======================================="
    echo "1. Access your router admin panel:"
    echo "   - Usually: http://192.168.1.1 or http://192.168.0.1"
    echo "   - Login with admin credentials"
    echo ""
    echo "2. Find 'Port Forwarding' or 'Virtual Server' settings"
    echo ""
    echo "3. Add new forwarding rule:"
    echo "   - Service Name: Robot Guardian"
    echo "   - Internal IP: $LOCAL_IP"
    echo "   - Internal Port: 5000"
    echo "   - External Port: 5000 (or choose different)"
    echo "   - Protocol: TCP"
    echo "   - Enable: Yes"
    echo ""
    echo "4. Save and apply router settings"
    echo ""
    echo "5. Find your public IP:"
    echo "   - Go to: https://whatismyipaddress.com"
    echo "   - Note your public IP address"
    echo ""
    echo "6. Access robot remotely:"
    echo "   - URL: http://YOUR_PUBLIC_IP:5000"
    echo ""
    print_warning "⚠️  SECURITY WARNINGS:"
    echo "• Enable router firewall"
    echo "• Consider changing default port (5000)"
    echo "• Monitor router logs for suspicious access"
    echo "• Use strong router admin password"
}

# Function to show VPN setup
show_vpn_setup() {
    echo ""
    print_highlight "🔒 VPN Setup (Most Secure):"
    echo "============================="
    echo "1. Install PiVPN on your Raspberry Pi:"
    echo "   curl -L https://install.pivpn.io | bash"
    echo ""
    echo "2. Follow the setup wizard"
    echo ""
    echo "3. Create client profile:"
    echo "   pivpn add"
    echo ""
    echo "4. Download profile to your device"
    echo ""
    echo "5. Connect via VPN and access:"
    echo "   http://$LOCAL_IP:5000"
    echo ""
    print_status "VPN provides the most secure remote access!"
}

# Function to show dynamic DNS setup
show_dynamic_dns() {
    echo ""
    print_highlight "🌐 Dynamic DNS Setup:"
    echo "======================"
    echo "If your ISP changes your IP address:"
    echo ""
    echo "1. Sign up for free DDNS service:"
    echo "   - No-IP.com"
    echo "   - DuckDNS.org"
    echo "   - Afraid.org"
    echo ""
    echo "2. Install DDNS client on router or Pi"
    echo ""
    echo "3. Configure automatic IP updates"
    echo ""
    echo "4. Access via: http://yourdomain.ddns.net:5000"
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

# Function to show firewall setup
setup_firewall() {
    print_step "Configuring firewall..."
    
    if command -v ufw &> /dev/null; then
        # Allow port 5000
        sudo ufw allow 5000/tcp
        
        # Show status
        print_status "Firewall configured to allow port 5000"
        sudo ufw status
    else
        print_warning "UFW firewall not installed"
        echo "Install with: sudo apt install ufw"
    fi
}

# Main menu
main_menu() {
    LOCAL_IP=$(get_local_ip)
    
    clear
    echo "🤖 Robot Guardian - Remote Access Setup"
    echo "========================================"
    echo ""
    print_status "Current system info:"
    echo "  Local IP: $LOCAL_IP"
    echo "  Server status: $(check_server_running && echo "Running ✅" || echo "Stopped ❌")"
    echo ""
    
    echo "Choose remote access method:"
    echo ""
    echo "1) 🔒 ngrok Tunnel (Recommended - Easy & Secure)"
    echo "2) 🌐 Port Forwarding (Requires router access)"  
    echo "3) 🔐 VPN Setup (Most secure)"
    echo "4) 🌍 Dynamic DNS (For changing IPs)"
    echo "5) 🧪 Test local access"
    echo "6) 🔥 Configure firewall"
    echo "7) 🚀 Start robot server"
    echo "8) ❓ Show all methods"
    echo "9) 🚪 Exit"
    echo ""
    
    read -p "Enter choice (1-9): " choice
    
    case $choice in
        1)
            # Start server if needed
            if ! check_server_running; then
                start_robot_server
            fi
            setup_ngrok
            ;;
        2)
            show_port_forwarding
            ;;
        3)
            show_vpn_setup
            ;;
        4)
            show_dynamic_dns
            ;;
        5)
            test_local_access
            ;;
        6)
            setup_firewall
            ;;
        7)
            start_robot_server
            ;;
        8)
            # Show all methods
            if ! check_server_running; then
                start_robot_server
            fi
            setup_ngrok
            show_port_forwarding
            show_vpn_setup
            show_dynamic_dns
            ;;
        9)
            print_status "Goodbye! 🤖"
            exit 0
            ;;
        *)
            print_error "Invalid choice"
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
    main_menu
}

# Check if script is run with parameters
if [[ $# -gt 0 ]]; then
    case $1 in
        --ngrok)
            start_robot_server
            setup_ngrok
            ;;
        --port-forward)
            show_port_forwarding
            ;;
        --vpn)
            show_vpn_setup
            ;;
        --test)
            test_local_access
            ;;
        --start-server)
            start_robot_server
            ;;
        *)
            echo "Usage: $0 [--ngrok|--port-forward|--vpn|--test|--start-server]"
            exit 1
            ;;
    esac
else
    # Run interactive menu
    main_menu
fi