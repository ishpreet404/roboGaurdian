# Remote Access Setup for Raspberry Pi Robot

## 🌍 **Methods to Access Your Robot Remotely**

### **Method 1: ngrok (Easiest & Secure) ⭐ Recommended**

ngrok creates a secure tunnel to your local server without port forwarding.

#### **Setup ngrok:**

```bash
# On Raspberry Pi - Install ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# Sign up at https://ngrok.com (free account)
# Get your auth token from dashboard
ngrok config add-authtoken YOUR_AUTH_TOKEN

# Start tunnel for your robot server (port 5000)
ngrok http 5000
```

#### **Expected Output:**
```
Session Status                online
Account                      your-email@domain.com
Version                      3.x.x
Region                       United States (us)
Forwarding                   https://abc123.ngrok.io -> http://localhost:5000
Forwarding                   http://abc123.ngrok.io -> http://localhost:5000
```

#### **Access Your Robot:**
- **Control Panel:** `https://abc123.ngrok.io/`
- **Video Stream:** `https://abc123.ngrok.io/?action=stream`
- **Send Commands:** 
  ```bash
  curl -X POST https://abc123.ngrok.io/move \
    -H "Content-Type: application/json" \
    -d '{"command": "F"}'
  ```

### **Method 2: Cloudflare Tunnel (Free & Fast)**

Cloudflare tunnels are free and very fast.

#### **Setup Cloudflare Tunnel:**

```bash
# Install cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
sudo dpkg -i cloudflared-linux-arm64.deb

# Login to Cloudflare (opens browser)
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create robot-pi

# Configure tunnel
echo "tunnel: robot-pi
credentials-file: /home/pi/.cloudflared/robot-pi.json

ingress:
  - hostname: your-robot.yourdomain.com
    service: http://localhost:5000
  - service: http_status:404" > ~/.cloudflared/config.yml

# Run tunnel
cloudflared tunnel run robot-pi
```

### **Method 3: Dynamic DNS + Port Forwarding (Traditional)**

#### **Setup Dynamic DNS:**

```bash
# Install ddclient for dynamic DNS
sudo apt install ddclient

# Configure with your router's public IP
# Services: No-IP, DuckDNS, DynDNS
# Example: robot-pi.ddns.net -> your home IP
```

#### **Router Configuration:**
- Forward port 5000 → Raspberry Pi IP (10.214.108.26:5000)
- Enable UPnP or manual port forwarding
- Access via: `http://robot-pi.ddns.net:5000`

### **Method 4: VPN (Most Secure)**

#### **Setup WireGuard VPN:**

```bash
# Install WireGuard on Pi
sudo apt install wireguard

# Generate keys
wg genkey | tee privatekey | wg pubkey > publickey

# Configure VPN server on Pi or use commercial VPN
# Access robot through VPN tunnel
```

## 🛡️ **Security Enhancements**

### **1. Add Authentication to Your Server:**

```python
# Add to raspberry_pi_server.py
from functools import wraps
import hashlib

class SecureRobotServer(RobotCommandServer):
    def __init__(self):
        super().__init__()
        self.api_key = "your-secret-api-key-here"  # Change this!
        self.allowed_ips = set()  # Optional IP whitelist
        
    def require_auth(self, f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check API key
            auth_header = request.headers.get('Authorization')
            if not auth_header or auth_header != f"Bearer {self.api_key}":
                return jsonify({'error': 'Unauthorized'}), 401
            
            # Optional: Check IP whitelist
            client_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
            if self.allowed_ips and client_ip not in self.allowed_ips:
                return jsonify({'error': 'IP not allowed'}), 403
                
            return f(*args, **kwargs)
        return decorated_function
    
    def setup_routes(self):
        """Setup routes with authentication"""
        
        @self.app.route('/', methods=['GET'])
        def index():
            # Public status (no auth needed)
            return jsonify({
                'status': 'Robot Server Online',
                'version': '2.0',
                'auth_required': True
            })
        
        @self.app.route('/move', methods=['POST'])
        @self.require_auth
        def move_robot():
            # Protected route - requires API key
            return super().move_robot()
        
        @self.app.route('/status', methods=['GET']) 
        @self.require_auth
        def get_status():
            # Protected route
            return super().get_status()
```

### **2. HTTPS & Rate Limiting:**

```python
# Add rate limiting
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per hour", "10 per minute"]
)

@self.app.route('/move', methods=['POST'])
@limiter.limit("30 per minute")  # Max 30 commands per minute
@self.require_auth
def move_robot():
    # Rate limited movement
    pass
```

## 📱 **Web Interface for Remote Control**

### **Create Mobile-Friendly Web Controller:**

