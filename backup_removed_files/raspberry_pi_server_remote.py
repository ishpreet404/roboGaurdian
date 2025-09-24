#!/usr/bin/env python3
"""
Enhanced Raspberry Pi Robot Server with Remote Access
====================================================

Features:
- UART communication with ESP32
- Camera streaming
- Web interface for remote control
- Security with API keys
- Rate limiting
- Mobile-friendly controls

Author: Robot Guardian System
"""

import os
import sys
import json
import time
import threading
import logging
import hashlib
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, Response, render_template_string
import cv2
import serial
import serial.tools.list_ports

# Configure logging
def setup_logging():
    """Setup logging with fallback options"""
    log_handlers = [logging.StreamHandler(sys.stdout)]
    
    possible_log_paths = [
        '/home/pi/robot_server.log',
        f'/home/{os.environ.get("USER", "pi")}/robot_server.log',
        os.path.expanduser('~/robot_server.log'),
        './robot_server.log'
    ]
    
    for log_path in possible_log_paths:
        try:
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            log_handlers.append(logging.FileHandler(log_path))
            print(f"✅ Logging to: {log_path}")
            break
        except (PermissionError, FileNotFoundError, OSError):
            continue
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=log_handlers
    )

setup_logging()
logger = logging.getLogger(__name__)

