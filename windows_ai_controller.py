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

import os
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
import socket
import torch
import collections
from flask import Flask, Response, render_template_string
import pygame

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WindowsAIController:
    def __init__(self):
        # ⚠️ UPDATE THESE URLs WITH YOUR PI ⚠️
        self.PI_BASE_URL = "http://192.168.27.192:5000"  # Updated by set_pi_server_url.py
        env_pi_url = os.getenv("WINDOWS_PI_BASE_URL")
        if env_pi_url:
            self.PI_BASE_URL = env_pi_url.rstrip("/")
        
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
        self.command_cooldown = 0.1  # Reduced from 0.3 to 0.1 seconds for faster response
        # Gentle turn sequencing state
        self.pending_turn_sequence = None
        self.last_turn_sequence_info = {'stops_sent': 0, 'total_stops': 0}

        # Multi-mode behaviour (care companion, watchdog, edumate)
        self.operating_mode = 'care_companion'
        self.mode_metadata = {}
        self.mode_lock = threading.Lock()
        self.available_modes = [
            {
                'id': 'care_companion',
                'label': 'Care Companion',
                'description': 'Friendly reminders, Hindi assistant, and gentle alerts.',
            },
            {
                'id': 'watchdog',
                'label': 'Watchdog',
                'description': 'Security sweep mode with loud alarms on motion.',
            },
            {
                'id': 'edumate',
                'label': 'Edumate',
                'description': 'Parents push Hindi lessons; robot stays still and listens.',
            },
        ]
        self.watchdog_alert_interval = 8.0
        self._last_watchdog_alert = 0.0
        self._watchdog_person_present = False
        self._watchdog_alarm_stop = threading.Event()
        self._watchdog_alarm_thread = None
        self._watchdog_alarm_active = False
        self._auto_tracking_before_mode = self.auto_tracking.get()
        self._mode_summary_cache = None

        # Inference performance tuning - OPTIMIZED
        self.inference_size = 224            # Smaller size for much faster inference (224 vs 320)
        self.max_inference_fps = 5           # Reduced from 8 to 5 FPS to prevent overload
        self.last_inference_time = 0
        self.model_device = 'cpu'            # will be set appropriately when model loads
        self.inference_skip_frames = 12       # Skip 6 frames between inferences (every 6th frame)
        self.current_skip_count = 0
        self.model_retry_count = 0
        self.max_model_retries = 3
        self.model_crashed = False
        # Detection smoothing (avoid flicker) - optimized for lower memory
        self.detection_history = collections.deque(maxlen=6)  # Reduced from 8 to 6 for memory
        self.detection_keep_seconds = 0.8   # Increased to smooth over longer period
        self.crying_history = collections.deque(maxlen=6)     # Reduced for memory optimization
        
        # Connection status
        self.pi_connected = False
        
        # Crying detection variables
        self.crying_detection_enabled = tk.BooleanVar(value=True)
        self.crying_detected = False
        self.last_crying_alert = 0
        self.crying_alert_cooldown = 5.0  # seconds
        self.crying_confidence_threshold = tk.DoubleVar(value=0.7)
        # Tuning: require multiple positives within window
        self.crying_min_positives = 3
        self.crying_window_seconds = 2.0
        # Throttle crying checks to avoid running heavy face analysis every frame
        self.crying_check_interval = 0.4
        self._last_crying_check_time = 0
        
        # Face detection setup (will be initialized after GUI)
        self.face_detection = None  # Use OpenCV fallback
        self.face_cascade = None
        self.eye_cascade = None
        
        # Internet streaming variables
        self.streaming_enabled = tk.BooleanVar(value=False)
        self.streaming_port = tk.IntVar(value=8080)
        self.flask_app = None
        self.streaming_thread = None
        self.stream_frame = None
        self.stream_lock = threading.Lock()
        # Streaming performance tuning - OPTIMIZED
        self.stream_fps = 15           # Increased for smoother display
        self.jpeg_quality = 50         # Lower quality for better performance  
        # Display throttling to avoid PhotoImage overload on main thread
        self.display_fps = 25          # Increased for 1080p display (higher FPS)
        self._last_display_time = 0
        self.display_width = 960       # Display width for 1080p (half size for performance)
        self.display_height = 540      # Display height for 1080p (half size for performance)
        
        # Memory management
        self.last_cleanup_time = 0
        self.cleanup_interval = 10.0   # Clean up every 10 seconds
        
        # Initialize pygame for audio alerts
        try:
            pygame.mixer.init()
            self.audio_available = True
        except:
            self.audio_available = False
            # Don't log here yet - GUI not ready
        
        self.setup_gui()
        self.load_yolo_model()
        self.init_face_detection()  # Initialize after GUI is ready
        
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
        
        # Video canvas
        self.video_canvas = tk.Label(self.video_frame, text="🔄 Connecting to Pi camera...", 
                                    font=('Arial', 14), fg='white', bg='black')
        self.video_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Search overlay (initially hidden)
        self.search_overlay = tk.Frame(self.video_frame, bg='#1a1a1a', relief=tk.RAISED, bd=2)
        self.search_overlay.place_forget()  # Initially hidden
        
        self.search_status_label = tk.Label(self.search_overlay, text="🔍 Searching...", 
                                          font=('Arial', 16, 'bold'), fg='yellow', bg='#1a1a1a')
        self.search_status_label.pack(pady=10)
        
        self.search_progress_label = tk.Label(self.search_overlay, text="Initializing search mode", 
                                            font=('Arial', 12), fg='white', bg='#1a1a1a')
        self.search_progress_label.pack(pady=5)
        
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
        
        self.crying_status = tk.Label(ai_status_frame, text="😊 No Crying", 
                                     font=('Arial', 10), fg='lime', bg='#4b4b4b')
        self.crying_status.pack(side=tk.LEFT, padx=5, pady=5)
        
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
        
        # Internet Streaming section
        stream_frame = tk.LabelFrame(right_frame, text="🌐 Internet Streaming", 
                                    fg='white', bg='#3b3b3b', font=('Arial', 12, 'bold'))
        stream_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Checkbutton(stream_frame, text="📡 Enable Internet Stream", variable=self.streaming_enabled,
                      fg='white', bg='#3b3b3b', selectcolor='#5b5b5b', 
                      command=self.toggle_streaming).pack(anchor='w', padx=5, pady=2)
        
        tk.Label(stream_frame, text="Port:", fg='white', bg='#3b3b3b').pack(anchor='w', padx=5, pady=(5,2))
        port_frame = tk.Frame(stream_frame, bg='#3b3b3b')
        port_frame.pack(fill=tk.X, padx=5, pady=2)
        
        self.port_entry = tk.Entry(port_frame, textvariable=self.streaming_port, width=10)
        self.port_entry.pack(side=tk.LEFT, padx=2)
        
        tk.Button(port_frame, text="🔗 Get URL", command=self.show_stream_url,
                 bg='#FF9800', fg='white', font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=5)
        
        self.stream_status = tk.Label(stream_frame, text="⚫ Stream Offline", 
                                     fg='red', bg='#3b3b3b', font=('Arial', 10))
        self.stream_status.pack(pady=5)
        
        # AI Control section
        ai_frame = tk.LabelFrame(right_frame, text="🧠 AI Control", 
                                fg='white', bg='#3b3b3b', font=('Arial', 12, 'bold'))
        ai_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Checkbutton(ai_frame, text="🎯 Auto Person Tracking", variable=self.auto_tracking,
                      fg='white', bg='#3b3b3b', selectcolor='#5b5b5b', 
                      command=self.toggle_auto_tracking).pack(anchor='w', padx=5, pady=2)
        
        tk.Checkbutton(ai_frame, text="📏 Track Largest Person", variable=self.track_largest_person,
                      fg='white', bg='#3b3b3b', selectcolor='#5b5b5b').pack(anchor='w', padx=5, pady=2)
        
        tk.Checkbutton(ai_frame, text="😢 Crying Detection", variable=self.crying_detection_enabled,
                      fg='white', bg='#3b3b3b', selectcolor='#5b5b5b').pack(anchor='w', padx=5, pady=2)
        
        # Confidence threshold
        tk.Label(ai_frame, text="🎚️ Detection Confidence:", fg='white', bg='#3b3b3b').pack(anchor='w', padx=5, pady=(10,2))
        confidence_frame = tk.Frame(ai_frame, bg='#3b3b3b')
        confidence_frame.pack(fill=tk.X, padx=5, pady=2)
        
        confidence_scale = tk.Scale(confidence_frame, from_=0.1, to=0.9, resolution=0.1,
                                   orient=tk.HORIZONTAL, variable=self.confidence_threshold,
                                   bg='#3b3b3b', fg='white', highlightthickness=0)
        confidence_scale.pack(fill=tk.X)
        
        # Crying detection threshold
        tk.Label(ai_frame, text="😢 Crying Sensitivity:", fg='white', bg='#3b3b3b').pack(anchor='w', padx=5, pady=(10,2))
        crying_frame = tk.Frame(ai_frame, bg='#3b3b3b')
        crying_frame.pack(fill=tk.X, padx=5, pady=2)
        
        crying_scale = tk.Scale(crying_frame, from_=0.3, to=0.9, resolution=0.1,
                               orient=tk.HORIZONTAL, variable=self.crying_confidence_threshold,
                               bg='#3b3b3b', fg='white', highlightthickness=0)
        crying_scale.pack(fill=tk.X)
        
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
                 command=lambda: self.start_turn_sequence('L', auto=False, source='manual'),
                 bg='#2196F3', fg='white').grid(row=1, column=0, padx=2, pady=2)
        tk.Button(btn_frame, text="⏹", font=('Arial', 14, 'bold'), width=4, height=2,
                 command=lambda: self.send_command('S'), bg='#f44336', fg='white').grid(row=1, column=1, padx=2, pady=2)
        tk.Button(btn_frame, text="→", font=('Arial', 14, 'bold'), width=4, height=2,
                 command=lambda: self.start_turn_sequence('R', auto=False, source='manual'),
                 bg='#2196F3', fg='white').grid(row=1, column=2, padx=2, pady=2)
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
        """Load YOLO model in background with error recovery"""
        def load_model():
            try:
                self.log("🧠 Loading optimized YOLO model...")
                # Choose device: prefer CPU for stability on resource-constrained systems
                try:
                    import torch
                    if torch.cuda.is_available() and torch.cuda.get_device_properties(0).total_memory > 2e9:
                        self.model_device = 'cuda'
                        self.log("🎯 Using CUDA (sufficient VRAM detected)")
                    else:
                        self.model_device = 'cpu'
                        self.log("🎯 Using CPU (recommended for stability)")
                except Exception:
                    self.model_device = 'cpu'
                    self.log("🎯 Using CPU (torch not available)")

                # Load with optimizations for stability
                self.model = YOLO('yolov8n.pt')  # Nano version for speed
                
                # Configure model for optimal performance
                try:
                    if hasattr(self.model, 'to'):
                        self.model.to(self.model_device)
                    # Set model to evaluation mode for consistency
                    if hasattr(self.model.model, 'eval'):
                        self.model.model.eval()
                except Exception as e:
                    self.log(f"⚠️ Model optimization warning: {e}")
                    
                self.model_loaded = True
                self.model_crashed = False
                self.model_retry_count = 0
                self.root.after(0, lambda: self.model_label.config(text="Model: YOLOv8n Ready ✅", fg='lime'))
                self.log("✅ YOLO model loaded successfully")
                
            except Exception as e:
                self.model_retry_count += 1
                self.model_crashed = True
                self.root.after(0, lambda: self.model_label.config(text="Model: Error ❌", fg='red'))
                self.log(f"❌ Failed to load YOLO model (attempt {self.model_retry_count}): {e}")
                
                # Retry logic
                if self.model_retry_count < self.max_model_retries:
                    self.log(f"🔄 Retrying model load in 5 seconds...")
                    time.sleep(5)
                    load_model()  # Recursive retry
                
        threading.Thread(target=load_model, daemon=True).start()
    
    def init_face_detection(self):
        """Initialize face detection after GUI is ready"""
        try:
            # Load OpenCV cascade classifiers
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
            self.log("✅ OpenCV face detection loaded for crying detection")
        except Exception as e:
            self.log(f"⚠️ Face detection unavailable: {e}")
        
        # Log audio system status
        if not self.audio_available:
            self.log("⚠️ Audio system not available - visual alerts only")
        else:
            self.log("✅ Audio alert system ready")
        
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
                # Progress any pending gentle turn sequences
                self.process_turn_sequence()

                ret, frame = self.cap.read()
                
                if not ret:
                    self.log("⚠️ Failed to read frame from Pi")
                    time.sleep(0.1)
                    continue
                    
                # Store current frame
                with self.frame_lock:
                    self.current_frame = frame.copy()
                
                # Run YOLO detection with optimized frame skipping and error handling
                processed_frame = frame.copy()
                detections = []

                # Implement frame skipping for better performance
                self.current_skip_count += 1
                skip_inference = self.current_skip_count < self.inference_skip_frames

                # Throttle inference to target FPS and resize for faster processing
                now = time.time()
                min_interval = 1.0 / float(self.max_inference_fps)
                time_based_skip = (now - self.last_inference_time) < min_interval

                should_run_inference = (self.model_loaded and self.model and 
                                      not self.model_crashed and 
                                      not skip_inference and 
                                      not time_based_skip)

                if should_run_inference:
                    try:
                        # Reset skip counter
                        self.current_skip_count = 0
                        
                        # Resize frame before inference to reduce processing load
                        inference_frame = cv2.resize(frame, (self.inference_size, self.inference_size))
                        
                        # Run inference with error handling
                        results = self.model(inference_frame, 
                                           classes=[0],  # Person class only
                                           conf=self.confidence_threshold.get(), 
                                           imgsz=self.inference_size, 
                                           device=self.model_device, 
                                           verbose=False,
                                           half=False)  # Disable half precision for stability
                        
                        self.last_inference_time = now

                        if len(results) > 0 and len(results[0].boxes) > 0:
                            # Scale coordinates back to original frame size
                            orig_h, orig_w = frame.shape[:2]
                            scale_x = orig_w / self.inference_size
                            scale_y = orig_h / self.inference_size
                            
                            # Iterate detections
                            boxes = results[0].boxes.xyxy.cpu().numpy()
                            confidences = results[0].boxes.conf.cpu().numpy()
                            for i, (box, conf) in enumerate(zip(boxes, confidences)):
                                # Scale back to original coordinates
                                x1, y1, x2, y2 = box.astype(int)
                                x1 = int(x1 * scale_x)
                                y1 = int(y1 * scale_y)
                                x2 = int(x2 * scale_x)
                                y2 = int(y2 * scale_y)
                                detections.append({
                                    'box': (x1, y1, x2, y2), 
                                    'confidence': float(conf), 
                                    'area': (x2 - x1) * (y2 - y1)
                                })

                        # Save detection snapshot for smoothing
                        if detections:
                            self.detection_history.append((now, detections))

                    except Exception as e:
                        self.log(f"⚠️ YOLO detection error: {e}")
                        self.model_crashed = True
                        self.model_retry_count += 1
                        
                        # Try to recover if not too many failures
                        if self.model_retry_count <= self.max_model_retries:
                            self.log(f"🔄 Attempting model recovery ({self.model_retry_count}/{self.max_model_retries})")
                            try:
                                # Clear GPU memory if using CUDA
                                if self.model_device == 'cuda':
                                    import torch
                                    torch.cuda.empty_cache()
                                # Reinitialize model
                                self.model_loaded = False
                                self.load_yolo_model()
                            except Exception as recovery_e:
                                self.log(f"❌ Model recovery failed: {recovery_e}")
                        time.sleep(0.1)

                # If we skipped inference or had no detections, try to reuse recent detections for smoothing
                if not detections:
                    # Find the most recent detection snapshot within keep_seconds
                    chosen = None
                    for ts, dets in reversed(self.detection_history):
                        if now - ts <= self.detection_keep_seconds and dets:
                            chosen = dets
                            break
                    if chosen:
                        detections = chosen.copy()

                # Draw detections (smoothed) onto frame
                for d in detections:
                    x1, y1, x2, y2 = d['box']
                    conf = d.get('confidence', 0.0)
                    cv2.rectangle(processed_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(processed_frame, f'Person {conf:.2f}', (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                with self.mode_lock:
                    active_mode = self.operating_mode

                # Auto tracking logic only in care companion mode
                if active_mode == 'care_companion' and self.auto_tracking.get():
                    if detections:
                        if hasattr(self, 'search_active') and self.search_active:
                            self.search_active = False
                            if self.turn_sequence_active():
                                self.pending_turn_sequence = None
                            self.send_command('S', auto=True, force=True)
                            self.update_search_overlay("", "")
                            self.log("🎯 Person found! Stopping search, starting tracking")
                            time.sleep(0.2)

                        self.process_auto_tracking(detections, processed_frame.shape)
                    else:
                        self.process_search_mode()
                else:
                    if hasattr(self, 'search_active') and self.search_active:
                        self.search_active = False
                        self.update_search_overlay("", "")

                self._handle_mode_logic(active_mode, detections, now)

                # Crying detection only makes sense in care companion mode
                if active_mode == 'care_companion' and self.crying_detection_enabled.get() and detections:
                    try:
                        target = max(detections, key=lambda d: d.get('area', 0))
                        self.detect_crying(frame, target['box'], processed_frame)
                    except Exception as e:
                        self.log(f"⚠️ Crying detect call failed: {e}")
                elif active_mode != 'care_companion' and self.crying_detected:
                    self.crying_detected = False
                    self.root.after(0, lambda: self.crying_status.config(text="😊 No Crying", fg='lime'))
                
                # Update display
                self.update_video_display(processed_frame)
                self.update_detection_count(len(detections))

                # Update stream frame for internet streaming
                try:
                    if self.stream_lock.acquire(timeout=0.05):
                        try:
                            self.stream_frame = processed_frame.copy()
                        finally:
                            self.stream_lock.release()
                except Exception:
                    pass
                
                # Update FPS
                self.fps_counter += 1

                # Finish any turn sequences that may have pending stop commands
                self.process_turn_sequence()
                
                # Memory cleanup every 10 seconds
                now_cleanup = time.time()
                if now_cleanup - self.last_cleanup_time > self.cleanup_interval:
                    self.cleanup_memory()
                    self.last_cleanup_time = now_cleanup
                
            except Exception as e:
                self.log(f"❌ Video processing error: {e}")
                time.sleep(0.1)
                
    def detect_crying(self, frame, person_box, display_frame):
        """FIXED crying detection with improved stability"""
        try:
            # Throttle crying checks to reduce CPU
            now = time.time()
            if now - self._last_crying_check_time < self.crying_check_interval:
                return
            self._last_crying_check_time = now

            x1, y1, x2, y2 = person_box
            
            # Extract face region with padding
            padding = 10
            face_y1 = max(0, y1 - padding)
            face_y2 = min(frame.shape[0], y1 + int((y2 - y1) * 0.5))  # Upper 50% for face
            face_x1 = max(0, x1 - padding)
            face_x2 = min(frame.shape[1], x2 + padding)
            
            face_region = frame[face_y1:face_y2, face_x1:face_x2]
            
            if face_region.size == 0:
                return
            
            # Analyze facial distress with improved method
            crying_score = self.analyze_facial_distress_improved(face_region)
            
            # Store result with timestamp for voting system
            self.crying_history.append((now, crying_score))
            
            # Clean old entries
            self.crying_history = collections.deque([
                (t, score) for t, score in self.crying_history 
                if now - t <= self.crying_window_seconds
            ], maxlen=self.crying_history.maxlen)
            
            # Calculate average score in recent window
            recent_scores = [score for t, score in self.crying_history if now - t <= 1.0]  # Last 1 second
            
            if len(recent_scores) >= 3:  # Need at least 3 samples
                avg_score = sum(recent_scores) / len(recent_scores)
                crying_detected = avg_score > self.crying_confidence_threshold.get()
                
                if crying_detected and not self.crying_detected:
                    # New crying detection
                    self.trigger_crying_alert()
                    # Draw alert on display
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                    cv2.putText(display_frame, f"😢 CRYING! ({avg_score:.2f})", 
                              (x1, y1-30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    
                elif not crying_detected and self.crying_detected:
                    # Crying stopped
                    self.crying_detected = False
                    self.root.after(0, lambda: self.crying_status.config(text="😊 No Crying", fg='lime'))
                    self.log("😊 Crying detection cleared")
                    
        except Exception as e:
            self.log(f"❌ Crying detection error: {e}")
    
    def analyze_facial_distress_improved(self, face_region):
        """Improved facial distress analysis"""
        try:
            # Convert to different color spaces
            gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            hsv = cv2.cvtColor(face_region, cv2.COLOR_BGR2HSV)
            
            distress_score = 0.0
            
            # 1. Face detection first
            if self.face_cascade is None:
                return 0.0
                
            faces = self.face_cascade.detectMultiScale(gray, 1.2, 3, minSize=(30, 30))
            
            if len(faces) == 0:
                return 0.0
            
            # Use the largest face
            face = max(faces, key=lambda f: f[2] * f[3])
            fx, fy, fw, fh = face
            
            # Extract face ROI
            face_roi = gray[fy:fy+fh, fx:fx+fw]
            face_roi_color = face_region[fy:fy+fh, fx:fx+fw]
            
            # 2. Mouth region analysis (crying = open mouth)
            mouth_y1 = int(fy + fh * 0.6)
            mouth_y2 = int(fy + fh * 0.9)
            mouth_roi = gray[mouth_y1:mouth_y2, fx:fx+fw]
            
            if mouth_roi.size > 0:
                # Detect dark regions (open mouth)
                _, mouth_thresh = cv2.threshold(mouth_roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                dark_ratio = np.sum(mouth_thresh == 0) / mouth_thresh.size
                
                if dark_ratio > 0.2:  # Significant mouth opening
                    distress_score += 0.4
                    
                # Mouth shape analysis using contours
                contours, _ = cv2.findContours(255 - mouth_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if contours:
                    largest_contour = max(contours, key=cv2.contourArea)
                    area = cv2.contourArea(largest_contour)
                    if area > 100:  # Large mouth opening
                        distress_score += 0.3
            
            # 3. Eye region analysis
            if self.eye_cascade is not None:
                eyes = self.eye_cascade.detectMultiScale(face_roi, 1.1, 3, minSize=(15, 15))
                
                if len(eyes) >= 1:
                    for (ex, ey, ew, eh) in eyes[:2]:  # Check up to 2 eyes
                        eye_roi = face_roi[ey:ey+eh, ex:ex+ew]
                        if eye_roi.size > 0:
                            eye_mean = np.mean(eye_roi)
                            # Squinted/closed eyes (crying)
                            if eye_mean < 80:
                                distress_score += 0.2
            
            # 4. Color analysis - red/flushed face
            hsv_roi = hsv[fy:fy+fh, fx:fx+fw]
            
            # Red areas (crying face)
            lower_red1 = np.array([0, 50, 50])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([170, 50, 50])
            upper_red2 = np.array([180, 255, 255])
            
            red_mask1 = cv2.inRange(hsv_roi, lower_red1, upper_red1)
            red_mask2 = cv2.inRange(hsv_roi, lower_red2, upper_red2)
            red_mask = cv2.bitwise_or(red_mask1, red_mask2)
            
            red_ratio = np.sum(red_mask > 0) / red_mask.size
            if red_ratio > 0.15:  # Significant red coloring
                distress_score += 0.3
            
            # 5. Edge density (facial distortion from crying)
            edges = cv2.Canny(face_roi, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            if edge_density > 0.08:  # High edge density
                distress_score += 0.2
            
            # 6. Brightness variance (tears/wet face)
            brightness_std = np.std(face_roi)
            if brightness_std > 40:  # High brightness variance
                distress_score += 0.1
            
            return min(distress_score, 1.0)  # Cap at 1.0
            
        except Exception as e:
            self.log(f"⚠️ Facial distress analysis error: {e}")
            return 0.0
    
    def analyze_facial_distress(self, face_region):
        """Legacy method - kept for compatibility"""
        return self.analyze_facial_distress_improved(face_region)
    
    def opencv_crying_detection(self, face_region):
        """Simple OpenCV-based crying detection"""
        try:
            # Convert to grayscale and HSV
            gray = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            hsv = cv2.cvtColor(face_region, cv2.COLOR_BGR2HSV)
            
            # Detect high contrast areas (open mouth, squinting)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            
            # Detect red/flushed areas (crying face)
            lower_red = np.array([0, 50, 50])
            upper_red = np.array([10, 255, 255])
            red_mask = cv2.inRange(hsv, lower_red, upper_red)
            red_ratio = np.sum(red_mask > 0) / red_mask.size
            
            # Simple scoring
            crying_score = 0.0
            
            if edge_density > 0.05:  # High edge density (facial distortion)
                crying_score += 0.4
                
            if red_ratio > 0.1:  # Red/flushed face
                crying_score += 0.3
                
            # Brightness analysis (tears/wet face)
            brightness = np.mean(gray)
            if brightness > 120:  # Bright reflective areas (tears)
                crying_score += 0.3
            
            return crying_score > self.crying_confidence_threshold.get()
            
        except Exception as e:
            self.log(f"⚠️ OpenCV crying detection error: {e}")
            return False
    
    def trigger_crying_alert(self):
        """Trigger crying/distress alert system"""
        current_time = time.time()
        
        # Rate limiting
        if current_time - self.last_crying_alert < self.crying_alert_cooldown:
            return
            
        if not self.crying_detected:
            self.crying_detected = True
            self.last_crying_alert = current_time
            
            # Update GUI
            self.root.after(0, lambda: self.crying_status.config(text="😢 CRYING!", fg='red'))
            
            # Log alert
            self.log("🚨 CRYING DETECTED - Alert triggered!")
            
            # Audio alert
            self.play_crying_alert()
            
            # Could add more alert mechanisms here:
            # - Send notification to phone
            # - Email alert
            # - Robot movement to approach person
    
    def play_crying_alert(self):
        """Play audio alert for crying detection"""
        try:
            if self.audio_available:
                # Simple system beep as fallback
                def generate_beep():
                    try:
                        # Try pygame mixer
                        if pygame.mixer.get_init():
                            # Create a simple tone
                            duration = 500  # milliseconds
                            sample_rate = 22050
                            frequency = 800
                            
                            frames = int(duration * sample_rate / 1000)
                            arr = np.sin(2 * np.pi * frequency * np.linspace(0, duration / 1000, frames))
                            arr = (arr * 32767).astype(np.int16)
                            arr = np.repeat(arr.reshape(frames, 1), 2, axis=1)
                            
                            sound = pygame.sndarray.make_sound(arr)
                            sound.play()
                    except:
                        # Fallback to system beep
                        import winsound
                        winsound.Beep(800, 500)  # 800Hz for 500ms
                        
                # Play beep in separate thread
                threading.Thread(target=generate_beep, daemon=True).start()
                
        except Exception as e:
            self.log(f"⚠️ Audio alert error: {e}")
            # Visual-only alert as last resort
            self.log("🔊 AUDIO ALERT: CRYING DETECTED!")

    def process_auto_tracking(self, detections, frame_shape):
        """Process automatic person tracking with balanced movement"""
        if not detections:
            return

        current_time = time.time()

        # Slow cooldown to match search rotation speed and prevent overshooting
        gentle_cooldown = 0.5  # 500ms between auto commands (same as search rotation speed)
        if current_time - self.last_command_time < gentle_cooldown:
            return

        # Find the target person (largest if enabled, otherwise first)
        if self.track_largest_person.get():
            target = max(detections, key=lambda d: d['area'])
        else:
            target = detections[0]

        x1, y1, x2, y2 = target['box']
        center_x = (x1 + x2) / 2
        frame_width, frame_height = frame_shape[1], frame_shape[0]

        # Calculate movement command with refined thresholds
        command = self.calculate_movement_command(center_x, (y1 + y2) / 2, target['area'],
                                                  frame_width, frame_height)

        if not hasattr(self, 'last_auto_command'):
            self.last_auto_command = 'S'

        if command in ['L', 'R']:
            if command != self.last_auto_command or not self.turn_sequence_active():
                direction_name = {'L': 'Left', 'R': 'Right'}[command]
                self.log(f"🎯 Tracking adjustment: {direction_name}")
            self.last_auto_command = command
            self.start_turn_sequence(command, auto=True, source='tracking')
            return

        if command and command != self.last_auto_command:
            direction_name = {'F': 'Forward', 'B': 'Backward'}.get(command, command)
            if command != 'S':
                self.log(f"🎯 Tracking adjustment: {direction_name}")

        if command:
            self.last_auto_command = command
            if command == 'S' and self.turn_sequence_active():
                self.pending_turn_sequence = None
            self.send_command(command, auto=True)
            
    def process_search_mode(self):
        """Fast 360-degree search with short scans and 2s pauses between turns"""
        current_time = time.time()
        
        # Initialize search mode tracking
        if not hasattr(self, 'search_active'):
            self.search_active = False
            self.search_start_time = 0
            self.search_last_command_time = 0
            self.search_phase = 'scan'
            self.total_micro_turns = 0
            self.target_micro_turns = 36  # 36 × 10° ≈ 360°
            self.current_cycle = 1

        # Start search if not already active
        if not self.search_active:
            self.search_active = True
            self.search_start_time = current_time
            self.search_last_command_time = current_time
            self.search_phase = 'scan'
            self.total_micro_turns = 0
            self.current_cycle = 1
            self.log("🔍 Starting fast 360° search (36 micro-turns × 10°)")
            # Update GUI overlay
            self.update_search_overlay("Starting Fast Search", "36 micro-turn cycle")

        # Update GUI overlay with current status
        progress = (self.total_micro_turns / self.target_micro_turns) * 100 if self.target_micro_turns else 0
        cycle_info = f"Cycle {self.current_cycle} | Turn {self.total_micro_turns}/{self.target_micro_turns} ({progress:.1f}%)"

        # Phase-based search with crisp pauses
        if self.search_phase == 'scan':
            # Quick scan before turning
            scan_duration = 0.5
            elapsed = current_time - self.search_last_command_time
            self.update_search_overlay(f"🔍 Scanning ({elapsed:.2f}s/0.50s)", cycle_info)

            if elapsed >= scan_duration:
                self.search_phase = 'pre_turn'
                self.search_last_command_time = current_time
                self.log(f"🔍 Scan complete → micro-turn {self.total_micro_turns + 1}")

        elif self.search_phase == 'pre_turn':
            # Brief stabilization before turn
            pre_turn_duration = 0.05
            elapsed = current_time - self.search_last_command_time
            self.update_search_overlay(f"⚙️ Stabilising ({elapsed:.2f}s/0.05s)", cycle_info)

            if elapsed >= pre_turn_duration:
                self.search_phase = 'micro_turn'
                self.search_last_command_time = current_time

        elif self.search_phase == 'micro_turn':
            # Quick micro-turn with slightly longer hold for better coverage
            micro_turn_duration = 0.12
            elapsed = current_time - self.search_last_command_time
            self.update_search_overlay(f"↻ Turning ({elapsed:.2f}s/0.12s)", cycle_info)

            if elapsed >= micro_turn_duration:
                self.start_turn_sequence('R', auto=True, source='search')
                self.search_phase = 'stop_spam'
                self.search_last_command_time = current_time

        elif self.search_phase == 'stop_spam':
            stops_sent, total_stops = self.get_turn_sequence_progress()
            if self.turn_sequence_active():
                total_display = total_stops if total_stops else 3
                self.update_search_overlay(f"🛑 Settling ({stops_sent}/{total_display})", cycle_info)
            else:
                self.total_micro_turns += 1
                self.search_phase = 'long_pause'
                self.search_last_command_time = current_time

        elif self.search_phase == 'long_pause':
            # 250ms pause between turns
            long_pause_duration = 0.25
            elapsed = current_time - self.search_last_command_time
            remaining = max(0.0, long_pause_duration - elapsed)
            self.update_search_overlay(f"⏸️ Pause {remaining:.2f}s", cycle_info)

            if elapsed >= long_pause_duration:
                if self.total_micro_turns >= self.target_micro_turns:
                    self.search_phase = 'cycle_rest'
                    self.search_last_command_time = current_time
                else:
                    self.search_phase = 'scan'
                    self.search_last_command_time = current_time

        elif self.search_phase == 'cycle_rest':
            # Short rest between cycles
            cycle_rest_duration = 0.25
            elapsed = current_time - self.search_last_command_time
            remaining = max(0.0, cycle_rest_duration - elapsed)
            self.update_search_overlay(f"😴 Rest {remaining:.2f}s", f"Completed Cycle {self.current_cycle}")

            if elapsed >= cycle_rest_duration:
                self.total_micro_turns = 0
                self.current_cycle += 1
                self.search_phase = 'scan'
                self.search_last_command_time = current_time

        # Timeout protection
        if current_time - self.search_start_time > 240:  # 4 minute timeout
            self.log("🔍 Search timeout (4 min) - Stopping to conserve power")
            self.send_command('S', auto=True)
            self.search_active = False
            self.update_search_overlay("⏹️ Search Stopped", "Timeout reached")
            
    def calculate_movement_command(self, center_x, center_y, area, frame_width, frame_height):
        """Calculate robot movement based on person position for smooth tracking"""
        frame_center_x = frame_width / 2
        offset_x = center_x - frame_center_x
        total_pixels = frame_width * frame_height

        # Thresholds tuned for smoother behaviour
        x_threshold = frame_width * 0.18          # 18% dead zone left/right
        min_area = total_pixels * 0.03           # If person is very small, push forward
        ideal_area = total_pixels * 0.22         # Comfortable following distance (move until here)
        max_area = total_pixels * 0.38           # Too close, stop

        offset_percent = abs(offset_x) / (frame_width / 2) * 100
        area_percent = (area / total_pixels) * 100 if total_pixels else 0

        # Distance control
        if area < min_area:
            self.log(f"🚶 Closing distance (size {area_percent:.1f}%)")
            return 'F'
        if area > max_area:
            self.log("🛑 Person extremely close - holding position")
            return 'S'

        # Lateral alignment only when significantly off-centre
        if offset_x > x_threshold and offset_percent > 18:
            self.log(f"↪️ Adjusting right ({offset_percent:.1f}% offset)")
            return 'R'
        if offset_x < -x_threshold and offset_percent > 18:
            self.log(f"↩️ Adjusting left ({offset_percent:.1f}% offset)")
            return 'L'

        # Maintain forward drift until ideal size reached
        if area < ideal_area:
            self.log(f"🚶 Continuing forward (target {ideal_area/total_pixels*100:.1f}% area)")
            return 'F'

        # Otherwise stay put
        return 'S'

    def turn_sequence_active(self):
        return self.pending_turn_sequence is not None

    def get_turn_sequence_progress(self):
        if self.pending_turn_sequence:
            info = self.pending_turn_sequence
            return info.get('stops_sent', 0), info.get('total_stops', 0)
        return (self.last_turn_sequence_info.get('stops_sent', 0),
                self.last_turn_sequence_info.get('total_stops', 0))

    def _build_turn_sequence(self, direction, source):
        base_hold = {
            'search': 0.28,
            'tracking': 0.24,
            'manual': 0.24
        }.get(source, 0.24)
        stop_spacing = 0.12
        total_stops = 3

        steps = [{'command': direction, 'delay': 0.0, 'force': True}]
        for idx in range(total_stops):
            steps.append({'command': 'S',
                          'delay': base_hold + idx * stop_spacing,
                          'force': True})
        return steps, total_stops

    def start_turn_sequence(self, direction, auto=True, source='tracking'):
        if direction not in ['L', 'R']:
            self.send_command(direction, auto=auto)
            return

        if self.pending_turn_sequence and self.pending_turn_sequence.get('active'):
            current_direction = self.pending_turn_sequence.get('direction')
            if current_direction == direction:
                # Already executing same direction; let it finish
                return
            # Different direction requested - break previous sequence gently
            self.send_command('S', auto=auto, force=True)
            self.pending_turn_sequence = None

        steps, total_stops = self._build_turn_sequence(direction, source)
        self.pending_turn_sequence = {
            'direction': direction,
            'auto': auto,
            'steps': steps,
            'step_index': 0,
            'start_time': time.time(),
            'active': True,
            'stops_sent': 0,
            'total_stops': total_stops
        }
        self.last_turn_sequence_info = {'stops_sent': 0, 'total_stops': total_stops}
        # Kick off sequence immediately
        self.process_turn_sequence()

    def process_turn_sequence(self):
        if not self.pending_turn_sequence:
            return

        sequence = self.pending_turn_sequence
        now = time.time()
        elapsed = now - sequence['start_time']

        while sequence['step_index'] < len(sequence['steps']):
            step = sequence['steps'][sequence['step_index']]
            if elapsed < step['delay']:
                break

            self.send_command(step['command'], auto=sequence['auto'], force=step.get('force', False))

            if step['command'] == 'S':
                sequence['stops_sent'] += 1
                self.last_turn_sequence_info = {
                    'stops_sent': sequence['stops_sent'],
                    'total_stops': sequence['total_stops']
                }

            sequence['step_index'] += 1
            now = time.time()
            elapsed = now - sequence['start_time']

        if sequence['step_index'] >= len(sequence['steps']):
            self.pending_turn_sequence = None
    
    def send_command(self, command, auto=False, force=False):
        """Send movement command to Pi → ESP32 (GPIO1/3 UART0)"""
        try:
            # Rate limiting - Different speeds for tracking vs search
            current_time = time.time()

            # Unified slow timing for both tracking and search to prevent overshooting
            if auto and hasattr(self, 'search_active') and not self.search_active:
                # In tracking mode - use same slow speed as search rotation
                min_interval = 0.5  # 500ms between tracking commands (same as search cycle)
            elif auto and hasattr(self, 'search_active') and self.search_active:
                # In search mode - use search-specific timing
                min_interval = 0.02  # 20ms for search stop spam
            else:
                # Manual mode - responsive but not overwhelming
                min_interval = 0.08

            if not force and current_time - self.last_command_time < min_interval:
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

    # ------------------------------------------------------------------
    # Mode management
    # ------------------------------------------------------------------
    def _normalize_mode(self, mode: str) -> str:
        normalized = (mode or '').strip().lower()
        if normalized not in {'care_companion', 'watchdog', 'edumate'}:
            raise ValueError(f"Unsupported operating mode: {mode}")
        return normalized

    def get_available_modes(self):
        return list(self.available_modes)

    def set_operating_mode(self, mode: str, *, metadata=None, summary: str | None = None, speak_summary: bool = False):
        normalized = self._normalize_mode(mode)
        metadata = metadata or {}

        with self.mode_lock:
            previous_mode = self.operating_mode
            previous_metadata = dict(self.mode_metadata)
            if normalized != previous_mode:
                self.operating_mode = normalized
                self.mode_metadata = dict(metadata)
            else:
                merged = dict(previous_metadata)
                merged.update(metadata)
                self.mode_metadata = merged

            current_metadata = dict(self.mode_metadata)

        if normalized != previous_mode:
            self.log(f"🎛️ Mode change: {previous_mode} → {normalized}")
            self._on_mode_exit(previous_mode)
            self._on_mode_enter(normalized, current_metadata)
        else:
            self._on_mode_update(normalized, current_metadata, previous_metadata)

        mode_summary = summary or self._mode_summary_for(normalized, current_metadata, previous_mode)

        if normalized == 'edumate' and metadata.get('prompt'):
            prompt_text = metadata['prompt']
            delivered = self.trigger_edumate_prompt(prompt_text, speak=True)
            timestamp = datetime.utcnow().isoformat()
            with self.mode_lock:
                self.mode_metadata['last_prompt'] = prompt_text
                self.mode_metadata['last_prompt_at'] = timestamp
            if delivered:
                self.register_manual_alert('Edumate prompt delivered', prompt_text, level='info')
            else:
                self.register_manual_alert('Edumate prompt failed', prompt_text, level='warning')
                if not summary:
                    mode_summary = f"⚠️ Edumate lesson delivery failed: {prompt_text}"

        self._sync_mode_to_pi(
            mode=self.operating_mode,
            metadata=self.mode_metadata,
            summary=mode_summary,
            speak=speak_summary and normalized == 'edumate',
            watchdog_alarm_active=self._watchdog_alarm_active,
        )

        return {'mode': self.operating_mode, 'metadata': dict(self.mode_metadata)}

    def _on_mode_enter(self, mode: str, metadata: dict | None = None) -> None:
        if mode in {'watchdog', 'edumate'}:
            self._auto_tracking_before_mode = self.auto_tracking.get()
            if self.auto_tracking.get():
                self.auto_tracking.set(False)
                self.log('🤖 Auto tracking paused for new mode')
            if hasattr(self, 'search_active'):
                self.search_active = False
                self.update_search_overlay('', '')
            self.send_command('S', auto=True, force=True)

        if mode == 'watchdog':
            self._watchdog_person_present = False
            self._last_watchdog_alert = 0.0
            self._stop_watchdog_alarm()
            self.register_manual_alert('Watchdog mode armed', 'Security sweep is active.', level='warning')
        elif mode == 'edumate':
            self._stop_watchdog_alarm()
            self.register_manual_alert('Edumate mode ready', 'Robot will stay still for lessons.', level='info')
        elif mode == 'care_companion':
            if self._auto_tracking_before_mode:
                self.auto_tracking.set(True)
            self._stop_watchdog_alarm()

    def _on_mode_exit(self, mode: str) -> None:
        if mode == 'watchdog':
            self._stop_watchdog_alarm()
            self._watchdog_person_present = False

    def _on_mode_update(self, mode: str, current_metadata: dict, previous_metadata: dict) -> None:
        if mode == 'watchdog':
            alarm_active = current_metadata.get('alarm_active')
            if alarm_active is False:
                self._stop_watchdog_alarm()

    def _mode_summary_for(self, mode: str, metadata: dict | None = None, previous: str | None = None) -> str:
        metadata = metadata or {}
        if mode == 'care_companion':
            return "💞 Mode update: 'Care Companion' mode is active—friendly reminders and conversation are ready."
        if mode == 'watchdog':
            return "🛡️ Mode update: 'Watchdog' security mode is active. A loud alarm will sound if motion is detected."
        if mode == 'edumate':
            prompt = metadata.get('prompt') or metadata.get('last_prompt')
            if prompt:
                clean_prompt = (prompt[:140] + '…') if len(prompt) > 140 else prompt
                return f"📚 Mode update: 'Edumate' learning mode active. Latest lesson: {clean_prompt}"
            return "📚 Mode update: 'Edumate' learning mode is active. Family lessons will play immediately."
        return f"ℹ️ Mode changed to {mode}"

    def _sync_mode_to_pi(self, *, mode: str | None = None, metadata: dict | None = None, summary: str | None = None, speak: bool = False, watchdog_alarm_active: bool | None = None) -> None:
        payload: dict[str, object] = {}
        if mode is not None:
            payload['mode'] = mode
        if metadata is None:
            with self.mode_lock:
                metadata_copy = dict(self.mode_metadata)
        else:
            metadata_copy = dict(metadata)
        if metadata_copy:
            payload['metadata'] = metadata_copy
        if summary:
            payload['summary'] = summary
        if speak:
            payload['speak'] = True
        if watchdog_alarm_active is not None:
            payload['watchdog_alarm_active'] = bool(watchdog_alarm_active)

        if not payload:
            return

        try:
            response = requests.post(
                f"{self.PI_BASE_URL}/assistant/mode",
                json=payload,
                timeout=5,
            )
            response.raise_for_status()
        except Exception as exc:
            self.log(f"⚠️ Mode sync failed: {exc}")

    def _handle_mode_logic(self, mode: str, detections, timestamp: float) -> None:
        if mode == 'watchdog':
            self._handle_watchdog_mode(detections, timestamp)
        elif mode == 'edumate':
            self._handle_edumate_mode(detections, timestamp)
        else:
            self._stop_watchdog_alarm()

    def _handle_watchdog_mode(self, detections, timestamp: float) -> None:
        person_present = bool(detections)

        if person_present and not self._watchdog_person_present:
            self._last_watchdog_alert = timestamp
            self.register_manual_alert(
                'Watchdog alert',
                'Movement detected — alarm sounding.',
                level='danger',
            )
            with self.mode_lock:
                self.mode_metadata['last_detection_at'] = datetime.utcnow().isoformat()
            self._start_watchdog_alarm()
        elif person_present:
            if timestamp - self._last_watchdog_alert >= self.watchdog_alert_interval:
                self._last_watchdog_alert = timestamp
                self.register_manual_alert(
                    'Watchdog ongoing',
                    'Security alarm still active.',
                    level='warning',
                )
            self._start_watchdog_alarm()
        else:
            if self._watchdog_person_present:
                self.register_manual_alert(
                    'Watchdog clear',
                    'Area clear. Alarm stopped.',
                    level='success',
                )
            self._stop_watchdog_alarm()

        self._watchdog_person_present = person_present

    def _handle_edumate_mode(self, detections, timestamp: float) -> None:
        learner_present = bool(detections)
        with self.mode_lock:
            self.mode_metadata['learner_present'] = learner_present
            self.mode_metadata['last_check_at'] = datetime.utcnow().isoformat()

    def _set_watchdog_alarm_state(self, active: bool, summary: str | None = None) -> None:
        if self._watchdog_alarm_active == active and not summary:
            return

        self._watchdog_alarm_active = active
        with self.mode_lock:
            self.mode_metadata['alarm_active'] = active

        if active:
            self.log('🔔 Watchdog alarm engaged')
        else:
            self.log('🔕 Watchdog alarm silenced')

        self._sync_mode_to_pi(
            mode=None,
            metadata=self.mode_metadata,
            summary=summary,
            watchdog_alarm_active=active,
        )

    def _start_watchdog_alarm(self) -> None:
        if self._watchdog_alarm_active:
            return
        self._watchdog_alarm_stop.clear()
        self._set_watchdog_alarm_state(True)
        thread = threading.Thread(target=self._watchdog_alarm_loop, name='WatchdogAlarmLoop', daemon=True)
        self._watchdog_alarm_thread = thread
        thread.start()

    def _stop_watchdog_alarm(self) -> None:
        if not self._watchdog_alarm_active and not (self._watchdog_alarm_thread and self._watchdog_alarm_thread.is_alive()):
            return
        self._watchdog_alarm_stop.set()
        self._set_watchdog_alarm_state(False)
        self._watchdog_alarm_thread = None

    def _watchdog_alarm_loop(self) -> None:
        while not self._watchdog_alarm_stop.wait(1.2):
            try:
                self.play_crying_alert()
            except Exception as exc:
                self.log(f"⚠️ Watchdog alarm beep failed: {exc}")

    def silence_watchdog_alarm(self) -> None:
        self._stop_watchdog_alarm()
        self._watchdog_person_present = False
        self._last_watchdog_alert = time.time()
        self.register_manual_alert(
            'Watchdog alarm silenced',
            'Alarm muted from dashboard.',
            level='info',
        )
        self._sync_mode_to_pi(
            mode=None,
            metadata=self.mode_metadata,
            summary='🕊️ Watchdog alarm silenced from dashboard.',
            watchdog_alarm_active=False,
        )

    def trigger_edumate_prompt(self, prompt: str, *, speak: bool = True) -> bool:
        text = (prompt or '').strip()
        if not text:
            return False

        try:
            response = requests.post(
                f"{self.PI_BASE_URL}/assistant/message",
                json={
                    'text': text,
                    'speak': speak,
                    'history_limit': 40,
                },
                timeout=15,
            )
            response.raise_for_status()
            self.log(f"📘 Edumate prompt delivered: {text[:80]}…")
            return True
        except Exception as exc:
            self.log(f"⚠️ Edumate prompt delivery failed: {exc}")
            return False
            
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
            # Stop search mode and hide overlay
            if hasattr(self, 'search_active'):
                self.search_active = False
            self.update_search_overlay("", "")
            self.send_command('S')  # Stop robot
    
    def toggle_streaming(self):
        """Toggle internet streaming"""
        if self.streaming_enabled.get():
            self.start_internet_streaming()
        else:
            self.stop_internet_streaming()
    
    def start_internet_streaming(self):
        """Start Flask server for internet streaming"""
        try:
            if self.streaming_thread and self.streaming_thread.is_alive():
                return
                
            port = self.streaming_port.get()
            
            # Create Flask app
            self.flask_app = Flask(__name__)
            self.flask_app.config['DEBUG'] = False
            
            # HTML template for stream viewer
            stream_html = '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>🤖 Robot Guardian Live Stream</title>
                <style>
                    body { 
                        background: #1a1a1a; 
                        color: white; 
                        font-family: Arial, sans-serif;
                        text-align: center;
                        margin: 0;
                        padding: 20px;
                    }
                    .container { max-width: 1200px; margin: 0 auto; }
                    .stream { 
                        border: 3px solid #4CAF50;
                        border-radius: 10px;
                        max-width: 100%;
                        height: auto;
                    }
                    .status {
                        background: #333;
                        padding: 15px;
                        border-radius: 10px;
                        margin: 20px 0;
                    }
                    .alert {
                        background: #f44336;
                        color: white;
                        padding: 10px;
                        border-radius: 5px;
                        margin: 10px 0;
                        animation: blink 1s infinite;
                    }
                    @keyframes blink {
                        0%, 50% { opacity: 1; }
                        51%, 100% { opacity: 0.5; }
                    }
                </style>
                <script>
                    function refreshPage() {
                        location.reload();
                    }
                    setInterval(refreshPage, 30000); // Refresh every 30 seconds
                </script>
            </head>
            <body>
                <div class="container">
                    <h1>🤖 Robot Guardian Live Stream</h1>
                    <div class="status">
                        <p>📹 Real-time AI-powered surveillance with person tracking and crying detection</p>
                        <p>🕒 Stream started: {{ timestamp }}</p>
                    </div>
                    
                    <img class="stream" src="/video_feed" alt="Live Stream">
                    
                    <div class="status">
                        <p>🔄 Auto-refresh every 30 seconds</p>
                        <p>💡 Features: YOLO Person Detection | Crying/Distress Alert | Robot Control</p>
                    </div>
                </div>
            </body>
            </html>
            '''
            
            @self.flask_app.route('/')
            def index():
                return render_template_string(stream_html, timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            @self.flask_app.route('/video_feed')
            def video_feed():
                return Response(self.generate_stream_frames(),
                              mimetype='multipart/x-mixed-replace; boundary=frame')
            
            @self.flask_app.route('/status')
            def status():
                return {
                    'streaming': True,
                    'crying_detected': self.crying_detected,
                    'person_count': len(getattr(self, 'last_detections', [])),
                    'timestamp': datetime.now().isoformat()
                }
            
            # Start Flask server in separate thread
            def run_flask():
                try:
                    self.flask_app.run(host='0.0.0.0', port=port, threaded=True, use_reloader=False)
                except Exception as e:
                    self.log(f"❌ Streaming server error: {e}")
                    self.root.after(0, self.stop_internet_streaming)
            
            self.streaming_thread = threading.Thread(target=run_flask, daemon=True)
            self.streaming_thread.start()
            
            # Update GUI
            self.root.after(0, lambda: self.stream_status.config(text="🟢 Stream Online", fg='lime'))
            
            # Get local IP for URL display
            local_ip = self.get_local_ip()
            stream_url = f"http://{local_ip}:{port}"
            
            self.log(f"🌐 Internet streaming started on port {port}")
            self.log(f"📱 Stream URL: {stream_url}")
            
        except Exception as e:
            self.log(f"❌ Failed to start streaming: {e}")
            self.streaming_enabled.set(False)
            self.root.after(0, lambda: self.stream_status.config(text="❌ Stream Error", fg='red'))
    
    def stop_internet_streaming(self):
        """Stop internet streaming"""
        try:
            self.streaming_enabled.set(False)
            
            if self.flask_app:
                # Flask doesn't have a clean shutdown method, so we'll let the thread finish
                self.flask_app = None
            
            self.root.after(0, lambda: self.stream_status.config(text="⚫ Stream Offline", fg='red'))
            self.log("🛑 Internet streaming stopped")
            
        except Exception as e:
            self.log(f"⚠️ Error stopping streaming: {e}")
    
    def generate_stream_frames(self):
        """Generate frames for Flask streaming"""
        target_interval = 1.0 / float(self.stream_fps)
        last_sent = time.monotonic()
        while self.streaming_enabled.get():
            try:
                start = time.monotonic()
                # Copy the latest frame with minimal locking
                frame = None
                if self.stream_lock.acquire(timeout=0.05):
                    try:
                        if self.stream_frame is not None:
                            frame = self.stream_frame.copy()
                    finally:
                        self.stream_lock.release()

                if frame is None:
                    # Create a lightweight placeholder frame
                    frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(frame, "No Signal", (20, 260), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

                # Resize to a reasonable streaming size to reduce payload
                try:
                    stream_h, stream_w = 480, 640
                    if frame.shape[0] != stream_h or frame.shape[1] != stream_w:
                        frame = cv2.resize(frame, (stream_w, stream_h), interpolation=cv2.INTER_LINEAR)
                except Exception:
                    pass

                # Encode frame as JPEG with tuned quality
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality])
                frame_bytes = buffer.tobytes()

                # Yield frame in MJPEG format
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

                # Pace the generator to target interval to avoid bursts
                elapsed = time.monotonic() - start
                sleep_time = target_interval - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

            except GeneratorExit:
                # Client disconnected
                break
            except Exception as e:
                self.log(f"⚠️ Stream frame generation error: {e}")
                time.sleep(0.05)
    
    def get_local_ip(self):
        """Get local IP address for streaming URL"""
        try:
            # Connect to a remote server to get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "localhost"
    
    def show_stream_url(self):
        """Show streaming URL in popup"""
        if self.streaming_enabled.get():
            local_ip = self.get_local_ip()
            port = self.streaming_port.get()
            url = f"http://{local_ip}:{port}"
            
            msg = f"🌐 Internet Stream URL:\n\n{url}\n\n"
            msg += "📱 Access from any device on your network!\n"
            msg += "🔗 Share this URL to stream to the internet\n\n"
            msg += "💡 For external access, configure router port forwarding\n"
            msg += f"   Forward external port → {local_ip}:{port}"
            
            messagebox.showinfo("Stream URL", msg)
        else:
            messagebox.showwarning("Stream Offline", "Enable internet streaming first!")
    def update_search_overlay(self, status_text, progress_text):
        """Update the search overlay display"""
        def _update():
            if hasattr(self, 'search_active') and self.search_active:
                # Show overlay
                self.search_overlay.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
                self.search_status_label.config(text=status_text)
                self.search_progress_label.config(text=progress_text)
            else:
                # Hide overlay
                self.search_overlay.place_forget()
        
        self.root.after(0, _update)

    def update_detection_count(self, count):
        """Update detection counter"""
        # Store last detections for streaming status
        self.last_detections = [1] * count  # Simple way to store count
        self.root.after(0, lambda: self.detection_label.config(text=f"Detections: {count}"))

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
            # Throttle GUI display updates to reduce main-thread load
            now = time.time()
            min_interval = 1.0 / float(self.display_fps) if self.display_fps > 0 else 0
            if now - self._last_display_time < min_interval:
                return
            self._last_display_time = now

            # Resize frame for display (scale down 1080p to manageable size)
            display_frame = cv2.resize(frame, (self.display_width, self.display_height), interpolation=cv2.INTER_LINEAR)

            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)

            # Convert to PIL Image (do NOT create PhotoImage off main thread)
            pil_image = Image.fromarray(frame_rgb)

            # Schedule creation of PhotoImage in main thread
            self.root.after(0, self._update_display, pil_image)

        except Exception as e:
            self.log(f"❌ Display update error: {e}")

    def _update_display(self, photo):
        """Update display in main thread"""
        try:
            # If a PIL Image is passed, create PhotoImage here (main thread)
            if isinstance(photo, Image.Image):
                tk_photo = ImageTk.PhotoImage(photo)
            else:
                tk_photo = photo

            self.video_canvas.configure(image=tk_photo, text='')
            self.video_canvas.image = tk_photo
        except Exception as e:
            self.log(f"❌ _update_display error: {e}")
    
    def update_detection_count(self, count):
        """Update detection counter"""
        self.root.after(0, lambda: self.detection_label.config(text=f"Detections: {count}"))
        
    def update_performance_display(self):
        """Update FPS and performance metrics"""
        # Keep gentle turn sequences flowing even if video loop paused
        self.process_turn_sequence()

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
            command = key_map[key]
            if command in ['L', 'R']:
                self.start_turn_sequence(command, auto=False, source='manual')
            else:
                if command == 'S' and self.turn_sequence_active():
                    self.pending_turn_sequence = None
                self.send_command(command, auto=False, force=(command == 'S'))
    
    def register_manual_alert(self, title: str, message: str, *, level: str = 'info') -> None:
        self.log(f"[{level.upper()}] {title}: {message}")

    def log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # Update text widget in main thread if available
        def update_log():
            if hasattr(self, 'stats_text') and self.stats_text:
                self.stats_text.insert(tk.END, log_entry)
                self.stats_text.see(tk.END)
                
                # Keep only last 50 lines
                lines = self.stats_text.get("1.0", tk.END).split('\n')
                if len(lines) > 50:
                    self.stats_text.delete("1.0", f"{len(lines)-50}.0")
                    
        if hasattr(self, 'stats_text') and self.stats_text:
            if threading.current_thread() == threading.main_thread():
                update_log()
            else:
                self.root.after(0, update_log)
        
        # Always log to console/logger
        logger.info(message)
        print(f"[{timestamp}] {message}")  # Also print for immediate visibility
        
    def run(self):
        """Start the application"""
        self.log("🚀 Robot Guardian AI Control Center Started")
        self.log(f"Pi URL: {self.PI_BASE_URL}")
        self.log("1. Update Pi URL above")
        self.log("2. Click '🔄 Connect' to start")
        self.log("3. Enable '🎯 Auto Person Tracking'")
        self.log("4. Enable '😢 Crying Detection' for alerts")
        self.log("5. Enable '🌐 Internet Streaming' to share")
        
        try:
            self.root.mainloop()
        finally:
            self.cleanup()
    
    def cleanup_memory(self):
        """Periodic memory cleanup to prevent accumulation"""
        try:
            # Clean old detection history
            now = time.time()
            self.detection_history = collections.deque([
                (ts, dets) for ts, dets in self.detection_history 
                if now - ts <= self.detection_keep_seconds
            ], maxlen=self.detection_history.maxlen)
            
            # Clean old crying history
            self.crying_history = collections.deque([
                (ts, score) for ts, score in self.crying_history 
                if now - ts <= self.crying_window_seconds
            ], maxlen=self.crying_history.maxlen)
            
            # GPU memory cleanup if using CUDA
            if self.model_device == 'cuda' and self.model_loaded:
                try:
                    import torch
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                except Exception:
                    pass
                    
        except Exception as e:
            self.log(f"⚠️ Memory cleanup error: {e}")

    def cleanup(self):
        """Clean up resources on exit"""
        self.stop_tracking()
        self.stop_internet_streaming()
        
        # Final memory cleanup
        self.cleanup_memory()
        
        if self.audio_available:
            try:
                pygame.mixer.quit()
            except:
                pass

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
    print("✅ 😢 Crying/Distress detection with alerts")
    print("✅ 🌐 Internet video streaming")
    print("✅ 🔊 Audio alert system")
    print()
    print("Requirements:")
    print("pip install flask mediapipe sounddevice soundfile pygame scipy")
    print()
    print("Setup:")
    print("1. Update PI_BASE_URL in code with your Pi IP")
    print("2. Make sure Pi server is running")
    print("3. Click Connect and start tracking!")
    print("4. Enable crying detection for baby monitoring")
    print("5. Enable internet streaming to share video")
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