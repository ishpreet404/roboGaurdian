#!/usr/bin/env python3
"""
🔍 Quick Camera Diagnostic for Pi Robot Server
=============================================

This script tests camera functionality and suggests fixes.
Run this before starting the pi_camera_server.py

Usage: python3 camera_test.py

Author: Robot Guardian System  
Date: September 2025
"""

import cv2
import os
import sys
import time
import subprocess

def run_command(cmd):
    """Run shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_camera_permissions():
    """Check camera permissions and device files"""
    print("🔐 Checking camera permissions...")
    
    # Check if video devices exist
    video_devices = []
    for i in range(5):
        device = f"/dev/video{i}"
        if os.path.exists(device):
            video_devices.append(device)
    
    if video_devices:
        print(f"✅ Found video devices: {', '.join(video_devices)}")
        
        # Check permissions
        for device in video_devices[:2]:  # Check first 2 devices
            try:
                stat = os.stat(device)
                print(f"   {device}: permissions {oct(stat.st_mode)[-3:]}")
            except Exception as e:
                print(f"   {device}: permission error - {e}")
    else:
        print("❌ No video devices found (/dev/video*)")
        print("   Fix: sudo modprobe bcm2835-v4l2")
        return False
    
    # Check user groups
    success, output, error = run_command("groups")
    if success and "video" in output:
        print("✅ User is in 'video' group")
    else:
        print("❌ User not in 'video' group")
        print("   Fix: sudo usermod -a -G video $USER (then logout/login)")
        
    return True

def test_camera_backends():
    """Test camera with different OpenCV backends"""
    print("\n📹 Testing camera backends...")
    
    backends = [
        (cv2.CAP_V4L2, "V4L2 (Recommended for Pi)"),
        (cv2.CAP_GSTREAMER, "GStreamer"),  
        (cv2.CAP_ANY, "Auto-detect")
    ]
    
    working_cameras = []
    
    for backend_id, backend_name in backends:
        print(f"\n🔍 Testing {backend_name}...")
        
        for camera_id in [0, 1, -1]:
            try:
                # Try to open camera
                cap = cv2.VideoCapture(camera_id, backend_id)
                
                if cap.isOpened():
                    print(f"   📷 Camera {camera_id}: Opened successfully")
                    
                    # Test frame capture
                    frame_count = 0
                    for attempt in range(5):
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            frame_count += 1
                            if attempt == 0:  # Show info for first successful frame
                                height, width = frame.shape[:2]
                                print(f"      Frame size: {width}x{height}")
                        time.sleep(0.1)
                    
                    if frame_count >= 3:
                        print(f"   ✅ Camera {camera_id}: {frame_count}/5 frames captured successfully")
                        working_cameras.append((camera_id, backend_id, backend_name))
                    else:
                        print(f"   ⚠️  Camera {camera_id}: Only {frame_count}/5 frames captured")
                        
                    # Get camera properties
                    try:
                        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        print(f"      Properties: {width}x{height} @ {fps:.1f}fps")
                    except:
                        pass
                        
                else:
                    print(f"   ❌ Camera {camera_id}: Failed to open")
                
                cap.release()
                
            except Exception as e:
                print(f"   ❌ Camera {camera_id}: Exception - {e}")
    
    return working_cameras

def test_optimized_settings():
    """Test camera with robot server optimized settings"""
    print("\n⚙️ Testing with robot server settings...")
    
    # Settings from pi_camera_server.py
    target_width = 320
    target_height = 240
    target_fps = 21
    
    try:
        # Try V4L2 backend first (best for Pi)
        cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        
        if not cap.isOpened():
            # Fallback to auto-detect
            cap = cv2.VideoCapture(0)
            
        if cap.isOpened():
            # Apply robot server settings
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, target_width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, target_height)
            cap.set(cv2.CAP_PROP_FPS, target_fps)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Test multiple frames like robot server does
            success_count = 0
            for i in range(10):
                ret, frame = cap.read()
                if ret:
                    success_count += 1
                time.sleep(0.05)  # 20fps test
            
            if success_count >= 7:
                print(f"✅ Robot server simulation: {success_count}/10 frames captured")
                
                # Get actual settings
                actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                actual_fps = cap.get(cv2.CAP_PROP_FPS)
                
                print(f"   Target: {target_width}x{target_height} @ {target_fps}fps")
                print(f"   Actual: {actual_width}x{actual_height} @ {actual_fps:.1f}fps")
                
                return True
            else:
                print(f"❌ Robot server simulation: Only {success_count}/10 frames captured")
                print("   This may cause 'Camera test failed' errors")
                return False
                
        else:
            print("❌ Cannot open camera for robot server test")
            return False
            
    except Exception as e:
        print(f"❌ Robot server test failed: {e}")
        return False
    finally:
        try:
            cap.release()
        except:
            pass

def check_camera_interface():
    """Check Pi camera interface status"""
    print("\n🔧 Checking Pi camera interface...")
    
    success, output, error = run_command("vcgencmd get_camera")
    if success:
        if "detected=1" in output:
            print("✅ Pi Camera detected by system")
        else:
            print("❌ Pi Camera not detected")
            
        if "supported=1" in output:
            print("✅ Pi Camera supported by system")
        else:
            print("❌ Pi Camera not supported - enable in raspi-config")
            
    # Check raspi-config camera setting
    success, output, error = run_command("raspi-config nonint get_camera")
    if success:
        if output.strip() == "0":
            print("✅ Camera interface enabled in raspi-config")
        else:
            print("❌ Camera interface disabled")
            print("   Fix: sudo raspi-config → Interface Options → Camera")

def provide_solutions(working_cameras):
    """Provide solutions based on test results"""
    print("\n" + "="*50)
    print("📋 DIAGNOSTIC RESULTS & SOLUTIONS")
    print("="*50)
    
    if working_cameras:
        print("✅ GOOD NEWS: Camera is working!")
        print("\nWorking configurations:")
        for cam_id, backend_id, backend_name in working_cameras:
            print(f"   • Camera {cam_id} with {backend_name}")
        
        print("\n🔧 If pi_camera_server.py still fails:")
        print("1. Make sure no other programs are using the camera")
        print("2. Restart the Pi: sudo reboot")
        print("3. Run: sudo systemctl stop motion (if motion is installed)")
        print("4. Check camera cable connection")
        
    else:
        print("❌ CAMERA NOT WORKING - Try these fixes:")
        print("\n1. 🔌 Hardware fixes:")
        print("   • Check camera cable connection")
        print("   • Try a different USB port (for USB cameras)")
        print("   • Test with a different camera")
        
        print("\n2. 🔧 Software fixes:")
        print("   • Enable camera: sudo raspi-config → Interface Options → Camera")
        print("   • Add to video group: sudo usermod -a -G video $USER")
        print("   • Load camera module: sudo modprobe bcm2835-v4l2")
        print("   • Restart Pi: sudo reboot")
        
        print("\n3. 📦 Package fixes:")
        print("   • Update system: sudo apt update && sudo apt upgrade")
        print("   • Install camera tools: sudo apt install v4l-utils")
        print("   • Reinstall OpenCV: pip3 install --upgrade opencv-python")

def main():
    """Main diagnostic routine"""
    print("🔍 Robot Guardian - Camera Diagnostic Tool")
    print("=" * 50)
    print()
    
    # Check basic system info
    print(f"🖥️  Running on: {os.uname().sysname} {os.uname().machine}")
    print(f"🐍 Python version: {sys.version.split()[0]}")
    print(f"📹 OpenCV version: {cv2.__version__}")
    print()
    
    # Run diagnostic steps
    check_camera_permissions()
    check_camera_interface()
    working_cameras = test_camera_backends()
    robot_server_compatible = test_optimized_settings()
    
    # Provide solutions
    provide_solutions(working_cameras)
    
    print(f"\n🎯 ROBOT SERVER COMPATIBILITY:")
    if robot_server_compatible:
        print("✅ Camera should work with pi_camera_server.py")
    else:
        print("❌ Camera may fail with pi_camera_server.py")
        print("   Apply the suggested fixes above")
    
    print(f"\n💡 Quick test command:")
    print(f"   python3 -c \"import cv2; cap=cv2.VideoCapture(0); print('✅ Works' if cap.read()[0] else '❌ Failed')\"")
    
    print(f"\n🚀 Next steps:")
    print(f"1. Apply any suggested fixes")
    print(f"2. Reboot Pi if needed: sudo reboot")
    print(f"3. Test robot server: python3 pi_camera_server.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Diagnostic cancelled by user")
    except Exception as e:
        print(f"\n❌ Diagnostic error: {e}")
        print("This may indicate a serious system issue.")