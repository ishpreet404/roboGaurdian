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
        self.PI_BASE_URL = "http://10.173.125.26:5000"  # Updated Pi IP from error log
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
        self.command_cooldown = 0.1  # Reduced from 0.3 to 0.1 seconds between commands
        # Gentle turn sequencing state
        self.pending_turn_sequence = None
        self.last_turn_sequence_info = {'stops_sent': 0, 'total_stops': 0}

        # Inference performance tuning for low latency
        self.inference_size = 224            # Even smaller for faster inference (224 vs 320)
        self.max_inference_fps = 15         # Increased from 8 to 15 FPS for more responsive tracking
        self.last_inference_time = 0
        self.model_device = 'cpu'           # will be set appropriately when model loads
        # Detection smoothing (avoid flicker) - reduced for lower latency
        self.detection_history = collections.deque(maxlen=4)  # Reduced from 8 to 4 for faster response
        self.detection_keep_seconds = 0.3  # Reduced from 0.6 to 0.3 seconds for faster response
        self.crying_history = collections.deque(maxlen=4)  # Reduced for faster response
        
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
        # Streaming performance tuning for low latency
        self.stream_fps = 15           # Increased from 12 to 15 FPS for smoother display
        self.jpeg_quality = 40         # Reduced from 60 to 40 for lower latency
        # Display throttling to avoid PhotoImage overload on main thread
        self.display_fps = 20          # Increased from 12 to 20 for more responsive display
        self._last_display_time = 0
        
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
        """Load YOLO model in background"""
        def load_model():
            try:
                self.log("🧠 Loading YOLO model...")
                # Choose device: prefer CUDA when available
                try:
                    if torch.cuda.is_available():
                        self.model_device = 'cuda'
                    else:
                        self.model_device = 'cpu'
                except Exception:
                    self.model_device = 'cpu'

                self.model = YOLO('yolov8n.pt')  # Nano version for speed
                # If the ultralytics API supports moving to device, do it (best-effort)
                try:
                    self.model.to(self.model_device)
                except Exception:
                    pass
                self.model_loaded = True
                self.root.after(0, lambda: self.model_label.config(text="Model: YOLOv8n Ready ✅", fg='lime'))
                self.log("✅ YOLO model loaded successfully")
            except Exception as e:
                self.root.after(0, lambda: self.model_label.config(text="Model: Error ❌", fg='red'))
                self.log(f"❌ Failed to load YOLO model: {e}")
                
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
                
                # Run YOLO detection if model is loaded
                processed_frame = frame.copy()
                detections = []

                # Throttle inference to target FPS and resize for faster processing
                now = time.time()
                min_interval = 1.0 / float(self.max_inference_fps)
                do_infer = (now - self.last_inference_time) >= min_interval

                if self.model_loaded and self.model and do_infer:
                    try:
                        # Pass imgsz and device to model call for faster inference
                        results = self.model(frame, classes=[0], conf=self.confidence_threshold.get(), imgsz=self.inference_size, device=self.model_device, verbose=False)
                        self.last_inference_time = now

                        if len(results) > 0 and len(results[0].boxes) > 0:
                            # Iterate detections
                            boxes = results[0].boxes.xyxy.cpu().numpy()
                            confidences = results[0].boxes.conf.cpu().numpy()
                            for i, (box, conf) in enumerate(zip(boxes, confidences)):
                                x1, y1, x2, y2 = box.astype(int)
                                detections.append({'box': (x1, y1, x2, y2), 'confidence': float(conf), 'area': (x2 - x1) * (y2 - y1)})

                        # Save detection snapshot for smoothing
                        if detections:
                            self.detection_history.append((now, detections))

                    except Exception as e:
                        self.log(f"⚠️ YOLO detection error: {e}")
                        time.sleep(0.05)

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

                # Auto tracking logic - FIXED
                if self.auto_tracking.get():
                    if detections:
                        # Person found - stop search mode and track
                        if hasattr(self, 'search_active') and self.search_active:
                            self.search_active = False
                            if self.turn_sequence_active():
                                self.pending_turn_sequence = None
                            self.send_command('S', auto=True, force=True)  # Stop first
                            # Hide search overlay
                            self.update_search_overlay("", "")
                            self.log("🎯 Person found! Stopping search, starting tracking")
                            time.sleep(0.2)  # Brief pause before tracking
                        
                        self.process_auto_tracking(detections, processed_frame.shape)
                    else:
                        # No person detected - start/continue search
                        self.process_search_mode()

                # Crying detection: check largest person to reduce CPU
                if self.crying_detection_enabled.get() and detections:
                    try:
                        # pick largest detection
                        target = max(detections, key=lambda d: d.get('area', 0))
                        self.detect_crying(frame, target['box'], processed_frame)
                    except Exception as e:
                        self.log(f"⚠️ Crying detect call failed: {e}")
                
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

        # Faster cooldown for more responsive tracking
        gentle_cooldown = 0.2  # Reduced from 500ms to 200ms between auto commands for faster response
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
            
            response = requests.post(url, json=data, timeout=1)
            
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
                
                response = requests.get(url, timeout=2)
                
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
                        video_response = requests.get(video_url, timeout=1, stream=True)
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

            # Resize frame for display
            display_frame = cv2.resize(frame, (640, 480), interpolation=cv2.INTER_LINEAR)

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
    
    def cleanup(self):
        """Clean up resources on exit"""
        self.stop_tracking()
        self.stop_internet_streaming()
        
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