#!/usr/bin/env python3
"""
🥧 Robot Guardian - Raspberry Pi Camera Server (FIXED VERSION)
=============================================================

Runs on Raspberry Pi to:
- Stream camera video via HTTP
- Receive robot commands via HTTP API
- Forward commands to ESP32 via UART
- Provide status information

Requirements:
- sudo apt install python3-opencv python3-pip
- pip3 install flask pyserial opencv-python

Usage: python3 pi_camera_server_fixed.py

Hardware Setup:
- Pi GPIO14 (Pin 8, TX) → ESP32 GPIO1 (TX/D1)  
- Pi GPIO15 (Pin 10, RX) ← ESP32 GPIO3 (RX/D3)
- Pi GND (Pin 6) → ESP32 GND

Author: Robot Guardian System
Date: September 2025
"""

import base64
import json
import logging
import os
import queue
import subprocess
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple, List

import cv2
import psutil
from flask import Flask, Response, request, jsonify, render_template_string
try:
    import serial
except ImportError:
    print("⚠️ pyserial not installed. Install with: pip3 install pyserial")
    serial = None
try:
    import pyttsx3  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - optional dependency
    pyttsx3 = None

ASSISTANT_MODE = os.getenv('PI_ASSISTANT_MODE', 'fallback').strip().lower()
USE_GITHUB_ASSISTANT = ASSISTANT_MODE in {'full', 'github', 'assistant', 'chirpy', 'enabled'}

if USE_GITHUB_ASSISTANT:
    try:
        from pi_voice_chatbot_single import VoiceChatbotService, _prepare_for_speech  # type: ignore[import-not-found]
    except ImportError:  # pragma: no cover - optional dependency
        VoiceChatbotService = None  # type: ignore[assignment]

        def _prepare_for_speech(text: str) -> str:  # type: ignore[override]
            return text.strip()
else:
    VoiceChatbotService = None  # type: ignore[assignment]

    def _prepare_for_speech(text: str) -> str:
        return (text or '').strip()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
    response.headers['Access-Control-Max-Age'] = '3600'
    return response

