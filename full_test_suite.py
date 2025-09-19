import cv2
import numpy as np
import time
import os
from datetime import datetime

class PersonTrackingTester:
    def __init__(self):
        self.test_results = []
        
    def test_camera_access(self):
        """Test if camera can be accessed"""
        print("\n🎥 Testing camera access...")
        cap = cv2.VideoCapture(0)
        
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                print("✓ Camera access successful")
                print(f"  Resolution: {frame.shape[1]}x{frame.shape[0]}")
                return True
            else:
                print("❌ Camera opened but couldn't read frame")
                return False
        else:
            print("❌ Cannot access camera")
            print("  Tip: Check if camera is connected and not used by another app")
            return False
    
    def test_model_loading(self):
        """Test if AI model loads correctly"""
        print("\n🤖 Testing model loading...")
        
        try:
            net = cv2.dnn.readNetFromCaffe(
                "MobileNetSSD_deploy.prototxt",
                "MobileNetSSD_deploy.caffemodel"
            )
            print("✓ Model loaded successfully")
            return True
        except Exception as e:
            print(f"❌ Model loading failed: {e}")
            return False
    
    def test_person_detection(self):
        """Test person detection on a sample image"""
        print("\n👤 Testing person detection...")
        
        # Create a simple test image with a person-like shape
        test_image = np.ones((480, 640, 3), dtype=np.uint8) * 255
        
        # Draw a simple person-like shape (rectangle for body)
        cv2.rectangle(test_image, (300, 200), (340, 350), (0, 0, 0), -1)
        cv2.circle(test_image, (320, 180), 20, (0, 0, 0), -1)  # Head
        
        try:
            net = cv2.dnn.readNetFromCaffe(
                "MobileNetSSD_deploy.prototxt",
                "MobileNetSSD_deploy.caffemodel"
            )
            
            blob = cv2.dnn.blobFromImage(test_image, 0.007843, (300, 300), 127.5)
            net.setInput(blob)
            detections = net.forward()
            
            print("✓ Detection algorithm runs successfully")
            return True
        except Exception as e:
            print(f"❌ Detection failed: {e}")
            return False
    
    def test_command_generation(self):
        """Test command generation logic"""
        print("\n🎮 Testing command generation...")
        
        test_cases = [
            {"person_x": 320, "person_area": 25000, "expected": "S", "desc": "Person centered, good distance"},
            {"person_x": 450, "person_area": 25000, "expected": "R", "desc": "Person to the right"},
            {"person_x": 190, "person_area": 25000, "expected": "L", "desc": "Person to the left"},
            {"person_x": 320, "person_area": 10000, "expected": "F", "desc": "Person far away"},
            {"person_x": 320, "person_area": 40000, "expected": "B", "desc": "Person too close"},
        ]
        
        frame_center_x = 320
        center_threshold = 80
        ideal_area = 25000
        
        all_passed = True
        for test in test_cases:
            x_offset = test["person_x"] - frame_center_x
            area = test["person_area"]
            
            # Simulate command logic
            if abs(x_offset) > center_threshold:
                command = 'R' if x_offset > 0 else 'L'
            elif area < ideal_area * 0.7:
                command = 'F'
            elif area > ideal_area * 1.3:
                command = 'B'
            else:
                command = 'S'
            
            if command == test["expected"]:
                print(f"✓ {test['desc']}: {command}")
            else:
                print(f"❌ {test['desc']}: Expected {test['expected']}, got {command}")
                all_passed = False
        
        return all_passed
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*50)
        print("🧪 PERSON TRACKING ROBOT - TEST SUITE")
        print("="*50)
        
        tests = [
            ("Camera Access", self.test_camera_access),
            ("Model Loading", self.test_model_loading),
            ("Person Detection", self.test_person_detection),
            ("Command Generation", self.test_command_generation)
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                passed = test_func()
                results.append((test_name, passed))
            except Exception as e:
                print(f"❌ {test_name} crashed: {e}")
                results.append((test_name, False))
        
        # Summary
        print("\n" + "="*50)
        print("📊 TEST SUMMARY")
        print("="*50)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"{test_name}: {status}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 All tests passed! Ready to track people!")
        else:
            print("\n⚠️  Some tests failed. Please fix issues before running main program.")
        
        return passed == total

# Quick setup script
def quick_setup():
    """Quick setup helper"""
    print("\n🚀 QUICK SETUP GUIDE")
    print("="*50)
    
    # Check Python version
    import sys
    print(f"Python version: {sys.version}")
    if sys.version_info < (3, 6):
        print("⚠️  Python 3.6+ recommended")
    
    # Check OpenCV
    try:
        import cv2
        print(f"✓ OpenCV installed: {cv2.__version__}")
    except:
        print("❌ OpenCV not installed")
        print("  Run: pip install opencv-python opencv-contrib-python")
    
    # Check model files
    files_needed = [
        ("MobileNetSSD_deploy.prototxt", "https://raw.githubusercontent.com/chuanqi305/MobileNet-SSD/master/deploy.prototxt"),
        ("MobileNetSSD_deploy.caffemodel", "https://drive.google.com/file/d/0B3gersZ2cHIxRm5PMWRoTkdHdHc/view")
    ]
    
    print("\nModel files:")
    for filename, url in files_needed:
        if os.path.exists(filename):
            size = os.path.getsize(filename) / 1024 / 1024
            print(f"✓ {filename} ({size:.1f} MB)")
        else:
            print(f"❌ {filename} - Download from: {url}")

if __name__ == "__main__":
    print("PERSON TRACKING ROBOT - PC TEST SETUP")
    print("="*50)
    print("1. Run quick setup check")
    print("2. Run test suite")
    print("3. Start tracking test (webcam)")
    print("4. Start tracking test (video file)")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == '1':
        quick_setup()
    elif choice == '2':
        tester = PersonTrackingTester()
        tester.run_all_tests()
    elif choice == '3':
        from test_person_tracker import PersonTrackerTest
        tracker = PersonTrackerTest(0)
        tracker.run_test()
    elif choice == '4':
        from test_person_tracker import PersonTrackerTest
        video_file = input("Enter video file path: ").strip()
        tracker = PersonTrackerTest(video_file)
        tracker.run_test()