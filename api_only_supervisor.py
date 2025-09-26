#!/usr/bin/env python3
"""
Simple API-only version of Windows Robot Supervisor for testing endpoints
"""

import sys
import os
import threading
import time
from pathlib import Path

# Add current directory to Python path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from flask import Flask
from windows_robot_supervisor import WindowsRobotSupervisor

class APIOnlySupervisor(WindowsRobotSupervisor):
    """API-only version without GUI for testing"""
    
    def run(self) -> None:
        print("🌐 Starting API-only Windows bridge...")
        self.start_api()
        print(f"✅ Bridge ready at http://localhost:{self.port}/api/status")
        print("🧪 API endpoints ready for testing")
        print("Press Ctrl+C to stop...")
        
        try:
            # Keep the server running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("👋 API supervisor shutting down.")

def main() -> None:
    APIOnlySupervisor().run()

if __name__ == "__main__":
    main()