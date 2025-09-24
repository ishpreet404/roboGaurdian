#!/usr/bin/env python3
"""
🔧 UART Test Tool - Direct ESP32 Communication
==============================================

Tests UART communication directly to ESP32 on /dev/ttyS0
Sends commands F, B, L, R, S and checks for responses

Usage: python3 uart_test.py
"""

import serial
import time
import sys

def test_uart_direct():
    """Direct UART test to ESP32"""
    print("🔧 UART Direct Test - ESP32 Communication")
    print("=" * 50)
    
    try:
        # Open UART connection
        print(f"📡 Opening UART on /dev/ttyS0 at 9600 baud...")
        uart = serial.Serial(
            port='/dev/ttyS0',
            baudrate=9600,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1.0,
            write_timeout=1.0
        )
        
        # Clear buffers
        uart.reset_input_buffer()
        uart.reset_output_buffer()
        time.sleep(0.1)
        
        print("✅ UART connection established")
        print("")
        
        # Test commands
        test_commands = ['S', 'F', 'S', 'B', 'S', 'L', 'S', 'R', 'S']
        
        for i, cmd in enumerate(test_commands):
            print(f"📤 Test {i+1}/9: Sending '{cmd}'")
            
            # Send command
            command_str = f"{cmd}\n"
            uart.write(command_str.encode('utf-8'))
            uart.flush()
            
            # Wait for response
            start_time = time.time()
            response = ""
            
            while time.time() - start_time < 0.5:  # 500ms timeout
                if uart.in_waiting > 0:
                    try:
                        data = uart.readline().decode('utf-8', errors='ignore').strip()
                        if data:
                            response = data
                            break
                    except Exception as e:
                        print(f"   ❌ Read error: {e}")
                time.sleep(0.01)
            
            if response:
                print(f"   ✅ ESP32 response: {response}")
            else:
                print(f"   ⚠️ No response from ESP32")
            
            time.sleep(1)  # 1 second between commands
            
        print("\n🎯 UART test complete!")
        
        # Interactive mode
        print("\n🎮 Interactive mode (type 'quit' to exit):")
        while True:
            try:
                cmd = input("Enter command (F/B/L/R/S): ").upper().strip()
                
                if cmd == 'QUIT':
                    break
                elif cmd in ['F', 'B', 'L', 'R', 'S']:
                    print(f"📤 Sending: {cmd}")
                    uart.write(f"{cmd}\n".encode('utf-8'))
                    uart.flush()
                    
                    # Check response
                    time.sleep(0.2)
                    if uart.in_waiting > 0:
                        response = uart.readline().decode('utf-8', errors='ignore').strip()
                        print(f"   ✅ Response: {response}")
                    else:
                        print(f"   ⚠️ No response")
                else:
                    print("❌ Invalid command. Use F, B, L, R, or S")
                    
            except KeyboardInterrupt:
                break
        
        uart.close()
        print("\n👋 UART test finished!")
        
    except serial.SerialException as e:
        print(f"❌ UART connection failed: {e}")
        print("\n💡 Troubleshooting:")
        print("1. Check UART is enabled:")
        print("   sudo raspi-config → Interface Options → Serial Port")
        print("2. Check device exists:")
        print("   ls -la /dev/ttyS0")
        print("3. Check permissions:")
        print("   sudo usermod -a -G dialout $USER")
        print("   (then logout/login)")
        print("4. Check wiring:")
        print("   Pi GPIO14 → ESP32 RX")
        print("   Pi GPIO15 ← ESP32 TX") 
        print("   Pi GND → ESP32 GND")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_uart_direct()