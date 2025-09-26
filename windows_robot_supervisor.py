#!/usr/bin/env python3
"""Windows orchestration layer exposing an HTTP bridge for the React UI.

This file keeps the original `windows_ai_controller.py` untouched while making
its rich functionality available through a lightweight Flask API that the new
frontend can consume.
"""
from __future__ import annotations

import collections
import logging
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional

import requests
from flask import Flask, jsonify, request

ROOT = Path(__file__).resolve().parent
_assistant_paths = [ROOT / "raspi-chatbot", ROOT / "assistant", ROOT]
for _path in _assistant_paths:
    if _path.exists():
        sys.path.insert(0, str(_path))

try:  # pragma: no cover - optional import on Windows PC
    from pi_voice_chatbot_single import VoiceChatbotService, _prepare_for_speech
except Exception:  # pragma: no cover - fallback when assistant not present
    VoiceChatbotService = None  # type: ignore

    def _prepare_for_speech(text: str) -> str:  # type: ignore
        return text

from windows_ai_controller import WindowsAIController


logger = logging.getLogger(__name__)


if VoiceChatbotService is not None:

    class RemoteVoiceChatbotService(VoiceChatbotService):  # type: ignore[misc]
        """Voice service variant that forwards speech to a remote speaker."""

        def __init__(self, speak_callback):
            self._remote_speaker = speak_callback
            super().__init__(enable_speaker=False)

        def speak_async(self, text: str) -> None:  # type: ignore[override]
            if not text:
                return
            try:
                cleaned = _prepare_for_speech(text)
                self._remote_speaker(cleaned)
            except Exception as exc:  # pragma: no cover - network/hardware specific
                logger.warning("Remote speech dispatch failed: %s", exc)

else:  # pragma: no cover - only hit when assistant module missing entirely

    class RemoteVoiceChatbotService:  # type: ignore[misc]
        def __init__(self, *_args, **_kwargs) -> None:
            raise RuntimeError(
                "Voice assistant module missing. Copy 'raspi-chatbot' to the Windows machine "
                "or install pi_voice_chatbot_single before starting the supervisor."
            )


