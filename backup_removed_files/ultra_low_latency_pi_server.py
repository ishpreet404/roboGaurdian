#!/usr/bin/env python3
"""
Ultra Low-Latency Pi Server Configuration
========================================

Optimized Raspberry Pi server for minimal streaming latency.
This version includes aggressive optimizations for tunnel streaming.

Key Optimizations:
- Reduced frame buffering 
- Lower resolution options
- Faster JPEG compression
- Minimal processing overhead
- Optimized for remote access

Author: Robot Guardian System
Date: September 2025
"""

import cv2
import time
import threading
from flask import Flask, Response, request, jsonify, render_template_string
import serial
import json
import psutil
import os
from datetime import datetime, timedelta
import logging
import queue

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

class UltraLowLatencyPiServer:
    def __init__(self):
        # UART Configuration
        self.uart_port = '/dev/serial0'
        self.baud_rate = 9600
        self.uart = None
        self.uart_connected = False
        
        # Camera Configuration - Optimized for speed
        self.camera = None
        self.camera_active = False
        self.frame_queue = queue.Queue(maxsize=1)  # Ultra minimal buffer
        self.current_frame = None
        self.frame_lock = threading.Lock()
        
        # Performance settings
        self.frame_width = 480       # Reduced for speed
        self.frame_height = 360      # Reduced for speed  
        self.target_fps = 20         # Balanced FPS
        self.jpeg_quality = 60       # Balanced quality/speed
        self.frame_skip = 1          # Skip frames if needed
        
        # Statistics
        self.commands_sent = 0
        self.frames_served = 0
        self.start_time = datetime.now()
        self.last_command_time = None
        
        # Auto-optimization
        self.enable_auto_optimization = True
        self.performance_samples = []
        self.optimization_interval = 10  # seconds
        
        self.initialize_hardware()
        
    def initialize_hardware(self):
        """Initialize UART and camera with optimizations"""
        # Initialize UART
        try:
            self.uart = serial.Serial(
                port=self.uart_port,
                baudrate=self.baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.1,  # Short timeout for responsiveness
                write_timeout=0.1
            )
            self.uart_connected = True
            logger.info(f"✅ UART initialized on {self.uart_port} at {self.baud_rate} baud")
        except Exception as e:
            logger.error(f"❌ UART initialization failed: {e}")
            self.uart_connected = False
            
        # Initialize camera with optimizations
        try:
            self.camera = cv2.VideoCapture(0)
            
            if self.camera.isOpened():
                # Set camera properties for speed
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
                self.camera.set(cv2.CAP_PROP_FPS, self.target_fps)
                self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimal buffer
                
                # Additional optimizations
                self.camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # Faster exposure
                self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 0)          # Disable autofocus
                
                # Start camera thread
                self.camera_active = True
                threading.Thread(target=self.camera_loop, daemon=True).start()
                
                logger.info(f"✅ Camera initialized: {self.frame_width}x{self.frame_height} @ {self.target_fps}fps")
            else:
                logger.error("❌ Camera initialization failed")
                
        except Exception as e:
            logger.error(f"❌ Camera setup error: {e}")
            
        # Start performance monitoring
        if self.enable_auto_optimization:
            threading.Thread(target=self.performance_monitor, daemon=True).start()
            
    def camera_loop(self):
        """Ultra-optimized camera capture loop"""
        frame_count = 0
        last_optimize_time = time.time()
        
        while self.camera_active and self.camera:
            try:
                ret, frame = self.camera.read()
                
                if ret:
                    frame_count += 1
                    
                    # Frame skipping for performance
                    if frame_count % (self.frame_skip + 1) != 0:
                        continue
                    
                    # Resize if needed (additional speed optimization)
                    if frame.shape[1] != self.frame_width or frame.shape[0] != self.frame_height:
                        frame = cv2.resize(frame, (self.frame_width, self.frame_height), 
                                         interpolation=cv2.INTER_LINEAR)
                    
                    # Store frame (non-blocking)
                    with self.frame_lock:
                        self.current_frame = frame
                        
                    # Dynamic optimization every few seconds
                    current_time = time.time()
                    if self.enable_auto_optimization and current_time - last_optimize_time > 5:
                        self.optimize_settings()
                        last_optimize_time = current_time
                        
                else:
                    logger.warning("⚠️ Failed to capture frame")
                    time.sleep(0.01)
                    
            except Exception as e:
                logger.error(f"❌ Camera loop error: {e}")
                time.sleep(0.1)
                
    def optimize_settings(self):
        """Dynamically optimize settings based on performance"""
        try:
            # Get system load
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_percent = psutil.virtual_memory().percent
            
            # Adjust settings based on load
            if cpu_percent > 80:
                # High CPU load - reduce quality
                if self.frame_width > 320:
                    self.frame_width = max(320, self.frame_width - 80)
                    self.frame_height = max(240, self.frame_height - 60)
                    self.jpeg_quality = max(30, self.jpeg_quality - 10)
                    self.frame_skip = min(3, self.frame_skip + 1)
                    logger.info(f"🚀 CPU optimization: {self.frame_width}x{self.frame_height}, Q={self.jpeg_quality}")
                    
            elif cpu_percent < 40:
                # Low CPU load - increase quality
                if self.frame_width < 640:
                    self.frame_width = min(640, self.frame_width + 80)
                    self.frame_height = min(480, self.frame_height + 60)
                    self.jpeg_quality = min(80, self.jpeg_quality + 10)
                    self.frame_skip = max(0, self.frame_skip - 1)
                    logger.info(f"🔥 CPU optimization: {self.frame_width}x{self.frame_height}, Q={self.jpeg_quality}")
                    
        except Exception as e:
            logger.error(f"❌ Optimization error: {e}")
            
    def performance_monitor(self):
        """Monitor performance and log statistics"""
        while True:
            try:
                time.sleep(10)
                
                # Calculate uptime
                uptime = datetime.now() - self.start_time
                
                # Get system stats
                cpu_percent = psutil.cpu_percent()
                memory = psutil.virtual_memory()
                
                logger.info(f"📊 Performance - CPU: {cpu_percent:.1f}%, "
                          f"Memory: {memory.percent:.1f}%, "
                          f"Frames: {self.frames_served}, "
                          f"Commands: {self.commands_sent}, "
                          f"Uptime: {uptime}")
                          
            except Exception as e:
                logger.error(f"❌ Performance monitor error: {e}")
                
    def send_uart_command(self, command):
        """Send command via UART with optimization"""
        if not self.uart_connected or not self.uart:
            logger.warning(f"⚠️ UART not available for command: {command}")
            return False
            
        try:
            # Send command
            command_str = f"{command}\n"
            self.uart.write(command_str.encode('utf-8'))
            self.uart.flush()  # Ensure immediate send
            
            # Try to read acknowledgment (non-blocking)
            start_time = time.time()
            ack_received = False
            
            while time.time() - start_time < 0.1:  # 100ms timeout
                if self.uart.in_waiting > 0:
                    response = self.uart.readline().decode('utf-8', errors='ignore').strip()
                    if response:
                        logger.info(f"📤 Command {command} → ESP32 response: {response}")
                        ack_received = True
                        break
                time.sleep(0.01)
            
            if not ack_received:
                logger.warning(f"⚠️ No acknowledgment for command: {command}")
                
            self.commands_sent += 1
            self.last_command_time = datetime.now()
            return True
            
        except Exception as e:
            logger.error(f"❌ UART command error: {e}")
            return False
            
    def generate_frames(self):
        """Generate optimized video frames"""
        while True:
            try:
                frame = None
                
                # Get latest frame
                with self.frame_lock:
                    if self.current_frame is not None:
                        frame = self.current_frame.copy()
                        
                if frame is not None:
                    # Encode with optimized settings
                    encode_params = [
                        cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality,
                        cv2.IMWRITE_JPEG_OPTIMIZE, 1,
                        cv2.IMWRITE_JPEG_PROGRESSIVE, 0  # Faster encoding
                    ]
                    
                    ret, buffer = cv2.imencode('.jpg', frame, encode_params)
                    
                    if ret:
                        frame_bytes = buffer.tobytes()
                        
                        # Yield frame in MJPEG format
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n'
                               b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n' +
                               frame_bytes + b'\r\n')
                        
                        self.frames_served += 1
                    else:
                        logger.warning("⚠️ Frame encoding failed")
                        
                else:
                    # No frame available, send empty response
                    time.sleep(0.033)  # ~30 FPS fallback
                    
            except Exception as e:
                logger.error(f"❌ Frame generation error: {e}")
                time.sleep(0.1)

