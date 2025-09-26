#!/usr/bin/env python3
"""
🥧 Robot Guardian - Raspberry Pi Camera Server
==============================================

Runs on Raspberry Pi to:
- Stream camera video via HTTP
- Receive robot commands via HTTP API
- Forward commands to ESP32 via UART
- Provide status information

Requirements:
- sudo apt install python3-opencv python3-pip
- pip3 install flask pyserial opencv-python

Usage: python3 pi_camera_server.py

Hardware Setup:
- Pi GPIO14 (Pin 8, TX) → ESP32 GPIO1 (TX/D1)  
- Pi GPIO15 (Pin 10, RX) ← ESP32 GPIO3 (RX/D3)
- Pi GND (Pin 6) → ESP32 GND

Author: Robot Guardian System
Date: September 2025
"""

import cv2
import time
                                        logger.info(f"✅ Camera test successful on attempt {attempt + 1}")
class PiFallbackSpeaker:
    def __init__(self) -> None:
        self._engine = None
        self._queue: "queue.Queue[Optional[str]]" = queue.Queue()
        self._thread: Optional[threading.Thread] = None
        self.ready = False

        if pyttsx3 is None:
            logger.warning("🔇 pyttsx3 not installed; Pi fallback speaker disabled.")
            return

        try:
            self._engine = pyttsx3.init()
            self.ready = True
            self._thread = threading.Thread(target=self._worker, name="PiSpeakerThread", daemon=True)
            self._thread.start()
            logger.info("🔊 Fallback speech engine ready.")
        except Exception as exc:  # pragma: no cover - hardware specific
            logger.error(f"❌ Failed to initialise fallback speaker: {exc}")
            self.ready = False

    def _worker(self) -> None:
        while True:
            text = self._queue.get()
            if text is None:
                break
            if not text:
                continue
            try:
                if self._engine is not None:
                    self._engine.say(text)
                    self._engine.runAndWait()
            except Exception as exc:  # pragma: no cover - hardware specific
                logger.error(f"⚠️ Fallback speaker error: {exc}")

    def speak_async(self, text: str) -> bool:
        if not self.ready or not text:
            return False
        self._queue.put(text)
        return True

    def shutdown(self) -> None:
        if not self.ready:
            return
        self._queue.put(None)


                                    # Apply advanced optimizations after successful test
if assistant_service is None:
    fallback_speaker = PiFallbackSpeaker()


