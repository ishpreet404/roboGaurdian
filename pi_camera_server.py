#!/usr/bin/env python3
"""
🥧 Robot Guardian - Raspberry Pi Camera Server
==============================================

Runs on Raspberry Pi to:
- Stream camera video via HTTP
- Receive robot commands via HTTP API
- Forward commands to ESP32 via UART
- Provide status information

Requirements:
- sudo apt install python3-opencv python3-pip
- pip3 install flask pyserial opencv-python

Usage: python3 pi_camera_server.py

Hardware Setup:
- Pi GPIO14 (Pin 8, TX) → ESP32 GPIO1 (TX/D1)  
- Pi GPIO15 (Pin 10, RX) ← ESP32 GPIO3 (RX/D3)
- Pi GND (Pin 6) → ESP32 GND

Author: Robot Guardian System
Date: September 2025
"""

import cv2
import time
import threading
import json
import os
import psutil
from datetime import datetime
from flask import Flask, Response, request, jsonify, render_template_string
import serial
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

class PiCameraServer:
    def __init__(self):
        # Hardware configuration for ESP32 UART0 communication
        # Pi GPIO14/15 → ESP32 GPIO1/3 (UART0)
        self.uart_port = '/dev/ttyS0'
        self.baud_rate = 9600
        self.uart = None
        self.uart_connected = False
        
        # Camera configuration
        self.camera = None
        self.camera_active = False
        self.current_frame = None
        self.frame_lock = threading.Lock()
        
        # Camera settings (optimized for streaming)
        self.frame_width = 640
        self.frame_height = 480
        self.fps = 30
        self.jpeg_quality = 80
        
        # Statistics
        self.commands_received = 0
        self.frames_served = 0
        self.start_time = datetime.now()
        self.last_command_time = None
        self.last_command = None
        
        self.initialize_hardware()
        
    def initialize_hardware(self):
        """Initialize UART and camera"""
        # Initialize UART for ESP32 communication
        try:
            self.uart = serial.Serial(
                port=self.uart_port,
                baudrate=self.baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.5,
                write_timeout=0.5
            )
            
            # Test UART
            self.uart.reset_input_buffer()
            self.uart.reset_output_buffer()
            
            self.uart_connected = True
            logger.info(f"✅ UART initialized on {self.uart_port} at {self.baud_rate} baud")
            
        except Exception as e:
            logger.error(f"❌ UART initialization failed: {e}")
            logger.error("   Make sure UART is enabled: sudo raspi-config → Interface Options → Serial Port")
            self.uart_connected = False
            
        # Initialize camera
        try:
            # Try different camera indices (Pi Camera or USB)
            for camera_id in [0, 1, -1]:
                self.camera = cv2.VideoCapture(camera_id)
                if self.camera.isOpened():
                    logger.info(f"📹 Found camera at index {camera_id}")
                    break
                else:
                    self.camera.release()
                    
            if not self.camera.isOpened():
                raise Exception("No camera found - check camera connection")
                
            # Set optimized camera properties for robot streaming
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height) 
            self.camera.set(cv2.CAP_PROP_FPS, self.fps)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimal buffering for low latency
            
            # Test camera
            ret, test_frame = self.camera.read()
            if ret:
                self.camera_active = True
                logger.info(f"✅ Camera ready: {self.frame_width}x{self.frame_height} @ {self.fps}fps")
                
                # Start camera capture thread
                threading.Thread(target=self.camera_capture_loop, daemon=True).start()
            else:
                raise Exception("Camera test failed - check camera permissions")
                
        except Exception as e:
            logger.error(f"❌ Camera initialization failed: {e}")
            logger.error("   Make sure camera is connected and enabled")
            self.camera_active = False
            
    def camera_capture_loop(self):
        """Continuous camera capture loop"""
        logger.info("📹 Camera capture loop started")
        
        while self.camera_active and self.camera:
            try:
                ret, frame = self.camera.read()
                
                if ret:
                    # Store frame thread-safely
                    with self.frame_lock:
                        self.current_frame = frame.copy()
                else:
                    logger.warning("⚠️ Failed to capture frame")
                    time.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"❌ Camera capture error: {e}")
                time.sleep(0.5)
                
        logger.info("📹 Camera capture loop stopped")
        
    def generate_video_stream(self):
        """Generate MJPEG video stream"""
        while True:
            frame = None
            
            # Get current frame
            with self.frame_lock:
                if self.current_frame is not None:
                    frame = self.current_frame.copy()
                    
            if frame is not None:
                try:
                    # Encode frame as JPEG
                    encode_params = [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality]
                    ret, buffer = cv2.imencode('.jpg', frame, encode_params)
                    
                    if ret:
                        frame_bytes = buffer.tobytes()
                        self.frames_served += 1
                        
                        # Yield frame in MJPEG format
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n'
                               b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n' +
                               frame_bytes + b'\r\n')
                    else:
                        logger.warning("⚠️ Frame encoding failed")
                        
                except Exception as e:
                    logger.error(f"❌ Frame encoding error: {e}")
                    
            else:
                # No frame available, send placeholder
                time.sleep(0.033)  # ~30 FPS fallback
                
    def send_uart_command(self, command):
        """Send command to ESP32 via UART"""
        if not self.uart_connected or not self.uart:
            logger.warning(f"⚠️ UART not available for command: {command}")
            return False
            
        try:
            # Send single command character (ESP32 expects F, B, L, R, S)
            command_str = f"{command}\n"
            self.uart.write(command_str.encode('utf-8'))
            self.uart.flush()
            
            # Try to read ESP32 acknowledgment (ACK:F or NAK:F)
            start_time = time.time()
            response = ""
            
            while time.time() - start_time < 0.5:  # 500ms timeout for ESP32 response
                if self.uart.in_waiting > 0:
                    try:
                        response = self.uart.readline().decode('utf-8', errors='ignore').strip()
                        if response:
                            if response.startswith('ACK:'):
                                logger.info(f"✅ Command {command} → ESP32: {response}")
                            elif response.startswith('NAK:'):
                                logger.warning(f"⚠️ ESP32 rejected command {command}: {response}")
                            else:
                                logger.info(f"📤 ESP32 response: {response}")
                            break
                    except Exception as e:
                        logger.error(f"UART read error: {e}")
                        break
                time.sleep(0.01)
                
            if not response:
                logger.info(f"📤 Command {command} sent to ESP32 (no acknowledgment)")
            
            self.commands_received += 1
            self.last_command_time = datetime.now()
            self.last_command = command
            return True
            
        except Exception as e:
            logger.error(f"❌ UART command error: {e}")
            return False
            
    def get_system_status(self):
        """Get comprehensive system status"""
        try:
            # Calculate uptime
            uptime = datetime.now() - self.start_time
            
            # Get system info
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get temperature (if available)
            temperature = "Unknown"
            try:
                with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                    temp = int(f.read()) / 1000.0
                    temperature = f"{temp:.1f}°C"
            except Exception:
                pass
                
            return {
                'status': 'running',
                'uart_status': 'connected' if self.uart_connected else 'disconnected',
                'camera_status': 'active' if self.camera_active else 'inactive',
                'baud_rate': self.baud_rate,
                'resolution': f"{self.frame_width}x{self.frame_height}",
                'fps': self.fps,
                'jpeg_quality': self.jpeg_quality,
                'commands_received': self.commands_received,
                'frames_served': self.frames_served,
                'uptime': str(uptime).split('.')[0],
                'last_command': self.last_command or 'None',
                'last_command_time': self.last_command_time.strftime('%H:%M:%S') if self.last_command_time else 'None',
                'cpu_usage': f"{cpu_percent:.1f}%",
                'memory_usage': f"{memory.percent:.1f}%",
                'disk_usage': f"{disk.percent:.1f}%",
                'temperature': temperature
            }
            
        except Exception as e:
            logger.error(f"❌ Status error: {e}")
            return {'status': 'error', 'message': str(e)}