class PiCameraServer:
    def __init__(self):
        # Hardware configuration for ESP32 UART0 communication
        # Pi GPIO14/15 → ESP32 GPIO1/3 (UART0)
        self.uart_port = '/dev/ttyS0'
        self.baud_rate = 9600
        self.uart = None
        self.uart_connected = False
        
        # Camera configuration
        self.camera = None
        self.camera_active = False
        self.current_frame = None
        self.frame_lock = threading.Lock()
        
        # Camera settings (optimized for low latency)
        self.frame_width = 1280   # Target 720p HD stream width
        self.frame_height = 720   # Target 720p HD stream height
        self.fps = 30             # Maintain smoother 30 FPS
        self.jpeg_quality = 60    # Lower quality for smaller payloads → less latency
        self.capture_flush_frames = 2  # Drop buffered frames to keep stream real-time
        self.capture_retry_delay = 0.02
        self.last_frame_timestamp = 0
        self.encode_params = self._build_encode_params()

        # Boost OpenCV performance on constrained hardware
        try:
            cv2.setUseOptimized(True)
            if hasattr(cv2, "setNumThreads"):
                target_threads = min(4, max(1, os.cpu_count() or 1))
                cv2.setNumThreads(target_threads)
        except Exception as opt_err:
            logger.debug(f"OpenCV optimization tuning skipped: {opt_err}")
        
        # Statistics
        self.commands_received = 0
        self.frames_served = 0
        self.start_time = datetime.now()
        self.last_command_time = None
        self.last_command = None
        
        self.initialize_hardware()
        
    def initialize_hardware(self):
        """Initialize UART and camera"""
        # Initialize UART for ESP32 communication
        if serial:
            try:
                self.uart = serial.Serial(
                    port=self.uart_port,
                    baudrate=self.baud_rate,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=0.5,
                    write_timeout=0.5
                )
                
                # Test UART
                self.uart.reset_input_buffer()
                self.uart.reset_output_buffer()
                
                self.uart_connected = True
                logger.info(f"✅ UART initialized on {self.uart_port} at {self.baud_rate} baud")
                
            except Exception as e:
                logger.error(f"❌ UART initialization failed: {e}")
                logger.error("   Make sure UART is enabled: sudo raspi-config → Interface Options → Serial Port")
                self.uart_connected = False
        else:
            logger.warning("⚠️ pyserial not available - UART disabled")
            self.uart_connected = False
            
        # Initialize camera with multiple fallback methods
        try:
            camera_backends = [
                (cv2.CAP_V4L2, "V4L2"),     # Linux Video4Linux2 (best for Pi)
                (cv2.CAP_GSTREAMER, "GStreamer"),  # Alternative for Pi Camera
                (cv2.CAP_ANY, "Auto")       # Fallback to any available backend
            ]
            
            self.camera = None
            camera_found = False
            
            for backend, backend_name in camera_backends:
                logger.info(f"🔍 Trying {backend_name} backend...")
                
                try:
                    # Try different camera indices with current backend
                    for camera_id in [0, 1, -1]:
                        try:
                            self.camera = cv2.VideoCapture(camera_id, backend)
                            
                            if self.camera.isOpened():
                                logger.info(f"📹 Found camera at index {camera_id} with {backend_name}")
                                
                                # Set basic properties first
                                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
                                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
                                self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimal buffering
                                
                                # Test camera capture multiple times (sometimes first read fails)
                                for attempt in range(3):
                                    ret, test_frame = self.camera.read()
                                    if ret and test_frame is not None:
                                        logger.info(f"✅ Camera test successful on attempt {attempt + 1}")
                                        camera_found = True
                                        break
                                    else:
                                        logger.warning(f"⚠️ Camera test attempt {attempt + 1} failed, retrying...")
                                        time.sleep(0.1)
                                
                                if camera_found:
                                    # Apply advanced optimizations after successful test
                                    try:
                                        self.camera.set(cv2.CAP_PROP_FPS, self.fps)
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
                logger.error("   Troubleshooting steps:")
                logger.error("   1. Check camera connection")
                logger.error("   2. Enable camera: sudo raspi-config → Interface Options → Camera")  
                logger.error("   3. Check permissions: sudo usermod -a -G video $USER")
                logger.error("   4. Restart Pi: sudo reboot")
                logger.error("   5. Run diagnostic: python3 camera_test.py")
                if self.camera:
                    self.camera.release()
                self.camera_active = False
                
        except Exception as e:
            logger.error(f"❌ Camera initialization failed: {e}")
            logger.error("   Make sure camera is connected and enabled")
            self.camera_active = False
            
    def camera_capture_loop(self):
        """Continuous camera capture loop"""
        logger.info("📹 Camera capture loop started")
        
        while self.camera_active and self.camera:
            try:
                ret, frame = self.camera.read()
                
                if ret:
                    # Drop any stale buffered frames to minimize latency
                    flushed = 0
                    while flushed < self.capture_flush_frames and self.camera:
                        if not self.camera.grab():
                            break
                        ret_flush, flush_frame = self.camera.retrieve()
                        if not ret_flush:
                            break
                        frame = flush_frame
                        flushed += 1

                    # Store frame thread-safely
                    with self.frame_lock:
                        self.current_frame = frame
                        self.last_frame_timestamp = time.time()
                else:
                    logger.warning("⚠️ Failed to capture frame")
                    time.sleep(self.capture_retry_delay)
                    
            except Exception as e:
                logger.error(f"❌ Camera capture error: {e}")
                time.sleep(self.capture_retry_delay * 2)
                
        logger.info("📹 Camera capture loop stopped")

    def _build_encode_params(self):
        params = [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality]
        if hasattr(cv2, 'IMWRITE_JPEG_LUMA_QUALITY'):
            params.extend([cv2.IMWRITE_JPEG_LUMA_QUALITY, self.jpeg_quality])
        if hasattr(cv2, 'IMWRITE_JPEG_CHROMA_QUALITY'):
            chroma_quality = max(10, self.jpeg_quality - 15)
            params.extend([cv2.IMWRITE_JPEG_CHROMA_QUALITY, chroma_quality])
        return params
        
    def generate_video_stream(self):
        """Generate MJPEG video stream"""
        while True:
            frame = None
            
            # Get current frame
            with self.frame_lock:
                if self.current_frame is not None:
                    frame = self.current_frame
                    
            if frame is not None:
                try:
                    # Encode frame as JPEG
                    ret, buffer = cv2.imencode('.jpg', frame, self.encode_params)
                    
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
                # No frame available, send placeholder with lower latency
                fallback_delay = 1.0 / self.fps if self.fps else self.capture_retry_delay
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
            
            while time.time() - start_time < 0.1:  # Reduced to 100ms timeout for faster response
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
                'temperature': temperature
            }
            
        except Exception as e:
            logger.error(f"❌ Status error: {e}")
            return {'status': 'error', 'message': str(e)}

