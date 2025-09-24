#!/usr/bin/env python3
"""
🔧 Quick ESP32 Robot Test Tool
============================

Tests ESP32 communication via Pi server
- Direct command testing
- UART status checking  
- ESP32 response monitoring

Usage: python test_esp32.py
"""

import requests
import time
import sys

class ESP32Tester:
    def __init__(self, pi_ip="192.168.1.2", pi_port=5000):
        self.pi_url = f"http://{pi_ip}:{pi_port}"
        self.test_commands = ['S', 'F', 'S', 'B', 'S', 'L', 'S', 'R', 'S']
        
    def test_connection(self):
        """Test Pi server connection"""
        print(f"🔍 Testing Pi connection: {self.pi_url}")
        try:
            response = requests.get(f"{self.pi_url}/status", timeout=3)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Pi Status: {data.get('status')}")
                print(f"📡 UART: {data.get('uart_status')}")
                print(f"📹 Camera: {data.get('camera_status')}")
                print(f"⚡ Baud: {data.get('baud_rate')}")
                return data.get('uart_status') == 'connected'
            else:
                print(f"❌ Pi server error: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
            
    def send_command(self, cmd):
        """Send single command to ESP32"""
        print(f"\n📤 Sending: {cmd}")
        try:
            response = requests.post(
                f"{self.pi_url}/move", 
                json={"direction": cmd}, 
                timeout=3
            )
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status')
                uart_status = result.get('uart_status')
                message = result.get('message', '')
                
                if status == 'success':
                    print(f"✅ Pi: {message}")
                    print(f"📡 UART: {uart_status}")
                else:
                    print(f"❌ Pi: {message}")
                    
            else:
                print(f"❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            
    def run_test_sequence(self):
        """Run automated test sequence"""
        print("🤖 ESP32 Robot Test Sequence")
        print("=" * 40)
        
        if not self.test_connection():
            print("\n❌ Cannot connect to Pi server!")
            print("Make sure:")
            print("1. Pi is running pi_camera_server.py")
            print("2. ESP32 is connected via GPIO14/15") 
            print("3. ESP32 has correct firmware uploaded")
            return
            
        print(f"\n🎮 Testing commands: {' → '.join(self.test_commands)}")
        print("Watch ESP32 serial monitor for ACK responses!\n")
        
        for i, cmd in enumerate(self.test_commands, 1):
            print(f"[{i}/{len(self.test_commands)}] ", end="")
            self.send_command(cmd)
            time.sleep(2)  # 2 second delay between commands
            
        print("\n✅ Test sequence complete!")
        print("\nExpected ESP32 serial output:")
        print("📤 Pi command received: F → FORWARD")
        print("📤 Pi command received: S → STOP")
        print("🔍 Distance: XX cm")
        
    def interactive_mode(self):
        """Interactive command testing"""
        print("\n🎮 Interactive Mode")
        print("Commands: F=Forward, B=Back, L=Left, R=Right, S=Stop")
        print("Type 'quit' to exit\n")
        
        while True:
            try:
                cmd = input("Command (F/B/L/R/S): ").upper().strip()
                
                if cmd == 'QUIT':
                    break
                elif cmd in ['F', 'B', 'L', 'R', 'S']:
                    self.send_command(cmd)
                else:
                    print("❌ Invalid. Use F, B, L, R, or S")
                    
            except KeyboardInterrupt:
                print("\n👋 Exiting...")
                break

def main():
    print("🔧 ESP32 Robot Test Tool")
    
    # Get Pi IP from command line or use default
    pi_ip = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.2"
    
    tester = ESP32Tester(pi_ip)
    
    print("Choose mode:")
    print("1. Automated test sequence")
    print("2. Interactive mode")
    
    try:
        choice = input("\nEnter choice (1/2): ").strip()
        
        if choice == '1':
            tester.run_test_sequence()
        elif choice == '2':
            tester.interactive_mode()
        else:
            print("Invalid choice")
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()