import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import cv2
from PIL import Image, ImageTk
import threading
import time
import queue
import os
import numpy as np
from datetime import datetime
import webbrowser
import threading as _threading
import math

class PersonTrackerGUI:
    def __init__(self, window):
        self.window = window
        self.window.title("Person Tracking Robot Controller")
        self.window.geometry("900x700")
        self.window.configure(bg='#f0f0f0')
        
        # Initialize variables
        self.cap = None
        self.tracking = False
        self.tracking_thread = None
        self.frame_queue = queue.Queue(maxsize=2)
        self.command_history = []
        self.current_command = 'S'
        # Source metadata (for video file playback timing)
        self.source_is_file = False
        self.source_fps = None
        self.source_frame_interval = None
        self.last_frame_time = None
        # Detection backend settings
        self.detection_backend = tk.StringVar(value="YOLO")  # default to YOLO now
        self.conf_threshold = tk.DoubleVar(value=0.1)
        self.dnn_net = None
        self.dnn_loaded = False
        self.last_backend_used = None
        self.frame_index = 0
        self.ssd_frame_skip = 1  # Can raise to 2-3 on slow machines
        # YOLO backend (lazy loaded)
        self.yolo_model = None
        self.yolo_loaded = False
        self.yolo_model_name = tk.StringVar(value="yolov8n.pt")  # fixed single model
        self.yolo_frame_skip = 1
        self.yolo_import_error = None
        # Removed model variants; fixed to yolov8n.pt
        
        # Robot connection
        self.robot_connected = False
        self.robot_ip = tk.StringVar(value="192.168.1.100")
        
        # Video source
        self.video_source = tk.IntVar(value=0)
        self.video_file = tk.StringVar()
        
        # Create GUI elements
        self.create_widgets()
        
        # Start update loop
        self.update_frame()
        
    def create_widgets(self):
        """Create all GUI widgets"""
        
        # Title
        title_label = tk.Label(
            self.window, 
            text="🤖 Person Tracking Robot Controller",
            font=("Arial", 18, "bold"),
            bg='#f0f0f0'
        )
        title_label.pack(pady=10)
        
        # Main container
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Video and controls
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, padx=5, sticky="nsew")
        
        # Video display
        self.video_label = tk.Label(left_frame, bg='black', width=640, height=480)
        self.video_label.pack(pady=5)
        
        # Status bar
        status_frame = ttk.Frame(left_frame)
        status_frame.pack(fill=tk.X, pady=5)
        
        self.status_label = tk.Label(
            status_frame, 
            text="Status: Ready", 
            font=("Arial", 10),
            bg='lightgray',
            relief=tk.SUNKEN,
            anchor='w'
        )
        self.status_label.pack(fill=tk.X, padx=2)
        
        # Control buttons
        control_frame = ttk.LabelFrame(left_frame, text="Controls", padding="10")
        control_frame.pack(fill=tk.X, pady=5)
        
        button_frame = ttk.Frame(control_frame)
        button_frame.pack()
        
        self.start_button = ttk.Button(
            button_frame, 
            text="▶ Start Tracking",
            command=self.start_tracking,
            width=15
        )
        self.start_button.grid(row=0, column=0, padx=5, pady=5)
        
        self.stop_button = ttk.Button(
            button_frame, 
            text="⏹ Stop Tracking",
            command=self.stop_tracking,
            state=tk.DISABLED,
            width=15
        )
        self.stop_button.grid(row=0, column=1, padx=5, pady=5)
        
        # Right panel - Settings and info
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, padx=5, sticky="nsew")
        
        # Video source selection
        source_frame = ttk.LabelFrame(right_frame, text="Video Source", padding="10")
        source_frame.pack(fill=tk.X, pady=5)
        
        ttk.Radiobutton(
            source_frame, 
            text="Webcam", 
            variable=self.video_source, 
            value=0
        ).pack(anchor='w')
        
        ttk.Radiobutton(
            source_frame, 
            text="Video File", 
            variable=self.video_source, 
            value=1
        ).pack(anchor='w')
        
        file_frame = ttk.Frame(source_frame)
        file_frame.pack(fill=tk.X, pady=5)
        
        self.file_entry = ttk.Entry(file_frame, textvariable=self.video_file)
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(
            file_frame,
            text="Browse",
            command=self.browse_video_file
        ).pack(side=tk.RIGHT, padx=5)
        
        # Robot connection
        robot_frame = ttk.LabelFrame(right_frame, text="Robot Connection", padding="10")
        robot_frame.pack(fill=tk.X, pady=5)
        
        self.robot_connected_var = tk.BooleanVar(value=False)
        self.robot_check = ttk.Checkbutton(
            robot_frame,
            text="Connect to Robot",
            variable=self.robot_connected_var,
            command=self.toggle_robot_connection
        )
        self.robot_check.pack(anchor='w')
        
        ip_frame = ttk.Frame(robot_frame)
        ip_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(ip_frame, text="Robot IP:").pack(side=tk.LEFT)
        ttk.Entry(ip_frame, textvariable=self.robot_ip, width=15).pack(side=tk.LEFT, padx=5)
        
        # Current command display
        command_frame = ttk.LabelFrame(right_frame, text="Current Command", padding="10")
        command_frame.pack(fill=tk.X, pady=5)
        
        self.command_display = tk.Label(
            command_frame,
            text="STOP",
            font=("Arial", 24, "bold"),
            fg="red",
            bg="black",
            width=10
        )
        self.command_display.pack(pady=10)
        
        # Command visualization
        visual_frame = ttk.Frame(command_frame)
        visual_frame.pack()
        
        # Arrow buttons for visualization
        self.arrow_frame = ttk.Frame(visual_frame)
        self.arrow_frame.pack()
        
        # Create arrow display
        self.create_arrow_display()
        
        # Command history
        history_frame = ttk.LabelFrame(right_frame, text="Command History", padding="10")
        history_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # History listbox with scrollbar
        history_scroll = ttk.Scrollbar(history_frame)
        history_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.history_listbox = tk.Listbox(
            history_frame,
            yscrollcommand=history_scroll.set,
            height=8,
            font=("Courier", 9)
        )
        self.history_listbox.pack(fill=tk.BOTH, expand=True)
        history_scroll.config(command=self.history_listbox.yview)
        
        # Statistics
        stats_frame = ttk.LabelFrame(right_frame, text="Statistics", padding="10")
        stats_frame.pack(fill=tk.X, pady=5)
        
        self.stats_labels = {
            'fps': tk.Label(stats_frame, text="FPS: 0.0"),
            'people': tk.Label(stats_frame, text="People detected: 0"),
            'tracking': tk.Label(stats_frame, text="Tracking: No")
        }
        
        for label in self.stats_labels.values():
            label.pack(anchor='w')

        # Detector settings panel
        detector_frame = ttk.LabelFrame(right_frame, text="Detector Settings", padding="10")
        detector_frame.pack(fill=tk.X, pady=5)

        ttk.Label(detector_frame, text="Backend:").grid(row=0, column=0, sticky='w')
        backend_combo = ttk.Combobox(detector_frame, values=["Haar", "SSD", "YOLO"], textvariable=self.detection_backend, state="readonly", width=10)
        backend_combo.grid(row=0, column=1, padx=5, pady=2, sticky='w')

        ttk.Label(detector_frame, text="Confidence:").grid(row=1, column=0, sticky='w')
        conf_scale = ttk.Scale(detector_frame, from_=0.1, to=0.9, orient='horizontal', variable=self.conf_threshold)
        conf_scale.grid(row=1, column=1, padx=5, pady=2, sticky='we')

        detector_frame.columnconfigure(1, weight=1)

        ttk.Button(detector_frame, text="Download SSD Model", command=self.ensure_model_download).grid(row=2, column=0, columnspan=2, pady=4, sticky='we')

        self.detector_status_label = tk.Label(detector_frame, text="Backend: YOLO", anchor='w')
        self.detector_status_label.grid(row=3, column=0, columnspan=2, sticky='we')
    
    def create_arrow_display(self):
        """Create arrow buttons for command visualization"""
        # Arrow configuration
        arrow_config = {
            'F': ('↑', 1, 1, 'green'),
            'B': ('↓', 3, 1, 'orange'),
            'L': ('←', 2, 0, 'blue'),
            'R': ('→', 2, 2, 'purple'),
            'S': ('⏹', 2, 1, 'red')
        }
        
        self.arrow_labels = {}
        
        for cmd, (symbol, row, col, color) in arrow_config.items():
            label = tk.Label(
                self.arrow_frame,
                text=symbol,
                font=("Arial", 20),
                width=3,
                height=1,
                bg='lightgray',
                relief=tk.RAISED
            )
            label.grid(row=row, column=col, padx=2, pady=2)
            self.arrow_labels[cmd] = (label, color)
    
    def update_arrow_display(self, command):
        """Update arrow display based on current command"""
        for cmd, (label, color) in self.arrow_labels.items():
            if cmd == command:
                label.config(bg=color, relief=tk.SUNKEN)
            else:
                label.config(bg='lightgray', relief=tk.RAISED)
    
    def browse_video_file(self):
        """Open file dialog to select video file"""
        filename = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.video_file.set(filename)
    
    def toggle_robot_connection(self):
        """Toggle robot connection"""
        self.robot_connected = self.robot_connected_var.get()
        if self.robot_connected:
            self.update_status(f"Connected to robot at {self.robot_ip.get()}")
        else:
            self.update_status("Robot disconnected")
    
    def start_tracking(self):
        """Start person tracking"""
        if self.tracking:
            return
        
        # Get video source
        if self.video_source.get() == 0:
            source = 0  # Webcam
            self.source_is_file = False
        else:
            source = self.video_file.get()
            if not source or not os.path.exists(source):
                messagebox.showerror("Error", "Please select a valid video file")
                return
            self.source_is_file = True
        
        # Open video capture
        # On Windows, using CAP_DSHOW improves reliability with some webcams
        cap = None
        if source == 0:
            try:
                cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            except Exception:
                cap = None
        if cap is None:
            cap = cv2.VideoCapture(source)
        
        if not cap.isOpened():
            messagebox.showerror("Error", "Failed to open video source")
            return
        
        # Try to set reasonable defaults
        if source == 0:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)
            # Give the camera a brief moment to warm up
            time.sleep(0.3)
            # Estimate FPS for webcam later dynamically
            self.source_fps = None
            self.source_frame_interval = None
        
        # Probe a few frames to ensure capture works
        ok = False
        for _ in range(10):
            ret, test_frame = cap.read()
            if ret and test_frame is not None:
                ok = True
                break
            time.sleep(0.05)
        if not ok:
            cap.release()
            messagebox.showerror("Error", "Camera opened but failed to read frames")
            return
        
        # Assign the verified capture
        self.cap = cap
        if self.source_is_file:
            fps_val = self.cap.get(cv2.CAP_PROP_FPS)
            if fps_val and fps_val > 1 and fps_val < 240:
                self.source_fps = fps_val
                self.source_frame_interval = 1.0 / self.source_fps
            else:
                # Fallback default
                self.source_fps = 30.0
                self.source_frame_interval = 1.0 / 30.0
        self.last_frame_time = None
        
        # Clear any leftover frames
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except Exception:
                break
        
        # Start tracking
        self.tracking = True
        self.tracking_thread = threading.Thread(target=self.tracking_loop, daemon=True)
        self.tracking_thread.start()
        
        # Update UI
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.update_status("Tracking started")
        self.detector_status_label.config(text=f"Backend: {self.detection_backend.get()}")
    
    def stop_tracking(self):
        """Stop person tracking"""
        self.tracking = False
        
        # Wait for thread to finish
        if self.tracking_thread:
            self.tracking_thread.join(timeout=1.0)
        
        # Release video capture
        if self.cap:
            self.cap.release()
            self.cap = None
        
        # Clear video display
        self.video_label.config(image='')
        
        # Update UI
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.update_status("Tracking stopped")
        
        # Send stop command
        self.update_command('S')
    
    def tracking_loop(self):
        """Main tracking loop (runs in separate thread)"""
        # Prepare detectors (lazy load)
        face_cascade = None
        body_cascade = None
        
        fps_time = time.time()
        
        while self.tracking and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                if self.video_source.get() == 1:  # Video file
                    # Loop video
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    break
            # Throttle playback for file sources to original FPS
            if self.source_is_file and self.source_frame_interval:
                now = time.time()
                if self.last_frame_time is None:
                    self.last_frame_time = now
                else:
                    elapsed = now - self.last_frame_time
                    remaining = self.source_frame_interval - elapsed
                    if remaining > 0:
                        time.sleep(min(remaining, 0.05))
                    self.last_frame_time = time.time()
            
            # Calculate FPS
            now2 = time.time()
            fps = 1.0 / (now2 - fps_time) if now2 - fps_time > 0 else 0
            fps_time = now2
            
            # Keep original for detection; make a resized copy for display
            orig_h, orig_w = frame.shape[:2]
            display_frame = cv2.resize(frame, (640, 480))
            disp_h, disp_w = display_frame.shape[:2]
            
            # Select detector backend
            backend = self.detection_backend.get()
            if backend != self.last_backend_used:
                # Reset / (re)load as needed
                if backend == 'Haar':
                    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                    body_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_fullbody.xml')
                elif backend == 'SSD':
                    self.load_ssd_model()
                elif backend == 'YOLO':
                    self.load_yolo_model()
                self.last_backend_used = backend
            
            people = []
            if backend == 'Haar':
                if face_cascade is None or body_cascade is None:
                    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                    body_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_fullbody.xml')
                gray = cv2.cvtColor(display_frame, cv2.COLOR_BGR2GRAY)
                faces = []
                bodies = []
                try:
                    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                except Exception:
                    pass
                try:
                    bodies = body_cascade.detectMultiScale(gray, 1.1, 3)
                except Exception:
                    pass
                for (x, y, w, h) in faces:
                    people.append((x, y - h, w, h * 3))
                for (x, y, w, h) in bodies:
                    people.append((x, y, w, h))
            elif backend == 'SSD':
                process_this = True
                if self.ssd_frame_skip > 1:
                    process_this = (self.frame_index % self.ssd_frame_skip == 0)
                if process_this and self.dnn_net is not None and self.dnn_loaded:
                    people = self.run_ssd(display_frame, self.conf_threshold.get())
                self.frame_index += 1
            elif backend == 'YOLO':
                process_this = True
                if self.yolo_frame_skip > 1:
                    process_this = (self.frame_index % self.yolo_frame_skip == 0)
                if process_this and self.yolo_loaded and self.yolo_model is not None:
                    # Run on original frame for better accuracy
                    yolo_people = self.run_yolo(frame, self.conf_threshold.get())
                    # Scale boxes to display frame size if sizes differ
                    if (orig_w, orig_h) != (disp_w, disp_h):
                        scale_x = disp_w / orig_w
                        scale_y = disp_h / orig_h
                        for (x, y, w, h) in yolo_people:
                            nx = int(x * scale_x)
                            ny = int(y * scale_y)
                            nw = int(w * scale_x)
                            nh = int(h * scale_y)
                            if nw > 4 and nh > 8:
                                people.append((nx, ny, nw, nh))
                    else:
                        people = yolo_people
                self.frame_index += 1
            
            # Select closest/largest person
            target_person = None
            if people:
                # Sort by area (largest first)
                people.sort(key=lambda p: p[2] * p[3], reverse=True)
                target_person = people[0]
            
            # Calculate command
            command = self.calculate_command(target_person, display_frame.shape[1])
            
            # Draw visualization
            display_frame = self.draw_tracking_info(display_frame, people, target_person, command, fps)
            
            # Update statistics
            self.update_stats(fps, len(people), target_person is not None)
            
            # Put frame in queue for display
            try:
                self.frame_queue.put_nowait(display_frame)
            except queue.Full:
                # Drop oldest and insert newest to keep UI fresh
                try:
                    self.frame_queue.get_nowait()
                except Exception:
                    pass
                try:
                    self.frame_queue.put_nowait(display_frame)
                except Exception:
                    pass
            
            # Small delay to avoid overwhelming the UI thread
            time.sleep(0.01)
    
    def calculate_command(self, person, frame_width):
        """Calculate movement command based on person position"""
        if not person:
            return 'S'
        
        x, y, w, h = person
        center_x = x + w // 2
        frame_center = frame_width // 2
        
        # Calculate offset from center
        offset = center_x - frame_center
        threshold = 100
        
        # Determine command
        if abs(offset) > threshold:
            command = 'R' if offset > 0 else 'L'
        elif h < 150:  # Person far away (small)
            command = 'F'
        elif h > 350:  # Person too close (large)
            command = 'B'
        else:
            command = 'S'
        
        # Update command
        if command != self.current_command:
            self.update_command(command)
        
        return command
    
    def draw_tracking_info(self, frame, people, target, command, fps):
        """Draw tracking visualization on frame"""
        # Draw all detected people
        for i, (x, y, w, h) in enumerate(people):
            if (x, y, w, h) == target:
                # Target in green
                color = (0, 255, 0)
                thickness = 3
                cv2.putText(frame, "TARGET", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            else:
                # Others in gray
                color = (128, 128, 128)
                thickness = 1
            
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, thickness)
        
        # Draw center line
        center_x = frame.shape[1] // 2
        cv2.line(frame, (center_x, 0), (center_x, frame.shape[0]), (255, 255, 0), 1)
        
        # Draw safe zones
        threshold = 100
        cv2.line(frame, (center_x - threshold, 0), (center_x - threshold, frame.shape[0]), (255, 0, 0), 1)
        cv2.line(frame, (center_x + threshold, 0), (center_x + threshold, frame.shape[0]), (255, 0, 0), 1)
        
        # Draw status info
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Command: {command}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"People: {len(people)}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        return frame
    
    def update_frame(self):
        """Update video frame in GUI"""
        try:
            if not self.frame_queue.empty():
                # Non-blocking read from queue so UI stays responsive
                try:
                    frame = self.frame_queue.get_nowait()
                except Exception:
                    frame = None
                
                if frame is not None:
                    # Convert frame to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Convert to PIL Image
                    image = Image.fromarray(frame_rgb)
                    
                    # Convert to PhotoImage
                    photo = ImageTk.PhotoImage(image=image)
                    
                    # Update label (keep a reference to prevent GC)
                    self.video_label.config(image=photo)
                    self.video_label.image = photo
        except Exception as e:
            print(f"Error updating frame: {e}")
        
        # Schedule next update
        self.window.after(33, self.update_frame)
    
    def update_command(self, command):
        """Update current command and display"""
        previous_command = self.current_command
        self.current_command = command
        
        # Update command display
        command_text = {
            'F': 'FORWARD',
            'B': 'BACKWARD',
            'L': 'LEFT',
            'R': 'RIGHT',
            'S': 'STOP'
        }
        
        command_color = {
            'F': 'green',
            'B': 'orange',
            'L': 'blue',
            'R': 'purple',
            'S': 'red'
        }
        
        self.command_display.config(
            text=command_text.get(command, 'UNKNOWN'),
            fg=command_color.get(command, 'white')
        )
        
        # Update arrow display
        self.update_arrow_display(command)
        
        # Add to history
        timestamp = datetime.now().strftime("%H:%M:%S")
        history_entry = f"{timestamp} - {command_text.get(command, 'UNKNOWN')}"
        self.history_listbox.insert(tk.END, history_entry)
        self.history_listbox.see(tk.END)
        
        # Limit history size
        if self.history_listbox.size() > 100:
            self.history_listbox.delete(0)
        
        # Send to robot if connected and command changed
        if self.robot_connected and command != previous_command:
            self.send_command_to_robot(command)
    
    def send_command_to_robot(self, command):
        """Send command to robot (simulated)"""
        try:
            if self.robot_connected:
                # In real implementation, this would send HTTP request
                # For testing, just log it
                print(f"Sending command '{command}' to robot at {self.robot_ip.get()}")
                
                # Simulate sending with threading to avoid blocking
                def simulate_send():
                    import requests
                    try:
                        url = f"http://{self.robot_ip.get()}:5000/move"
                        response = requests.post(url, json={'command': command}, timeout=0.5)
                        print(f"Robot response: {response.status_code}")
                    except:
                        pass  # Ignore errors in simulation
                
                # Uncomment to actually send commands
                # threading.Thread(target=simulate_send, daemon=True).start()
        except Exception as e:
            print(f"Error sending command: {e}")
    
    def update_status(self, message):
        """Update status bar"""
        self.status_label.config(text=f"Status: {message}")
    
    def update_stats(self, fps, people_count, tracking):
        """Update statistics display"""
        def _update():
            source_info = "File" if self.source_is_file else "Webcam"
            if self.source_is_file and self.source_fps:
                source_info += f" ({self.source_fps:.1f} fps)"
            backend = self.detection_backend.get()
            status = f"Backend: {backend}"
            if backend == 'SSD' and not self.dnn_loaded:
                status += " (not loaded)"
            if backend == 'YOLO':
                if self.yolo_import_error:
                    status += " (pip install ultralytics)"
                elif not self.yolo_loaded:
                    status += " (loading)"
            self.detector_status_label.config(text=status)
            self.stats_labels['fps'].config(text=f"FPS (proc): {fps:.1f}")
            self.stats_labels['people'].config(text=f"People detected: {people_count}")
            self.stats_labels['tracking'].config(text=f"Tracking: {'Yes' if tracking else 'No'} | Source: {source_info}")
        self.window.after(0, _update)

    def open_model_download(self):
        """Open browser to download SSD model if missing"""
        url = "https://drive.google.com/uc?export=download&id=0B3gersZ2cHIxRm5PMWRoTkdHdHc"
        try:
            webbrowser.open(url)
        except Exception:
            messagebox.showinfo("Download", f"Open this link manually:\n{url}")

    def ensure_model_download(self):
        """Ensure the SSD model file exists; if not, attempt automatic download."""
        prototxt = os.path.join(os.getcwd(), 'MobileNetSSD_deploy.prototxt')
        caffemodel = os.path.join(os.getcwd(), 'MobileNetSSD_deploy.caffemodel')
        if os.path.exists(caffemodel) and os.path.getsize(caffemodel) > 1_000_000:
            messagebox.showinfo("Model", "Model already present.")
            return
        # Ask user to proceed
        if not messagebox.askyesno("Download Model", "Download MobileNetSSD_deploy.caffemodel now (~23MB)?"):
            return
        # Run in background thread
        t = _threading.Thread(target=self._download_model_thread, args=(caffemodel,), daemon=True)
        t.start()

    def _download_model_thread(self, dest_path):
        import requests
        url = "https://raw.githubusercontent.com/chuanqi305/MobileNet-SSD/master/MobileNetSSD_deploy.caffemodel"
        # Fallback note: if this URL 404s, user must manual download from Google Drive
        try:
            self.update_status("Downloading SSD model...")
            resp = requests.get(url, stream=True, timeout=30)
            if resp.status_code != 200:
                self.update_status("Download failed (status)")
                messagebox.showwarning("Download Failed", f"HTTP {resp.status_code}. Opening browser for manual download.")
                self.open_model_download()
                return
            total = int(resp.headers.get('Content-Length', 0))
            downloaded = 0
            chunk_size = 8192
            tmp_path = dest_path + '.part'
            with open(tmp_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=chunk_size):
                    if not chunk:
                        continue
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        pct = downloaded / total * 100
                        if downloaded % (chunk_size * 25) == 0:
                            self.update_status(f"Downloading SSD model... {pct:.1f}%")
            # Basic size sanity check (>5MB)
            if os.path.getsize(tmp_path) < 5_000_000:
                os.remove(tmp_path)
                self.update_status("Download corrupted")
                messagebox.showerror("Download Error", "Downloaded file too small / corrupt.")
                self.open_model_download()
                return
            # Rename to final
            if os.path.exists(dest_path):
                try:
                    os.remove(dest_path)
                except Exception:
                    pass
            os.replace(tmp_path, dest_path)
            self.update_status("Model downloaded")
            messagebox.showinfo("Model", "MobileNet SSD model downloaded successfully.")
            # Attempt immediate load if SSD selected
            if self.detection_backend.get() == 'SSD':
                self.dnn_loaded = False
                self.load_ssd_model()
        except Exception as e:
            self.update_status("Download failed")
            messagebox.showerror("Download Failed", f"Automatic download failed: {e}\nOpening browser...")
            self.open_model_download()

    def load_ssd_model(self):
        """Load MobileNet SSD model if available, else mark as not loaded."""
        if self.dnn_loaded:
            return
        prototxt = os.path.join(os.getcwd(), 'MobileNetSSD_deploy.prototxt')
        caffemodel = os.path.join(os.getcwd(), 'MobileNetSSD_deploy.caffemodel')
        if not os.path.exists(prototxt) or not os.path.exists(caffemodel):
            self.dnn_loaded = False
            return
        try:
            self.dnn_net = cv2.dnn.readNetFromCaffe(prototxt, caffemodel)
            # Prefer OpenCL if available for speed
            try:
                self.dnn_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_DEFAULT)
                self.dnn_net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
            except Exception:
                pass
            self.dnn_loaded = True
        except Exception as e:
            print(f"Failed to load SSD model: {e}")
            self.dnn_loaded = False

    def run_ssd(self, frame, conf_threshold):
        """Run SSD detection on frame and return list of (x,y,w,h) for persons only."""
        people = []
        try:
            blob = cv2.dnn.blobFromImage(frame, 0.007843, (300, 300), 127.5, swapRB=True, crop=False)
            self.dnn_net.setInput(blob)
            detections = self.dnn_net.forward()
            (h, w) = frame.shape[:2]
            # Class id for person in MobileNet SSD (VOC) is 15
            for i in range(detections.shape[2]):
                confidence = detections[0, 0, i, 2]
                if confidence < conf_threshold:
                    continue
                class_id = int(detections[0, 0, i, 1])
                if class_id != 15:
                    continue
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (x1, y1, x2, y2) = box.astype("int")
                x1 = max(0, x1); y1 = max(0, y1)
                x2 = min(w-1, x2); y2 = min(h-1, y2)
                bw = x2 - x1
                bh = y2 - y1
                if bw > 10 and bh > 20:
                    people.append((x1, y1, bw, bh))
        except Exception as e:
            # On error fallback silently
            # print(f"SSD error: {e}")
            pass
        return people

    def load_yolo_model(self):
        """Load YOLO model using ultralytics package (lazy)."""
        model_name = self.yolo_model_name.get()
        if self.yolo_loaded:
            return
        try:
            from ultralytics import YOLO  # type: ignore
        except ImportError as e:
            self.yolo_import_error = str(e)
            self.yolo_loaded = False
            # Notify user once
            try:
                messagebox.showwarning(
                    "YOLO Not Installed",
                    "Ultralytics YOLO not installed. Run: pip install ultralytics"
                )
            except Exception:
                pass
            return
        try:
            self.update_status(f"Loading YOLO model {model_name} ...")
            self.yolo_model = YOLO(model_name)
            self.yolo_loaded = True
            self.yolo_current_name = model_name
            self.yolo_import_error = None
            self.update_status(f"YOLO model {model_name} loaded")
        except Exception as e:
            self.yolo_loaded = False
            self.yolo_import_error = str(e)
            self.update_status("YOLO load error")
            try:
                messagebox.showerror("YOLO Load Error", f"Failed to load YOLO model: {e}")
            except Exception:
                pass

    def run_yolo(self, frame, conf_threshold):
        """Run YOLO inference and extract person boxes."""
        people = []
        if not self.yolo_loaded or self.yolo_model is None:
            return people
        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.yolo_model.predict(rgb, verbose=False, imgsz=640)
            if not results:
                return people
            res = results[0]
            if hasattr(res, 'boxes') and res.boxes is not None:
                for b in res.boxes:
                    try:
                        cls = int(b.cls[0]) if b.cls is not None else -1
                        conf = float(b.conf[0]) if b.conf is not None else 0.0
                        if cls != 0 or conf < conf_threshold:
                            continue
                        x1, y1, x2, y2 = b.xyxy[0].tolist()
                        x1 = int(max(0, x1)); y1 = int(max(0, y1))
                        x2 = int(min(frame.shape[1]-1, x2)); y2 = int(min(frame.shape[0]-1, y2))
                        w = x2 - x1; h = y2 - y1
                        if w > 10 and h > 20:
                            people.append((x1, y1, w, h))
                    except Exception:
                        continue
        except Exception:
            pass
        return people
    
    def on_closing(self):
        """Handle window closing"""
        if self.tracking:
            self.stop_tracking()
        self.window.destroy()