# Global server instance
server = PiCameraServer()

# Flask routes
@app.route('/')
def index():
    """Web interface for robot control"""
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>🥧 Pi Robot Camera Server</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            background: #1e1e1e; 
            color: white; 
            margin: 0; 
            padding: 20px; 
            text-align: center;
        }
        .container { max-width: 800px; margin: 0 auto; }
        .header { margin-bottom: 30px; }
        .status { 
            background: #2a2a2a; 
            padding: 15px; 
            border-radius: 10px; 
            margin: 20px 0; 
            text-align: left;
        }
        .video-container { margin: 20px 0; }
        .video-stream { 
            max-width: 100%; 
            height: auto;
            border: 3px solid #333; 
            border-radius: 10px; 
        }
        .controls { 
            display: flex; 
            justify-content: center; 
            gap: 10px; 
            margin: 20px 0; 
            flex-wrap: wrap;
        }
        .btn { 
            background: #4CAF50; 
            color: white; 
            border: none; 
            padding: 15px 20px; 
            margin: 5px; 
            border-radius: 8px; 
            cursor: pointer; 
            font-size: 16px;
            font-weight: bold;
            min-width: 60px;
        }
        .btn:hover { background: #45a049; }
        .btn.stop { background: #f44336; }
        .btn.dir { background: #2196F3; }
        .grid { 
            display: grid; 
            grid-template-columns: repeat(3, 1fr); 
            gap: 10px; 
            max-width: 200px; 
            margin: 0 auto; 
        }
        .info { font-size: 14px; color: #ccc; margin: 10px 0; }
        @media (max-width: 600px) {
            .controls { flex-direction: column; align-items: center; }
            .grid { max-width: 150px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🥧 Pi Robot Camera Server</h1>
            <p class="info">Raspberry Pi Camera Stream & Robot Control</p>
        </div>
        
        <div class="video-container">
            <img class="video-stream" src="/video_feed" alt="Robot Camera Feed" id="videoStream">
        </div>
        
        <div class="controls">
            <div>
                <h3>🎮 Robot Controls</h3>
                <div class="grid">
                    <div></div>
                    <button class="btn dir" onclick="sendCommand('F')" title="Forward">↑</button>
                    <div></div>
                    <button class="btn dir" onclick="sendCommand('L')" title="Left">←</button>
                    <button class="btn stop" onclick="sendCommand('S')" title="Stop">⏹</button>
                    <button class="btn dir" onclick="sendCommand('R')" title="Right">→</button>
                    <div></div>
                    <button class="btn dir" onclick="sendCommand('B')" title="Backward">↓</button>
                    <div></div>
                </div>
            </div>
        </div>
        
        <div class="controls">
            <button class="btn" onclick="getStatus()">📊 System Status</button>
            <button class="btn stop" onclick="sendCommand('S')">🛑 Emergency Stop</button>
        </div>
        
        <div class="status" id="statusDisplay">
            <h3>📊 System Information</h3>
            <p>Click "System Status" to update...</p>
        </div>
        
        <div class="info">
            <p>🖥️ <strong>For AI Control:</strong> Use the Windows AI Controller app</p>
            <p>🌐 <strong>This Interface:</strong> Basic manual control and monitoring</p>
            <p>⌨️ <strong>Keyboard:</strong> Arrow keys or WASD for movement, Space to stop</p>
        </div>
    </div>
    
    <script>
        // Send robot command
        function sendCommand(cmd) {
            fetch('/move', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({direction: cmd})
            })
            .then(response => response.json())
            .then(data => {
                console.log('Command result:', data);
                if (data.status !== 'success') {
                    alert('Command failed: ' + (data.message || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Command error:', error);
                alert('Command failed: ' + error.message);
            });
        }
        
        // Get system status
        function getStatus() {
            fetch('/status')
            .then(response => response.json())
            .then(data => {
                const statusHtml = `
                    <h3>📊 System Status</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div>
                            <p><strong>🟢 Server:</strong> ${data.status}</p>
                            <p><strong>📡 UART:</strong> ${data.uart_status}</p>
                            <p><strong>📹 Camera:</strong> ${data.camera_status}</p>
                            <p><strong>⚡ Baud Rate:</strong> ${data.baud_rate}</p>
                            <p><strong>📐 Resolution:</strong> ${data.resolution}</p>
                            <p><strong>🎬 FPS:</strong> ${data.fps}</p>
                        </div>
                        <div>
                            <p><strong>🕒 Uptime:</strong> ${data.uptime}</p>
                            <p><strong>📤 Commands:</strong> ${data.commands_received}</p>
                            <p><strong>🎥 Frames:</strong> ${data.frames_served}</p>
                            <p><strong>🌡️ CPU:</strong> ${data.cpu_usage}</p>
                            <p><strong>💾 Memory:</strong> ${data.memory_usage}</p>
                            <p><strong>🔥 Temp:</strong> ${data.temperature}</p>
                        </div>
                    </div>
                    <p><strong>🎮 Last Command:</strong> ${data.last_command} (${data.last_command_time})</p>
                `;
                document.getElementById('statusDisplay').innerHTML = statusHtml;
            })
            .catch(error => {
                console.error('Status error:', error);
                document.getElementById('statusDisplay').innerHTML = 
                    '<h3>❌ Status Error</h3><p>' + error.message + '</p>';
            });
        }
        
        // Keyboard controls
        document.addEventListener('keydown', function(event) {
            switch(event.key) {
                case 'ArrowUp': case 'w': case 'W': sendCommand('F'); break;
                case 'ArrowDown': case 's': case 'S': sendCommand('B'); break;
                case 'ArrowLeft': case 'a': case 'A': sendCommand('L'); break;
                case 'ArrowRight': case 'd': case 'D': sendCommand('R'); break;
                case ' ': case 'Escape': sendCommand('S'); event.preventDefault(); break;
            }
        });
        
        // Auto-refresh status every 30 seconds
        setInterval(getStatus, 30000);
        
        // Load initial status
        setTimeout(getStatus, 1000);
        
        // Video stream error handling
        document.getElementById('videoStream').onerror = function() {
            this.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQwIiBoZWlnaHQ9IjQ4MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjMzMzIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIyMCIgZmlsbD0iI2ZmZiIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPvCfk7kgQ2FtZXJhIE5vdCBBdmFpbGFibGU8L3RleHQ+PC9zdmc+';
            this.alt = '📹 Camera stream not available';
        };
    </script>
</body>
</html>
    """)

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    if not server.camera_active:
        # Return error image if camera not available
        def error_stream():
            yield b'--frame\r\nContent-Type: text/plain\r\n\r\nCamera not available\r\n'
        return Response(error_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')
    
    return Response(
        server.generate_video_stream(),
        mimetype='multipart/x-mixed-replace; boundary=frame',
        headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
    )

@app.route('/move', methods=['POST'])
def move_robot():
    """Handle robot movement commands"""
    try:
        data = request.get_json()
        
        if not data or 'direction' not in data:
            return jsonify({'status': 'error', 'message': 'Missing direction parameter'}), 400
            
        direction = data['direction'].upper().strip()
        
        # Validate command
        valid_commands = ['F', 'B', 'L', 'R', 'S']
        if direction not in valid_commands:
            return jsonify({
                'status': 'error',
                'message': f'Invalid direction: {direction}. Valid: {valid_commands}'
            }), 400
            
        # Send command to ESP32
        success = server.send_uart_command(direction)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'Command {direction} sent successfully',
                'uart_status': 'connected' if server.uart_connected else 'disconnected',
                'command': direction
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to send command to ESP32',
                'uart_status': 'disconnected'
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Move command error: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Get system status"""
    try:
        status = server.get_system_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"❌ Status error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    logger.info("🥧 Pi Robot Camera Server Starting...")
    logger.info("=" * 50)
    logger.info(f"UART: {server.uart_port} at {server.baud_rate} baud")
    logger.info(f"Camera: {server.frame_width}x{server.frame_height} @ {server.fps}fps")
    logger.info(f"UART Status: {'✅ Connected' if server.uart_connected else '❌ Disconnected'}")
    logger.info(f"Camera Status: {'✅ Active' if server.camera_active else '❌ Inactive'}")
    logger.info("")
    
    if not server.uart_connected:
        logger.warning("⚠️  UART not connected! Commands will not reach ESP32.")
        logger.warning("   Enable UART: sudo raspi-config → Interface Options → Serial Port")
        logger.warning("   Hardware: Connect Pi GPIO14→ESP32 RX2, Pi GPIO15←ESP32 TX2, GND-GND")
        
    if not server.camera_active:
        logger.warning("⚠️  Camera not active! Video stream will not work.")
        logger.warning("   Check camera connection and enable it in raspi-config")
        
    logger.info("🌐 Starting Flask server...")
    logger.info("   Local access: http://PI_IP:5000")
    logger.info("   Video stream: http://PI_IP:5000/video_feed")
    logger.info("   Status API: http://PI_IP:5000/status")
    logger.info("")
    logger.info("🖥️  Connect from Windows AI Controller for full AI features!")
    logger.info("")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
    finally:
        if server.camera:
            server.camera.release()
        if server.uart:
            server.uart.close()
        logger.info("👋 Goodbye!")