#!/usr/bin/env python3
"""
🔍 Camera Diagnostic Tool for Pi Robot
=====================================

This script helps diagnose camera connection issues on Raspberry Pi.
Run this before starting the main server to identify problems.

Usage: python3 camera_diagnostic.py
"""

import cv2
import os
import subprocess
import sys
import time

def print_header():
    print("🔍 Pi Camera Diagnostic Tool")
    print("=" * 40)
    print()

def check_system_info():
    print("📋 System Information:")
    try:
        # Check if we're on a Pi
        with open('/proc/device-tree/model', 'r') as f:
            model = f.read().strip('\x00')
            print(f"   Device: {model}")
    except:
        print("   Device: Not a Raspberry Pi or model unknown")
    
    try:
        # Check OS
        result = subprocess.run(['uname', '-a'], capture_output=True, text=True)
        print(f"   OS: {result.stdout.strip()}")
    except:
        print("   OS: Unknown")
    print()

def check_camera_permissions():
    print("🔐 Camera Permissions:")
    
    # Check video group membership
    try:
        result = subprocess.run(['groups'], capture_output=True, text=True)
        groups = result.stdout.strip()
        if 'video' in groups:
            print("   ✅ User is in 'video' group")
        else:
            print("   ❌ User NOT in 'video' group")
            print("      Fix: sudo usermod -a -G video $USER")
            print("      Then logout and login again")
    except:
        print("   ⚠️ Cannot check video group membership")
    
    # Check /dev/video* devices
    video_devices = []
    try:
        for device in os.listdir('/dev'):
            if device.startswith('video'):
                device_path = f"/dev/{device}"
                if os.access(device_path, os.R_OK | os.W_OK):
                    video_devices.append(f"{device_path} (accessible)")
                else:
                    video_devices.append(f"{device_path} (permission denied)")
        
        if video_devices:
            print("   📹 Video devices found:")
            for device in video_devices:
                print(f"      {device}")
        else:
            print("   ❌ No /dev/video* devices found")
    except:
        print("   ⚠️ Cannot scan /dev/video* devices")
    print()

