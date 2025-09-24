#!/usr/bin/env python3
"""
🤖 Robot Guardian - Windows AI Control Center
=============================================

Runs on Windows PC to:
- Display GUI interface
- Run YOLO AI model locally 
- Send robot commands to Pi
- Show person tracking with boxes

Requirements:
- pip install opencv-python ultralytics requests tkinter pillow numpy

Usage: python windows_ai_controller.py

Author: Robot Guardian System
Date: September 2025
"""

import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import numpy as np
import requests
import threading
import time
import queue
from datetime import datetime
import json
from PIL import Image, ImageTk
from ultralytics import YOLO
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WindowsAIController:
    def __init__(self):
        # ⚠️ UPDATE THESE URLs WITH YOUR PI ⚠️
        self.PI_BASE_URL = "http://192.168.1.12:5000"  # Updated Pi IP from error log
        # OR use tunnel URL:
        # self.PI_BASE_URL = "https://your-tunnel-url.serveo.net"
        
        # GUI setup
        self.root = tk.Tk()
        self.root.title("🤖 Robot Guardian - AI Control Center")
        self.root.geometry("1000x800")
        self.root.configure(bg='#2b2b2b')
        
        # AI and tracking variables
        self.model = None
        self.model_loaded = False
        self.cap = None
        self.tracking_active = False
        self.current_frame = None
        self.frame_lock = threading.Lock()
        
        # Person tracking settings
        self.auto_tracking = tk.BooleanVar(value=False)
        self.confidence_threshold = tk.DoubleVar(value=0.5)
        self.track_largest_person = tk.BooleanVar(value=True)
        
        # Performance monitoring
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0
        self.commands_sent = 0
        self.last_command_time = 0
        self.command_cooldown = 0.3  # seconds between commands
        
        # Connection status
        self.pi_connected = False
        
        self.setup_gui()
        self.load_yolo_model()
        
    def setup_gui(self):
        """Setup the main GUI interface"""
        # Title bar
        title_frame = tk.Frame(self.root, bg='#2b2b2b', height=60)
        title_frame.pack(fill=tk.X, padx=10, pady=5)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="🤖 Robot Guardian - AI Control Center", 
                              font=('Arial', 18, 'bold'), fg='white', bg='#2b2b2b')
        title_label.pack(side=tk.LEFT, pady=15)
        
        self.connection_status = tk.Label(title_frame, text="⚫ Disconnected", 
                                         font=('Arial', 12), fg='red', bg='#2b2b2b')
        self.connection_status.pack(side=tk.RIGHT, pady=15)
        
        # Main content frame
        main_frame = tk.Frame(self.root, bg='#2b2b2b')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Left side - Video and AI
        left_frame = tk.Frame(main_frame, bg='#3b3b3b', relief=tk.RAISED, bd=2)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Video display
        video_label = tk.Label(left_frame, text="📹 Camera Feed", 
                              font=('Arial', 12, 'bold'), fg='white', bg='#3b3b3b')
        video_label.pack(pady=5)
        
        self.video_frame = tk.Frame(left_frame, bg='black', relief=tk.SUNKEN, bd=2)
        self.video_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.video_canvas = tk.Label(self.video_frame, text="🔄 Connecting to Pi camera...", 
                                    font=('Arial', 14), fg='white', bg='black')
        self.video_canvas.pack(fill=tk.BOTH, expand=True)
        
        # AI status bar
        ai_status_frame = tk.Frame(left_frame, bg='#4b4b4b', height=40)
        ai_status_frame.pack(fill=tk.X, padx=10, pady=5)
        ai_status_frame.pack_propagate(False)
        
        self.fps_label = tk.Label(ai_status_frame, text="FPS: 0", 
                                 font=('Arial', 10), fg='lime', bg='#4b4b4b')
        self.fps_label.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.detection_label = tk.Label(ai_status_frame, text="Detections: 0", 
                                       font=('Arial', 10), fg='cyan', bg='#4b4b4b')
        self.detection_label.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.model_label = tk.Label(ai_status_frame, text="Model: Loading...", 
                                   font=('Arial', 10), fg='yellow', bg='#4b4b4b')
        self.model_label.pack(side=tk.RIGHT, padx=5, pady=5)
        
        # Right side - Controls
        right_frame = tk.Frame(main_frame, bg='#3b3b3b', relief=tk.RAISED, bd=2, width=300)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        right_frame.pack_propagate(False)
        
        # Connection section
        conn_frame = tk.LabelFrame(right_frame, text="🔗 Pi Connection", 
                                  fg='white', bg='#3b3b3b', font=('Arial', 12, 'bold'))
        conn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(conn_frame, text="Pi IP/URL:", fg='white', bg='#3b3b3b').pack(anchor='w', padx=5, pady=2)
        self.pi_url_var = tk.StringVar(value=self.PI_BASE_URL)
        pi_entry = tk.Entry(conn_frame, textvariable=self.pi_url_var, width=35)
        pi_entry.pack(fill=tk.X, padx=5, pady=2)
        
        conn_btn_frame = tk.Frame(conn_frame, bg='#3b3b3b')
        conn_btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(conn_btn_frame, text="🔄 Connect", command=self.connect_to_pi,
                 bg='#4CAF50', fg='white', font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=2)
        tk.Button(conn_btn_frame, text="📊 Test", command=self.test_pi_connection,
                 bg='#2196F3', fg='white', font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=2)
        
        # AI Control section
        ai_frame = tk.LabelFrame(right_frame, text="🧠 AI Control", 
                                fg='white', bg='#3b3b3b', font=('Arial', 12, 'bold'))
        ai_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Checkbutton(ai_frame, text="🎯 Auto Person Tracking", variable=self.auto_tracking,
                      fg='white', bg='#3b3b3b', selectcolor='#5b5b5b', 
                      command=self.toggle_auto_tracking).pack(anchor='w', padx=5, pady=2)
        
        tk.Checkbutton(ai_frame, text="📏 Track Largest Person", variable=self.track_largest_person,
                      fg='white', bg='#3b3b3b', selectcolor='#5b5b5b').pack(anchor='w', padx=5, pady=2)
        
        # Confidence threshold
        tk.Label(ai_frame, text="🎚️ Confidence:", fg='white', bg='#3b3b3b').pack(anchor='w', padx=5, pady=(10,2))
        confidence_frame = tk.Frame(ai_frame, bg='#3b3b3b')
        confidence_frame.pack(fill=tk.X, padx=5, pady=2)
        
        confidence_scale = tk.Scale(confidence_frame, from_=0.1, to=0.9, resolution=0.1,
                                   orient=tk.HORIZONTAL, variable=self.confidence_threshold,
                                   bg='#3b3b3b', fg='white', highlightthickness=0)
        confidence_scale.pack(fill=tk.X)
        
        # Manual Controls section
        manual_frame = tk.LabelFrame(right_frame, text="🎮 Manual Control", 
                                    fg='white', bg='#3b3b3b', font=('Arial', 12, 'bold'))
        manual_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Direction buttons
        btn_frame = tk.Frame(manual_frame, bg='#3b3b3b')
        btn_frame.pack(padx=10, pady=10)
        
        tk.Button(btn_frame, text="↑", font=('Arial', 14, 'bold'), width=4, height=2,
                 command=lambda: self.send_command('F'), bg='#4CAF50', fg='white').grid(row=0, column=1, padx=2, pady=2)
        tk.Button(btn_frame, text="←", font=('Arial', 14, 'bold'), width=4, height=2,
                 command=lambda: self.send_command('L'), bg='#2196F3', fg='white').grid(row=1, column=0, padx=2, pady=2)
        tk.Button(btn_frame, text="⏹", font=('Arial', 14, 'bold'), width=4, height=2,
                 command=lambda: self.send_command('S'), bg='#f44336', fg='white').grid(row=1, column=1, padx=2, pady=2)
        tk.Button(btn_frame, text="→", font=('Arial', 14, 'bold'), width=4, height=2,
                 command=lambda: self.send_command('R'), bg='#2196F3', fg='white').grid(row=1, column=2, padx=2, pady=2)
        tk.Button(btn_frame, text="↓", font=('Arial', 14, 'bold'), width=4, height=2,
                 command=lambda: self.send_command('B'), bg='#FF9800', fg='white').grid(row=2, column=1, padx=2, pady=2)
        
        # Statistics section
        stats_frame = tk.LabelFrame(right_frame, text="📊 Statistics", 
                                   fg='white', bg='#3b3b3b', font=('Arial', 12, 'bold'))
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.stats_text = tk.Text(stats_frame, height=8, width=35, bg='#2b2b2b', fg='white',
                                 font=('Courier', 9), wrap=tk.WORD)
        stats_scrollbar = tk.Scrollbar(stats_frame, orient=tk.VERTICAL, command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=stats_scrollbar.set)
        
        self.stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        stats_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Keyboard bindings
        self.root.bind('<Key>', self.on_key_press)
        self.root.focus_set()
        
        # Start performance monitoring
        self.update_performance_display()
        
    def load_yolo_model(self):
        """Load YOLO model in background"""
        def load_model():
            try:
                self.log("🧠 Loading YOLO model...")
                self.model = YOLO('yolov8n.pt')  # Nano version for speed
                self.model_loaded = True
                self.root.after(0, lambda: self.model_label.config(text="Model: YOLOv8n Ready ✅", fg='lime'))
                self.log("✅ YOLO model loaded successfully")
            except Exception as e:
                self.root.after(0, lambda: self.model_label.config(text="Model: Error ❌", fg='red'))
                self.log(f"❌ Failed to load YOLO model: {e}")
                
        threading.Thread(target=load_model, daemon=True).start()
        
    def connect_to_pi(self):
        """Connect to Pi camera stream"""
        if self.tracking_active:
            self.stop_tracking()
            
        self.PI_BASE_URL = self.pi_url_var.get()
        
        def start_stream():
            try:
                stream_url = f"{self.PI_BASE_URL}/video_feed"
                self.log(f"🔄 Connecting to Pi stream: {stream_url}")
                
                # Configure OpenCV for low-latency MJPEG streaming
                self.cap = cv2.VideoCapture(stream_url)
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimal buffering
                
                if self.cap.isOpened():
                    self.tracking_active = True
                    self.pi_connected = True
                    
                    self.root.after(0, lambda: self.connection_status.config(text="🟢 Pi Connected", fg='lime'))
                    self.log("✅ Connected to Pi camera → ESP32 system")
                    
                    # Start video processing with AI
                    threading.Thread(target=self.process_video_stream, daemon=True).start()
                else:
                    self.root.after(0, lambda: self.connection_status.config(text="❌ Stream Failed", fg='red'))
                    self.log("❌ Pi camera stream failed - check Pi server status")
                    
            except Exception as e:
                self.root.after(0, lambda: self.connection_status.config(text="❌ Error", fg='red'))
                self.log(f"❌ Connection error: {e}")
                
        threading.Thread(target=start_stream, daemon=True).start()
        
    def process_video_stream(self):
        """Process video stream with AI detection"""
        while self.tracking_active and self.cap:
            try:
                ret, frame = self.cap.read()
                
                if not ret:
                    self.log("⚠️ Failed to read frame from Pi")
                    time.sleep(0.1)
                    continue
                    
                # Store current frame
                with self.frame_lock:
                    self.current_frame = frame.copy()
                
                # Run YOLO detection if model is loaded
                processed_frame = frame.copy()
                detections = []
                
                if self.model_loaded and self.model:
                    try:
                        results = self.model(frame, classes=[0], conf=self.confidence_threshold.get(), verbose=False)
                        
                        if len(results[0].boxes) > 0:
                            boxes = results[0].boxes.xyxy.cpu().numpy()
                            confidences = results[0].boxes.conf.cpu().numpy()
                            
                            for i, (box, conf) in enumerate(zip(boxes, confidences)):
                                x1, y1, x2, y2 = box.astype(int)
                                
                                # Draw detection box
                                cv2.rectangle(processed_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                                cv2.putText(processed_frame, f'Person {conf:.2f}', 
                                          (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                                
                                detections.append({
                                    'box': (x1, y1, x2, y2),
                                    'confidence': conf,
                                    'area': (x2 - x1) * (y2 - y1)
                                })
                    
                    except Exception as e:
                        self.log(f"⚠️ YOLO detection error: {e}")
                
                # Auto tracking logic
                if self.auto_tracking.get():
                    if detections:
                        # Reset search mode when person found - send forward first for better movement
                        if hasattr(self, 'search_active') and self.search_active:
                            self.search_active = False
                            self.search_to_tracking_transition = True
                            self.log("🎯 Person found - Transitioning to tracking mode")
                        self.process_auto_tracking(detections, processed_frame.shape)
                    else:
                        # No person detected - activate search mode
                        self.process_search_mode()
                
                # Update display
                self.update_video_display(processed_frame)
                self.update_detection_count(len(detections))
                
                # Update FPS
                self.fps_counter += 1
                
            except Exception as e:
                self.log(f"❌ Video processing error: {e}")
                time.sleep(0.1)
                
    def process_auto_tracking(self, detections, frame_shape):
        """Process automatic person tracking"""
        if not detections or time.time() - self.last_command_time < self.command_cooldown:
            return
        
        # Handle transition from search to tracking - send forward first
        if hasattr(self, 'search_to_tracking_transition') and self.search_to_tracking_transition:
            self.search_to_tracking_transition = False
            self.send_command('F', auto=True)  # Forward first for smooth transition
            self.log("🎯 Search→Track: Forward command sent first")
            return
            
        # Find the target person (largest if enabled, otherwise first)
        if self.track_largest_person.get():
            target = max(detections, key=lambda d: d['area'])
        else:
            target = detections[0]
            
        x1, y1, x2, y2 = target['box']
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        
        frame_width, frame_height = frame_shape[1], frame_shape[0]
        frame_center_x = frame_width / 2
        
        # Calculate movement command
        command = self.calculate_movement_command(center_x, center_y, target['area'], 
                                                frame_width, frame_height)
        
        if command:
            self.send_command(command, auto=True)
            
    def process_search_mode(self):
        """360-degree search when no person is detected"""
        current_time = time.time()
        
        # Initialize search mode tracking
        if not hasattr(self, 'search_active'):
            self.search_active = False
            self.search_start_time = 0
            self.search_last_command_time = 0
            self.search_step = 'scan1'  # 'scan1' -> 'turn' -> 'scan2' -> 'pause'
        
        # Start search if not already active
        if not self.search_active:
            self.search_active = True
            self.search_start_time = current_time
            self.search_last_command_time = 0
            self.search_step = 'scan1'
            self.log("🔍 No person detected - Starting ultra-slow 360° search")
        
        # Initialize turn spam counter for ultra-slow rotation
        if not hasattr(self, 'turn_spam_count'):
            self.turn_spam_count = 0
            self.turn_direction = 'R'  # Start with right, then alternate L/R
            self.micro_turn_count = 0  # Track individual micro-turns
            
        # Ultra-extremely slow multi-phase search with maximum stops
        if self.search_step == 'scan1':
            # Ultra-extended first scanning phase - very long pause
            if current_time - self.search_last_command_time > 12.0:  # 12 second ultra-deep scan
                self.search_last_command_time = current_time
                self.search_step = 'turn_right'
                self.turn_spam_count = 0
                self.micro_turn_count = 0
                self.log("🔍 Search: 12s ultra-deep scan complete → Pico-micro-turns")
                
        elif self.search_step == 'turn_right':
            # Ultra-minimal turn commands with extreme precision
            if current_time - self.search_last_command_time > 0.002:  # 2ms pico-micro-turn
                self.send_command(self.turn_direction, auto=True)  # Turn (R or L)
                self.search_last_command_time = current_time
                self.search_step = 'turn_stop'
                self.micro_turn_count += 1
                direction_name = "right" if self.turn_direction == 'R' else "left"
                self.log(f"🔍 Search: Pico-micro-{direction_name} #{self.micro_turn_count}")
                
        elif self.search_step == 'turn_stop':
            # Immediate stop after each pico-micro-turn
            if current_time - self.search_last_command_time > 0.001:  # 1ms then stop
                self.send_command('S', auto=True)  # Stop
                self.search_last_command_time = current_time
                self.search_step = 'turn_pause1'
                self.log(f"🔍 Search: STOP #{self.micro_turn_count}")
                
        elif self.search_step == 'turn_pause1':
            # First pause phase - extended pause
            if current_time - self.search_last_command_time > 3.0:  # 3s pause for detection
                self.search_last_command_time = current_time
                self.search_step = 'turn_pause2'
                self.log("🔍 Search: Extended pause phase 1 → Pause phase 2")
                
        elif self.search_step == 'turn_pause2':
            # Second pause phase - ultra-extended pause
            if current_time - self.search_last_command_time > 4.0:  # 4s ultra-extended pause
                self.search_last_command_time = current_time
                self.turn_spam_count += 1
                
                # Do 20 pico-micro turn cycles before moving to scan2 (maximum cycles, minimal intensity each)
                if self.turn_spam_count >= 20:
                    self.search_step = 'scan2'
                    direction_name = "right" if self.turn_direction == 'R' else "left"
                    self.log(f"🔍 Search: 20 pico-micro-{direction_name} complete → Long scan phase 2")
                else:
                    self.search_step = 'turn_right'
                    direction_name = "right" if self.turn_direction == 'R' else "left"
                    self.log(f"🔍 Search: Cycle {self.turn_spam_count}/20 complete → Next pico-micro-{direction_name}")
                
        elif self.search_step == 'scan2':
            # Ultra-extended second scanning phase - very long pause
            if current_time - self.search_last_command_time > 10.0:  # 10 second ultra-extended scan
                # Alternate direction for next cycle
                self.turn_direction = 'L' if self.turn_direction == 'R' else 'R'
                next_dir = "left" if self.turn_direction == 'L' else "right"
                
                self.search_last_command_time = current_time
                self.search_step = 'scan1'  # Back to start
                self.log(f"🔍 Search: 10s ultra-extended scan complete → Next ultra-slow cycle ({next_dir})")
            
        # Extend search time for thorough scanning
        if current_time - self.search_start_time > 120:  # 2 minutes of thorough search
            self.log("🔍 Search timeout (2 min) - Stopping to conserve power")
            self.send_command('S', auto=True)
            self.search_active = False
            time.sleep(10)  # Rest for 10 seconds
            
    def calculate_movement_command(self, center_x, center_y, area, frame_width, frame_height):
        """Calculate robot movement based on person position with decreased distance"""
        # Thresholds - adjusted for closer approach
        x_threshold = frame_width * 0.12  # 12% dead zone (tighter centering)
        min_area = (frame_width * frame_height) * 0.08  # 8% minimum size (approach closer)
        max_area = (frame_width * frame_height) * 0.45  # 45% maximum size (get much closer before stopping)
        
        frame_center_x = frame_width / 2
        offset_x = center_x - frame_center_x
        
        # Check if we need to alternate with STOP commands for ESP32 timing
        current_time = time.time()
        if not hasattr(self, 'last_movement_command'):
            self.last_movement_command = 'S'
            self.last_movement_time = 0
        
        # Person too small (far away) - move forward cautiously
        if area < min_area:
            command = 'F'
            
        # Person too large (too close) - stop and maintain distance
        elif area > max_area:
            command = 'S'
            self.log("🛑 Person too close - maintaining safe distance")
            
        # Person off-center horizontally - turn to center
        elif offset_x > x_threshold:
            command = 'R'  # Turn right
        elif offset_x < -x_threshold:
            command = 'L'  # Turn left
            
        # Person centered and good size - approach slowly
        else:
            command = 'F'
        
        # Only add stops for turning commands (L/R), not forward (F)
        if command in ['L', 'R'] and self.last_movement_command not in ['S', command]:
            # For turns, ensure we stop first if coming from different movement
            if current_time - self.last_movement_time > 0.2:  # 200ms since last movement
                self.last_movement_command = 'S'
                self.last_movement_time = current_time
                return 'S'
        
        # Forward movement (F) - no forced stops, allow continuous movement
        # Backward movement (B) and Stop (S) - immediate execution
        
        self.last_movement_command = command
        if command != 'S':
            self.last_movement_time = current_time
            
        return command
        
    def send_command(self, command, auto=False):
        """Send movement command to Pi → ESP32 (GPIO1/3 UART0)"""
        try:
            # Rate limiting - Different speeds for different commands
            current_time = time.time()
            min_interval = 0.05 if command == 'F' else 0.1  # 50ms for forward, 100ms for others
            if current_time - self.last_command_time < min_interval:
                return
                
            # Validate ESP32 command format (must be single uppercase letters)
            if command not in ['F', 'B', 'L', 'R', 'S']:
                self.log(f"❌ Invalid ESP32 command: {command}. Valid: F/B/L/R/S")
                return
                
            url = f"{self.PI_BASE_URL}/move"
            data = {"direction": command}
            
            self.log(f"📤 Windows → Pi → ESP32: {command}")
            
            response = requests.post(url, json=data, timeout=3)
            
            if response.status_code == 200:
                self.commands_sent += 1
                self.last_command_time = current_time
                
                # Parse Pi server response for ESP32 status
                try:
                    result = response.json()
                    uart_status = result.get('uart_status', 'unknown')
                    message = result.get('message', '')
                    prefix = "🤖 Auto" if auto else "🎮 Manual"
                    
                    if uart_status == 'connected':
                        self.log(f"{prefix}: {command} ✅ ESP32 via GPIO1/3")
                    else:
                        self.log(f"{prefix}: {command} ⚠️ Pi OK, ESP32 UART issue")
                        self.log(f"   Check: GPIO1/3 wiring, /dev/ttyS0 permissions")
                        
                except Exception as e:
                    prefix = "🤖 Auto" if auto else "🎮 Manual"
                    self.log(f"{prefix} command: {command} → Pi (response parse error: {e})")
                    
            else:
                self.log(f"❌ Command {command} failed: HTTP {response.status_code}")
                try:
                    error_data = response.json()
                    error_msg = error_data.get('message', 'Unknown error')
                    self.log(f"   💬 Pi error: {error_msg}")
                except:
                    self.log(f"   💬 Raw response: {response.text[:100]}")
                try:
                    error_msg = response.json().get('message', 'Unknown error')
                    self.log(f"   Error details: {error_msg}")
                except:
                    self.log(f"   Response: {response.text[:100]}")
                
        except requests.ConnectionError:
            self.log(f"❌ Command {command} failed: Cannot connect to Pi at {self.PI_BASE_URL}")
            self.log(f"   Check: 1) Pi running? 2) Correct IP? 3) Pi server started?")
        except requests.Timeout:
            self.log(f"⏱️ Command {command} timeout (Pi slow/busy)")
        except Exception as e:
            self.log(f"❌ Command {command} error: {e}")
            
    def test_pi_connection(self):
        """Test connection to Pi server"""
        def test():
            pi_url = self.pi_url_var.get()
            self.log(f"🔍 Testing Pi connection: {pi_url}")
            
            try:
                # Test basic connectivity
                url = f"{pi_url}/status"
                self.log(f"📡 Checking status endpoint: {url}")
                
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Detailed diagnostics
                    uart_status = data.get('uart_status', 'Unknown')
                    camera_status = data.get('camera_status', 'Unknown')
                    commands_received = data.get('commands_received', 0)
                    
                    status_msg = f"✅ Pi Connection Successful!\n\n"
                    status_msg += f"🖥️  Pi Status: {data.get('status', 'Unknown')}\n"
                    status_msg += f"📡 UART to ESP32: {uart_status}\n"
                    status_msg += f"📹 Camera: {camera_status}\n"
                    status_msg += f"🎮 Commands Received: {commands_received}\n"
                    status_msg += f"⚡ Baud Rate: {data.get('baud_rate', 'Unknown')}\n\n"
                    
                    if uart_status != 'connected':
                        status_msg += "⚠️  UART Issue Detected!\n"
                        status_msg += "Fix: Check GPIO wiring Pi↔ESP32\n"
                        status_msg += "Pi GPIO14→ESP32 GPIO1, Pi GPIO15←ESP32 GPIO3\n\n"
                        
                    if camera_status != 'active':
                        status_msg += "⚠️  Camera Issue Detected!\n"
                        status_msg += "Fix: Check camera connection\n\n"
                        
                    status_msg += "Ready for AI tracking!"
                        
                    def show_result():
                        messagebox.showinfo("Pi Connection Test", status_msg)
                        
                    self.root.after(0, show_result)
                    self.log("✅ Pi connection test successful")
                    
                    # Test video feed
                    try:
                        video_url = f"{pi_url}/video_feed"
                        self.log(f"📹 Testing video feed: {video_url}")
                        video_response = requests.get(video_url, timeout=3, stream=True)
                        if video_response.status_code == 200:
                            self.log("✅ Video feed accessible")
                        else:
                            self.log(f"⚠️ Video feed issue: HTTP {video_response.status_code}")
                    except Exception as ve:
                        self.log(f"⚠️ Video feed test failed: {ve}")
                        
                else:
                    error_msg = f"❌ Pi Connection Failed\n\n"
                    error_msg += f"HTTP Status: {response.status_code}\n"
                    error_msg += f"URL: {url}\n\n"
                    error_msg += "Troubleshooting:\n"
                    error_msg += "1. Is Pi server running?\n"
                    error_msg += "2. Correct IP address?\n"
                    error_msg += "3. Network connectivity?"
                    
                    self.root.after(0, lambda: messagebox.showerror("Connection Failed", error_msg))
                    self.log(f"❌ Pi connection failed: HTTP {response.status_code}")
                    
            except requests.ConnectionError:
                error_msg = f"❌ Cannot Connect to Pi\n\n"
                error_msg += f"URL: {pi_url}\n\n"
                error_msg += "Troubleshooting:\n"
                error_msg += "1. Pi server running?\n   python3 pi_camera_server.py\n\n"
                error_msg += "2. Correct Pi IP address?\n\n"
                error_msg += "3. Pi and Windows on same network?\n\n"
                error_msg += "4. Pi firewall blocking port 5000?"
                
                self.root.after(0, lambda: messagebox.showerror("Connection Error", error_msg))
                self.log(f"❌ Connection error: Cannot reach Pi at {pi_url}")
                
            except requests.Timeout:
                error_msg = f"⏱️ Pi Connection Timeout\n\n"
                error_msg += f"Pi is reachable but slow to respond.\n"
                error_msg += f"Try again or check Pi performance."
                
                self.root.after(0, lambda: messagebox.showerror("Timeout Error", error_msg))
                self.log(f"⏱️ Pi connection timeout")
                
            except Exception as e:
                error_msg = f"❌ Connection Error\n\n{str(e)}\n\n"
                error_msg += "Check network and Pi server status."
                
                self.root.after(0, lambda: messagebox.showerror("Connection Error", error_msg))
                self.log(f"❌ Connection error: {e}")
                
        threading.Thread(target=test, daemon=True).start()
        
    def toggle_auto_tracking(self):
        """Toggle automatic tracking mode"""
        if self.auto_tracking.get():
            self.log("🎯 Auto tracking enabled")
        else:
            self.log("🎯 Auto tracking disabled")
            self.send_command('S')  # Stop robot
            
    def stop_tracking(self):
        """Stop video tracking"""
        self.tracking_active = False
        self.pi_connected = False
        
        if self.cap:
            self.cap.release()
            self.cap = None
            
        self.connection_status.config(text="⚫ Disconnected", fg='red')
        self.video_canvas.config(image='', text="📹 Disconnected")
        self.video_canvas.image = None
        
        self.send_command('S')  # Stop robot
        self.log("🛑 Tracking stopped")
        
    def update_video_display(self, frame):
        """Update video display with processed frame"""
        try:
            # Resize frame for display
            display_frame = cv2.resize(frame, (640, 480), interpolation=cv2.INTER_LINEAR)
            
            # Add search mode indicator
            if hasattr(self, 'search_active') and self.search_active:
                cv2.putText(display_frame, "🔍 SEARCHING FOR PERSON...", 
                          (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                # Add rotating search indicator
                import math
                center = (320, 240)
                angle = (time.time() * 90) % 360  # Rotating indicator
                x = int(center[0] + 50 * math.cos(math.radians(angle)))
                y = int(center[1] + 50 * math.sin(math.radians(angle)))
                cv2.circle(display_frame, (x, y), 8, (0, 255, 255), -1)
            
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            
            # Convert to PhotoImage
            image = Image.fromarray(frame_rgb)
            photo = ImageTk.PhotoImage(image)
            
            # Update display (must be in main thread)
            self.root.after(0, self._update_display, photo)
            
        except Exception as e:
            self.log(f"❌ Display update error: {e}")
            
    def _update_display(self, photo):
        """Update display in main thread"""
        self.video_canvas.configure(image=photo, text='')
        self.video_canvas.image = photo
        
    def update_detection_count(self, count):
        """Update detection counter"""
        self.root.after(0, lambda: self.detection_label.config(text=f"Detections: {count}"))
        
    def update_performance_display(self):
        """Update FPS and performance metrics"""
        current_time = time.time()
        elapsed = current_time - self.fps_start_time
        
        if elapsed >= 1.0:
            self.current_fps = self.fps_counter / elapsed
            self.fps_counter = 0
            self.fps_start_time = current_time
            
        self.fps_label.config(text=f"FPS: {self.current_fps:.1f}")
        
        # Schedule next update
        self.root.after(100, self.update_performance_display)
        
    def on_key_press(self, event):
        """Handle keyboard controls"""
        key = event.keysym.lower()
        
        key_map = {
            'up': 'F', 'w': 'F',
            'down': 'B', 's': 'B', 
            'left': 'L', 'a': 'L',
            'right': 'R', 'd': 'R',
            'space': 'S', 'escape': 'S'
        }
        
        if key in key_map:
            self.send_command(key_map[key])
            
    def log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # Update text widget in main thread
        def update_log():
            self.stats_text.insert(tk.END, log_entry)
            self.stats_text.see(tk.END)
            
            # Keep only last 50 lines
            lines = self.stats_text.get("1.0", tk.END).split('\n')
            if len(lines) > 50:
                self.stats_text.delete("1.0", f"{len(lines)-50}.0")
                
        if threading.current_thread() == threading.main_thread():
            update_log()
        else:
            self.root.after(0, update_log)
            
        logger.info(message)
        
    def run(self):
        """Start the application"""
        self.log("🚀 Robot Guardian AI Control Center Started")
        self.log(f"Pi URL: {self.PI_BASE_URL}")
        self.log("1. Update Pi URL above")
        self.log("2. Click '🔄 Connect' to start")
        self.log("3. Enable '🎯 Auto Person Tracking'")
        
        try:
            self.root.mainloop()
        finally:
            self.stop_tracking()

if __name__ == "__main__":
    print("🤖 Robot Guardian - Windows AI Control Center")
    print("=" * 50)
    print()
    print("Features:")
    print("✅ YOLO AI person detection")
    print("✅ Automatic robot following") 
    print("✅ Manual control interface")
    print("✅ Real-time video display")
    print("✅ Performance monitoring")
    print()
    print("Setup:")
    print("1. Update PI_BASE_URL in code with your Pi IP")
    print("2. Make sure Pi server is running")
    print("3. Click Connect and start tracking!")
    print()
    
    try:
        app = WindowsAIController()
        app.run()
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        print(f"❌ Application error: {e}")
        import traceback
        traceback.print_exc()