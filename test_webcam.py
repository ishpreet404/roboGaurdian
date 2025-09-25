#!/usr/bin/env python3
"""
Simple webcam test to diagnose camera issues
"""

import cv2
import sys

def test_webcam():
    print("🎥 Testing webcam availability...")
    
    # Test different backends
    backends = [
        (cv2.CAP_DSHOW, "DirectShow"),
        (cv2.CAP_MSMF, "Microsoft Media Foundation"),  
        (cv2.CAP_ANY, "Any available")
    ]
    
    for camera_index in range(3):
        print(f"\n📷 Testing camera index {camera_index}:")
        
        for backend_id, backend_name in backends:
            try:
                print(f"  Trying {backend_name}...")
                cap = cv2.VideoCapture(camera_index, backend_id)
                
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        h, w, c = frame.shape
                        print(f"    ✅ SUCCESS! Resolution: {w}x{h}")
                        cap.release()
                        return camera_index, backend_id, backend_name
                    else:
                        print(f"    ❌ Opened but no frame")
                else:
                    print(f"    ❌ Failed to open")
                    
                cap.release()
                    
            except Exception as e:
                print(f"    ❌ Error: {e}")
                
    print("\n❌ No working camera found")
    return None, None, None

def test_camera_with_display(camera_index, backend_id):
    """Test camera with live display"""
    print(f"\n🔴 Testing live camera {camera_index} with backend {backend_id}")
    print("Press 'q' to quit")
    
    cap = cv2.VideoCapture(camera_index, backend_id)
    
    if not cap.isOpened():
        print("❌ Could not open camera")
        return False
        
    # Set properties
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            print("❌ Failed to read frame")
            break
            
        frame_count += 1
        
        # Add frame counter
        cv2.putText(frame, f"Frame: {frame_count}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        cv2.imshow('Webcam Test', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print(f"✅ Camera test completed. Frames captured: {frame_count}")
    return True

if __name__ == "__main__":
    print("🤖 Robot Guardian - Webcam Diagnostic Tool")
    print("=" * 50)
    
    # Test for available cameras
    camera_index, backend_id, backend_name = test_webcam()
    
    if camera_index is not None:
        print(f"\n✅ Best camera found:")
        print(f"   Index: {camera_index}")
        print(f"   Backend: {backend_name}")
        
        # Ask user if they want to test with display
        try:
            response = input("\nTest with live display? (y/n): ").lower()
            if response == 'y':
                test_camera_with_display(camera_index, backend_id)
        except KeyboardInterrupt:
            print("\nTest cancelled by user")
    else:
        print("\n💡 Troubleshooting tips:")
        print("1. Make sure camera is connected")
        print("2. Check Windows Privacy Settings > Camera")
        print("3. Close other applications using camera")
        print("4. Try unplugging and reconnecting USB camera")
        
    print("\n🏁 Diagnostic complete")