class AudioPlaybackQueue:
    def __init__(self) -> None:
        self._queue: "queue.Queue[Optional[str]]" = queue.Queue()
        self._thread = threading.Thread(target=self._worker, name="PiAudioQueue", daemon=True)
        self._thread.start()

    def enqueue(self, file_path: str) -> None:
        if not file_path:
            return
        self._queue.put(file_path)

    def shutdown(self) -> None:
        self._queue.put(None)
        if self._thread.is_alive():
            self._thread.join(timeout=1.5)

    def _worker(self) -> None:
        while True:
            file_path = self._queue.get()
            if file_path is None:
                break
            try:
                if not _play_audio_file(file_path):
                    logger.error("� Audio playback failed for %s", file_path)
            finally:
                try:
                    os.remove(file_path)
                except FileNotFoundError:
                    pass
                except Exception as exc:  # pragma: no cover - filesystem specific
                    logger.warning("⚠️ Failed to remove temp audio file %s: %s", file_path, exc)


                                    try:
    commands = []
    extension = Path(file_path).suffix.lower()
    if extension in {".wav", ".wave"}:
        commands.append(["aplay", "-q", file_path])

    commands.extend(
        [
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", file_path],
            ["mpv", "--really-quiet", file_path],
        ]
    )

    for command in commands:
        try:
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except FileNotFoundError:
            continue
        except subprocess.CalledProcessError as exc:  # pragma: no cover - playback specific
            logger.warning("⚠️ Audio command failed (%s): %s", command[0], exc)
            continue

    logger.error("❌ No compatible audio player found for %s", file_path)
    return False


                                        self.camera.set(cv2.CAP_PROP_FPS, self.fps)
    suffix = Path(filename or "voice-note").suffix or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(data)
        return temp_file.name


                                        self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
                                        self.camera.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
                                    except:
                                        logger.warning("⚠️ Some advanced camera settings not supported")
                                    break
                            
                            if self.camera:
                                self.camera.release()
                                
                        except Exception as e:
                            logger.warning(f"⚠️ Camera {camera_id} with {backend_name} failed: {e}")
                            if self.camera:
                                self.camera.release()
                                self.camera = None
                    
                    if camera_found:
                        break
                        
                except Exception as e:
                    logger.warning(f"⚠️ {backend_name} backend failed: {e}")
            
            if camera_found and self.camera and self.camera.isOpened():
                self.camera_active = True
                logger.info(f"✅ Camera ready: {self.frame_width}x{self.frame_height} @ {self.fps}fps")
                
                # Start camera capture thread
                threading.Thread(target=self.camera_capture_loop, daemon=True).start()
            else:
                logger.error(f"❌ Camera initialization failed: no working camera found")
                
        except Exception as e:
            logger.error(f"❌ Camera initialization failed: {e}")
            logger.error("🔧 Troubleshooting steps:")
            logger.error("   === For Pi Camera (CSI) ===")
            logger.error("   1. Check vcgencmd get_camera output")
            logger.error("   2. If supported=0: Enable camera in sudo raspi-config → Interface Options → Camera")
            logger.error("   3. If detected=0: Check ribbon cable connection (contacts away from ethernet)")
            logger.error("   4. Add to /boot/config.txt: camera_auto_detect=1")
            logger.error("   5. Install packages: sudo apt install python3-picamera2 python3-libcamera")
            logger.error("   6. Test: raspistill -o test.jpg")
            logger.error("   === For USB Camera ===")
            logger.error("   1. Check USB connection: lsusb")
            logger.error("   2. Check permissions: sudo usermod -a -G video $USER")
            logger.error("   3. Test different USB ports")
            logger.error("   4. Try: python3 camera_diagnostic.py")
            logger.error("   === General ===")
            logger.error("   1. Reboot after changes: sudo reboot")
            logger.error("   2. Run fix script: ./fix_pi_camera.sh")
            if self.camera:
                self.camera.release()
            self.camera_active = False
            
    def camera_capture_loop(self):
        """Continuous camera capture loop"""
        logger.info("📹 Camera capture loop started")
        
        while self.camera_active and self.camera:
            try:
                ret, frame = self.camera.read()
                
                if ret:
                    # Store frame thread-safely
                    with self.frame_lock:
                        self.current_frame = frame.copy()
                else:
                    logger.warning("⚠️ Failed to capture frame")
                    time.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"❌ Camera capture error: {e}")
                time.sleep(0.5)
                
        logger.info("📹 Camera capture loop stopped")
        
    def generate_video_stream(self):
        """Generate MJPEG video stream"""
        while True:
            frame = None
            
            # Get current frame
            with self.frame_lock:
                if self.current_frame is not None:
                    frame = self.current_frame.copy()
                    
            if frame is not None:
                try:
                    # Encode frame as JPEG
                    encode_params = [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality]
                    ret, buffer = cv2.imencode('.jpg', frame, encode_params)
                    
                    if ret:
                        frame_bytes = buffer.tobytes()
                        self.frames_served += 1
                        
                        # Yield frame in MJPEG format
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n'
                               b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n\r\n' +
                               frame_bytes + b'\r\n')
                    else:
                        logger.warning("⚠️ Frame encoding failed")
                        
                except Exception as e:
                    logger.error(f"❌ Frame encoding error: {e}")
                    
                else:
                    # No frame available, send placeholder
                    fallback_delay = 1.0 / self.fps if self.fps else 0.033
                    time.sleep(fallback_delay)
                
    def send_uart_command(self, command):
        """Send command to ESP32 via UART"""
        if not self.uart_connected or not self.uart:
            logger.warning(f"⚠️ UART not available for command: {command}")
            return False
            
        try:
            # Send single command character (ESP32 expects F, B, L, R, S)
            command_str = f"{command}\n"
            self.uart.write(command_str.encode('utf-8'))
            self.uart.flush()
            
            # Try to read ESP32 acknowledgment (ACK:F or NAK:F)
            start_time = time.time()
            response = ""
            
            while time.time() - start_time < 0.5:  # 500ms timeout for ESP32 response
                if self.uart.in_waiting > 0:
                    try:
                        response = self.uart.readline().decode('utf-8', errors='ignore').strip()
                        if response:
                            if response.startswith('ACK:'):
                                logger.info(f"✅ Command {command} → ESP32: {response}")
                            elif response.startswith('NAK:'):
                                logger.warning(f"⚠️ ESP32 rejected command {command}: {response}")
                            else:
                                logger.info(f"📤 ESP32 response: {response}")
                            break
                    except Exception as e:
                        logger.error(f"UART read error: {e}")
                        break
                time.sleep(0.01)
                
            if not response:
                logger.info(f"📤 Command {command} sent to ESP32 (no acknowledgment)")
            
            self.commands_received += 1
            self.last_command_time = datetime.now()
            self.last_command = command
            return True
            
        except Exception as e:
            logger.error(f"❌ UART command error: {e}")
            return False
            
    def get_system_status(self):
        """Get comprehensive system status"""
        try:
            # Calculate uptime
            uptime = datetime.now() - self.start_time
            
            # Get system info
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Get temperature (if available)
            temperature = "Unknown"
            try:
                with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                    temp = int(f.read()) / 1000.0
                    temperature = f"{temp:.1f}°C"
            except Exception:
                pass

            voice_ready = False
            if assistant_service:
                try:
                    voice_ready = bool(assistant_service.status().get('voice_ready'))
                except Exception as voice_error:
                    logger.warning(f"⚠️ Voice assistant status failed: {voice_error}")
                
            return {
                'status': 'running',
                'uart_status': 'connected' if self.uart_connected else 'disconnected',
                'camera_status': 'active' if self.camera_active else 'inactive',
                'baud_rate': self.baud_rate,
                'resolution': f"{self.frame_width}x{self.frame_height}",
                'fps': self.fps,
                'jpeg_quality': self.jpeg_quality,
                'commands_received': self.commands_received,
                'frames_served': self.frames_served,
                'uptime': str(uptime).split('.')[0],
                'last_command': self.last_command or 'None',
                'last_command_time': self.last_command_time.strftime('%H:%M:%S') if self.last_command_time else 'None',
                'cpu_usage': f"{cpu_percent:.1f}%",
                'memory_usage': f"{memory.percent:.1f}%",
                'disk_usage': f"{disk.percent:.1f}%",
                'temperature': temperature,
                'voice_ready': voice_ready
            }
            
        except Exception as e:
            logger.error(f"❌ Status error: {e}")
            return {'status': 'error', 'message': str(e)}