# ---------------------------------------------------------------------------
# Audio playback and assistant helpers
# ---------------------------------------------------------------------------
_AUDIO_SUFFIX_MAP = {
    'audio/wav': '.wav',
    'audio/x-wav': '.wav',
    'audio/wave': '.wav',
    'audio/mpeg': '.mp3',
    'audio/mp3': '.mp3',
    'audio/ogg': '.ogg',
    'audio/webm': '.webm',
    'audio/mp4': '.m4a',
}


def _coerce_optional_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        return float(text)
    return None


def _parse_delay_values(*, seconds_value: Any = None, minutes_value: Any = None) -> float:
    seconds = _coerce_optional_float(seconds_value)
    minutes = _coerce_optional_float(minutes_value)
    if seconds is not None:
        delay = seconds
    elif minutes is not None:
        delay = minutes * 60.0
    else:
        delay = 0.0
    if delay < 0:
        raise ValueError('Delay must be non-negative.')
    return delay


def _coerce_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value

    if isinstance(value, (int, float)):
        return datetime.utcnow() + timedelta(seconds=float(value))

    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError('Reminder time cannot be empty.')
        if text.endswith('Z'):
            text = text[:-1] + '+00:00'
        try:
            dt = datetime.fromisoformat(text)
        except ValueError as exc:
            raise ValueError('Invalid reminder time. Use ISO format, e.g. 2025-09-26T18:30.') from exc
        if dt.tzinfo:
            return dt.astimezone().replace(tzinfo=None)
        return dt

    raise ValueError('Unsupported reminder time format.')


def _decode_base64_audio(value: str) -> bytes:
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Audio payload missing.')
    stripped = value.strip()
    if stripped.startswith('data:'):
        _, _, stripped = stripped.partition(',')
    try:
        return base64.b64decode(stripped, validate=True)
    except Exception as exc:  # pragma: no cover - validation specific
        raise ValueError('Invalid base64 audio payload.') from exc


def _determine_suffix(filename: Optional[str], content_type: Optional[str]) -> str:
    if filename:
        suffix = Path(filename).suffix
        if suffix:
            return suffix
    if content_type:
        key = content_type.split(';', 1)[0].strip().lower()
        return _AUDIO_SUFFIX_MAP.get(key, '.wav')
    return '.wav'


def _write_temp_audio(data: bytes, filename: Optional[str], content_type: Optional[str]) -> str:
    suffix = _determine_suffix(filename, content_type)
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(data)
        temp_path = temp_file.name
    logger.debug('💾 Stored voice note at %s', temp_path)
    return temp_path


def _play_audio_file(file_path: str) -> bool:
    commands = []
    extension = Path(file_path).suffix.lower()
    if extension in {'.wav', '.wave'}:
        commands.append(['aplay', '-q', file_path])

    commands.extend(
        [
            ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet', file_path],
            ['mpv', '--really-quiet', file_path],
        ]
    )

    for command in commands:
        try:
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except FileNotFoundError:
            continue
        except subprocess.CalledProcessError as exc:  # pragma: no cover - playback specific
            logger.warning('⚠️ Audio command failed (%s): %s', command[0], exc)
            continue

    logger.error('❌ No compatible audio player found for %s', file_path)
    return False


class AudioPlaybackQueue:
    def __init__(self) -> None:
        self._queue: 'queue.Queue[Optional[str]]' = queue.Queue()
        self._thread = threading.Thread(target=self._worker, name='PiAudioQueue', daemon=True)
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
                    logger.error('🔇 Audio playback failed for %s', file_path)
            finally:
                try:
                    os.remove(file_path)
                except FileNotFoundError:
                    pass
                except Exception as exc:  # pragma: no cover - filesystem specific
                    logger.warning('⚠️ Failed to remove temp audio file %s: %s', file_path, exc)