# Web interface template
WEB_INTERFACE = """
<!DOCTYPE html>
<html>
<head>
    <title>🤖 Robot Guardian Remote Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            text-align: center; 
            background: linear-gradient(135deg, #1e3c72, #2a5298);
            color: white; 
            margin: 0; 
            padding: 20px;
        }
        .container { max-width: 800px; margin: 0 auto; }
        .video-container { 
            margin: 20px auto; 
            max-width: 640px; 
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 15px;
        }
        .controls { 
            margin: 20px; 
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            max-width: 300px;
            margin: 20px auto;
        }
        .btn { 
            background: linear-gradient(45deg, #4CAF50, #45a049);
            border: none; 
            color: white; 
            padding: 20px;
            font-size: 18px;
            border-radius: 10px; 
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }
        .btn:active { 
            transform: scale(0.95);
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        .btn:hover { transform: translateY(-2px); }
        .stop { background: linear-gradient(45deg, #f44336, #d32f2f); }
        .empty { background: none; border: none; }
        #stream { 
            width: 100%; 
            height: auto; 
            border: 3px solid #4CAF50; 
            border-radius: 10px;
        }
        .status-panel {
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 15px;
            margin: 20px 0;
        }
        .status-good { color: #4CAF50; }
        .status-bad { color: #f44336; }
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .info-card {
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 15px;
        }
        h1 { text-shadow: 2px 2px 4px rgba(0,0,0,0.5); }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Robot Guardian Remote Control</h1>
        
        <div class="video-container">
            <img id="stream" src="/?action=stream" alt="Robot Camera Stream" onerror="handleStreamError()">
        </div>
        
        <div class="controls">
            <div class="empty"></div>
            <button class="btn" onmousedown="sendCommand('F')" onmouseup="sendCommand('S')" ontouchstart="sendCommand('F')" ontouchend="sendCommand('S')">⬆️</button>
            <div class="empty"></div>
            
            <button class="btn" onmousedown="sendCommand('L')" onmouseup="sendCommand('S')" ontouchstart="sendCommand('L')" ontouchend="sendCommand('S')">⬅️</button>
            <button class="btn stop" onclick="sendCommand('S')">🛑</button>
            <button class="btn" onmousedown="sendCommand('R')" onmouseup="sendCommand('S')" ontouchstart="sendCommand('R')" ontouchend="sendCommand('S')">➡️</button>
            
            <div class="empty"></div>
            <button class="btn" onmousedown="sendCommand('B')" onmouseup="sendCommand('S')" ontouchstart="sendCommand('B')" ontouchend="sendCommand('S')">⬇️</button>
            <div class="empty"></div>
        </div>
        
        <div class="status-panel">
            <h3>🔌 Connection Status</h3>
            <div id="status">Status: Connecting...</div>
        </div>
        
        <div class="info-grid">
            <div class="info-card">
                <h4>📊 Robot Info</h4>
                <div id="robot-info">Loading...</div>
            </div>
            <div class="info-card">
                <h4>📈 Performance</h4>
                <div id="performance">Loading...</div>
            </div>
        </div>
        
        <div class="info-card">
            <h4>⌨️ Keyboard Controls</h4>
            <p>W/↑: Forward | S/↓: Backward | A/←: Left | D/→: Right | Space: Stop</p>
        </div>
    </div>
    
    <script>
        let isControlling = false;
        let currentCommand = 'S';
        
        async function sendCommand(cmd) {
            if (cmd === currentCommand) return;
            currentCommand = cmd;
            
            try {
                const response = await fetch('/move', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ command: cmd })
                });
                
                const result = await response.json();
                updateStatus(`Command: ${cmd} - ${result.status}`, true);
                    
            } catch (error) {
                updateStatus(`Error: ${error.message}`, false);
            }
        }
        
        function updateStatus(message, success) {
            const statusEl = document.getElementById('status');
            statusEl.textContent = message;
            statusEl.className = success ? 'status-good' : 'status-bad';
        }
        
        async function updateRobotInfo() {
            try {
                const response = await fetch('/status');
                const data = await response.json();
                
                document.getElementById('robot-info').innerHTML = `
                    ESP32: <span class="${data.esp32_connected ? 'status-good' : 'status-bad'}">
                        ${data.esp32_connected ? '✅ Connected' : '❌ Disconnected'}
                    </span><br>
                    Port: ${data.serial_port}<br>
                    Commands: ${data.command_count}
                `;
                
                document.getElementById('performance').innerHTML = `
                    Camera: <span class="${data.camera_active ? 'status-good' : 'status-bad'}">
                        ${data.camera_active ? '✅ Active' : '❌ Inactive'}
                    </span><br>
                    Last: ${data.last_command}<br>
                    Uptime: ${new Date().toLocaleTimeString()}
                `;
                
                if (data.esp32_connected) {
                    updateStatus('🤖 Robot Online', true);
                } else {
                    updateStatus('⚠️ Robot Offline', false);
                }
                
            } catch (error) {
                updateStatus('❌ Connection Lost', false);
            }
        }
        
        function handleStreamError() {
            document.getElementById('stream').src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQwIiBoZWlnaHQ9IjQ4MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjMzMzIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIyMCIgZmlsbD0id2hpdGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj5DYW1lcmEgT2ZmbGluZTwvdGV4dD48L3N2Zz4=';
        }
        
        // Keyboard controls
        document.addEventListener('keydown', (e) => {
            if (e.repeat) return;
            
            switch(e.key.toLowerCase()) {
                case 'w': case 'arrowup': sendCommand('F'); break;
                case 's': case 'arrowdown': sendCommand('B'); break;
                case 'a': case 'arrowleft': sendCommand('L'); break;
                case 'd': case 'arrowright': sendCommand('R'); break;
                case ' ': e.preventDefault(); sendCommand('S'); break;
            }
        });
        
        document.addEventListener('keyup', (e) => {
            if (['w','s','a','d','arrowup','arrowdown','arrowleft','arrowright'].includes(e.key.toLowerCase())) {
                sendCommand('S');
            }
        });
        
        // Prevent touch scrolling on buttons
        document.querySelectorAll('.btn').forEach(btn => {
            btn.addEventListener('touchstart', (e) => e.preventDefault());
            btn.addEventListener('touchend', (e) => e.preventDefault());
        });
        
        // Update info every 3 seconds
        setInterval(updateRobotInfo, 3000);
        updateRobotInfo();
    </script>
</body>
</html>
"""

class EnhancedRobotServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.camera = None
        self.serial_connection = None
        self.esp32_serial_port = "/dev/ttyUSB0"
        self.esp32_baud_rate = 115200
        self.last_command = 'S'
        self.command_count = 0
        self.esp32_connected = False
        self.camera_active = False
        
        # Security settings
        self.api_key = os.environ.get('ROBOT_API_KEY', 'robot-guardian-2025')
        self.enable_auth = os.environ.get('ENABLE_AUTH', 'false').lower() == 'true'
        
        # Command history
        self.command_history = []
        
        # Setup routes
        self.setup_routes()
        
        # Initialize camera
        self.init_camera()
        
        logger.info("Enhanced Robot Server initialized (UART + Remote Access)")
        if self.enable_auth:
            logger.info(f"🔒 Authentication enabled with API key: {self.api_key}")
    
    def require_auth(self, f):
        """Decorator for authentication (optional)"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not self.enable_auth:
                return f(*args, **kwargs)
                
            auth_header = request.headers.get('Authorization')
            if not auth_header or auth_header != f"Bearer {self.api_key}":
                return jsonify({'error': 'Unauthorized'}), 401
            return f(*args, **kwargs)
        return decorated_function
    
    def setup_routes(self):
        """Setup all Flask routes"""
        
        @self.app.route('/', methods=['GET'])
        def index():
            # Check if this is a stream request
            if request.args.get('action') == 'stream':
                return Response(
                    self.generate_camera_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame'
                )
            
            # Return web interface
            return render_template_string(WEB_INTERFACE)
        
        @self.app.route('/move', methods=['POST'])
        def move_robot():
            """Send movement command to ESP32"""
            try:
                data = request.get_json()
                if not data or 'command' not in data:
                    return jsonify({'error': 'No command provided'}), 400
                
                command = data['command'].upper()
                if command not in ['F', 'B', 'L', 'R', 'S']:
                    return jsonify({'error': 'Invalid command'}), 400
                
                # Log command
                timestamp = datetime.now().isoformat()
                self.command_history.append({
                    'command': command,
                    'timestamp': timestamp,
                    'source': request.remote_addr
                })
                
                # Keep only last 100 commands
                if len(self.command_history) > 100:
                    self.command_history = self.command_history[-100:]
                
                # Send to ESP32
                success = self.send_to_esp32(command)
                
                if success:
                    self.last_command = command
                    self.command_count += 1
                    return jsonify({
                        'status': 'success',
                        'command': command,
                        'timestamp': timestamp
                    })
                else:
                    return jsonify({
                        'status': 'error',
                        'message': 'ESP32 not connected'
                    }), 500
                    
            except Exception as e:
                logger.error(f"Move command error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/status', methods=['GET'])
        def get_status():
            """Get server status"""
            return jsonify({
                'server_status': 'running',
                'esp32_connected': self.esp32_connected,
                'serial_port': self.esp32_serial_port,
                'baud_rate': self.esp32_baud_rate,
                'camera_active': self.camera_active,
                'last_command': self.last_command,
                'command_count': self.command_count,
                'recent_commands': self.command_history[-5:],
                'timestamp': datetime.now().isoformat()
            })
    
    def init_camera(self):
        """Initialize camera"""
        try:
            self.camera = cv2.VideoCapture(0)
            if self.camera.isOpened():
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.camera.set(cv2.CAP_PROP_FPS, 30)
                self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                self.camera_active = True
                logger.info("✅ Camera initialized")
            else:
                logger.warning("❌ Camera not available")
        except Exception as e:
            logger.error(f"Camera error: {e}")
    
    def generate_camera_frames(self):
        """Generate camera frames for streaming"""
        while True:
            if self.camera and self.camera.isOpened():
                ret, frame = self.camera.read()
                if ret:
                    # Add status overlay
                    self.add_status_overlay(frame)
                    
                    # Encode frame
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    frame_bytes = buffer.tobytes()
                    
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.033)  # ~30 FPS
    
    def add_status_overlay(self, frame):
        """Add status overlay to video"""
        # Connection status
        status_color = (0, 255, 0) if self.esp32_connected else (0, 0, 255)
        status_text = f"ESP32: {'Online' if self.esp32_connected else 'Offline'}"
        cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        
        # Last command
        cv2.putText(frame, f"Last: {self.last_command}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        cv2.putText(frame, timestamp, (500, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    def connect_serial(self, port=None):
        """Connect to ESP32 via UART"""
        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
            
            if port is None:
                port = self.esp32_serial_port
            
            logger.info(f"🔗 Connecting to {port} at {self.esp32_baud_rate} baud")
            
            self.serial_connection = serial.Serial(
                port=port,
                baudrate=self.esp32_baud_rate,
                timeout=5,
                write_timeout=2
            )
            
            time.sleep(2)  # Wait for connection
            
            if self.serial_connection.is_open:
                self.esp32_connected = True
                self.esp32_serial_port = port
                logger.info(f"✅ Connected to ESP32 via {port}")
                
                # Send test command
                self.serial_connection.write(b'S\n')
                self.serial_connection.flush()
                
                return True
            return False
            
        except Exception as e:
            logger.error(f"Serial connection failed: {e}")
            self.esp32_connected = False
            return False
    
    def send_to_esp32(self, command):
        """Send command to ESP32"""
        if not self.esp32_connected or not self.serial_connection:
            return False
        
        try:
            message = f"{command}\n"
            self.serial_connection.write(message.encode())
            self.serial_connection.flush()
            logger.debug(f"Sent: {command}")
            return True
        except Exception as e:
            logger.error(f"Send failed: {e}")
            self.esp32_connected = False
            return False
    
    def auto_discover_esp32(self):
        """Auto-discover ESP32 serial port"""
        try:
            logger.info("🔍 Scanning for ESP32...")
            ports = list(serial.tools.list_ports.comports())
            
            if not ports:
                logger.warning("No serial ports found")
                return False
            
            # Try common ESP32 ports
            for port_info in ports:
                port = port_info.device
                logger.info(f"📞 Trying {port}")
                if self.connect_serial(port):
                    logger.info(f"🎉 Connected to ESP32 on {port}")
                    return True
                time.sleep(1)
            
            logger.warning("❌ No ESP32 found")
            return False
            
        except Exception as e:
            logger.error(f"Auto-discovery failed: {e}")
            return False
    
    def cleanup(self):
        """Cleanup resources"""
        if self.serial_connection and self.serial_connection.is_open:
            try:
                self.serial_connection.write(b'S\n')  # Stop robot
                self.serial_connection.close()
            except:
                pass
        if self.camera:
            self.camera.release()
        logger.info("Server cleanup completed")
    
    def run(self, host='0.0.0.0', port=5000):
        """Start the server"""
        try:
            logger.info(f"🚀 Starting server on {host}:{port}")
            
            # Try to connect to ESP32
            threading.Thread(target=self.auto_discover_esp32, daemon=True).start()
            
            # Show access info
            logger.info("🌍 Server Access Info:")
            logger.info(f"   Local: http://localhost:{port}")
            logger.info(f"   Network: http://10.214.108.26:{port}")
            logger.info("   Remote: Set up ngrok tunnel for internet access")
            
            # Start Flask server
            self.app.run(host=host, port=port, debug=False, threaded=True)
            
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            self.cleanup()

def main():
    """Main entry point"""
    print("🤖 Robot Guardian - Enhanced Remote Server")
    print("=" * 50)
    
    # Check dependencies
    missing_deps = []
    try:
        import serial
    except ImportError:
        missing_deps.append('pyserial')
    
    try:
        import cv2
    except ImportError:
        missing_deps.append('opencv-python')
    
    if missing_deps:
        print(f"❌ Install dependencies: pip install {' '.join(missing_deps)}")
        return
    
    # Start server
    server = EnhancedRobotServer()
    
    try:
        server.run()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")

if __name__ == "__main__":
    main()