class ReactBridgeWindowsController(WindowsAIController):
    """Subclass that mirrors internal state to share with the web dashboard."""

    def __init__(self) -> None:  # type: ignore[override]
        self.bridge_alerts: Deque[Dict[str, Any]] = collections.deque(maxlen=30)
        self.bridge_events: Deque[Dict[str, Any]] = collections.deque(maxlen=60)
        self.assistant_history: Deque[Dict[str, Any]] = collections.deque(maxlen=120)
        self.assistant_lock = threading.Lock()
        self.voice_ready = False
        self.voice_error: Optional[str] = None
        self.voice_service: Optional[RemoteVoiceChatbotService] = None
        self.last_speaker_status: Optional[Dict[str, Any]] = None
        super().__init__()
        self._init_voice_service()

    def _timestamp(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ------------------------------------------------------------------
    # Voice assistant helpers
    # ------------------------------------------------------------------
    def _init_voice_service(self) -> None:
        if VoiceChatbotService is None:
            self.voice_ready = False
            self.voice_error = (
                "Voice assistant module missing on Windows. Sync 'raspi-chatbot' folder "
                "or install pi_voice_chatbot_single.py"
            )
            logger.warning(self.voice_error)
            return

        try:
            self.voice_service = RemoteVoiceChatbotService(self._send_to_pi_speaker)
            self.voice_ready = True
            self.voice_error = None
            logger.info("🧠 Windows voice assistant initialised (remote speaker mode)")
        except Exception as exc:  # pragma: no cover - setup specific
            self.voice_service = None
            self.voice_ready = False
            self.voice_error = str(exc)
            logger.error("Voice assistant startup failed on Windows: %s", exc)

    def _send_to_pi_speaker(self, text: str, *, async_mode: bool = True) -> bool:
        cleaned = (text or "").strip()
        if not cleaned:
            return False

        url = f"{self.PI_BASE_URL.rstrip('/')}/assistant/speak"
        payload = {"text": cleaned, "async": async_mode}
        try:
            response = requests.post(url, json=payload, timeout=6)
            if response.status_code >= 400:
                try:
                    body = response.json()
                    message = body.get("message") or body.get("details")
                except ValueError:
                    message = response.text
                raise RuntimeError(message or f"HTTP {response.status_code}")
        except Exception as exc:  # pragma: no cover - network specific
            self.last_speaker_status = {
                "success": False,
                "error": str(exc),
                "timestamp": datetime.utcnow().isoformat(),
            }
            self.bridge_alerts.appendleft(
                {
                    "id": f"speaker-error-{time.time():.0f}",
                    "title": "Speaker relay failed",
                    "message": str(exc),
                    "level": "warning",
                    "timestamp": self._timestamp(),
                }
            )
            logger.warning("Pi speaker relay failed: %s", exc)
            return False

        self.last_speaker_status = {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
        }
        return True

    def handle_assistant_exchange(
        self,
        text: str,
        *,
        speak: bool = True,
        history_limit: int = 40,
    ) -> Dict[str, Any]:
        if not self.voice_service:
            raise RuntimeError(self.voice_error or "Voice assistant unavailable on Windows")

        cleaned = (text or "").strip()
        if not cleaned:
            raise ValueError("Message cannot be empty")

        with self.assistant_lock:
            result = self.voice_service.process_text(cleaned, speak_reply=speak)
            reply = result.get("reply", "")
            timestamp = result.get("timestamp") or datetime.utcnow().isoformat()

            user_entry = {
                "role": "user",
                "content": cleaned,
                "timestamp": timestamp,
            }
            self.assistant_history.append(user_entry)

            if reply:
                assistant_entry = {
                    "role": "assistant",
                    "content": reply,
                    "timestamp": result.get("timestamp") or datetime.utcnow().isoformat(),
                }
                self.assistant_history.append(assistant_entry)

            history = list(self.assistant_history)[-history_limit:]

        return {
            "reply": reply,
            "timestamp": result.get("timestamp") or datetime.utcnow().isoformat(),
            "history": history,
            "spoken": speak and bool(reply),
            "speaker_status": self.last_speaker_status,
        }

    def get_assistant_status_snapshot(self) -> Dict[str, Any]:
        with self.assistant_lock:
            history = list(self.assistant_history)
        with self.mode_lock:
            mode = self.operating_mode
            metadata = dict(self.mode_metadata)
            watchdog = getattr(self, "_watchdog_alarm_active", False)

        reminders: List[Dict[str, Any]] = []
        if self.voice_service:
            try:
                reminders = self.voice_service.list_reminders()
            except Exception as exc:  # pragma: no cover - scheduler specific
                logger.warning("Failed to fetch reminders from voice assistant: %s", exc)

        return {
            "status": "online" if self.voice_ready else "offline",
            "voice_ready": self.voice_ready,
            "voice_error": self.voice_error,
            "history": history,
            "available_modes": self.get_available_modes(),
            "mode": mode,
            "mode_metadata": metadata,
            "watchdog_alarm_active": watchdog,
            "pi_speaker_status": self.last_speaker_status,
            "reminders": reminders,
        }

    # ------------------------------------------------------------------
    # Hooks for alerts and logs
    # ------------------------------------------------------------------
    def trigger_crying_alert(self):  # type: ignore[override]
        super().trigger_crying_alert()
        self.bridge_alerts.appendleft(
            {
                "id": f"crying-{time.time():.0f}",
                "title": "Crying detected",
                "message": "Distress levels exceeded threshold in camera feed.",
                "level": "warning",
                "timestamp": self._timestamp(),
            }
        )

    def log(self, message):  # type: ignore[override]
        super().log(message)
        self.bridge_events.appendleft(
            {
                "id": f"log-{time.time():.0f}",
                "title": "System log",
                "details": message,
                "timestamp": self._timestamp(),
                "level": "info",
            }
        )

    def register_manual_alert(self, title: str, message: str, *, level: str = "info") -> None:
        self.bridge_alerts.appendleft(
            {
                "id": f"manual-{time.time():.0f}",
                "title": title,
                "message": message,
                "level": level,
                "timestamp": self._timestamp(),
            }
        )


class WindowsRobotSupervisor:
    """Expose the Windows AI controller data through a REST API."""

    def __init__(self, *, host: str = "0.0.0.0", port: int = 5050) -> None:
        self.host = host
        self.port = port
        self.controller = ReactBridgeWindowsController()
        self.app = Flask(__name__)
        self._api_thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._configure_routes()

    # ------------------------------------------------------------------
    # Flask routes
    # ------------------------------------------------------------------
    def _configure_routes(self) -> None:
        app = self.app
        controller = self.controller

        @app.after_request
        def add_cors_headers(response):  # type: ignore[override]
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
            return response

        @app.route("/api/status", methods=["GET"])
        def status() -> Any:
            with self._lock:
                mode_metadata = dict(controller.mode_metadata)
                data = {
                    "pi_base_url": controller.PI_BASE_URL,
                    "pi_connected": bool(getattr(controller, "pi_connected", False)),
                    "model_loaded": bool(getattr(controller, "model_loaded", False)),
                    "fps": round(getattr(controller, "current_fps", 0.0), 2),
                    "commands": getattr(controller, "commands_sent", 0),
                    "auto_tracking": bool(controller.auto_tracking.get()),
                    "voice_ready": controller.voice_ready,
                    "voice_error": controller.voice_error,
                    "alerts": list(controller.bridge_alerts),
                    "operating_mode": controller.operating_mode,
                    "mode_metadata": mode_metadata,
                    "watchdog_alarm_active": getattr(controller, "_watchdog_alarm_active", False),
                    "available_modes": controller.get_available_modes(),
                    "assistant_history": list(controller.assistant_history),
                    "pi_speaker_status": controller.last_speaker_status,
                }
            return jsonify(data)

        @app.route("/api/assistant/status", methods=["GET"])
        def assistant_status() -> Any:
            with self._lock:
                snapshot = controller.get_assistant_status_snapshot()
            return jsonify(snapshot)

        @app.route("/api/assistant/message", methods=["POST", "OPTIONS"])
        def assistant_message() -> Any:
            if request.method == "OPTIONS":
                return ("", 204)

            payload = request.get_json(force=True, silent=True) or {}
            text = (payload.get("text") or payload.get("message") or "").strip()
            speak = bool(payload.get("speak", True))
            history_limit = int(payload.get("history_limit", 40))

            if not text:
                return jsonify({"status": "error", "message": "text is required"}), 400

            with self._lock:
                if not controller.voice_service:
                    return (
                        jsonify(
                            {
                                "status": "offline",
                                "message": controller.voice_error or "Voice assistant not available on Windows",
                            }
                        ),
                        503,
                    )

            try:
                result = controller.handle_assistant_exchange(text, speak=speak, history_limit=history_limit)
            except ValueError as exc:  # noqa: BLE001
                return jsonify({"status": "error", "message": str(exc)}), 400
            except Exception as exc:  # noqa: BLE001
                logger.error("Assistant processing failed: %s", exc)
                return jsonify({"status": "error", "message": str(exc)}), 500

            return jsonify({"status": "success", **result})

        def _proxy_pi_request(
            method: str,
            path: str,
            *,
            json_payload: Optional[Dict[str, Any]] = None,
            data_payload: Optional[Dict[str, Any]] = None,
            files_payload: Optional[Dict[str, Any]] = None,
            timeout: float = 10.0,
        ) -> Any:
            url = f"{controller.PI_BASE_URL.rstrip('/')}{path}"
            try:
                response = requests.request(
                    method,
                    url,
                    json=json_payload,
                    data=data_payload,
                    files=files_payload,
                    timeout=timeout,
                )
            except Exception as exc:  # pragma: no cover - network specific
                logger.error("Pi proxy request to %s failed: %s", url, exc)
                return jsonify({"status": "error", "message": str(exc)}), 502

            try:
                body = response.json()
            except ValueError:
                body = {"status": "error", "message": response.text or "Pi response was not JSON"}

            return jsonify(body), response.status_code

        @app.route("/api/assistant/voice-note", methods=["POST", "OPTIONS"])
        def assistant_voice_note() -> Any:
            if request.method == "OPTIONS":
                return ("", 204)

            files: Optional[Dict[str, Any]] = None
            json_payload: Optional[Dict[str, Any]] = None
            form_payload: Optional[Dict[str, Any]] = None

            if request.files:
                file = next(iter(request.files.values()))
                data = file.read()
                if not data:
                    return jsonify({"status": "error", "message": "Uploaded file is empty"}), 400
                files = {
                    "file": (
                        file.filename or "voice-note.wav",
                        data,
                        file.mimetype or "application/octet-stream",
                    )
                }

                delay_value = request.form.get("delay_seconds") or request.form.get("delayMinutes")
                if delay_value is not None:
                    try:
                        form_payload = {"delay_seconds": float(delay_value)}
                    except ValueError:
                        return jsonify({"status": "error", "message": "Invalid delay value"}), 400
            else:
                json_payload = request.get_json(force=True, silent=True) or {}
                if not any(key in json_payload for key in ("audio", "data", "voice_note", "voiceNote")):
                    return jsonify({"status": "error", "message": "Audio payload missing"}), 400

            return _proxy_pi_request(
                "POST",
                "/assistant/voice_note",
                json_payload=json_payload,
                data_payload=form_payload,
                files_payload=files,
                timeout=15.0,
            )

        @app.route("/api/assistant/reminders", methods=["GET", "POST", "OPTIONS"])
        def assistant_reminders() -> Any:
            if request.method == "OPTIONS":
                return ("", 204)

            with self._lock:
                service = controller.voice_service
                voice_error = controller.voice_error

            if not service:
                if request.method == "GET":
                    return _proxy_pi_request("GET", "/assistant/reminders", timeout=10.0)

                payload = request.get_json(force=True, silent=True) or {}
                return _proxy_pi_request("POST", "/assistant/reminders", json_payload=payload, timeout=15.0)

            if request.method == "GET":
                try:
                    with controller.assistant_lock:
                        reminders = service.list_reminders()
                except Exception as exc:  # noqa: BLE001
                    logger.error("Failed to fetch reminders: %s", exc)
                    return jsonify({"status": "error", "message": "Failed to fetch reminders"}), 500
                return jsonify({"status": "success", "reminders": reminders})

            data = request.get_json(force=True, silent=True) or {}
            message = data.get("message") or data.get("text")
            remind_at = data.get("remind_at") or data.get("time")
            delay_seconds = data.get("delay_seconds")
            if delay_seconds is None:
                delay_minutes = data.get("delay_minutes")
                if delay_minutes is not None:
                    try:
                        delay_seconds = float(delay_minutes) * 60.0
                    except (TypeError, ValueError):
                        return jsonify({"status": "error", "message": "Invalid delay_minutes value"}), 400

            voice_note = data.get("voice_note") or data.get("voiceNote")

            try:
                with controller.assistant_lock:
                    reminder = service.add_reminder(
                        message,
                        remind_at=remind_at,
                        delay_seconds=delay_seconds,
                        voice_note=voice_note,
                    )
            except ValueError as exc:  # noqa: BLE001
                return jsonify({"status": "error", "message": str(exc)}), 400
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to create reminder: %s", exc)
                return jsonify({"status": "error", "message": "Failed to create reminder"}), 500

            return jsonify({"status": "success", "reminder": reminder}), 201

        @app.route("/api/assistant/reminders/<reminder_id>", methods=["DELETE", "OPTIONS"])
        def assistant_delete_reminder(reminder_id: str) -> Any:
            if request.method == "OPTIONS":
                return ("", 204)

            with self._lock:
                service = controller.voice_service
                voice_error = controller.voice_error

            if not service:
                return _proxy_pi_request("DELETE", f"/assistant/reminders/{reminder_id}", timeout=10.0)

            try:
                with controller.assistant_lock:
                    removed = service.remove_reminder(reminder_id)
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to delete reminder: %s", exc)
                return jsonify({"status": "error", "message": "Failed to delete reminder"}), 500

            if not removed:
                return jsonify({"status": "error", "message": "Reminder not found"}), 404

            return jsonify({"status": "success", "reminder": removed})

        @app.route("/api/assistant/audio-chat", methods=["POST", "OPTIONS"])
        def assistant_audio_chat() -> Any:
            """One-way audio chat: send audio from laptop mic to Pi speaker"""
            if request.method == "OPTIONS":
                return ("", 204)

            if not request.files:
                return jsonify({"status": "error", "message": "Audio file is required"}), 400

            file = next(iter(request.files.values()))
            data = file.read()
            if not data:
                return jsonify({"status": "error", "message": "Audio file is empty"}), 400

            files = {
                "file": (
                    file.filename or "mic_audio.wav",
                    data,
                    file.mimetype or "audio/wav",
                )
            }

            return _proxy_pi_request(
                "POST",
                "/assistant/audio_chat",
                files_payload=files,
                timeout=15.0,
            )

        @app.route("/api/command", methods=["POST", "OPTIONS"])
        def send_command() -> Any:
            if request.method == "OPTIONS":
                return ("", 204)
            payload = request.get_json(force=True, silent=True) or {}
            command = payload.get("command")
            if not command:
                return jsonify({"status": "error", "message": "command missing"}), 400

            try:
                with self._lock:
                    controller.send_command(command, auto=False, force=True)
                    controller.register_manual_alert(
                        "Manual command dispatched",
                        f"Sent '{command}' to robot via Windows bridge",
                        level="info",
                    )
            except Exception as exc:  # noqa: BLE001 - propagate message
                return (
                    jsonify({"status": "error", "message": str(exc)}),
                    500,
                )

            return jsonify({"status": "success"})

        @app.route("/api/connect", methods=["POST", "OPTIONS"])
        def update_pi_url() -> Any:
            if request.method == "OPTIONS":
                return ("", 204)
            payload = request.get_json(force=True, silent=True) or {}
            new_url = payload.get("pi_base_url")
            if not new_url:
                return jsonify({"status": "error", "message": "pi_base_url missing"}), 400

            with self._lock:
                controller.PI_BASE_URL = new_url
                controller.register_manual_alert(
                    "Pi endpoint updated",
                    f"New URL: {new_url}",
                    level="info",
                )
            return jsonify({"status": "success"})

        @app.route("/api/events", methods=["GET"])
        def events() -> Any:
            with self._lock:
                events_payload = list(controller.bridge_events)
            return jsonify({"events": events_payload})

        @app.route("/api/mode", methods=["GET", "POST"])
        def operating_mode() -> Any:
            if request.method == "GET":
                with self._lock:
                    return jsonify(
                        {
                            "mode": controller.operating_mode,
                            "metadata": dict(controller.mode_metadata),
                            "available_modes": controller.get_available_modes(),
                            "watchdog_alarm_active": getattr(controller, "_watchdog_alarm_active", False),
                        }
                    )

            payload = request.get_json(force=True, silent=True) or {}
            action = (payload.get("action") or "").strip().lower()

            try:
                if action == "silence_alarm":
                    with self._lock:
                        controller.silence_watchdog_alarm()
                        response_data = {
                            "mode": controller.operating_mode,
                            "metadata": dict(controller.mode_metadata),
                            "watchdog_alarm_active": getattr(controller, "_watchdog_alarm_active", False),
                        }
                    return jsonify({"status": "success", **response_data})

                mode = payload.get("mode")
                if not mode:
                    return jsonify({"status": "error", "message": "mode is required"}), 400

                metadata = payload.get("metadata")
                if metadata is not None and not isinstance(metadata, dict):
                    return jsonify({"status": "error", "message": "metadata must be an object"}), 400

                summary = payload.get("summary")
                speak_summary = bool(payload.get("speak_summary"))

                with self._lock:
                    result = controller.set_operating_mode(
                        mode,
                        metadata=metadata or {},
                        summary=summary,
                        speak_summary=speak_summary,
                    )
                    result.update(
                        {
                            "available_modes": controller.get_available_modes(),
                            "watchdog_alarm_active": getattr(controller, "_watchdog_alarm_active", False),
                        }
                    )
                return jsonify({"status": "success", **result})
            except ValueError as exc:  # noqa: BLE001
                return jsonify({"status": "error", "message": str(exc)}), 400
            except Exception as exc:  # noqa: BLE001
                return jsonify({"status": "error", "message": str(exc)}), 500

    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------
    def start_api(self) -> None:
        if self._api_thread and self._api_thread.is_alive():
            return

        def _serve() -> None:
            self.app.run(
                host=self.host,
                port=self.port,
                debug=False,
                use_reloader=False,
                threaded=True,
            )

        self._api_thread = threading.Thread(
            target=_serve,
            name="WindowsBridgeAPIThread",
            daemon=True,
        )
        self._api_thread.start()

    def run(self) -> None:
        print("🌐 Starting Windows bridge API…")
        self.start_api()
        print(f"✅ Bridge ready at http://localhost:{self.port}/api/status")
        print("🧠 Launching Windows AI Control Center UI…")
        try:
            self.controller.run()
        finally:
            print("👋 Windows supervisor shutting down.")


def main() -> None:
    WindowsRobotSupervisor().run()


if __name__ == "__main__":
    main()