# Global server instance
server = PiCameraServer()

assistant_service = None
assistant_init_error: Optional[str] = None
if VoiceChatbotService:
    try:
        assistant_service = VoiceChatbotService()
        logger.info("🎙️ Voice assistant initialised")
    except Exception as assistant_error:
        logger.error(f"❌ Voice assistant init failed: {assistant_error}")
        assistant_service = None
        assistant_init_error = str(assistant_error)
else:
    logger.warning("ℹ️ Voice assistant module unavailable; skipping assistant features.")
    assistant_init_error = (
        "Voice assistant module not available. Ensure 'pi_voice_chatbot_single.py' is present "
        "and accessible on the PYTHONPATH."
    )


class PiFallbackSpeaker:
    def __init__(self) -> None:
        self._engine = None
        self._queue: "queue.Queue[Optional[str]]" = queue.Queue()
        self._thread: Optional[threading.Thread] = None
        self.ready = False

        if pyttsx3 is None:
            logger.warning("🔇 pyttsx3 not installed; Pi fallback speaker disabled.")
            return

        try:
            self._engine = pyttsx3.init()
            self.ready = True
            self._thread = threading.Thread(target=self._worker, name="PiSpeakerThread", daemon=True)
            self._thread.start()
            logger.info("🔊 Fallback speech engine ready.")
        except Exception as exc:  # pragma: no cover - hardware specific