# Global server instance
server = UltraLowLatencyPiServer()

# Flask routes
@app.route('/')
def index():
    """Optimized web interface"""
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>🚀 Ultra Low-Latency Robot Control</title>
    <style>
        body { font-family: Arial, sans-serif; background: #1e1e1e; color: white; margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 20px; }
        .video-container { text-align: center; margin: 20px 0; }
        .video-stream { max-width: 100%; border: 2px solid #333; border-radius: 8px; }
        .controls { display: flex; justify-content: space-around; flex-wrap: wrap; margin: 20px 0; }
        .control-group { background: #2a2a2a; padding: 15px; border-radius: 8px; margin: 10px; }
        .btn { background: #4CAF50; color: white; border: none; padding: 10px 20px; margin: 5px; border-radius: 5px; cursor: pointer; font-size: 16px; }
        .btn:hover { background: #45a049; }
        .btn.stop { background: #f44336; }
        .btn.dir { background: #2196F3; }
        .stats { background: #2a2a2a; padding: 15px; border-radius: 8px; margin-top: 20px; }
        .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; max-width: 200px; margin: 0 auto; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Ultra Low-Latency Robot Control</h1>
            <p>Optimized for remote tunnel streaming</p>
        </div>
        
        <div class="video-container">
            <img class="video-stream" src="/video_feed" alt="Robot Camera Stream">
        </div>
        
        <div class="controls">
            <div class="control-group">
                <h3>🎮 Robot Controls</h3>
                <div class="grid">
                    <div></div>
                    <button class="btn dir" onclick="sendCommand('F')">↑</button>
                    <div></div>
                    <button class="btn dir" onclick="sendCommand('L')">←</button>
                    <button class="btn stop" onclick="sendCommand('S')">⏹</button>
                    <button class="btn dir" onclick="sendCommand('R')">→</button>
                    <div></div>
                    <button class="btn dir" onclick="sendCommand('B')">↓</button>
                    <div></div>
                </div>
            </div>
            
            <div class="control-group">
                <h3>⚡ Quick Actions</h3>
                <button class="btn" onclick="getStatus()">📊 Status</button>
                <button class="btn stop" onclick="sendCommand('S')">🛑 Emergency Stop</button>
            </div>
        </div>
        
        <div class="stats" id="status">
            <h3>📊 System Status</h3>
            <p>Click "Status" to update...</p>
        </div>
    </div>
    
    <script>
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
                    alert('Command failed: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Command error:', error);
                alert('Command failed: ' + error);
            });
        }
        
        function getStatus() {
            fetch('/status')
            .then(response => response.json())
            .then(data => {
                document.getElementById('status').innerHTML = 
                    '<h3>📊 System Status</h3>' +
                    '<p><strong>Status:</strong> ' + data.status + '</p>' +
                    '<p><strong>UART:</strong> ' + data.uart_status + '</p>' +
                    '<p><strong>Camera:</strong> ' + data.camera_status + '</p>' +
                    '<p><strong>Resolution:</strong> ' + data.resolution + '</p>' +
                    '<p><strong>Quality:</strong> ' + data.jpeg_quality + '%</p>' +
                    '<p><strong>Commands Sent:</strong> ' + data.commands_sent + '</p>' +
                    '<p><strong>Frames Served:</strong> ' + data.frames_served + '</p>' +
                    '<p><strong>Uptime:</strong> ' + data.uptime + '</p>';
            })
            .catch(error => {
                console.error('Status error:', error);
                document.getElementById('status').innerHTML = 
                    '<h3>❌ Status Error</h3><p>' + error + '</p>';
            });
        }
        
        // Auto-refresh status every 10 seconds
        setInterval(getStatus, 10000);
        
        // Keyboard controls
        document.addEventListener('keydown', function(event) {
            switch(event.key) {
                case 'ArrowUp': case 'w': case 'W': sendCommand('F'); break;
                case 'ArrowDown': case 's': case 'S': sendCommand('B'); break;
                case 'ArrowLeft': case 'a': case 'A': sendCommand('L'); break;
                case 'ArrowRight': case 'd': case 'D': sendCommand('R'); break;
                case ' ': case 'Escape': sendCommand('S'); break;
            }
        });
    </script>
</body>
</html>
    """)

@app.route('/video_feed')
def video_feed():
    """Ultra low-latency video stream"""
    return Response(server.generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame',
                   headers={'Cache-Control': 'no-cache, no-store, must-revalidate',
                           'Pragma': 'no-cache',
                           'Expires': '0'})

@app.route('/move', methods=['POST'])
def move_robot():
    """Handle robot movement commands"""
    try:
        data = request.get_json()
        direction = data.get('direction', '').upper()
        
        # Validate command
        if direction not in ['F', 'B', 'L', 'R', 'S']:
            return jsonify({
                'status': 'error',
                'message': f'Invalid direction: {direction}'
            }), 400
            
        # Send command
        success = server.send_uart_command(direction)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'Command {direction} sent',
                'uart_status': 'connected' if server.uart_connected else 'disconnected'
            })
        else:
            return jsonify({
                'status': 'error', 
                'message': 'Failed to send command',
                'uart_status': 'disconnected'
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Move command error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Get system status"""
    try:
        uptime = datetime.now() - server.start_time
        
        return jsonify({
            'status': 'running',
            'uart_status': 'connected' if server.uart_connected else 'disconnected',
            'camera_status': 'active' if server.camera_active else 'inactive',
            'baud_rate': server.baud_rate,
            'resolution': f"{server.frame_width}x{server.frame_height}",
            'target_fps': server.target_fps,
            'jpeg_quality': server.jpeg_quality,
            'frame_skip': server.frame_skip,
            'commands_sent': server.commands_sent,
            'frames_served': server.frames_served,
            'uptime': str(uptime).split('.')[0],
            'last_command': server.last_command_time.strftime('%H:%M:%S') if server.last_command_time else 'None',
            'auto_optimization': server.enable_auto_optimization
        })
        
    except Exception as e:
        logger.error(f"❌ Status error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    logger.info("🚀 Ultra Low-Latency Pi Server Starting...")
    logger.info(f"UART: {server.uart_port} at {server.baud_rate} baud")
    logger.info(f"Camera: {server.frame_width}x{server.frame_height} @ {server.target_fps}fps")
    logger.info(f"JPEG Quality: {server.jpeg_quality}%")
    logger.info(f"Auto Optimization: {'Enabled' if server.enable_auto_optimization else 'Disabled'}")
    
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