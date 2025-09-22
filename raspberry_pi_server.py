#!/usr/bin/env python3
"""
Raspberry Pi Robot Command Server
==================================

This script runs on Raspberry Pi to:
1. Receive HTTP commands from the person tracking GUI
2. Forward commands to ESP32 via Bluetooth
3. Serve camera stream for remote monitoring

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
from flask import Flask, request, jsonify, Response
import cv2
import bluetooth
from bluetooth import BluetoothSocket, RFCOMM

# Configure logging
def setup_logging():
    """Setup logging with fallback options"""
    log_handlers = [logging.StreamHandler(sys.stdout)]
    
    # Try different log file locations
    possible_log_paths = [
        '/home/pi/robot_server.log',
        f'/home/{os.environ.get("USER", "pi")}/robot_server.log',
        os.path.expanduser('~/robot_server.log'),
        './robot_server.log'
    ]
    
    for log_path in possible_log_paths:
        try:
            # Create directory if it doesn't exist
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

class RobotCommandServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.camera = None
        self.bt_socket = None
        self.esp32_address = "1C:69:20:A4:30:2A"  # BT_CAR_32 MAC address
        self.last_command = 'S'
        self.command_count = 0
        self.esp32_connected = False
        self.camera_active = False
        
        # Command history for debugging
        self.command_history = []
        
        # Setup routes
        self.setup_routes()
        
        # Initialize camera
        self.init_camera()
        
        logger.info("Robot Command Server initialized")
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/', methods=['GET'])
        def index():
            # Check if this is a camera stream request
            if request.args.get('action') == 'stream':
                return Response(
                    self.generate_camera_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame'
                )
            
            # Otherwise return status
            return jsonify({
                'status': 'Robot Command Server Running',
                'version': '1.0',
                'timestamp': datetime.now().isoformat(),
                'esp32_connected': self.esp32_connected,
                'camera_active': self.camera_active,
                'last_command': self.last_command,
                'command_count': self.command_count
            })
        
        @self.app.route('/move', methods=['POST'])
        def move_robot():
            """Receive movement command and forward to ESP32"""
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
                    logger.info(f"Command sent: {command} from {request.remote_addr}")
                    return jsonify({
                        'status': 'success',
                        'command': command,
                        'timestamp': timestamp,
                        'esp32_connected': self.esp32_connected
                    })
                else:
                    logger.error(f"Failed to send command: {command}")
                    return jsonify({
                        'status': 'error',
                        'message': 'Failed to send to ESP32',
                        'esp32_connected': self.esp32_connected
                    }), 500
                    
            except Exception as e:
                logger.error(f"Error in move_robot: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/status', methods=['GET'])
        def get_status():
            """Get detailed server status"""
            return jsonify({
                'server_status': 'running',
                'esp32_connected': self.esp32_connected,
                'esp32_address': self.esp32_address,
                'camera_active': self.camera_active,
                'last_command': self.last_command,
                'command_count': self.command_count,
                'recent_commands': self.command_history[-10:],  # Last 10 commands
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/connect_esp32', methods=['POST'])
        def connect_esp32():
            """Manual ESP32 connection with provided address"""
            try:
                data = request.get_json()
                if not data or 'address' not in data:
                    return jsonify({'error': 'No ESP32 address provided'}), 400
                
                address = data['address']
                success = self.connect_bluetooth(address)
                
                if success:
                    return jsonify({
                        'status': 'connected',
                        'esp32_address': address,
                        'message': 'ESP32 connected successfully'
                    })
                else:
                    return jsonify({
                        'status': 'failed',
                        'message': 'Failed to connect to ESP32'
                    }), 500
                    
            except Exception as e:
                logger.error(f"Error connecting to ESP32: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/scan_bluetooth', methods=['GET'])
        def scan_bluetooth():
            """Scan for nearby Bluetooth devices"""
            try:
                logger.info("Scanning for Bluetooth devices...")
                nearby_devices = bluetooth.discover_devices(duration=8, lookup_names=True)
                
                devices = []
                for addr, name in nearby_devices:
                    devices.append({
                        'address': addr,
                        'name': name or 'Unknown'
                    })
                    logger.info(f"Found device: {name} ({addr})")
                
                return jsonify({
                    'devices': devices,
                    'count': len(devices),
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error scanning Bluetooth: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/camera_stream')
        def camera_stream():
            """Serve camera stream"""
            return Response(
                self.generate_camera_frames(),
                mimetype='multipart/x-mixed-replace; boundary=frame'
            )
    
    def init_camera(self):
        """Initialize camera for streaming"""
        try:
            self.camera = cv2.VideoCapture(0)
            if self.camera.isOpened():
                # Set camera properties
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.camera.set(cv2.CAP_PROP_FPS, 30)
                self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimal latency
                self.camera_active = True
                logger.info("Camera initialized successfully")
            else:
                logger.error("Failed to open camera")
                self.camera_active = False
        except Exception as e:
            logger.error(f"Camera initialization error: {e}")
            self.camera_active = False
    
    def generate_camera_frames(self):
        """Generate camera frames for streaming"""
        while True:
            if self.camera and self.camera.isOpened():
                ret, frame = self.camera.read()
                if ret:
                    # Add status overlay
                    self.add_status_overlay(frame)
                    
                    # Encode frame
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    frame_bytes = buffer.tobytes()
                    
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.033)  # ~30 FPS
    
    def add_status_overlay(self, frame):
        """Add status information to camera frame"""
        # Connection status
        status_color = (0, 255, 0) if self.esp32_connected else (0, 0, 255)
        status_text = f"ESP32: {'Connected' if self.esp32_connected else 'Disconnected'}"
        cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
        
        # Last command
        cmd_color = (0, 255, 255)
        cv2.putText(frame, f"Last: {self.last_command}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, cmd_color, 2)
        
        # Command count
        cv2.putText(frame, f"Count: {self.command_count}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, cmd_color, 2)
        
        # Timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        cv2.putText(frame, timestamp, (500, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    def connect_bluetooth(self, esp32_address):
        """Connect to ESP32 via Bluetooth with detailed error handling"""
        try:
            if self.bt_socket:
                try:
                    self.bt_socket.close()
                except:
                    pass
            
            logger.info(f"🔗 Attempting Bluetooth connection to {esp32_address}")
            
            # Create socket with timeout
            self.bt_socket = BluetoothSocket(RFCOMM)
            self.bt_socket.settimeout(15)  # 15 second timeout
            
            # Attempt connection
            logger.info(f"📞 Connecting to channel 1...")
            self.bt_socket.connect((esp32_address, 1))  # Channel 1
            
            self.esp32_address = esp32_address
            self.esp32_connected = True
            
            logger.info(f"✅ Successfully connected to ESP32: {esp32_address}")
            
            # Send test command and wait for response
            try:
                logger.info("🧪 Testing connection with STOP command...")
                self.bt_socket.send(b'S\n')
                
                # Try to read response
                self.bt_socket.settimeout(3)
                response = self.bt_socket.recv(1024).decode().strip()
                logger.info(f"📥 ESP32 response: {response}")
                
            except Exception as e:
                logger.warning(f"⚠️ No response from ESP32 (might be normal): {e}")
            
            # Reset timeout for normal operation
            self.bt_socket.settimeout(5)
            
            return True
            
        except bluetooth.BluetoothError as e:
            logger.error(f"❌ Bluetooth connection failed: {e}")
            if "Host is down" in str(e):
                logger.error("💡 ESP32 might be powered off or out of range")
            elif "Connection refused" in str(e):
                logger.error("💡 ESP32 might not be accepting connections")
            elif "No route to host" in str(e):
                logger.error("💡 Bluetooth adapter might need restart")
            
            self.esp32_connected = False
            self.bt_socket = None
            return False
            
        except Exception as e:
            logger.error(f"❌ Unexpected connection error: {e}")
            self.esp32_connected = False
            self.bt_socket = None
            return False
    
    def send_to_esp32(self, command):
        """Send command to ESP32 via Bluetooth"""
        if not self.esp32_connected or not self.bt_socket:
            logger.warning("ESP32 not connected")
            return False
        
        try:
            message = f"{command}\n"
            self.bt_socket.send(message.encode('utf-8'))
            logger.debug(f"Sent to ESP32: {command}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send command to ESP32: {e}")
            self.esp32_connected = False
            return False
    
    def auto_discover_esp32(self):
        """Automatically connect to BT_CAR_32 using hardcoded MAC address"""
        try:
            logger.info(f"Connecting to BT_CAR_32 at {self.esp32_address}...")
            
            # Direct connection using hardcoded MAC
            if self.connect_bluetooth(self.esp32_address):
                logger.info("🎉 Successfully connected to BT_CAR_32!")
                return True
            else:
                logger.error("❌ Failed to connect to BT_CAR_32")
                
                # Fallback: Try scanning if direct connection fails
                logger.info("🔍 Fallback: Scanning for BT_CAR_32...")
                nearby_devices = bluetooth.discover_devices(duration=10, lookup_names=True)
                
                for addr, name in nearby_devices:
                    logger.info(f"Found device: {name} ({addr})")
                    if name and ('BT_CAR' in name.upper() or addr == self.esp32_address):
                        logger.info(f"📡 Trying to connect to: {name} ({addr})")
                        if self.connect_bluetooth(addr):
                            self.esp32_address = addr  # Update MAC if different
                            return True
                
                logger.warning("❌ BT_CAR_32 not reachable")
                logger.info("💡 Make sure ESP32 is powered on and within range")
                return False
            
        except Exception as e:
            logger.error(f"Auto-connection failed: {e}")
            return False
    
    def test_esp32_connection(self):
        """Test direct connection to BT_CAR_32"""
        try:
            logger.info(f"🧪 Testing connection to BT_CAR_32 ({self.esp32_address})...")
            
            if self.connect_bluetooth(self.esp32_address):
                # Send test commands
                test_commands = ['S', 'F', 'S', 'B', 'S']
                for cmd in test_commands:
                    logger.info(f"📤 Testing command: {cmd}")
                    if self.send_to_esp32(cmd):
                        logger.info(f"✅ Command {cmd} sent successfully")
                    else:
                        logger.error(f"❌ Command {cmd} failed")
                    time.sleep(0.5)
                
                # Final stop
                self.send_to_esp32('S')
                logger.info("🎉 BT_CAR_32 connection test completed!")
                return True
            else:
                logger.error("❌ Could not establish test connection")
                return False
                
        except Exception as e:
            logger.error(f"Test connection failed: {e}")
            return False

    def cleanup(self):
        """Cleanup resources"""
        if self.bt_socket:
            self.bt_socket.close()
        if self.camera:
            self.camera.release()
        logger.info("Server cleanup completed")
    
    def run(self, host='0.0.0.0', port=5000):
        """Start the server"""
        try:
            logger.info(f"Starting Robot Command Server on {host}:{port}")
            
            # Try to auto-discover ESP32
            threading.Thread(target=self.auto_discover_esp32, daemon=True).start()
            
            # Start Flask server
            self.app.run(host=host, port=port, debug=False, threaded=True)
            
        except KeyboardInterrupt:
            logger.info("Server shutdown requested")
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            self.cleanup()

def main():
    """Main entry point"""
    print("🤖 Robot Guardian - Raspberry Pi Command Server")
    print("=" * 50)
    print("Starting server...")
    
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
    try:
        import bluetooth
    except ImportError:
        missing_deps.append('pybluez')
    
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
    
    # Start server
    server = RobotCommandServer()
    
    try:
        server.run()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    main()