def _play_audio_file(file_path: str) -> bool:
    commands = []
    extension = Path(file_path).suffix.lower()
    if extension in {".wav", ".wave"}:
        commands.append(["aplay", "-q", file_path])

    commands.extend(
        [
            ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", file_path],
            ["mpv", "--really-quiet", file_path],
        ]
    )

    for command in commands:
        try:
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except FileNotFoundError:
            continue
        except subprocess.CalledProcessError as exc:  # pragma: no cover - playback specific
            logger.warning("⚠️ Audio command failed (%s): %s", command[0], exc)
            continue

    logger.error("❌ No compatible audio player found for %s", file_path)
    return False


            logger.error(f"❌ Failed to initialise fallback speaker: {exc}")
    suffix = Path(filename or "voice-note").suffix or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(data)
        return temp_file.name


            self.ready = False



    def _worker(self) -> None:
        while True:
            text = self._queue.get()
            if text is None:
                break
            if not text:
                continue
            try:
                if self._engine is not None:
                    self._engine.say(text)
                    self._engine.runAndWait()
            except Exception as exc:  # pragma: no cover - hardware specific
                logger.error(f"⚠️ Fallback speaker error: {exc}")

    def speak_async(self, text: str) -> bool:
        if not self.ready or not text:
            return False
        self._queue.put(text)
        return True

    def shutdown(self) -> None:
        if not self.ready:
            return
        self._queue.put(None)


fallback_speaker: Optional[PiFallbackSpeaker] = None
if assistant_service is None:
    fallback_speaker = PiFallbackSpeaker()


class AudioPlaybackQueue:
    def __init__(self) -> None:
        self._queue: "queue.Queue[Optional[str]]" = queue.Queue()
        self._thread = threading.Thread(target=self._worker, name="PiAudioQueue", daemon=True)
        self._thread.start()

    def enqueue(self, file_path: str) -> None:
        if not file_path:
            return
        self._queue.put(file_path)

    def shutdown(self) -> None:
        self._queue.put(None)
        if self._thread.is_alive():
            self._thread.join(timeout=1.5)

    def _worker(self) -> None:
        while True:
            file_path = self._queue.get()
            if file_path is None:
                break
            try:
                if not _play_audio_file(file_path):
                    logger.error("🔇 Audio playback failed for %s", file_path)
            finally:
                try:
                    os.remove(file_path)
                except FileNotFoundError:
                    pass
                except Exception as exc:  # pragma: no cover - filesystem specific
                    logger.warning("⚠️ Failed to remove temp audio file %s: %s", file_path, exc)


def speak_text(text: str, async_mode: bool = True) -> bool:
    target = assistant_service or fallback_speaker
    if not target or not text:
        return False

    try:
        target.speak_async(text)
        return True
    except Exception as exc:  # pragma: no cover - hardware specific
        logger.error(f"⚠️ Failed to queue speech: {exc}")
        return False


def _assistant_offline_payload(message: str) -> dict:
    payload = {
        'status': 'offline',
        'message': message,
    }
    if assistant_init_error:
        payload['details'] = assistant_init_error
    return payload

VALID_MODES = {"care_companion", "watchdog", "edumate"}
mode_state = {
    'mode': 'care_companion',
    'metadata': {},
    'updated_at': datetime.utcnow().isoformat(),
    'watchdog_alarm_active': False,
    'last_summary': None,
}
mode_state_lock = threading.Lock()