```html
<!-- robot_controller.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Robot Remote Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial; text-align: center; background: #222; color: white; }
        .video-container { margin: 20px auto; max-width: 640px; }
        .controls { margin: 20px; }
        .btn { 
            background: #4CAF50; border: none; color: white; 
            padding: 15px 32px; margin: 5px; font-size: 16px;
            border-radius: 5px; cursor: pointer;
        }
        .btn:active { background: #45a049; }
        .stop { background: #f44336; }
        #stream { width: 100%; height: auto; border: 2px solid #4CAF50; }
    </style>
</head>
<body>
    <h1>🤖 Robot Guardian Remote Control</h1>
    
    <div class="video-container">
        <img id="stream" src="/?action=stream" alt="Robot Camera Stream">
    </div>
    
    <div class="controls">
        <div>
            <button class="btn" onmousedown="sendCommand('F')" onmouseup="sendCommand('S')">⬆️ Forward</button>
        </div>
        <div>
            <button class="btn" onmousedown="sendCommand('L')" onmouseup="sendCommand('S')">⬅️ Left</button>
            <button class="btn stop" onclick="sendCommand('S')">🛑 Stop</button>
            <button class="btn" onmousedown="sendCommand('R')" onmouseup="sendCommand('S')">➡️ Right</button>
        </div>
        <div>
            <button class="btn" onmousedown="sendCommand('B')" onmouseup="sendCommand('S')">⬇️ Backward</button>
        </div>
    </div>
    
    <div id="status">Status: Connecting...</div>
    
    <script>
        const apiKey = 'your-secret-api-key-here';  // Replace with your key
        
        async function sendCommand(cmd) {
            try {
                const response = await fetch('/move', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${apiKey}`
                    },
                    body: JSON.stringify({ command: cmd })
                });
                
                const result = await response.json();
                document.getElementById('status').textContent = 
                    `Status: ${result.status} - Command: ${cmd}`;
                    
            } catch (error) {
                document.getElementById('status').textContent = 
                    `Error: ${error.message}`;
            }
        }
        
        // Check connection status
        async function checkStatus() {
            try {
                const response = await fetch('/status', {
                    headers: { 'Authorization': `Bearer ${apiKey}` }
                });
                const data = await response.json();
                document.getElementById('status').textContent = 
                    `Connected - ESP32: ${data.esp32_connected ? 'Online' : 'Offline'}`;
            } catch (error) {
                document.getElementById('status').textContent = 'Disconnected';
            }
        }
        
        // Check status every 5 seconds
        setInterval(checkStatus, 5000);
        checkStatus();
        
        // Keyboard controls
        document.addEventListener('keydown', (e) => {
            switch(e.key.toLowerCase()) {
                case 'w': case 'arrowup': sendCommand('F'); break;
                case 's': case 'arrowdown': sendCommand('B'); break;
                case 'a': case 'arrowleft': sendCommand('L'); break;
                case 'd': case 'arrowright': sendCommand('R'); break;
                case ' ': sendCommand('S'); break;
            }
        });
        
        document.addEventListener('keyup', (e) => {
            if (['w','s','a','d','arrowup','arrowdown','arrowleft','arrowright'].includes(e.key.toLowerCase())) {
                sendCommand('S');
            }
        });
    </script>
</body>
</html>
```

## 🚀 **Complete Remote Setup Script**

```bash
#!/bin/bash
# setup_remote_robot.sh - Complete remote access setup

echo "🌍 Setting up Remote Robot Access..."

# 1. Install ngrok (easiest method)
if ! command -v ngrok &> /dev/null; then
    echo "📥 Installing ngrok..."
    curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
    echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
    sudo apt update && sudo apt install ngrok
fi

# 2. Install additional security packages
pip3 install flask-limiter flask-cors

# 3. Create startup script
cat > start_remote_robot.sh << 'EOF'
#!/bin/bash
echo "🤖 Starting Remote Robot Server..."

# Start robot server in background
python3 raspberry_pi_server.py &
SERVER_PID=$!

# Wait for server to start
sleep 5

# Start ngrok tunnel
ngrok http 5000 --log=stdout &
NGROK_PID=$!

echo "✅ Robot server started (PID: $SERVER_PID)"
echo "✅ ngrok tunnel started (PID: $NGROK_PID)"
echo "🌍 Check ngrok dashboard for public URL: http://localhost:4040"

# Wait for interrupt
trap "kill $SERVER_PID $NGROK_PID; exit" INT TERM
wait
EOF

chmod +x start_remote_robot.sh

echo "✅ Remote access setup complete!"
echo ""
echo "🚀 Next steps:"
echo "1. Sign up at https://ngrok.com (free)"
echo "2. Get your auth token: ngrok config add-authtoken YOUR_TOKEN"
echo "3. Run: ./start_remote_robot.sh"
echo "4. Access robot via ngrok URL from anywhere!"
```

## 📋 **Quick Start Commands**

### **1. Setup ngrok (Recommended):**
```bash
# Install and configure ngrok
sudo apt install ngrok
ngrok config add-authtoken YOUR_AUTH_TOKEN

# Start robot server
python3 raspberry_pi_server.py &

# Create tunnel (run in another terminal)
ngrok http 5000

# Access from anywhere via: https://xyz123.ngrok.io
```

### **2. Test Remote Commands:**
```bash
# From anywhere in the world:
curl -X POST https://xyz123.ngrok.io/move \
  -H "Content-Type: application/json" \
  -d '{"command": "F"}'

# View stream in browser:
https://xyz123.ngrok.io/?action=stream
```

## ✅ **Benefits of Remote Access:**

- 🌍 **Control from anywhere** - Home, office, travel
- 📱 **Mobile friendly** - Works on phones/tablets
- 📹 **Live video stream** - See what robot sees
- 🛡️ **Secure tunnels** - Encrypted connections
- 🚀 **Easy setup** - No router configuration needed
- 💰 **Free options** - ngrok free tier available

Your robot will be accessible from anywhere in the world! 🌍🤖

Would you like me to help you set up any specific remote access method?