def check_pi_camera():
    print("📸 Pi Camera (CSI) Check:")
    
    try:
        # Check if Pi camera is detected
        result = subprocess.run(['vcgencmd', 'get_camera'], capture_output=True, text=True)
        if result.returncode == 0:
            output = result.stdout.strip()
            print(f"   Camera status: {output}")
            
            if "detected=1" in output:
                print("   ✅ Pi Camera detected by hardware")
            else:
                print("   ❌ Pi Camera NOT detected by hardware")
                print("      - Check ribbon cable connection")
                print("      - Enable camera: sudo raspi-config → Interface Options → Camera")
        else:
            print("   ⚠️ vcgencmd not available (not on Pi?)")
            
    except FileNotFoundError:
        print("   ⚠️ vcgencmd not found (not on Raspberry Pi)")
    except Exception as e:
        print(f"   ⚠️ Error checking Pi camera: {e}")
    
    # Try raspistill test
    try:
        print("   Testing Pi camera with raspistill...")
        result = subprocess.run(['raspistill', '-t', '1', '-o', '/tmp/camera_test.jpg'], 
                               capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("   ✅ Pi camera test successful (image saved to /tmp/camera_test.jpg)")
        else:
            print("   ❌ Pi camera test failed")
            print(f"      Error: {result.stderr}")
    except FileNotFoundError:
        print("   ⚠️ raspistill not found")
    except subprocess.TimeoutExpired:
        print("   ❌ raspistill test timed out")
    except Exception as e:
        print(f"   ⚠️ Error testing raspistill: {e}")
    print()

def check_usb_cameras():
    print("🔌 USB Camera Check:")
    
    try:
        # List USB devices
        result = subprocess.run(['lsusb'], capture_output=True, text=True)
        if result.returncode == 0:
            usb_devices = result.stdout.strip().split('\n')
            camera_devices = [d for d in usb_devices if any(keyword in d.lower() 
                             for keyword in ['camera', 'webcam', 'video', 'uvc'])]
            
            if camera_devices:
                print("   📹 USB camera devices found:")
                for device in camera_devices:
                    print(f"      {device}")
            else:
                print("   ⚠️ No USB camera devices detected")
                print("      All USB devices:")
                for device in usb_devices:
                    print(f"      {device}")
    except Exception as e:
        print(f"   ⚠️ Error checking USB devices: {e}")
    print()

def test_opencv_cameras():
    print("🐍 OpenCV Camera Test:")
    
    working_cameras = []
    
    # Test different camera indices
    for i in range(5):
        try:
            print(f"   Testing camera index {i}...")
            cap = cv2.VideoCapture(i)
            
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    height, width = frame.shape[:2]
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    print(f"   ✅ Camera {i}: {width}x{height}, FPS: {fps}")
                    working_cameras.append(i)
                else:
                    print(f"   ❌ Camera {i}: Opens but cannot read frames")
            else:
                print(f"   ❌ Camera {i}: Cannot open")
                
            cap.release()
            
        except Exception as e:
            print(f"   ❌ Camera {i}: Error - {e}")
    
    # Test device paths
    for device_path in ['/dev/video0', '/dev/video1']:
        if os.path.exists(device_path):
            try:
                print(f"   Testing {device_path}...")
                cap = cv2.VideoCapture(device_path)
                
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        height, width = frame.shape[:2]
                        print(f"   ✅ {device_path}: {width}x{height}")
                        working_cameras.append(device_path)
                    else:
                        print(f"   ❌ {device_path}: Opens but cannot read frames")
                else:
                    print(f"   ❌ {device_path}: Cannot open")
                    
                cap.release()
                
            except Exception as e:
                print(f"   ❌ {device_path}: Error - {e}")
    
    if working_cameras:
        print(f"\n   ✅ Working cameras found: {working_cameras}")
        return working_cameras
    else:
        print("\n   ❌ No working cameras found!")
        return []

def test_high_resolution():
    print("\n🎯 High Resolution Test (1080p):")
    
    for camera_id in [0, 1, '/dev/video0']:
        try:
            print(f"   Testing 1080p on camera {camera_id}...")
            cap = cv2.VideoCapture(camera_id)
            
            if cap.isOpened():
                # Try to set 1080p
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
                cap.set(cv2.CAP_PROP_FPS, 30)
                
                # Check what we actually got
                actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                actual_fps = int(cap.get(cv2.CAP_PROP_FPS))
                
                print(f"      Requested: 1920x1080@30fps")
                print(f"      Actual: {actual_w}x{actual_h}@{actual_fps}fps")
                
                # Test capture
                ret, frame = cap.read()
                if ret and frame is not None:
                    h, w = frame.shape[:2]
                    print(f"      Captured frame: {w}x{h}")
                    if w >= 1280 and h >= 720:
                        print(f"   ✅ High resolution supported")
                    else:
                        print(f"   ⚠️ Limited to lower resolution")
                else:
                    print(f"   ❌ Cannot capture frames")
                    
            cap.release()
            
        except Exception as e:
            print(f"   ❌ Error testing camera {camera_id}: {e}")

def main():
    print_header()
    check_system_info()
    check_camera_permissions()
    check_pi_camera()
    check_usb_cameras()
    working_cameras = test_opencv_cameras()
    
    if working_cameras:
        test_high_resolution()
        print("\n✅ DIAGNOSIS COMPLETE")
        print(f"💡 Recommendation: Use camera {working_cameras[0]} in your Pi server")
    else:
        print("\n❌ DIAGNOSIS COMPLETE - NO WORKING CAMERAS FOUND")
        print("\n🔧 Next steps:")
        print("1. Check camera connection (USB or ribbon cable)")
        print("2. Enable camera interface: sudo raspi-config")
        print("3. Add user to video group: sudo usermod -a -G video $USER")
        print("4. Reboot: sudo reboot")
        print("5. Try a different camera")

if __name__ == "__main__":
    main()