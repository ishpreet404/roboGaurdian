#!/usr/bin/env python3
"""
Raspberry Pi Robot Command Server with GPIO UART
===============================================

This script runs on Raspberry Pi to:
1. Receive HTTP commands from the GUI
2. Forward commands to ESP32 via GPIO UART at 9600 baud
3. Serve camera stream for remote monitoring

GPIO UART Configuration:
- TX: GPIO14 (Pin 8)
- RX: GPIO15 (Pin 10) 
- GND: Pin 6
- Baud Rate: 9600

Commands: F (Forward), B (Backward), L (Left), R (Right), S (Stop)

Author: Robot Guardian System
Date: September 2025
"""

import os
import sys
import json
import time
import threading
import logging
from datetime import datetime
from flask import Flask, request, jsonify, Response, render_template_string
import cv2

# Try to import serial for UART communication
try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    print("❌ PySerial not installed. Run: pip install pyserial")
    SERIAL_AVAILABLE = False

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

# Enhanced web interface for robot control
WEB_INTERFACE = """
<!DOCTYPE html>
<html>
<head>
    <title>🤖 Robot Controller - GPIO UART</title>
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
        h1 { text-shadow: 2px 2px 4px rgba(0,0,0,0.5); }
        .uart-info {
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 15px;
            margin: 20px 0;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Robot Controller - GPIO UART</h1>
        
        <div class="video-container">
            <img id="stream" src="/?action=stream" alt="Robot Camera Stream" onerror="handleStreamError()">
        </div>
        
        <div class="controls">
            <div class="empty"></div>
            <button class="btn" onmousedown="sendCommand('F')" onmouseup="sendCommand('S')" ontouchstart="sendCommand('F')" ontouchend="sendCommand('S')">⬆️ FWD</button>
            <div class="empty"></div>
            
            <button class="btn" onmousedown="sendCommand('L')" onmouseup="sendCommand('S')" ontouchstart="sendCommand('L')" ontouchend="sendCommand('S')">⬅️ LEFT</button>
            <button class="btn stop" onclick="sendCommand('S')">🛑 STOP</button>
            <button class="btn" onmousedown="sendCommand('R')" onmouseup="sendCommand('S')" ontouchstart="sendCommand('R')" ontouchend="sendCommand('S')">➡️ RIGHT</button>
            
            <div class="empty"></div>
            <button class="btn" onmousedown="sendCommand('B')" onmouseup="sendCommand('S')" ontouchstart="sendCommand('B')" ontouchend="sendCommand('S')">⬇️ BACK</button>
            <div class="empty"></div>
        </div>
        
        <div class="status-panel">
            <h3>🔌 System Status</h3>
            <div id="status">Status: Connecting...</div>
        </div>
        
        <div class="uart-info">
            <h4>⚡ GPIO UART Configuration</h4>
            <div>Baud Rate: 9600 | TX: GPIO14 (Pin 8) | RX: GPIO15 (Pin 10)</div>
            <div>Device: /dev/serial0 | Protocol: 8N1</div>
        </div>
        
        <div class="status-panel">
            <h4>📊 Robot Status</h4>
            <div id="robot-info">Loading...</div>
        </div>
        
        <div class="uart-info">
            <h4>⌨️ Keyboard Controls</h4>
            <p>W/↑: Forward | S/↓: Backward | A/←: Left | D/→: Right | Space: Stop</p>
        </div>
    </div>
    
    <script>
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
                updateStatus(`Command: ${cmd} - ${result.status}`, result.status === 'success');
                    
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
                    UART: <span class="${data.uart_connected ? 'status-good' : 'status-bad'}">
                        ${data.uart_connected ? '✅ Connected' : '❌ Disconnected'}
                    </span><br>
                    Port: ${data.uart_port}<br>
                    Baud: ${data.uart_baud}<br>
                    Commands Sent: ${data.command_count}<br>
                    Last Command: ${data.last_command}<br>
                    Camera: <span class="${data.camera_active ? 'status-good' : 'status-bad'}">
                        ${data.camera_active ? '✅ Active' : '❌ Inactive'}
                    </span>
                `;
                
                if (data.uart_connected) {
                    updateStatus('🤖 Robot Online (GPIO UART)', true);
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
        
        // Update info every 2 seconds
        setInterval(updateRobotInfo, 2000);
        updateRobotInfo();
    </script>
</body>
</html>
"""

class GPIORobotServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.camera = None
        self.uart_connection = None
        self.uart_port = "/dev/serial0"  # GPIO UART port
        self.uart_baud_rate = 9600  # Changed to 9600 for ESP32
        self.last_command = 'S'
        self.command_count = 0
        self.uart_connected = False
        self.camera_active = False
        
        # Command history
        self.command_history = []
        
        # Setup routes
        self.setup_routes()
        
        # Initialize camera
        self.init_camera()
        
        # Configure GPIO UART
        self.setup_gpio_uart()
        
        logger.info("GPIO Robot Server initialized (9600 baud UART)")
    
    def setup_gpio_uart(self):
        """Configure GPIO UART for ESP32 communication"""
        try:
            logger.info("🔧 Configuring GPIO UART...")
            
            # Disable serial console (required for GPIO UART)
            import subprocess
            try:
                # Check if serial console is disabled
                result = subprocess.run(['raspi-config', 'nonint', 'get_serial'], 
                                      capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip() != '1':
                    logger.warning("⚠️ Serial console may be enabled. Disable it in raspi-config")
            except Exception:
                pass
            
            # Enable UART in config
            self.ensure_uart_enabled()
            
            logger.info("✅ GPIO UART configuration completed")
            
        except Exception as e:
            logger.error(f"GPIO UART configuration error: {e}")
    
    def ensure_uart_enabled(self):
        """Ensure UART is enabled in /boot/config.txt"""
        try:
            config_file = '/boot/config.txt'
            backup_file = '/boot/config.txt.backup'
            
            # Create backup
            if os.path.exists(config_file) and not os.path.exists(backup_file):
                import shutil
                shutil.copy(config_file, backup_file)
                logger.info("📋 Created config.txt backup")
            
            # Check current config
            uart_enabled = False
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    content = f.read()
                    if 'enable_uart=1' in content:
                        uart_enabled = True
            
            if not uart_enabled:
                logger.info("🔧 UART not enabled in config.txt")
                logger.info("💡 Add 'enable_uart=1' to /boot/config.txt and reboot")
            else:
                logger.info("✅ UART enabled in config.txt")
                
        except Exception as e:
            logger.warning(f"Could not check UART config: {e}")
    
    def setup_routes(self):
        """Setup Flask routes"""
        
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
            """Send movement command to ESP32 via GPIO UART"""
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
                
                # Send to ESP32 via GPIO UART
                success = self.send_to_esp32_uart(command)
                
                if success:
                    self.last_command = command
                    self.command_count += 1
                    return jsonify({
                        'status': 'success',
                        'command': command,
                        'timestamp': timestamp,
                        'method': 'GPIO UART',
                        'baud': self.uart_baud_rate
                    })
                else:
                    return jsonify({
                        'status': 'error',
                        'message': 'UART communication failed'
                    }), 500
                    
            except Exception as e:
                logger.error(f"Move command error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/status', methods=['GET'])
        def get_status():
            """Get server status"""
            return jsonify({
                'server_status': 'running',
                'uart_connected': self.uart_connected,
                'uart_port': self.uart_port,
                'uart_baud': self.uart_baud_rate,
                'camera_active': self.camera_active,
                'last_command': self.last_command,
                'command_count': self.command_count,
                'recent_commands': self.command_history[-5:],
                'gpio_uart': True,
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
        # UART connection status
        status_color = (0, 255, 0) if self.uart_connected else (0, 0, 255)
        status_text = f"GPIO UART: {'Connected' if self.uart_connected else 'Disconnected'}"
        cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
        
        # Baud rate info
        cv2.putText(frame, f"Baud: {self.uart_baud_rate}", (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        
        # Last command
        cv2.putText(frame, f"Last: {self.last_command}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # Timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        cv2.putText(frame, timestamp, (500, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    def connect_uart(self):
        """Connect to ESP32 via GPIO UART"""
        if not SERIAL_AVAILABLE:
            logger.error("❌ PySerial not available")
            return False
            
        try:
            if self.uart_connection and self.uart_connection.is_open:
                self.uart_connection.close()
            
            logger.info(f"🔗 Connecting to {self.uart_port} at {self.uart_baud_rate} baud")
            
            self.uart_connection = serial.Serial(
                port=self.uart_port,
                baudrate=self.uart_baud_rate,
                timeout=2,
                write_timeout=1,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            
            time.sleep(1)  # Wait for connection
            
            if self.uart_connection.is_open:
                self.uart_connected = True
                logger.info(f"✅ GPIO UART connected at {self.uart_baud_rate} baud")
                
                # Send test command
                self.uart_connection.write(b'S\n')
                self.uart_connection.flush()
                
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ GPIO UART connection failed: {e}")
            if "Permission denied" in str(e):
                logger.error("💡 Add user to dialout group: sudo usermod -a -G dialout $USER")
            elif "No such file" in str(e):
                logger.error("💡 Enable UART: Add 'enable_uart=1' to /boot/config.txt")
            
            self.uart_connected = False
            return False
    
    def send_to_esp32_uart(self, command):
        """Send command to ESP32 via GPIO UART"""
        if not self.uart_connected or not self.uart_connection:
            # Try to reconnect
            if not self.connect_uart():
                return False
        
        try:
            # Send single character command (matching ESP32 code)
            message = f"{command}\n"
            self.uart_connection.write(message.encode('utf-8'))
            self.uart_connection.flush()
            
            logger.info(f"📤 Sent via GPIO UART: {command}")
            return True
            
        except Exception as e:
            logger.error(f"UART send failed: {e}")
            self.uart_connected = False
            return False
    
    def cleanup(self):
        """Cleanup resources"""
        if self.uart_connection and self.uart_connection.is_open:
            try:
                self.uart_connection.write(b'S\n')  # Stop robot
                self.uart_connection.close()
            except:
                pass
        if self.camera:
            self.camera.release()
        logger.info("Server cleanup completed")
    
    def run(self, host='0.0.0.0', port=5000):
        """Start the server"""
        try:
            logger.info(f"🚀 Starting GPIO Robot Server on {host}:{port}")
            
            # Try to connect to ESP32 via GPIO UART
            threading.Thread(target=self.connect_uart, daemon=True).start()
            
            # Show access info
            logger.info("🌍 Server Access Info:")
            logger.info(f"   Local: http://localhost:{port}")
            logger.info("   Network: Check your Pi's IP address")
            logger.info("   GPIO UART: TX=Pin8, RX=Pin10, 9600 baud")
            
            # Start Flask server
            self.app.run(host=host, port=port, debug=False, threaded=True)
            
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            self.cleanup()

def main():
    """Main entry point"""
    print("🤖 Robot Guardian - GPIO UART Server (9600 baud)")
    print("=" * 55)
    
    # Check if running on Raspberry Pi
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
        if 'Raspberry Pi' not in cpuinfo:
            print("⚠️  Warning: Not running on Raspberry Pi")
    except:
        print("⚠️  Warning: Could not detect Raspberry Pi")
    
    # Check dependencies
    missing_deps = []
    
    if not SERIAL_AVAILABLE:
        missing_deps.append('pyserial')
    
    try:
        import cv2
    except ImportError:
        missing_deps.append('opencv-python')
    
    try:
        import flask
    except ImportError:
        missing_deps.append('flask')
    
    if missing_deps:
        print(f"❌ Missing dependencies: {', '.join(missing_deps)}")
        print("Install with: pip install " + " ".join(missing_deps))
        return
    
    # Show GPIO UART info
    print("\n📡 GPIO UART Configuration:")
    print("   Device: /dev/serial0")
    print("   Baud Rate: 9600")
    print("   TX: GPIO14 (Pin 8)")
    print("   RX: GPIO15 (Pin 10)")
    print("   GND: Pin 6")
    print("\n💡 ESP32 Connection:")
    print("   ESP32 RX2 → Pi GPIO14 (Pin 8)")
    print("   ESP32 TX2 → Pi GPIO15 (Pin 10)")
    print("   ESP32 GND → Pi GND (Pin 6)")
    
    # Start server
    server = GPIORobotServer()
    
    try:
        server.run()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    main()