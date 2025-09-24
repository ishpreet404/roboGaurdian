#!/usr/bin/env python3
"""
Complete System Integration Test
===============================

Tests the complete flow: GUI → Pi → ESP32
- Person tracking with YOLO
- Pi camera stream integration  
- GPIO UART communication at 9600 baud
- Robot movement commands

Hardware Setup Required:
- Raspberry Pi with camera
- ESP32 with motor driver
- UART connection: Pi GPIO14→ESP32 RX2, Pi GPIO15←ESP32 TX2, GND-GND

Author: Robot Guardian System
Date: September 2025
"""

import cv2
import numpy as np
import requests
import json
import time
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
import queue
from ultralytics import YOLO
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SystemTester:
    def __init__(self):
        self.pi_server_url = "http://192.168.1.100:5000"  # Update with Pi IP
        self.model = None
        self.cap = None
        self.running = False
        self.command_queue = queue.Queue()
        self.last_detection_time = 0
        self.detection_cooldown = 0.5  # seconds
        
        # GUI setup
        self.root = tk.Tk()
        self.root.title("🤖 Robot Guardian System - Full Integration Test")
        self.root.geometry("1200x800")
        
        self.setup_gui()
        self.load_model()
        
    def setup_gui(self):
        """Setup the testing GUI"""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = ttk.Label(main_frame, text="🤖 Robot Guardian System - Integration Test", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Connection frame
        conn_frame = ttk.LabelFrame(main_frame, text="🔗 Connection Status", padding=10)
        conn_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.status_label = ttk.Label(conn_frame, text="Not connected", foreground="red")
        self.status_label.pack(side=tk.LEFT)
        
        ttk.Button(conn_frame, text="Test Pi Connection", 
                  command=self.test_pi_connection).pack(side=tk.RIGHT)
        
        # Control frame
        control_frame = ttk.LabelFrame(main_frame, text="🎮 Manual Controls", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Control buttons
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack()
        
        ttk.Button(btn_frame, text="↑ Forward", command=lambda: self.send_command('F')).grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(btn_frame, text="← Left", command=lambda: self.send_command('L')).grid(row=1, column=0, padx=5, pady=2)
        ttk.Button(btn_frame, text="⏹ Stop", command=lambda: self.send_command('S')).grid(row=1, column=1, padx=5, pady=2)
        ttk.Button(btn_frame, text="→ Right", command=lambda: self.send_command('R')).grid(row=1, column=2, padx=5, pady=2)
        ttk.Button(btn_frame, text="↓ Backward", command=lambda: self.send_command('B')).grid(row=2, column=1, padx=5, pady=2)
        
        # Auto tracking frame
        auto_frame = ttk.LabelFrame(main_frame, text="🎯 Auto Tracking", padding=10)
        auto_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.auto_var = tk.BooleanVar()
        ttk.Checkbutton(auto_frame, text="Enable Auto Person Tracking", 
                       variable=self.auto_var, command=self.toggle_auto_tracking).pack(side=tk.LEFT)
        
        self.tracking_status = ttk.Label(auto_frame, text="Disabled", foreground="gray")
        self.tracking_status.pack(side=tk.RIGHT)
        
        # Statistics frame
        stats_frame = ttk.LabelFrame(main_frame, text="📊 Statistics", padding=10)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.stats_text = tk.Text(stats_frame, height=8, width=80)
        scrollbar = ttk.Scrollbar(stats_frame, orient=tk.VERTICAL, command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=scrollbar.set)
        
        self.stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bottom buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="🚀 Start System Test", 
                  command=self.start_system_test).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="🛑 Stop Test", 
                  command=self.stop_system_test).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📊 Show Pi Status", 
                  command=self.show_pi_status).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="❌ Exit", 
                  command=self.root.quit).pack(side=tk.RIGHT)
        
    def load_model(self):
        """Load YOLO model"""
        try:
            self.log("Loading YOLO model...")
            self.model = YOLO('yolov8n.pt')  # Nano version for speed
            self.log("✅ YOLO model loaded successfully")
        except Exception as e:
            self.log(f"❌ Failed to load YOLO model: {e}")
            
    def test_pi_connection(self):
        """Test connection to Raspberry Pi server"""
        try:
            self.log("Testing Pi connection...")
            response = requests.get(f"{self.pi_server_url}/status", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                self.status_label.config(text="✅ Connected", foreground="green")
                self.log(f"✅ Pi connection successful: {data}")
            else:
                self.status_label.config(text="❌ Error", foreground="red")
                self.log(f"❌ Pi responded with status {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            self.status_label.config(text="❌ No connection", foreground="red")
            self.log(f"❌ Cannot connect to Pi at {self.pi_server_url}")
        except Exception as e:
            self.status_label.config(text="❌ Error", foreground="red")
            self.log(f"❌ Connection test failed: {e}")
            
    def send_command(self, command):
        """Send command to robot via Pi server"""
        try:
            self.log(f"Sending command: {command}")
            
            response = requests.post(f"{self.pi_server_url}/move", 
                                   json={'direction': command}, 
                                   timeout=3)
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"✅ Command sent: {result}")
            else:
                self.log(f"❌ Command failed with status {response.status_code}")
                
        except Exception as e:
            self.log(f"❌ Failed to send command {command}: {e}")
            
    def toggle_auto_tracking(self):
        """Toggle automatic person tracking"""
        if self.auto_var.get():
            self.start_tracking()
        else:
            self.stop_tracking()
            
    def start_tracking(self):
        """Start person tracking"""
        try:
            self.log("Starting person tracking...")
            
            # Try Pi camera stream first
            stream_url = f"{self.pi_server_url}/video_feed"
            self.cap = cv2.VideoCapture(stream_url)
            
            if not self.cap.isOpened():
                self.log("Pi stream not available, using local camera...")
                self.cap = cv2.VideoCapture(0)
                
            if self.cap.isOpened():
                self.running = True
                self.tracking_status.config(text="Active", foreground="green")
                threading.Thread(target=self.tracking_loop, daemon=True).start()
                self.log("✅ Person tracking started")
            else:
                self.log("❌ No camera available")
                self.auto_var.set(False)
                
        except Exception as e:
            self.log(f"❌ Failed to start tracking: {e}")
            self.auto_var.set(False)
            
    def stop_tracking(self):
        """Stop person tracking"""
        self.running = False
        self.tracking_status.config(text="Disabled", foreground="gray")
        
        if self.cap:
            self.cap.release()
            self.cap = None
            
        self.send_command('S')  # Stop robot
        self.log("🛑 Person tracking stopped")
        
    def tracking_loop(self):
        """Main tracking loop"""
        while self.running and self.cap:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    self.log("❌ Failed to read frame")
                    break
                    
                # Run YOLO detection
                if self.model:
                    results = self.model(frame, classes=[0])  # Class 0 is 'person'
                    
                    # Process detections
                    if len(results[0].boxes) > 0:
                        self.process_detections(results[0].boxes, frame.shape)
                    else:
                        # No person detected - stop robot
                        if time.time() - self.last_detection_time > 1.0:  # 1 second timeout
                            self.send_command('S')
                            
                time.sleep(0.1)  # Small delay
                
            except Exception as e:
                self.log(f"❌ Tracking error: {e}")
                break
                
        self.running = False
        
    def process_detections(self, boxes, frame_shape):
        """Process person detections and send robot commands"""
        if time.time() - self.last_detection_time < self.detection_cooldown:
            return
            
        # Find the largest person (closest to camera)
        best_box = None
        best_area = 0
        
        for box in boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            area = (x2 - x1) * (y2 - y1)
            
            if area > best_area:
                best_area = area
                best_box = (x1, y1, x2, y2)
                
        if best_box:
            x1, y1, x2, y2 = best_box
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            
            frame_center_x = frame_shape[1] / 2
            frame_center_y = frame_shape[0] / 2
            
            # Calculate relative position
            offset_x = center_x - frame_center_x
            offset_y = center_y - frame_center_y
            
            # Determine command based on person position
            command = self.calculate_tracking_command(offset_x, offset_y, best_area, frame_shape)
            
            if command:
                self.send_command(command)
                self.last_detection_time = time.time()
                self.log(f"👤 Person detected: offset_x={offset_x:.1f}, offset_y={offset_y:.1f}, area={best_area:.0f}, command={command}")
                
    def calculate_tracking_command(self, offset_x, offset_y, area, frame_shape):
        """Calculate robot command based on person position"""
        frame_width = frame_shape[1]
        frame_height = frame_shape[0]
        
        # Thresholds
        x_threshold = frame_width * 0.1  # 10% of frame width
        min_area = (frame_width * frame_height) * 0.05  # 5% of frame area
        max_area = (frame_width * frame_height) * 0.3   # 30% of frame area
        
        # If person is too small (far), move forward
        if area < min_area:
            return 'F'
            
        # If person is too large (close), stop or move back
        if area > max_area:
            return 'S'
            
        # If person is off-center horizontally, turn
        if offset_x > x_threshold:
            return 'R'  # Person is to the right, turn right
        elif offset_x < -x_threshold:
            return 'L'  # Person is to the left, turn left
            
        # Person is centered, move forward slowly
        return 'F'
        
    def start_system_test(self):
        """Start comprehensive system test"""
        self.log("🚀 Starting comprehensive system test...")
        
        # Test 1: Pi connection
        self.test_pi_connection()
        time.sleep(1)
        
        # Test 2: Command sequence
        commands = ['F', 'S', 'L', 'S', 'R', 'S', 'B', 'S']
        for cmd in commands:
            self.send_command(cmd)
            time.sleep(0.5)
            
        # Test 3: Auto tracking
        if not self.auto_var.get():
            self.auto_var.set(True)
            self.start_tracking()
            
        self.log("✅ System test sequence completed")
        
    def stop_system_test(self):
        """Stop all testing"""
        self.stop_tracking()
        self.send_command('S')
        self.log("🛑 All tests stopped")
        
    def show_pi_status(self):
        """Show detailed Pi server status"""
        try:
            response = requests.get(f"{self.pi_server_url}/status", timeout=5)
            if response.status_code == 200:
                status = response.json()
                
                message = f"""📊 Raspberry Pi Status:
                
🔗 Connection: OK
⚡ UART Status: {status.get('uart_status', 'Unknown')}
📡 Baud Rate: {status.get('baud_rate', 'Unknown')}
📹 Camera: {status.get('camera_status', 'Unknown')}
🕒 Uptime: {status.get('uptime', 'Unknown')}
📊 Commands Sent: {status.get('commands_sent', 'Unknown')}
🐍 Python Version: {status.get('python_version', 'Unknown')}
💾 Free Memory: {status.get('free_memory', 'Unknown')}"""
                
                messagebox.showinfo("Pi Server Status", message)
            else:
                messagebox.showerror("Error", f"Failed to get status: {response.status_code}")
                
        except Exception as e:
            messagebox.showerror("Connection Error", f"Cannot connect to Pi: {e}")
            
    def log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        self.stats_text.insert(tk.END, log_message)
        self.stats_text.see(tk.END)
        logger.info(message)
        
        # Keep only last 100 lines
        lines = self.stats_text.get("1.0", tk.END).split('\n')
        if len(lines) > 100:
            self.stats_text.delete("1.0", f"{len(lines)-100}.0")
            
    def run(self):
        """Start the GUI"""
        self.log("🤖 Robot Guardian System - Integration Tester Started")
        self.log(f"Pi Server URL: {self.pi_server_url}")
        self.log("Click 'Test Pi Connection' to begin")
        
        try:
            self.root.mainloop()
        finally:
            self.stop_tracking()

if __name__ == "__main__":
    print("🤖 Robot Guardian System - Integration Tester")
    print("=" * 50)
    print()
    print("This tool tests the complete system:")
    print("✅ GUI → Raspberry Pi communication")
    print("✅ Pi → ESP32 UART communication (9600 baud)")
    print("✅ Person tracking with YOLO")
    print("✅ Automatic robot movement")
    print()
    print("Make sure to:")
    print("1. Update Pi IP address in the code")
    print("2. Run raspberry_pi_gpio_uart_server.py on Pi")
    print("3. Flash esp32_robot_9600_baud.ino to ESP32")
    print("4. Connect UART wires: Pi GPIO14→ESP32 RX2, Pi GPIO15←ESP32 TX2")
    print()
    
    try:
        tester = SystemTester()
        tester.run()
    except KeyboardInterrupt:
        print("\n🛑 System test interrupted by user")
    except Exception as e:
        print(f"❌ System test failed: {e}")
        import traceback
        traceback.print_exc()