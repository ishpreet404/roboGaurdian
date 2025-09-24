#!/usr/bin/env python3
"""
Low-Latency Robot Stream Client
==============================

Optimized GUI for minimal latency when streaming from remote Pi via tunnels.
Includes aggressive buffering, frame skipping, and compression optimizations.

Usage: python low_latency_client.py
Update STREAM_URL below with your serveo/tunnel URL.

Features:
- Minimal buffering (1 frame max)
- Aggressive frame skipping for real-time
- Reduced resolution options
- Direct HTTP stream without extra processing
- Optimized for tunnel connections

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

class LowLatencyStreamClient:
    def __init__(self):
        # ⚠️ UPDATE THIS WITH YOUR SERVEO URL ⚠️
        self.STREAM_URL = "https://0eb12f6c4bd4153084c9ee30fac391ff.serveo.net"
        self.PI_API_URL = self.STREAM_URL  # Same base URL
        
        # GUI setup
        self.root = tk.Tk()
        self.root.title("🚀 Low-Latency Robot Stream")
        self.root.geometry("800x700")
        self.root.configure(bg='#2b2b2b')
        
        # Stream variables
        self.cap = None
        self.streaming = False
        self.frame_queue = queue.Queue(maxsize=1)  # Ultra-minimal buffering
        self.current_frame = None
        self.frame_lock = threading.Lock()
        
        # Performance tracking
        self.fps_counter = 0
        self.fps_start_time = time.time()
        self.current_fps = 0
        self.total_frames = 0
        self.dropped_frames = 0
        
        # Stream settings
        self.stream_quality = tk.StringVar(value="medium")
        self.frame_skip = tk.IntVar(value=2)  # Skip frames for lower latency
        self.auto_quality = tk.BooleanVar(value=True)
        
        self.setup_gui()
        
    def setup_gui(self):
        """Setup the optimized GUI"""
        # Title frame
        title_frame = tk.Frame(self.root, bg='#2b2b2b')
        title_frame.pack(fill=tk.X, padx=10, pady=5)
        
        title_label = tk.Label(title_frame, text="🚀 Low-Latency Robot Stream", 
                              font=('Arial', 16, 'bold'), fg='white', bg='#2b2b2b')
        title_label.pack(side=tk.LEFT)
        
        # Connection status
        self.status_label = tk.Label(title_frame, text="⚫ Disconnected", 
                                   font=('Arial', 10), fg='red', bg='#2b2b2b')
        self.status_label.pack(side=tk.RIGHT)
        
        # Video display frame
        video_frame = tk.Frame(self.root, bg='black', relief=tk.SUNKEN, bd=2)
        video_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.video_label = tk.Label(video_frame, text="📹 Stream will appear here", 
                                  font=('Arial', 14), fg='white', bg='black')
        self.video_label.pack(fill=tk.BOTH, expand=True)
        
        # Performance info frame
        perf_frame = tk.Frame(self.root, bg='#3b3b3b', relief=tk.RAISED, bd=1)
        perf_frame.pack(fill=tk.X, padx=10, pady=2)
        
        self.fps_label = tk.Label(perf_frame, text="FPS: 0", 
                                 font=('Arial', 9), fg='lime', bg='#3b3b3b')
        self.fps_label.pack(side=tk.LEFT, padx=5)
        
        self.latency_label = tk.Label(perf_frame, text="Latency: --", 
                                    font=('Arial', 9), fg='cyan', bg='#3b3b3b')
        self.latency_label.pack(side=tk.LEFT, padx=5)
        
        self.dropped_label = tk.Label(perf_frame, text="Dropped: 0", 
                                    font=('Arial', 9), fg='yellow', bg='#3b3b3b')
        self.dropped_label.pack(side=tk.LEFT, padx=5)
        
        # Controls frame
        control_frame = tk.Frame(self.root, bg='#2b2b2b')
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Quality controls
        quality_frame = tk.LabelFrame(control_frame, text="📊 Stream Quality", 
                                     fg='white', bg='#2b2b2b', font=('Arial', 10, 'bold'))
        quality_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        
        quality_options = [("🔥 High", "high"), ("⚡ Medium", "medium"), ("🚀 Low (Fast)", "low")]
        for text, value in quality_options:
            tk.Radiobutton(quality_frame, text=text, variable=self.stream_quality, 
                          value=value, fg='white', bg='#2b2b2b', 
                          selectcolor='#4b4b4b', command=self.update_quality).pack(anchor=tk.W)
        
        tk.Checkbutton(quality_frame, text="🤖 Auto Quality", variable=self.auto_quality,
                      fg='white', bg='#2b2b2b', selectcolor='#4b4b4b').pack(anchor=tk.W)
        
        # Robot controls
        robot_frame = tk.LabelFrame(control_frame, text="🎮 Robot Control", 
                                   fg='white', bg='#2b2b2b', font=('Arial', 10, 'bold'))
        robot_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Direction buttons
        btn_frame = tk.Frame(robot_frame, bg='#2b2b2b')
        btn_frame.pack(padx=5, pady=5)
        
        tk.Button(btn_frame, text="↑", font=('Arial', 12, 'bold'), width=3,
                 command=lambda: self.send_command('F'), bg='#4CAF50', fg='white').grid(row=0, column=1, padx=2, pady=2)
        tk.Button(btn_frame, text="←", font=('Arial', 12, 'bold'), width=3,
                 command=lambda: self.send_command('L'), bg='#2196F3', fg='white').grid(row=1, column=0, padx=2, pady=2)
        tk.Button(btn_frame, text="⏹", font=('Arial', 12, 'bold'), width=3,
                 command=lambda: self.send_command('S'), bg='#f44336', fg='white').grid(row=1, column=1, padx=2, pady=2)
        tk.Button(btn_frame, text="→", font=('Arial', 12, 'bold'), width=3,
                 command=lambda: self.send_command('R'), bg='#2196F3', fg='white').grid(row=1, column=2, padx=2, pady=2)
        tk.Button(btn_frame, text="↓", font=('Arial', 12, 'bold'), width=3,
                 command=lambda: self.send_command('B'), bg='#FF9800', fg='white').grid(row=2, column=1, padx=2, pady=2)
        
        # Connection frame
        conn_frame = tk.LabelFrame(control_frame, text="🔗 Connection", 
                                  fg='white', bg='#2b2b2b', font=('Arial', 10, 'bold'))
        conn_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        tk.Button(conn_frame, text="🚀 Start Stream", command=self.start_stream,
                 bg='#4CAF50', fg='white', font=('Arial', 10, 'bold')).pack(fill=tk.X, padx=5, pady=2)
        tk.Button(conn_frame, text="🛑 Stop Stream", command=self.stop_stream,
                 bg='#f44336', fg='white', font=('Arial', 10, 'bold')).pack(fill=tk.X, padx=5, pady=2)
        tk.Button(conn_frame, text="📊 Test Connection", command=self.test_connection,
                 bg='#2196F3', fg='white', font=('Arial', 10, 'bold')).pack(fill=tk.X, padx=5, pady=2)
        
        # Start performance monitoring
        self.update_performance_display()
        
    def start_stream(self):
        """Start the video stream with optimizations"""
        if self.streaming:
            return
            
        try:
            self.log("🚀 Starting optimized stream...")
            
            # Build optimized stream URL with quality parameters
            quality_params = self.get_quality_params()
            stream_endpoint = f"{self.STREAM_URL}/video_feed"
            
            self.log(f"Connecting to: {stream_endpoint}")
            self.log(f"Quality: {self.stream_quality.get()}")
            
            # Use requests for better control over the stream
            response = requests.get(stream_endpoint, stream=True, timeout=10,
                                   headers={'Cache-Control': 'no-cache'})
            
            if response.status_code == 200:
                self.streaming = True
                self.status_label.config(text="🟢 Connected", fg='lime')
                
                # Start stream processing thread
                threading.Thread(target=self.process_stream, 
                               args=(response,), daemon=True).start()
                
                # Start display thread
                threading.Thread(target=self.display_frames, daemon=True).start()
                
                self.log("✅ Stream started successfully")
            else:
                self.log(f"❌ Stream failed: HTTP {response.status_code}")
                
        except Exception as e:
            self.log(f"❌ Stream error: {e}")
            self.status_label.config(text="❌ Error", fg='red')
            
    def process_stream(self, response):
        """Process the incoming stream with minimal latency"""
        bytes_buffer = b''
        frame_start_time = time.time()
        
        try:
            for chunk in response.iter_content(chunk_size=1024):
                if not self.streaming:
                    break
                    
                bytes_buffer += chunk
                
                # Look for JPEG boundaries
                start_marker = bytes_buffer.find(b'\xff\xd8')  # JPEG start
                end_marker = bytes_buffer.find(b'\xff\xd9')    # JPEG end
                
                if start_marker != -1 and end_marker != -1 and end_marker > start_marker:
                    # Extract JPEG frame
                    jpeg_data = bytes_buffer[start_marker:end_marker + 2]
                    bytes_buffer = bytes_buffer[end_marker + 2:]
                    
                    # Decode frame
                    frame_array = np.frombuffer(jpeg_data, dtype=np.uint8)
                    frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
                    
                    if frame is not None:
                        # Frame skipping for lower latency
                        self.total_frames += 1
                        if self.total_frames % (self.frame_skip.get() + 1) != 0:
                            self.dropped_frames += 1
                            continue
                        
                        # Calculate latency (rough estimate)
                        current_time = time.time()
                        estimated_latency = current_time - frame_start_time
                        
                        # Try to add frame to queue (non-blocking)
                        try:
                            self.frame_queue.put((frame, estimated_latency), block=False)
                        except queue.Full:
                            # Drop frame if queue is full (prioritize latest frame)
                            try:
                                self.frame_queue.get_nowait()
                                self.frame_queue.put((frame, estimated_latency), block=False)
                                self.dropped_frames += 1
                            except queue.Empty:
                                pass
                        
                        frame_start_time = current_time
                        
        except Exception as e:
            self.log(f"❌ Stream processing error: {e}")
        finally:
            self.streaming = False
            
    def display_frames(self):
        """Display frames with minimal delay"""
        while self.streaming:
            try:
                # Get latest frame (non-blocking)
                frame, latency = self.frame_queue.get(timeout=0.1)
                
                with self.frame_lock:
                    self.current_frame = frame
                    self.current_latency = latency
                
                # Resize frame for display
                display_frame = self.resize_for_display(frame)
                
                # Convert to PhotoImage
                frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                image = Image.fromarray(frame_rgb)
                photo = ImageTk.PhotoImage(image)
                
                # Update display (must be done in main thread)
                self.root.after(0, self.update_video_display, photo)
                
                # Update FPS counter
                self.fps_counter += 1
                
                # Auto quality adjustment
                if self.auto_quality.get():
                    self.adjust_quality_automatically(latency)
                    
            except queue.Empty:
                continue
            except Exception as e:
                self.log(f"❌ Display error: {e}")
                break
                
    def update_video_display(self, photo):
        """Update video display (called from main thread)"""
        self.video_label.configure(image=photo)
        self.video_label.image = photo  # Keep a reference
        
    def resize_for_display(self, frame):
        """Resize frame based on quality setting"""
        height, width = frame.shape[:2]
        
        if self.stream_quality.get() == "low":
            # Aggressive downscaling for speed
            new_width = min(480, width)
            new_height = int(height * (new_width / width))
        elif self.stream_quality.get() == "medium":
            new_width = min(640, width)
            new_height = int(height * (new_width / width))
        else:  # high
            new_width = min(800, width)
            new_height = int(height * (new_width / width))
            
        if new_width != width:
            frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_FAST)
            
        return frame
        
    def adjust_quality_automatically(self, latency):
        """Automatically adjust quality based on latency"""
        if latency > 1.0 and self.stream_quality.get() != "low":
            self.stream_quality.set("low")
            self.frame_skip.set(3)
            self.log("🚀 Auto: Switched to low quality (high latency detected)")
        elif latency < 0.3 and self.stream_quality.get() != "high":
            self.stream_quality.set("high")
            self.frame_skip.set(1)
            self.log("🔥 Auto: Switched to high quality (low latency)")
        elif 0.3 <= latency <= 1.0 and self.stream_quality.get() != "medium":
            self.stream_quality.set("medium")
            self.frame_skip.set(2)
            self.log("⚡ Auto: Switched to medium quality")
            
    def get_quality_params(self):
        """Get quality parameters for stream request"""
        quality = self.stream_quality.get()
        
        if quality == "low":
            return {"width": 320, "height": 240, "quality": 50, "fps": 15}
        elif quality == "medium":
            return {"width": 480, "height": 360, "quality": 70, "fps": 20}
        else:  # high
            return {"width": 640, "height": 480, "quality": 85, "fps": 30}
            
    def update_quality(self):
        """Update quality settings"""
        quality = self.stream_quality.get()
        
        if quality == "low":
            self.frame_skip.set(3)
        elif quality == "medium":
            self.frame_skip.set(2)
        else:  # high
            self.frame_skip.set(1)
            
        self.log(f"📊 Quality changed to: {quality}")
        
    def stop_stream(self):
        """Stop the video stream"""
        self.streaming = False
        self.status_label.config(text="⚫ Disconnected", fg='red')
        
        # Clear frame queue
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break
                
        # Reset video display
        self.video_label.configure(image='', text="📹 Stream stopped")
        self.video_label.image = None
        
        self.log("🛑 Stream stopped")
        
    def send_command(self, command):
        """Send robot command via API"""
        try:
            url = f"{self.PI_API_URL}/move"
            data = {"direction": command}
            
            # Use short timeout for responsiveness
            response = requests.post(url, json=data, timeout=2)
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"🎮 Command {command}: {result.get('status', 'OK')}")
            else:
                self.log(f"❌ Command {command} failed: HTTP {response.status_code}")
                
        except requests.Timeout:
            self.log(f"⏱️ Command {command} timeout")
        except Exception as e:
            self.log(f"❌ Command {command} error: {e}")
            
    def test_connection(self):
        """Test connection to Pi server"""
        try:
            self.log("🔍 Testing connection...")
            
            response = requests.get(f"{self.PI_API_URL}/status", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Connection OK: {data}")
                self.status_label.config(text="✅ Ready", fg='lime')
            else:
                self.log(f"❌ Connection failed: HTTP {response.status_code}")
                self.status_label.config(text="❌ Error", fg='red')
                
        except Exception as e:
            self.log(f"❌ Connection test failed: {e}")
            self.status_label.config(text="❌ No connection", fg='red')
            
    def update_performance_display(self):
        """Update performance indicators"""
        current_time = time.time()
        elapsed = current_time - self.fps_start_time
        
        if elapsed >= 1.0:  # Update every second
            self.current_fps = self.fps_counter / elapsed
            self.fps_counter = 0
            self.fps_start_time = current_time
            
        # Update displays
        self.fps_label.config(text=f"FPS: {self.current_fps:.1f}")
        self.dropped_label.config(text=f"Dropped: {self.dropped_frames}")
        
        if hasattr(self, 'current_latency'):
            self.latency_label.config(text=f"Latency: {self.current_latency:.2f}s")
        
        # Schedule next update
        self.root.after(100, self.update_performance_display)
        
    def log(self, message):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def run(self):
        """Start the application"""
        self.log("🚀 Low-Latency Stream Client Started")
        self.log(f"Stream URL: {self.STREAM_URL}")
        self.log("Click 'Start Stream' to begin")
        
        try:
            self.root.mainloop()
        finally:
            self.stop_stream()

if __name__ == "__main__":
    print("🚀 Low-Latency Robot Stream Client")
    print("=" * 40)
    print("Optimizations enabled:")
    print("✅ Minimal buffering (1 frame max)")
    print("✅ Aggressive frame skipping") 
    print("✅ Auto quality adjustment")
    print("✅ Direct HTTP streaming")
    print("✅ Performance monitoring")
    print()
    
    client = LowLatencyStreamClient()
    client.run()