# Flask routes
@app.route('/')
def index():


    """Web interface for robot control"""
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>🥧 Pi Robot Camera Server</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { 
            font-family: Arial, sans-serif; 
            background: #1e1e1e; 
            color: white; 
            margin: 0; 
            padding: 20px; 
            text-align: center;
        }
        .container { max-width: 800px; margin: 0 auto; }
        .header { margin-bottom: 30px; }
        .status { 
            background: #2a2a2a; 
            padding: 15px; 
            border-radius: 10px; 
            margin: 20px 0; 
            text-align: left;
        }
        .video-container { margin: 20px 0; }
        .video-stream { 
            max-width: 100%; 
            height: auto;
            border: 3px solid #333; 
            border-radius: 10px; 
        }
        .controls { 
            display: flex; 
            justify-content: center; 
            gap: 10px; 
            margin: 20px 0; 
            flex-wrap: wrap;
        }
        .btn { 
            background: #4CAF50; 
            color: white; 
            border: none; 
            padding: 15px 20px; 
            margin: 5px; 
            border-radius: 8px; 
            cursor: pointer; 
            font-size: 16px;
            font-weight: bold;
            min-width: 60px;
        }
        .btn:hover { background: #45a049; }
        .btn.stop { background: #f44336; }
        .btn.dir { background: #2196F3; }
        .grid { 
            display: grid; 
            grid-template-columns: repeat(3, 1fr); 
            gap: 10px; 
            max-width: 200px; 
            margin: 0 auto; 
        }
        .info { font-size: 14px; color: #ccc; margin: 10px 0; }
        @media (max-width: 600px) {
            .controls { flex-direction: column; align-items: center; }
            .grid { max-width: 150px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🥧 Pi Robot Camera Server</h1>
            <p class="info">Raspberry Pi Camera Stream & Robot Control</p>
        </div>
        
        <div class="video-container">
            <img class="video-stream" src="/video_feed" alt="Robot Camera Feed" id="videoStream">
        </div>
        
        <div class="controls">
            <div>
                <h3>🎮 Robot Controls</h3>
                <div class="grid">
                    <div></div>
                    <button class="btn dir" onclick="sendCommand('F')" title="Forward">↑</button>
                    <div></div>
                    <button class="btn dir" onclick="sendCommand('L')" title="Left">←</button>
                    <button class="btn stop" onclick="sendCommand('S')" title="Stop">⏹</button>
                    <button class="btn dir" onclick="sendCommand('R')" title="Right">→</button>
                    <div></div>
                    <button class="btn dir" onclick="sendCommand('B')" title="Backward">↓</button>
                    <div></div>
                </div>
            </div>
        </div>
        
        <div class="controls">
            <button class="btn" onclick="getStatus()">📊 System Status</button>
            <button class="btn stop" onclick="sendCommand('S')">🛑 Emergency Stop</button>
        </div>
        
        <div class="status" id="statusDisplay">
            <h3>📊 System Information</h3>
            <p>Click "System Status" to update...</p>
        </div>
        
        <div class="info">
            <p>🖥️ <strong>For AI Control:</strong> Use the Windows AI Controller app</p>
            <p>🌐 <strong>This Interface:</strong> Basic manual control and monitoring</p>
            <p>⌨️ <strong>Keyboard:</strong> Arrow keys or WASD for movement, Space to stop</p>
        </div>
    </div>
    
    <script>
        // Send robot command
        function sendCommand(cmd) {
            fetch('/move', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({direction: cmd})
            })
            .then(response => response.json())
            .then(data => {
                console.log('Command result:', data);
                if (data.status !== 'success') {
                    alert('Command failed: ' + (data.message || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Command error:', error);
                alert('Command failed: ' + error.message);
            });
        }
        
        // Get system status
        function getStatus() {
            fetch('/status')
            .then(response => response.json())
            .then(data => {
                const statusHtml = `
                    <h3>📊 System Status</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div>
                            <p><strong>🟢 Server:</strong> ${data.status}</p>
                            <p><strong>📡 UART:</strong> ${data.uart_status}</p>
                            <p><strong>📹 Camera:</strong> ${data.camera_status}</p>
                            <p><strong>⚡ Baud Rate:</strong> ${data.baud_rate}</p>
                            <p><strong>📐 Resolution:</strong> ${data.resolution}</p>
                            <p><strong>🎬 FPS:</strong> ${data.fps}</p>
                        </div>
                        <div>
                            <p><strong>🕒 Uptime:</strong> ${data.uptime}</p>
                            <p><strong>📤 Commands:</strong> ${data.commands_received}</p>
                            <p><strong>🎥 Frames:</strong> ${data.frames_served}</p>
                            <p><strong>🌡️ CPU:</strong> ${data.cpu_usage}</p>
                            <p><strong>💾 Memory:</strong> ${data.memory_usage}</p>
                            <p><strong>🔥 Temp:</strong> ${data.temperature}</p>
                        </div>
                    </div>
                    <p><strong>🎮 Last Command:</strong> ${data.last_command} (${data.last_command_time})</p>
                `;
                document.getElementById('statusDisplay').innerHTML = statusHtml;
            })
            .catch(error => {
                console.error('Status error:', error);
                document.getElementById('statusDisplay').innerHTML = 
                    '<h3>❌ Status Error</h3><p>' + error.message + '</p>';
            });
        }
        
        // Keyboard controls
        document.addEventListener('keydown', function(event) {
            switch(event.key) {
                case 'ArrowUp': case 'w': case 'W': sendCommand('F'); break;
                case 'ArrowDown': case 's': case 'S': sendCommand('B'); break;
                case 'ArrowLeft': case 'a': case 'A': sendCommand('L'); break;
                case 'ArrowRight': case 'd': case 'D': sendCommand('R'); break;
                case ' ': case 'Escape': sendCommand('S'); event.preventDefault(); break;
            }
        });
        
        // Auto-refresh status every 30 seconds
        setInterval(getStatus, 30000);
        
        // Load initial status
        setTimeout(getStatus, 1000);
        
        // Video stream error handling
        document.getElementById('videoStream').onerror = function() {
            this.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQwIiBoZWlnaHQ9IjQ4MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjMzMzIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIyMCIgZmlsbD0iI2ZmZiIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPvCfk7kgQ2FtZXJhIE5vdCBBdmFpbGFibGU8L3RleHQ+PC9zdmc+';
            this.alt = '📹 Camera stream not available';
        };
    </script>
</body>
</html>
    """)

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    if not server.camera_active:
        # Return error image if camera not available
        def error_stream():
            yield b'--frame\r\nContent-Type: text/plain\r\n\r\nCamera not available\r\n'
        return Response(error_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')
    
    return Response(
        server.generate_video_stream(),
        mimetype='multipart/x-mixed-replace; boundary=frame',
        headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
            'X-Accel-Buffering': 'no',  # Disable proxy buffering
            'Connection': 'keep-alive'   # Keep connection open for streaming
        }
    )

@app.route('/move', methods=['POST'])
def move_robot():
    """Handle robot movement commands"""
    try:
        data = request.get_json()
        
        if not data or 'direction' not in data:
            return jsonify({'status': 'error', 'message': 'Missing direction parameter'}), 400
            
        direction = data['direction'].upper().strip()
        
        # Validate command
        valid_commands = ['F', 'B', 'L', 'R', 'S']
        if direction not in valid_commands:
            return jsonify({
                'status': 'error',
                'message': f'Invalid direction: {direction}. Valid: {valid_commands}'
            }), 400
            
        # Send command to ESP32
        success = server.send_uart_command(direction)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'Command {direction} sent successfully',
                'uart_status': 'connected' if server.uart_connected else 'disconnected',
                'command': direction
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to send command to ESP32',
                'uart_status': 'disconnected'
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Move command error: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Get system status"""
    try:
        status = server.get_system_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"❌ Status error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/assistant/status', methods=['GET'])
def assistant_status():
    if not assistant_service:
        payload = _assistant_offline_payload('Voice assistant not available')
        payload['voice_ready'] = bool(fallback_speaker and fallback_speaker.ready)
        payload['speaker_only'] = bool(fallback_speaker and fallback_speaker.ready)
        status_code = 200 if payload['voice_ready'] else 503
        return jsonify(payload), status_code

    try:
        status = assistant_service.status()
        status['status'] = 'online'
        with mode_state_lock:
            status.update({
                'mode': mode_state.get('mode', 'care_companion'),
                'mode_metadata': mode_state.get('metadata', {}),
                'mode_updated_at': mode_state.get('updated_at'),
                'watchdog_alarm_active': mode_state.get('watchdog_alarm_active', False),
            })
        status['speaker_only'] = False
        return jsonify(status)
    except Exception as exc:
        logger.error(f"❌ Assistant status error: {exc}")
        return jsonify({'status': 'error', 'message': str(exc)}), 500


@app.route('/assistant/mode', methods=['GET', 'POST'])
def assistant_mode():
    if request.method == 'GET':
        with mode_state_lock:
            payload = {
                'status': 'success',
                'mode': mode_state.get('mode', 'care_companion'),
                'metadata': mode_state.get('metadata', {}),
                'updated_at': mode_state.get('updated_at'),
                'watchdog_alarm_active': mode_state.get('watchdog_alarm_active', False),
                'last_summary': mode_state.get('last_summary'),
            }
        return jsonify(payload)

    data = request.get_json(silent=True) or {}
    action = (data.get('action') or '').strip().lower()

    if action and action not in {'silence_alarm', 'status_update'}:
        return jsonify({'status': 'error', 'message': 'Unsupported action'}), 400

    mode = (data.get('mode') or '').strip().lower()
    metadata_payload = data.get('metadata')
    summary = data.get('summary')
    speak_summary = bool(data.get('speak'))
    watchdog_flag = data.get('watchdog_alarm_active')

    if mode and mode not in VALID_MODES:
        return jsonify({'status': 'error', 'message': 'Invalid mode supplied'}), 400

    if metadata_payload is not None and not isinstance(metadata_payload, dict):
        return jsonify({'status': 'error', 'message': 'metadata must be an object'}), 400

    with mode_state_lock:
        if mode:
            mode_state['mode'] = mode
            mode_state['metadata'] = metadata_payload or {}
            mode_state['updated_at'] = datetime.utcnow().isoformat()
        elif metadata_payload is not None:
            mode_state['metadata'] = metadata_payload

        if watchdog_flag is not None:
            mode_state['watchdog_alarm_active'] = bool(watchdog_flag)

        if action == 'silence_alarm':
            mode_state['watchdog_alarm_active'] = False

        if summary:
            mode_state['last_summary'] = summary

        response_snapshot = {
            'mode': mode_state.get('mode', 'care_companion'),
            'metadata': mode_state.get('metadata', {}),
            'updated_at': mode_state.get('updated_at'),
            'watchdog_alarm_active': mode_state.get('watchdog_alarm_active', False),
            'last_summary': mode_state.get('last_summary'),
        }

    if summary and assistant_service:
        try:
            assistant_service.add_system_note(summary, speak=speak_summary)
        except Exception as exc:
            logger.error(f"⚠️ Failed to log assistant summary: {exc}")

    return jsonify({'status': 'success', **response_snapshot})


@app.route('/assistant/message', methods=['POST'])
def assistant_message():
    if not assistant_service:
        return jsonify(_assistant_offline_payload('Voice assistant not available')), 503

    data = request.get_json(silent=True) or {}
    text = data.get('text') or data.get('message')
    speak = data.get('speak', True)
    history_limit = data.get('history_limit', 20)

    try:
        result = assistant_service.process_text(text, speak_reply=bool(speak))
        history = assistant_service.get_history(limit=int(history_limit))
        return jsonify({
            'status': 'success',
            'reply': result['reply'],
            'timestamp': result['timestamp'],
            'history': history
        })
    except ValueError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 400
    except Exception as exc:
        logger.error(f"❌ Assistant message error: {exc}")
        return jsonify({'status': 'error', 'message': 'Assistant processing failed'}), 500


@app.route('/assistant/reminders', methods=['GET', 'POST'])
def assistant_reminders():
    if not assistant_service:
        return jsonify(_assistant_offline_payload('Voice assistant not available')), 503

    if request.method == 'GET':
        try:
            reminders = assistant_service.list_reminders()
            return jsonify({'status': 'success', 'reminders': reminders})
        except Exception as exc:
            logger.error(f"❌ Assistant reminder fetch error: {exc}")
            return jsonify({'status': 'error', 'message': 'Failed to fetch reminders'}), 500

    data = request.get_json(silent=True) or {}
    message = data.get('message') or data.get('text')
    remind_at = data.get('remind_at') or data.get('time')
    delay_seconds = data.get('delay_seconds')
    if delay_seconds is None:
        delay_minutes = data.get('delay_minutes')
        if delay_minutes is not None:
            try:
                delay_seconds = float(delay_minutes) * 60.0
            except (TypeError, ValueError):
                return jsonify({'status': 'error', 'message': 'Invalid delay_minutes value'}), 400

    voice_note = data.get('voice_note') or data.get('voiceNote')

    try:
        reminder = assistant_service.add_reminder(
            message,
            remind_at=remind_at,
            delay_seconds=delay_seconds,
            voice_note=voice_note
        )
        return jsonify({'status': 'success', 'reminder': reminder}), 201
    except ValueError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 400
    except Exception as exc:
        logger.error(f"❌ Assistant reminder create error: {exc}")
        return jsonify({'status': 'error', 'message': 'Failed to create reminder'}), 500


@app.route('/assistant/reminders/<reminder_id>', methods=['DELETE'])
def assistant_delete_reminder(reminder_id):
    if not assistant_service:
        return jsonify(_assistant_offline_payload('Voice assistant not available')), 503


@app.route('/assistant/speak', methods=['POST'])
def assistant_speak():
    data = request.get_json(silent=True) or {}
    text = (data.get('text') or data.get('message') or '').strip()
    async_mode = bool(data.get('async', True))

    if not text:
        return jsonify({'status': 'error', 'message': 'text is required'}), 400

    if not (assistant_service or (fallback_speaker and fallback_speaker.ready)):
        return jsonify(_assistant_offline_payload('No speech engine configured on Pi')), 503

    success = speak_text(text, async_mode)
    if not success:
        return jsonify({'status': 'error', 'message': 'Failed to trigger speech'}), 500

    with mode_state_lock:
        mode_state['last_summary'] = text
        mode_state['updated_at'] = datetime.utcnow().isoformat()

    return jsonify({'status': 'success', 'spoken_text': text, 'async': async_mode})

    try:
        removed = assistant_service.remove_reminder(reminder_id)
        if not removed:
            return jsonify({'status': 'error', 'message': 'Reminder not found'}), 404
        return jsonify({'status': 'success', 'reminder': removed})
    except Exception as exc:
        logger.error(f"❌ Assistant reminder delete error: {exc}")
        return jsonify({'status': 'error', 'message': 'Failed to delete reminder'}), 500

if __name__ == '__main__':
    logger.info("🥧 Pi Robot Camera Server Starting...")
    logger.info("=" * 50)
    logger.info(f"UART: {server.uart_port} at {server.baud_rate} baud")
    logger.info(f"Camera: {server.frame_width}x{server.frame_height} @ {server.fps}fps")
    logger.info(f"UART Status: {'✅ Connected' if server.uart_connected else '❌ Disconnected'}")
    logger.info(f"Camera Status: {'✅ Active' if server.camera_active else '❌ Inactive'}")
    logger.info("")
    
    if not server.uart_connected:
        logger.warning("⚠️  UART not connected! Commands will not reach ESP32.")
        logger.warning("   Enable UART: sudo raspi-config → Interface Options → Serial Port")
        logger.warning("   Hardware: Connect Pi GPIO14→ESP32 RX2, Pi GPIO15←ESP32 TX2, GND-GND")
        
    if not server.camera_active:
        logger.warning("⚠️  Camera not active! Video stream will not work.")
        logger.warning("   Check camera connection and enable it in raspi-config")
        
    logger.info("🌐 Starting Flask server...")
    logger.info("   Local access: http://PI_IP:5000")
    logger.info("   Video stream: http://PI_IP:5000/video_feed")
    logger.info("   Status API: http://PI_IP:5000/status")
    logger.info("")
    logger.info("🖥️  Connect from Windows AI Controller for full AI features!")
    logger.info("")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
    finally:
        if server.camera:
            server.camera.release()
        if server.uart:
            server.uart.close()
        logger.info("👋 Goodbye!")