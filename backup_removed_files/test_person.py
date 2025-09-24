import cv2
import numpy as np
import time
from collections import deque

class PersonTrackerTest:
    def __init__(self, video_source=0):
        """
        video_source: 0 for webcam, or path to video file
        """
        self.video_source = video_source
        
        # Check if model files exist
        if not self.check_model_files():
            return
        
        # Initialize MobileNet SSD
        self.net = cv2.dnn.readNetFromCaffe(
            "MobileNetSSD_deploy.prototxt",
            "MobileNetSSD_deploy.caffemodel"
        )
        
        # Tracking parameters
        self.frame_center_x = 320
        self.frame_center_y = 240
        self.center_threshold = 80
        self.min_person_area = 5000
        self.max_person_area = 100000
        self.ideal_person_area = 25000
        
        # Movement smoothing
        self.command_history = deque(maxlen=5)
        self.last_command = 'S'
        
        # Classes in MobileNet SSD
        self.CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
                       "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
                       "dog", "horse", "motorbike", "person", "pottedplant", "sheep",
                       "sofa", "train", "tvmonitor"]
    
    def check_model_files(self):
        """Check if required model files exist"""
        files_exist = True
        
        if not os.path.exists("MobileNetSSD_deploy.prototxt"):
            print("❌ Missing: MobileNetSSD_deploy.prototxt")
            files_exist = False
        else:
            print("✓ Found: MobileNetSSD_deploy.prototxt")
            
        if not os.path.exists("MobileNetSSD_deploy.caffemodel"):
            print("❌ Missing: MobileNetSSD_deploy.caffemodel")
            print("  Please download from: https://drive.google.com/file/d/0B3gersZ2cHIxRm5PMWRoTkdHdHc/view")
            files_exist = False
        else:
            print("✓ Found: MobileNetSSD_deploy.caffemodel")
            
        return files_exist
    
    def detect_people(self, frame):
        """Detect people in frame using MobileNet SSD"""
        height, width = frame.shape[:2]
        
        # Prepare image
        blob = cv2.dnn.blobFromImage(frame, 0.007843, (300, 300), 127.5)
        self.net.setInput(blob)
        detections = self.net.forward()
        
        people = []
        
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            class_id = int(detections[0, 0, i, 1])
            
            # Class 15 is person
            if class_id == 15 and confidence > 0.5:
                box = detections[0, 0, i, 3:7] * np.array([width, height, width, height])
                x, y, x2, y2 = box.astype("int")
                
                # Ensure valid bbox
                x = max(0, x)
                y = max(0, y)
                x2 = min(width, x2)
                y2 = min(height, y2)
                
                w = x2 - x
                h = y2 - y
                center_x = x + w // 2
                center_y = y + h // 2
                
                people.append({
                    'bbox': (x, y, w, h),
                    'confidence': confidence,
                    'center': (center_x, center_y),
                    'area': w * h
                })
        
        return people
    
    def select_target_person(self, people):
        """Select the most prominent person to track"""
        if not people:
            return None
        
        # Filter by size
        valid_people = [p for p in people if self.min_person_area < p['area'] < self.max_person_area]
        
        if not valid_people:
            # If no one in valid range, pick closest to ideal size
            valid_people = people
        
        # Sort by area (closest person)
        valid_people.sort(key=lambda p: p['area'], reverse=True)
        
        return valid_people[0]
    
    def calculate_movement_command(self, person):
        """Calculate movement command based on person position"""
        if not person:
            return 'S'
        
        center_x, _ = person['center']
        area = person['area']
        
        # Horizontal offset from center
        x_offset = center_x - self.frame_center_x
        
        command = 'S'
        
        # Priority: Centering > Distance
        if abs(x_offset) > self.center_threshold:
            command = 'R' if x_offset > 0 else 'L'
        elif area < self.ideal_person_area * 0.7:
            command = 'F'
        elif area > self.ideal_person_area * 1.3:
            command = 'B'
        
        return command
    
    def smooth_command(self, command):
        """Smooth commands to avoid jerky movement"""
        self.command_history.append(command)
        
        if len(self.command_history) >= 3:
            # Count occurrences
            command_counts = {}
            for cmd in self.command_history:
                command_counts[cmd] = command_counts.get(cmd, 0) + 1
            
            # Return most frequent
            return max(command_counts, key=command_counts.get)
        
        return command
    
    def draw_tracking_info(self, frame, person, command, fps):
        """Draw tracking visualization on frame"""
        height, width = frame.shape[:2]
        
        # Resize frame center based on actual frame size
        self.frame_center_x = width // 2
        self.frame_center_y = height // 2
        
        if person:
            x, y, w, h = person['bbox']
            center_x, center_y = person['center']
            
            # Color based on command
            color_map = {
                'F': (0, 255, 0),    # Green - Forward
                'B': (0, 165, 255),  # Orange - Backward
                'L': (255, 0, 0),    # Blue - Left
                'R': (255, 0, 255),  # Magenta - Right
                'S': (0, 255, 255)   # Yellow - Stop
            }
            color = color_map.get(command, (255, 255, 255))
            
            # Draw bounding box
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            
            # Draw center point
            cv2.circle(frame, (center_x, center_y), 5, color, -1)
            
            # Draw line from frame center to person center
            cv2.line(frame, (self.frame_center_x, self.frame_center_y),
                    (center_x, center_y), color, 1)
            
            # Person info
            info_text = f"Size: {person['area']:.0f} | Conf: {person['confidence']:.2f}"
            cv2.putText(frame, info_text, (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Draw center guidelines
        cv2.line(frame, (self.frame_center_x - self.center_threshold, 0),
                (self.frame_center_x - self.center_threshold, height), (255, 0, 0), 1)
        cv2.line(frame, (self.frame_center_x + self.center_threshold, 0),
                (self.frame_center_x + self.center_threshold, height), (255, 0, 0), 1)
        
        # Draw crosshair at center
        cv2.line(frame, (self.frame_center_x - 20, self.frame_center_y),
                (self.frame_center_x + 20, self.frame_center_y), (255, 255, 255), 1)
        cv2.line(frame, (self.frame_center_x, self.frame_center_y - 20),
                (self.frame_center_x, self.frame_center_y + 20), (255, 255, 255), 1)
        
        # Status panel
        cv2.rectangle(frame, (10, 10), (200, 100), (0, 0, 0), -1)
        cv2.rectangle(frame, (10, 10), (200, 100), (255, 255, 255), 1)
        
        status = "TRACKING" if person else "SEARCHING"
        color = (0, 255, 0) if person else (0, 0, 255)
        cv2.putText(frame, status, (20, 35),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        cv2.putText(frame, f"Command: {command}", (20, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        cv2.putText(frame, f"FPS: {fps:.1f}", (20, 85),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Command legend
        legend_y = height - 100
        cv2.putText(frame, "Commands:", (10, legend_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, "F=Forward B=Back", (10, legend_y + 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        cv2.putText(frame, "L=Left R=Right S=Stop", (10, legend_y + 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        return frame
    
    def run_test(self):
        """Run in test mode without robot connection"""
        print("\n=== Person Tracking Test Mode ===")
        print("This will analyze video and show what commands would be sent")
        print("Press 'q' to quit, 'p' to pause\n")
        
        # Open video source
        if isinstance(self.video_source, int):
            print("Opening webcam...")
            cap = cv2.VideoCapture(self.video_source)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        else:
            print(f"Opening video file: {self.video_source}")
            cap = cv2.VideoCapture(self.video_source)
        
        if not cap.isOpened():
            print("Failed to open video source!")
            return
        
        paused = False
        fps_time = time.time()
        fps = 0
        
        try:
            while True:
                if not paused:
                    ret, frame = cap.read()
                    if not ret:
                        if isinstance(self.video_source, str):
                            # Loop video file
                            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                            continue
                        else:
                            print("Failed to read frame")
                            break
                
                # Calculate FPS
                fps = 1 / (time.time() - fps_time) if time.time() - fps_time > 0 else 0
                fps_time = time.time()
                
                            # Detect people
                people = self.detect_people(frame)
                target_person = self.select_target_person(people)
                
                # Calculate command
                raw_command = self.calculate_movement_command(target_person)
                command = self.smooth_command(raw_command)
                
                # Visualize
                frame = self.draw_tracking_info(frame, target_person, command, fps)
                
                # Show what would be sent to robot
                if command != self.last_command:
                    print(f"[{time.strftime('%H:%M:%S')}] Command: {command} -> ", end="")
                    if command == 'F':
                        print("Moving FORWARD")
                    elif command == 'B':
                        print("Moving BACKWARD")
                    elif command == 'L':
                        print("Turning LEFT")
                    elif command == 'R':
                        print("Turning RIGHT")
                    elif command == 'S':
                        print("STOP")
                    self.last_command = command
                
                cv2.imshow('Person Tracking Test', frame)
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('p'):
                    paused = not paused
                    print("PAUSED" if paused else "RESUMED")
                
        finally:
            cap.release()
            cv2.destroyAllWindows()
            print("\nTest ended")

# Simulated robot connection for testing
class MockRobotConnection:
    """Simulate robot connection for testing without hardware"""
    def __init__(self):
        self.commands_sent = []
        self.start_time = time.time()
    
    def send_command(self, command):
        timestamp = time.time() - self.start_time
        self.commands_sent.append((timestamp, command))
        return True
    
    def get_command_history(self):
        return self.commands_sent

# Main test script
if __name__ == "__main__":
    import os
    
    print("Person Tracking Robot - PC Test Setup")
    print("=" * 40)
    
    # Check for model files
    tracker = PersonTrackerTest()
    
    if not os.path.exists("MobileNetSSD_deploy.caffemodel"):
        print("\n❌ Model file missing!")
        print("Please download the caffemodel file first.")
        exit(1)
    
    print("\n✓ All model files found!")
    print("\nSelect video source:")
    print("1. Webcam")
    print("2. Video file")
    print("3. Sample video (download)")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == '1':
        # Use webcam
        tracker = PersonTrackerTest(0)
        tracker.run_test()
        
    elif choice == '2':
        # Use video file
        video_path = input("Enter video file path: ").strip()
        if os.path.exists(video_path):
            tracker = PersonTrackerTest(video_path)
            tracker.run_test()
        else:
            print("Video file not found!")
            
    elif choice == '3':
        # Download sample video
        print("\nDownloading sample video...")
        import urllib.request
        
        sample_url = "https://github.com/intel-iot-devkit/sample-videos/raw/master/people-detection.mp4"
        sample_file = "sample_people.mp4"
        
        if not os.path.exists(sample_file):
            urllib.request.urlretrieve(sample_url, sample_file)
            print("✓ Downloaded sample video")
        else:
            print("✓ Sample video already exists")
            
        tracker = PersonTrackerTest(sample_file)
        tracker.run_test()