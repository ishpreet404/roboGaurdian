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
import serial
import serial.tools.list_ports

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
        format='%(asctime)s - %(levelname)s - %(message should be the)s',
        handlers=log_handlers
    )

setup_logging()
logger = logging.getLogger(__name__)

class RobotCommandServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.camera = None
        self.serial_connection = None
        self.esp32_serial_port = "/dev/ttyUSB0"  # Default USB-to-Serial port
        self.esp32_baud_rate = 115200  # Match ESP32 serial baud rate
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
        
        logger.info("Robot Command Server initialized (UART mode)")
    
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
                'serial_port': self.esp32_serial_port,
                'baud_rate': self.esp32_baud_rate,
                'camera_active': self.camera_active,
                'last_command': self.last_command,
                'command_count': self.command_count,
                'recent_commands': self.command_history[-10:],  # Last 10 commands
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/connect_esp32', methods=['POST'])
        def connect_esp32():
            """Manual ESP32 connection with provided serial port"""
            try:
                data = request.get_json()
                if not data or 'port' not in data:
                    return jsonify({'error': 'No serial port provided'}), 400
                
                port = data['port']
                baud_rate = data.get('baud_rate', 115200)
                success = self.connect_serial(port, baud_rate)
                
                if success:
                    return jsonify({
                        'status': 'connected',
                        'serial_port': port,
                        'baud_rate': baud_rate,
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
        
        @self.app.route('/scan_serial', methods=['GET'])
        def scan_serial():
            """Scan for available serial ports"""
            try:
                logger.info("Scanning for serial ports...")
                available_ports = list(serial.tools.list_ports.comports())
                
                ports = []
                for port in available_ports:
                    ports.append({
                        'device': port.device,
                        'description': port.description,
                        'hwid': port.hwid
                    })
                    logger.info(f"Found port: {port.device} - {port.description}")
                
                return jsonify({
                    'ports': ports,
                    'count': len(ports),
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error scanning serial ports: {e}")
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
    
    def connect_serial(self, port=None, baud_rate=None):
        """Connect to ESP32 via UART serial connection"""
        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
            
            # Use provided port or default
            if port is None:
                port = self.esp32_serial_port
            if baud_rate is None:
                baud_rate = self.esp32_baud_rate
            
            logger.info(f"🔗 Attempting serial connection to {port} at {baud_rate} baud")
            
            # Create serial connection
            self.serial_connection = serial.Serial(
                port=port,
                baudrate=baud_rate,
                timeout=5,
                write_timeout=2,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            
            # Wait for connection to stabilize
            time.sleep(2)
            
            if self.serial_connection.is_open:
                self.esp32_serial_port = port
                self.esp32_baud_rate = baud_rate
                self.esp32_connected = True
                
                logger.info(f"✅ Successfully connected to ESP32 via {port}")
                
                # Send test command
                try:
                    logger.info("🧪 Testing connection with STOP command...")
                    self.serial_connection.write(b'S\n')
                    self.serial_connection.flush()
                    
                    # Try to read response
                    if self.serial_connection.in_waiting > 0:
                        response = self.serial_connection.read_all().decode().strip()
                        logger.info(f"📥 ESP32 response: {response}")
                    else:
                        logger.info("📥 No immediate response (normal)")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Test command failed (might be normal): {e}")
                
                return True
            else:
                logger.error("❌ Serial port failed to open")
                return False
                
        except serial.SerialException as e:
            logger.error(f"❌ Serial connection failed: {e}")
            if "Permission denied" in str(e):
                logger.error("💡 Add user to dialout group: sudo usermod -a -G dialout $USER")
            elif "No such file or directory" in str(e):
                logger.error("💡 Check if ESP32 is connected and port exists")
            elif "Device or resource busy" in str(e):
                logger.error("💡 Port might be in use by another program")
            
            self.esp32_connected = False
            self.serial_connection = None
            return False
            
        except Exception as e:
            logger.error(f"❌ Unexpected serial connection error: {e}")
            self.esp32_connected = False
            self.serial_connection = None
            return False
    
    def send_to_esp32(self, command):
        """Send command to ESP32 via UART serial"""
        if not self.esp32_connected or not self.serial_connection or not self.serial_connection.is_open:
            logger.warning("ESP32 not connected via serial")
            return False
        
        try:
            # Send single character command (matching your ESP32 code)
            message = f"{command}\n"
            self.serial_connection.write(message.encode('utf-8'))
            self.serial_connection.flush()  # Ensure data is sent immediately
            
            logger.debug(f"Sent to ESP32 via serial: {command}")
            
            # Try to read any response
            time.sleep(0.1)  # Small delay for ESP32 to respond
            if self.serial_connection.in_waiting > 0:
                response = self.serial_connection.read_all().decode().strip()
                logger.debug(f"ESP32 serial response: {response}")
            
            return True
            
        except serial.SerialException as e:
            logger.error(f"Serial communication error: {e}")
            self.esp32_connected = False
            return False
        except Exception as e:
            logger.error(f"Failed to send command to ESP32: {e}")
            self.esp32_connected = False
            return False
    
    def auto_discover_esp32(self):
        """Automatically discover and connect to ESP32 via serial ports"""
        try:
            logger.info("🔍 Scanning for ESP32 on serial ports...")
            
            # List all available serial ports
            available_ports = list(serial.tools.list_ports.comports())
            
            if not available_ports:
                logger.warning("❌ No serial ports found")
                return False
            
            logger.info("📋 Available serial ports:")
            for port in available_ports:
                logger.info(f"   {port.device} - {port.description}")
            
            # Try common ESP32 serial ports
            esp32_ports = [
                "/dev/ttyUSB0",  # USB-to-Serial adapter
                "/dev/ttyUSB1",
                "/dev/ttyACM0",  # Direct USB connection
                "/dev/ttyACM1",
                "/dev/serial0",  # Raspberry Pi serial
                "/dev/ttyS0"     # Hardware serial
            ]
            
            # Also add any detected USB-to-Serial devices
            for port in available_ports:
                if any(keyword in port.description.lower() for keyword in 
                      ['usb', 'serial', 'cp210x', 'ch340', 'ftdi']):
                    if port.device not in esp32_ports:
                        esp32_ports.insert(0, port.device)
            
            # Try connecting to each port
            for port in esp32_ports:
                if any(p.device == port for p in available_ports):
                    logger.info(f"� Trying port: {port}")
                    if self.connect_serial(port):
                        logger.info(f"🎉 Successfully connected to ESP32 on {port}!")
                        return True
                    time.sleep(1)  # Brief pause between attempts
            
            logger.warning("❌ Could not connect to ESP32 on any serial port")
            logger.info("💡 Check ESP32 connection and drivers")
            return False
            
        except Exception as e:
            logger.error(f"Auto-discovery failed: {e}")
            return False
    
    def test_esp32_connection(self):
        """Test direct serial connection to ESP32"""
        try:
            logger.info(f"🧪 Testing serial connection to ESP32 on {self.esp32_serial_port}...")
            
            if self.connect_serial(self.esp32_serial_port):
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
                logger.info("🎉 ESP32 serial connection test completed!")
                return True
            else:
                logger.error("❌ Could not establish test connection")
                return False
                
        except Exception as e:
            logger.error(f"Test connection failed: {e}")
            return False

    def cleanup(self):
        """Cleanup resources"""
        if self.serial_connection and self.serial_connection.is_open:
            try:
                # Send stop command before closing
                self.serial_connection.write(b'S\n')
                self.serial_connection.flush()
                time.sleep(0.1)
                self.serial_connection.close()
            except:
                pass
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
    print("🤖 Robot Guardian - Raspberry Pi Command Server (UART Mode)")
    print("=" * 60)
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
        import serial
    except ImportError:
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
    
    # Check for serial ports
    try:
        import serial.tools.list_ports
        ports = list(serial.tools.list_ports.comports())
        if ports:
            print("📋 Available serial ports:")
            for port in ports:
                print(f"   {port.device} - {port.description}")
        else:
            print("⚠️  No serial ports detected - check ESP32 connection")
    except Exception as e:
        print(f"⚠️  Could not scan serial ports: {e}")
    
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