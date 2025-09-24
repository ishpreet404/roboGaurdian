#!/usr/bin/env python3
"""
🔧 Robot Command Debug Tool
===========================

Tests the command flow step by step:
1. Windows → Pi HTTP API
2. Pi → ESP32 UART
3. ESP32 response

Usage: python debug_robot_commands.py
"""

import requests
import json
import time
import sys

class RobotDebugger:
    def __init__(self):
        # Update this with your Pi's IP
        self.PI_IP = "192.168.1.100"  # ⚠️ CHANGE THIS TO YOUR PI'S IP
        self.PI_PORT = 5000
        self.BASE_URL = f"http://{self.PI_IP}:{self.PI_PORT}"
        
    def test_connection(self):
        """Test basic connection to Pi"""
        print("🔗 Testing Pi connection...")
        try:
            response = requests.get(f"{self.BASE_URL}/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Pi server: {data.get('status', 'unknown')}")
                print(f"   📡 UART: {data.get('uart_status', 'unknown')}")
                print(f"   📹 Camera: {data.get('camera_status', 'unknown')}")
                print(f"   ⚡ Baud: {data.get('baud_rate', 'unknown')}")
                return True
            else:
                print(f"   ❌ Pi server error: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Connection failed: {e}")
            print(f"   💡 Make sure Pi is running at {self.BASE_URL}")
            return False
            
    def send_test_command(self, command):
        """Send single test command"""
        print(f"\n📤 Testing command: {command}")
        try:
            url = f"{self.BASE_URL}/move"
            data = {"direction": command}
            
            start_time = time.time()
            response = requests.post(url, json=data, timeout=5)
            response_time = (time.time() - start_time) * 1000
            
            print(f"   ⏱️ Response time: {response_time:.1f}ms")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Status: {result.get('status')}")
                print(f"   📡 UART: {result.get('uart_status')}")
                print(f"   💬 Message: {result.get('message')}")
                return True
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   💬 Error: {error_data.get('message', 'Unknown error')}")
                except:
                    print(f"   💬 Raw error: {response.text}")
                return False
                
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
            return False
            
    def interactive_test(self):
        """Interactive command testing"""
        print("\n🎮 Interactive Command Test")
        print("Commands: F=Forward, B=Back, L=Left, R=Right, S=Stop")
        print("Type 'quit' to exit")
        
        while True:
            try:
                cmd = input("\nEnter command (F/B/L/R/S): ").upper().strip()
                
                if cmd == 'QUIT':
                    break
                elif cmd in ['F', 'B', 'L', 'R', 'S']:
                    self.send_test_command(cmd)
                    time.sleep(0.5)  # Small delay between commands
                else:
                    print("❌ Invalid command. Use F, B, L, R, or S")
                    
            except KeyboardInterrupt:
                print("\n👋 Exiting...")
                break
                
    def automated_test(self):
        """Run automated command sequence"""
        print("\n🤖 Automated Test Sequence")
        commands = ['S', 'F', 'S', 'B', 'S', 'L', 'S', 'R', 'S']
        
        for cmd in commands:
            self.send_test_command(cmd)
            time.sleep(2)  # 2 second delay between commands
            
        print("\n✅ Automated test complete!")
        
    def run(self):
        """Main debug session"""
        print("🔧 Robot Command Debug Tool")
        print("=" * 40)
        print(f"Target Pi: {self.BASE_URL}")
        
        # Test connection first
        if not self.test_connection():
            print("\n❌ Cannot connect to Pi server!")
            print("💡 Make sure:")
            print("   1. Pi is powered on and connected to network")
            print("   2. Pi server is running: python3 pi_camera_server.py")
            print(f"   3. Pi IP address is correct: {self.PI_IP}")
            print("   4. No firewall blocking port 5000")
            return
            
        print("\n🎯 Connection successful! Choose test mode:")
        print("1. Interactive testing (manual commands)")
        print("2. Automated sequence")
        print("3. Single command test")
        
        try:
            choice = input("\nEnter choice (1/2/3): ").strip()
            
            if choice == '1':
                self.interactive_test()
            elif choice == '2':
                self.automated_test()
            elif choice == '3':
                cmd = input("Enter command (F/B/L/R/S): ").upper().strip()
                if cmd in ['F', 'B', 'L', 'R', 'S']:
                    self.send_test_command(cmd)
                else:
                    print("❌ Invalid command")
            else:
                print("❌ Invalid choice")
                
        except KeyboardInterrupt:
            print("\n👋 Debug session ended!")

def main():
    # Check if IP address provided as argument
    debugger = RobotDebugger()
    
    if len(sys.argv) > 1:
        debugger.PI_IP = sys.argv[1]
        debugger.BASE_URL = f"http://{debugger.PI_IP}:{debugger.PI_PORT}"
        print(f"🎯 Using Pi IP: {debugger.PI_IP}")
    
    debugger.run()

if __name__ == "__main__":
    main()