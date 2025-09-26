#!/usr/bin/env python3
"""Windows orchestration layer exposing an HTTP bridge for the React UI.

This file keeps the original `windows_ai_controller.py` untouched while making
its rich functionality available through a lightweight Flask API that the new
frontend can consume.
"""
from __future__ import annotations

import collections
import threading
import time
from datetime import datetime
from typing import Any, Deque, Dict, List

from flask import Flask, jsonify, request

from windows_ai_controller import WindowsAIController


class ReactBridgeWindowsController(WindowsAIController):
    """Subclass that mirrors internal state to share with the web dashboard."""

    def __init__(self) -> None:  # type: ignore[override]
        self.bridge_alerts: Deque[Dict[str, Any]] = collections.deque(maxlen=30)
        self.bridge_events: Deque[Dict[str, Any]] = collections.deque(maxlen=60)
        self.voice_ready = False
        super().__init__()
        # Mark voice ready after GUI startup; base class initialises TTS and UI.
        self.voice_ready = True

    def _timestamp(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
                    "alerts": list(controller.bridge_alerts),
                    "operating_mode": controller.operating_mode,
                    "mode_metadata": mode_metadata,
                    "watchdog_alarm_active": getattr(controller, "_watchdog_alarm_active", False),
                    "available_modes": controller.get_available_modes(),
                }
            return jsonify(data)

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