class PiFallbackSpeaker:
    def __init__(self) -> None:
        self._engine = None
        self._queue: 'queue.Queue[Optional[str]]' = queue.Queue()
        self._thread: Optional[threading.Thread] = None
        self.ready = False
        self.use_gtts = False
        
        # Try gTTS first for better quality (needs internet)
        try:
            import gtts  # type: ignore[import-not-found]
            self.use_gtts = True
            logger.info('🌐 gTTS available for high-quality speech')
        except ImportError:
            logger.info('📦 gTTS not installed, using pyttsx3 fallback')

        if pyttsx3 is None and not self.use_gtts:
            logger.warning('🔇 No TTS engines available; Pi fallback speaker disabled.')
            return

        try:
            if pyttsx3 is not None:
                self._engine = pyttsx3.init()
                # Configure for better Hindi support if available
                voices = self._engine.getProperty('voices')
                for voice in voices:
                    if 'hindi' in voice.name.lower() or 'hi' in voice.id.lower():
                        self._engine.setProperty('voice', voice.id)
                        logger.info(f'🇮🇳 Using Hindi voice: {voice.name}')
                        break
                # Set slower rate for clearer speech
                self._engine.setProperty('rate', 150)
                
            self.ready = True
            self._thread = threading.Thread(target=self._worker, name='PiSpeakerThread', daemon=True)
            self._thread.start()
            logger.info('🔊 Enhanced speech engine ready with Hindi support.')
        except Exception as exc:  # pragma: no cover - hardware specific
            logger.error('❌ Failed to initialise fallback speaker: %s', exc)
            self.ready = False

    def _worker(self) -> None:
        while True:
            text = self._queue.get()
            if text is None:
                break
            if not text:
                continue
            try:
                # Try gTTS first for better quality
                if self.use_gtts and self._try_gtts_speech(text):
                    continue
                
                # Fallback to pyttsx3
                if self._engine is not None:
                    self._engine.say(text)
                    self._engine.runAndWait()
                else:
                    # Last resort: use system espeak
                    self._try_system_speech(text)
            except Exception as exc:  # pragma: no cover - hardware specific
                logger.error('⚠️ Fallback speaker error: %s', exc)

    def _try_gtts_speech(self, text: str) -> bool:
        """Try using gTTS for high-quality speech."""
        try:
            import gtts  # type: ignore[import-not-found]
            import pygame  # type: ignore[import-not-found]
            
            # Detect language (simple heuristic)
            lang = 'hi' if any(ord(c) > 127 for c in text) else 'en'
            
            # Generate speech
            tts = gtts.gTTS(text=text, lang=lang, slow=False)
            
            # Save to temporary file and play
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                tts.save(tmp_file.name)
                
                # Play using pygame
                pygame.mixer.init()
                pygame.mixer.music.load(tmp_file.name)
                pygame.mixer.music.play()
                
                # Wait for playback to complete
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                
                # Cleanup
                pygame.mixer.quit()
                os.unlink(tmp_file.name)
                
            return True
        except Exception as exc:
            logger.debug('gTTS failed, using fallback: %s', exc)
            return False

    def _try_system_speech(self, text: str) -> bool:
        """Last resort: use system espeak."""
        try:
            # Try Hindi first if text contains non-ASCII chars
            if any(ord(c) > 127 for c in text):
                subprocess.run(['espeak', '-v', 'hi', text], check=True, capture_output=True)
            else:
                subprocess.run(['espeak', text], check=True, capture_output=True)
            return True
        except Exception:
            return False

    def speak_async(self, text: str) -> bool:
        if not self.ready or not text:
            return False
        self._queue.put(text)
        return True

    def shutdown(self) -> None:
        if not self.ready:
            return
        self._queue.put(None)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)


assistant_service: Optional[Any] = None
assistant_init_error: Optional[str] = None
fallback_speaker: Optional[PiFallbackSpeaker] = None


def _assistant_offline_payload(message: str) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        'status': 'offline',
        'message': message,
        'assistant_mode': ASSISTANT_MODE,
        'reminders_supported': False,
    }
    if assistant_init_error:
        payload['details'] = assistant_init_error
    return payload


def speak_text(text: str, async_mode: bool = True) -> bool:
    cleaned = (text or '').strip()
    if not cleaned:
        return False

    if assistant_service is not None:
        try:
            assistant_service.speak_async(_prepare_for_speech(cleaned))
            return True
        except Exception as exc:  # pragma: no cover - hardware specific
            logger.error('⚠️ Assistant speech failed: %s', exc)

    if fallback_speaker is not None and fallback_speaker.ready:
        return fallback_speaker.speak_async(cleaned)

    logger.warning('🔇 No speech engine available for text playback.')
    return False