# Standalone person detector for testing without robot
class SimplePersonDetector:
    """Simplified person detector using HOG for testing"""
    def __init__(self):
        self.hog = cv2.HOGDescriptor()
        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    
    def detect(self, frame):
        """Detect people in frame"""
        # Detect people
        (rects, weights) = self.hog.detectMultiScale(
            frame,
            winStride=(8, 8),
            padding=(8, 8),
            scale=1.05
        )
        
        people = []
        for (x, y, w, h) in rects:
            people.append((x, y, w, h))
        
        return people


def test_gui_without_camera():
    """Test GUI with simulated video"""
    root = tk.Tk()
    
    # Create a simple test video
    class SimulatedCamera:
        def __init__(self):
            self.frame_count = 0
            self.person_x = 100
            self.direction = 1
        
        def read(self):
            # Create blank frame
            frame = np.ones((480, 640, 3), dtype=np.uint8) * 255
            
            # Draw simulated person (rectangle)
            person_width = 80
            person_height = 200
            
            # Move person back and forth
            self.person_x += self.direction * 5
            if self.person_x > 500 or self.person_x < 50:
                self.direction *= -1
            
            # Draw person
            cv2.rectangle(
                frame,
                (self.person_x, 200),
                (self.person_x + person_width, 200 + person_height),
                (0, 0, 255),
                -1
            )
            
            # Draw head
            cv2.circle(
                frame,
                (self.person_x + person_width // 2, 180),
                30,
                (0, 0, 255),
                -1
            )
            
            self.frame_count += 1
            return True, frame
        
        def isOpened(self):
            return True
        
        def release(self):
            pass
    
    # Monkey patch cv2.VideoCapture for testing
    original_VideoCapture = cv2.VideoCapture
    
    def mock_VideoCapture(source):
        if source == 0:  # Webcam
            return SimulatedCamera()
        else:
            return original_VideoCapture(source)
    
    cv2.VideoCapture = mock_VideoCapture
    
    # Create and run GUI
    app = PersonTrackerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


# Main execution
if __name__ == "__main__":
    print("Person Tracking Robot GUI")
    print("=" * 50)
    print("1. Run GUI with real camera")
    print("2. Run GUI with simulated video (no camera needed)")
    print("3. Run simple test")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == '1':
        # Run with real camera
        root = tk.Tk()
        app = PersonTrackerGUI(root)
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        # Auto-start tracking when using real camera
        try:
            app.start_tracking()
        except Exception as e:
            print(f"Failed to start tracking automatically: {e}")
        root.mainloop()
        
    elif choice == '2':
        # Run with simulated video
        test_gui_without_camera()
        
    elif choice == '3':
        # Simple test
        print("\nTesting basic functionality...")
        
        # Test OpenCV
        try:
            import cv2
            print(f"✓ OpenCV version: {cv2.__version__}")
        except:
            print("❌ OpenCV not installed")
        
        # Test camera
        try:
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                print("✓ Camera accessible")
                cap.release()
            else:
                print("❌ No camera found")
        except:
            print("❌ Camera test failed")
        
        # Test GUI
        try:
            root = tk.Tk()
            root.withdraw()
            print("✓ Tkinter working")
            root.destroy()
        except:
            print("❌ Tkinter not working")