class VoiceNoteManager:
    def __init__(self, playback_queue: AudioPlaybackQueue, speak_callback: Callable[[str, bool], bool]) -> None:
        self._queue = playback_queue
        self._speak_callback = speak_callback
        self._timers: List[threading.Timer] = []
        self._lock = threading.Lock()

    def enqueue_audio(
        self,
        *,
        data: bytes,
        filename: Optional[str],
        content_type: Optional[str],
        delay_seconds: float,
    ) -> Dict[str, Any]:
        file_path = _write_temp_audio(data, filename, content_type)
        scheduled_for = datetime.utcnow()

        if delay_seconds <= 0:
            self._queue.enqueue(file_path)
            return {
                'file_path': file_path,
                'scheduled_for': scheduled_for.isoformat(),
                'delayed': False,
            }

        scheduled_for += timedelta(seconds=delay_seconds)

        def _play() -> None:
            try:
                self._queue.enqueue(file_path)
            finally:
                with self._lock:
                    try:
                        self._timers.remove(timer)
                    except ValueError:
                        pass

        timer = threading.Timer(delay_seconds, _play)
        timer.daemon = True
        with self._lock:
            self._timers.append(timer)
        timer.start()

        return {
            'file_path': file_path,
            'scheduled_for': scheduled_for.isoformat(),
            'delayed': True,
        }

    def enqueue_text(self, text: str, delay_seconds: float) -> Dict[str, Any]:
        scheduled_for = datetime.utcnow()
        prepared = _prepare_for_speech(text)

        if delay_seconds <= 0:
            success = self._speak_callback(prepared, True)
            return {
                'scheduled_for': scheduled_for.isoformat(),
                'delayed': False,
                'success': success,
            }

        scheduled_for += timedelta(seconds=delay_seconds)

        def _speak() -> None:
            try:
                self._speak_callback(prepared, True)
            finally:
                with self._lock:
                    try:
                        self._timers.remove(timer)
                    except ValueError:
                        pass

        timer = threading.Timer(delay_seconds, _speak)
        timer.daemon = True
        with self._lock:
            self._timers.append(timer)
        timer.start()

        return {
            'scheduled_for': scheduled_for.isoformat(),
            'delayed': True,
            'success': True,
        }

    def shutdown(self) -> None:
        with self._lock:
            for timer in self._timers:
                timer.cancel()
            self._timers.clear()


@dataclass
class LocalReminder:
    id: str
    message: str
    remind_at: datetime
    created_at: datetime
    voice_note: Optional[str] = None
    delivered: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'message': self.message,
            'remind_at': self.remind_at.isoformat(),
            'created_at': self.created_at.isoformat(),
            'voice_note': self.voice_note,
            'delivered': self.delivered,
        }


class LocalReminderScheduler:
    def __init__(self, voice_manager: VoiceNoteManager, speak_callback: Callable[[str, bool], bool]) -> None:
        self._voice_manager = voice_manager
        self._speak_callback = speak_callback
        self._reminders: Dict[str, LocalReminder] = {}
        self._lock = threading.Lock()
        self._event = threading.Event()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name='PiReminderScheduler', daemon=True)
        self._thread.start()

    def add_reminder(self, message: str, remind_at: datetime, *, voice_note: Optional[str] = None) -> Dict[str, Any]:
        reminder = LocalReminder(
            id=str(uuid.uuid4()),
            message=message.strip(),
            remind_at=remind_at,
            created_at=datetime.utcnow(),
            voice_note=(voice_note.strip() if voice_note else None),
        )
        with self._lock:
            self._reminders[reminder.id] = reminder
            self._event.set()
        return reminder.to_dict()

    def remove_reminder(self, reminder_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            reminder = self._reminders.pop(reminder_id, None)
            if reminder:
                self._event.set()
            return reminder.to_dict() if reminder else None

    def list_reminders(self) -> List[Dict[str, Any]]:
        with self._lock:
            reminders = sorted(self._reminders.values(), key=lambda item: item.remind_at)
            return [item.to_dict() for item in reminders]

    def shutdown(self) -> None:
        self._stop.set()
        self._event.set()
        if self._thread.is_alive():
            self._thread.join(timeout=1.5)

    def _due_reminder(self) -> Optional[LocalReminder]:
        with self._lock:
            pending = [item for item in self._reminders.values() if not item.delivered]
            if not pending:
                return None
            return min(pending, key=lambda item: item.remind_at)

    def _mark_delivered(self, reminder_id: str) -> Optional[LocalReminder]:
        with self._lock:
            reminder = self._reminders.get(reminder_id)
            if reminder:
                reminder.delivered = True
            return reminder

    def _run(self) -> None:
        while not self._stop.is_set():
            reminder = self._due_reminder()
            if reminder is None:
                self._event.wait(timeout=60)
                self._event.clear()
                continue

            now = datetime.utcnow()
            delay = (reminder.remind_at - now).total_seconds()
            if delay > 0:
                triggered = self._event.wait(timeout=min(delay, 60))
                if triggered:
                    self._event.clear()
                continue

            delivered = self._mark_delivered(reminder.id)
            if not delivered:
                continue

            announcement = delivered.voice_note or delivered.message
            try:
                logger.info(f'🔔 Triggering reminder: {delivered.message}')
                if announcement:
                    result = self._voice_manager.enqueue_text(announcement, 0.0)
                    logger.info(f'📢 Reminder speech result: {result}')
                else:
                    success = self._speak_callback('Reminder due.', True)
                    logger.info(f'📢 Default reminder speech success: {success}')
            except Exception as exc:
                logger.error(f'❌ Reminder delivery failed: {exc}')
            finally:
                self._event.set()


def _extract_voice_note_payload() -> Tuple[Optional[bytes], Optional[str], Optional[str], float, Optional[str]]:
    if request.files:
        file_storage = next(iter(request.files.values()))
        data = file_storage.read()
        if not data:
            raise ValueError('Uploaded file is empty.')

        delay_seconds = _parse_delay_values(
            seconds_value=request.form.get('delay_seconds') or request.form.get('delaySeconds'),
            minutes_value=request.form.get('delay_minutes') or request.form.get('delayMinutes'),
        )

        spoken_text = request.form.get('text') or request.form.get('message')
        if spoken_text is not None:
            spoken_text = spoken_text.strip() or None

        return (
            data,
            file_storage.filename,
            file_storage.mimetype,
            delay_seconds,
            spoken_text,
        )

    payload = request.get_json(force=True, silent=True) or {}

    delay_seconds = _parse_delay_values(
        seconds_value=payload.get('delay_seconds') or payload.get('delaySeconds'),
        minutes_value=payload.get('delay_minutes') or payload.get('delayMinutes'),
    )

    audio_field = (
        payload.get('audio')
        or payload.get('data')
        or payload.get('voice_note')
        or payload.get('voiceNote')
    )
    filename = payload.get('filename') or payload.get('name')
    content_type = payload.get('content_type') or payload.get('mime_type') or payload.get('mimeType')
    spoken_text = payload.get('text') or payload.get('message')
    if isinstance(spoken_text, str):
        spoken_text = spoken_text.strip() or None

    if audio_field:
        audio_bytes = _decode_base64_audio(audio_field)
        return audio_bytes, filename, content_type, delay_seconds, spoken_text

    if spoken_text:
        return None, None, None, delay_seconds, spoken_text

    raise ValueError('Audio payload missing.')

# Global server instance and assistant wiring
server = PiCameraServer()

audio_queue = AudioPlaybackQueue()
voice_note_manager = VoiceNoteManager(
    audio_queue,
    lambda text, async_mode=True: speak_text(text, async_mode),
)

reminder_scheduler: Optional[LocalReminderScheduler] = None

if VoiceChatbotService is not None:
    try:
        assistant_service = VoiceChatbotService()
        logger.info('🎙️ Voice assistant initialised.')
    except Exception as exc:  # pragma: no cover - external dependency
        assistant_service = None
        assistant_init_error = str(exc)
        logger.error('❌ Voice assistant init failed: %s', exc)
else:
    assistant_service = None
    assistant_init_error = (
        "Voice assistant module not available. Ensure 'pi_voice_chatbot_single.py' is present "
        'and accessible on the PYTHONPATH.'
    )
    logger.warning('ℹ️ Voice assistant module unavailable; skipping assistant features.')

if assistant_service is None:
    fallback_speaker = PiFallbackSpeaker()
    reminder_scheduler = LocalReminderScheduler(voice_note_manager, lambda text, async_mode=True: speak_text(text, async_mode))
else:
    fallback_speaker = None

@app.route('/assistant/status', methods=['GET'])
def assistant_status():
    if assistant_service is None:
        voice_ready = bool(fallback_speaker and fallback_speaker.ready)
        reminders_supported = reminder_scheduler is not None
        message = 'Speaker-only mode active; GitHub assistant disabled.' if voice_ready else 'No speech engine available on Pi.'
        payload = {
            'status': 'speaker_only' if voice_ready else 'offline',
            'voice_ready': voice_ready,
            'speaker_only': voice_ready,
            'assistant_mode': ASSISTANT_MODE,
            'reminders_supported': reminders_supported,
            'message': message,
        }
        status_code = 200 if voice_ready or reminders_supported else 503
        return jsonify(payload), status_code

    try:
        status = assistant_service.status()
        status.update({'status': 'online', 'speaker_only': False})
        return jsonify(status)
    except Exception as exc:  # pragma: no cover - external dependency
        logger.error('❌ Assistant status error: %s', exc)
        return jsonify({'status': 'error', 'message': 'Failed to fetch assistant status'}), 500


@app.route('/assistant/message', methods=['POST', 'OPTIONS'])
def assistant_message():
    if request.method == 'OPTIONS':
        return ('', 204)

    if assistant_service is None:
        return jsonify(_assistant_offline_payload('Voice assistant not available on Pi.')), 503

    data = request.get_json(force=True, silent=True) or {}
    text = (data.get('text') or data.get('message') or '').strip()
    speak = bool(data.get('speak', True))
    history_limit = int(data.get('history_limit', 20))

    if not text:
        return jsonify({'status': 'error', 'message': 'text is required'}), 400

    try:
        result = assistant_service.process_text(text, speak_reply=speak)
        history = assistant_service.get_history(limit=history_limit)
    except ValueError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 400
    except Exception as exc:  # pragma: no cover - external dependency
        logger.error('❌ Assistant message error: %s', exc)
        return jsonify({'status': 'error', 'message': 'Assistant processing failed'}), 500

    return jsonify({
        'status': 'success',
        'reply': result['reply'],
        'timestamp': result['timestamp'],
        'history': history,
    })


@app.route('/assistant/voice_note', methods=['POST', 'OPTIONS'])
def assistant_voice_note():
    if request.method == 'OPTIONS':
        return ('', 204)

    try:
        audio_bytes, filename, content_type, delay_seconds, spoken_text = _extract_voice_note_payload()
    except ValueError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 400
    except Exception as exc:  # pragma: no cover - defensive
        logger.error('❌ Voice note payload error: %s', exc)
        return jsonify({'status': 'error', 'message': 'Failed to parse voice note payload'}), 400

    try:
        if audio_bytes:
            result = voice_note_manager.enqueue_audio(
                data=audio_bytes,
                filename=filename,
                content_type=content_type,
                delay_seconds=delay_seconds,
            )
            playback_id = Path(result['file_path']).name
            response = {
                'status': 'success',
                'playback_mode': 'audio',
                'queued': result['delayed'],
                'scheduled_for': result['scheduled_for'],
                'playback_id': playback_id,
                'delay_seconds': delay_seconds,
            }
        elif spoken_text:
            result = voice_note_manager.enqueue_text(spoken_text, delay_seconds)
            if not result.get('success', True):
                return jsonify({'status': 'error', 'message': 'No speaker available on Pi'}), 503
            response = {
                'status': 'success',
                'playback_mode': 'text',
                'queued': result['delayed'],
                'scheduled_for': result['scheduled_for'],
                'spoken_text': _prepare_for_speech(spoken_text),
                'delay_seconds': delay_seconds,
            }
        else:
            return jsonify({'status': 'error', 'message': 'Audio payload missing'}), 400
    except ValueError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 400
    except Exception as exc:  # pragma: no cover - defensive
        logger.error('❌ Voice note processing error: %s', exc)
        return jsonify({'status': 'error', 'message': 'Failed to queue voice note'}), 500

    status_code = 202 if response.get('queued') else 200
    return jsonify(response), status_code


@app.route('/assistant/reminders', methods=['GET', 'POST', 'OPTIONS'])
def assistant_reminders():
    if request.method == 'OPTIONS':
        return ('', 204)

    if assistant_service is None and reminder_scheduler is None:
        payload = _assistant_offline_payload('Reminder service not available on Pi.')
        return jsonify(payload), 503

    if request.method == 'GET':
        if assistant_service is not None:
            try:
                reminders = assistant_service.list_reminders()
            except Exception as exc:  # pragma: no cover - external dependency
                logger.error('❌ Assistant reminder fetch error: %s', exc)
                return jsonify({'status': 'error', 'message': 'Failed to fetch reminders'}), 500
        else:
            reminders = reminder_scheduler.list_reminders() if reminder_scheduler else []
        return jsonify({'status': 'success', 'reminders': reminders})

    data = request.get_json(force=True, silent=True) or {}
    message = data.get('message') or data.get('text')
    remind_at = data.get('remind_at') or data.get('time')
    delay_seconds = data.get('delay_seconds') or data.get('delaySeconds')
    delay_minutes = data.get('delay_minutes') or data.get('delayMinutes')
    voice_note = data.get('voice_note') or data.get('voiceNote')

    try:
        if delay_seconds is None and delay_minutes is not None:
            delay_seconds = float(delay_minutes) * 60.0

        if assistant_service is not None:
            reminder = assistant_service.add_reminder(
                message,
                remind_at=remind_at,
                delay_seconds=None if delay_seconds is None else float(delay_seconds),
                voice_note=voice_note,
            )
        else:
            if not message or not message.strip():
                raise ValueError('Reminder message cannot be empty.')

            if remind_at is not None:
                remind_dt = _coerce_datetime(remind_at)
            else:
                if delay_seconds is None:
                    delay_seconds = 60.0
                remind_dt = datetime.utcnow() + timedelta(seconds=float(delay_seconds))

            reminder = reminder_scheduler.add_reminder(
                message.strip(),
                remind_dt,
                voice_note=voice_note,
            )
    except ValueError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 400
    except Exception as exc:  # pragma: no cover - external dependency
        logger.error('❌ Assistant reminder create error: %s', exc)
        return jsonify({'status': 'error', 'message': 'Failed to create reminder'}), 500

    return jsonify({'status': 'success', 'reminder': reminder}), 201


@app.route('/assistant/reminders/<reminder_id>', methods=['DELETE', 'OPTIONS'])
def assistant_delete_reminder(reminder_id: str):
    if request.method == 'OPTIONS':
        return ('', 204)

    if assistant_service is None and reminder_scheduler is None:
        payload = _assistant_offline_payload('Reminder service not available on Pi.')
        return jsonify(payload), 503

    try:
        if assistant_service is not None:
            removed = assistant_service.remove_reminder(reminder_id)
        else:
            removed = reminder_scheduler.remove_reminder(reminder_id) if reminder_scheduler else None
    except Exception as exc:  # pragma: no cover - external dependency
        logger.error('❌ Assistant reminder delete error: %s', exc)
        return jsonify({'status': 'error', 'message': 'Failed to delete reminder'}), 500

    if not removed:
        return jsonify({'status': 'error', 'message': 'Reminder not found'}), 404

    return jsonify({'status': 'success', 'reminder': removed})


@app.route('/assistant/speak', methods=['POST', 'OPTIONS'])
def assistant_speak():
    if request.method == 'OPTIONS':
        return ('', 204)

    data = request.get_json(force=True, silent=True) or {}
    text = (data.get('text') or data.get('message') or '').strip()
    async_mode = bool(data.get('async', True))

    if not text:
        return jsonify({'status': 'error', 'message': 'text is required'}), 400

    if not speak_text(text, async_mode=async_mode):
        return jsonify({'status': 'error', 'message': 'No speech engine available on Pi'}), 503

    return jsonify({'status': 'success', 'spoken_text': text, 'async': async_mode})


@app.route('/assistant/audio_chat', methods=['POST', 'OPTIONS'])
def assistant_audio_chat():
    """One-way audio chat: receive audio from laptop mic and play through Pi speaker"""
    if request.method == 'OPTIONS':
        return ('', 204)

    if not request.files:
        return jsonify({'status': 'error', 'message': 'Audio file is required'}), 400

    file_storage = next(iter(request.files.values()))
    audio_data = file_storage.read()
    
    if not audio_data:
        return jsonify({'status': 'error', 'message': 'Audio file is empty'}), 400

    try:
        # Create temporary file for the audio
        file_path = _write_temp_audio(
            audio_data, 
            file_storage.filename or 'chat_audio.wav',
            file_storage.mimetype
        )
        
        # Play immediately through Pi speaker
        audio_queue.enqueue(file_path)
        
        logger.info('🎤 One-way audio chat: playing received audio through Pi speaker')
        
        return jsonify({
            'status': 'success', 
            'message': 'Audio playing through Pi speaker',
            'file_size': len(audio_data)
        })
        
    except Exception as exc:
        logger.error(f'❌ Audio chat failed: {exc}')
        return jsonify({'status': 'error', 'message': str(exc)}), 500


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
            <h1>🥧 Pi Robot Camera Server (FIXED)</h1>
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
            'Cache-Control': 'no-store, no-cache, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
            'X-Accel-Buffering': 'no'
        }
    )

@app.route('/move', methods=['POST', 'OPTIONS'])
def move_robot():
    """Handle robot movement commands"""
    if request.method == 'OPTIONS':  # CORS preflight
        return ('', 204)
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

if __name__ == '__main__':
    logger.info("🥧 Pi Robot Camera Server Starting (FIXED VERSION)...")
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
        logger.warning("   Run diagnostic: python3 camera_test.py")
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
        try:
            voice_note_manager.shutdown()
        except Exception as exc:  # pragma: no cover - defensive cleanup
            logger.debug('Voice note manager shutdown warning: %s', exc)
        try:
            audio_queue.shutdown()
        except Exception:
            pass
        if reminder_scheduler is not None:
            try:
                reminder_scheduler.shutdown()
            except Exception as exc:  # pragma: no cover - defensive cleanup
                logger.debug('Reminder scheduler shutdown warning: %s', exc)
        if assistant_service is not None:
            try:
                assistant_service.shutdown()
            except Exception as exc:  # pragma: no cover - defensive cleanup
                logger.debug('Assistant shutdown warning: %s', exc)
        if fallback_speaker is not None:
            fallback_speaker.shutdown()
        logger.info("👋 Goodbye!")