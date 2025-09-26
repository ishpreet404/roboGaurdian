#!/usr/bin/env python3
"""Unified orchestrator for Raspberry Pi services.

This helper starts the Flask camera server and the Hindi voice chatbot
side-by-side so the robot exposes a single entry point during demos.

Usage (on Raspberry Pi):

    python3 pi_robot_supervisor.py

The script leaves the original modules untouched and simply coordinates them.
"""
from __future__ import annotations

import signal
import sys
import threading
from contextlib import suppress
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent
_assistant_candidates = [
    ROOT / "raspi-chatbot",
    ROOT / "assistant",
    ROOT,
]
for candidate in _assistant_candidates:
    if candidate.exists():
        sys.path.insert(0, str(candidate))

try:
    import pi_voice_chatbot_single as voice_chatbot  # type: ignore[import-not-found]
except ModuleNotFoundError as exc:  # pragma: no cover - runtime safeguard
    missing_name = getattr(exc, "name", None)
    if missing_name and missing_name != "pi_voice_chatbot_single":
        raise ModuleNotFoundError(
            "pi_voice_chatbot_single dependency missing: install the required "
            f"package '{missing_name}' (for example via 'pip install {missing_name}')."
        ) from exc

    raise ModuleNotFoundError(
        "pi_voice_chatbot_single module not found. Ensure the voice assistant "
        "file is located in 'raspi-chatbot/' or 'assistant/' alongside this "
        "script, or install it on the PYTHONPATH."
    ) from exc

# Importing pi_camera_server instantiates the server object immediately, which is
# acceptable here. We only need the Flask app reference for hosting.
from pi_camera_server import app as camera_app, server as camera_server  # type: ignore  # noqa: E402


class PiRobotSupervisor:
    """Run camera streaming and voice assistant together on a Pi."""

    def __init__(self, *, host: str = "0.0.0.0", port: int = 5000) -> None:
        self.host = host
        self.port = port
        self._camera_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    # ------------------------------------------------------------------
    # Camera server lifecycle
    # ------------------------------------------------------------------
    def start_camera_server(self) -> None:
        if self._camera_thread and self._camera_thread.is_alive():
            return

        def _serve_camera() -> None:
            # Flask's built-in server is sufficient for the Pi. Disable the
            # reloader because we're running from a background thread.
            camera_app.run(
                host=self.host,
                port=self.port,
                debug=False,
                threaded=True,
                use_reloader=False,
            )

        self._camera_thread = threading.Thread(
            target=_serve_camera,
            name="PiCameraServerThread",
            daemon=True,
        )
        self._camera_thread.start()

    def stop_camera_server(self) -> None:
        # The Flask dev server does not expose a graceful shutdown hook, but we
        # can at least free hardware resources.
        with suppress(Exception):  # pragma: no cover - best effort cleanup
            if camera_server.camera:
                camera_server.camera.release()
            if camera_server.uart:
                camera_server.uart.close()

    # ------------------------------------------------------------------
    # Voice interaction
    # ------------------------------------------------------------------
    def run_voice_console(self) -> None:
        print("🎙️  Initialising Chirpy voice assistant…")
        try:
            service = voice_chatbot.build_service()
        except Exception as exc:
            print(f"⚠️ Voice chatbot startup error: {exc}")
            return

        intro = (
            "नमस्ते! मैं Chirpy हूँ। सिस्टम तैयार है और कैमरा सर्वर बैकग्राउंड में चल रहा है। \n"
            "रोबोट को नियंत्रित करने या पूछताछ करने के लिए हिंदी में बात कीजिए। \n"
            "कमान्ड: 'exit' या Ctrl+C से बाहर निकलें।"
        )
        print(f"Assistant: {intro}")
        service.speak_async(intro)

        try:
            while not self._stop_event.is_set():
                try:
                    user_input = input("You: ")
                except EOFError:
                    break

                if user_input.strip().lower() in {"exit", "quit"}:
                    break
                if not user_input.strip():
                    continue

                try:
                    result = service.process_text(user_input)
                except Exception as exc:  # noqa: BLE001 - surface helpful error
                    print(f"🚨 GitHub Models API error: {exc}")
                    continue

                reply = result.get("reply", "") if isinstance(result, dict) else ""
                if not reply:
                    print("⚠️ Voice chatbot returned an empty reply.")
                    continue

                print(f"Assistant: {reply}")
        except KeyboardInterrupt:
            print("\n🔚 Keyboard interrupt received. Shutting down supervisor…")
        finally:
            with suppress(Exception):
                service.shutdown()

    # ------------------------------------------------------------------
    # Orchestration entry point
    # ------------------------------------------------------------------
    def run(self) -> None:
        self.start_camera_server()

        def _handle_sigint(signum, frame):  # noqa: ARG001 - required signature
            self._stop_event.set()

        signal.signal(signal.SIGINT, _handle_sigint)
        signal.signal(signal.SIGTERM, _handle_sigint)

        try:
            self.run_voice_console()
        finally:
            self._stop_event.set()
            self.stop_camera_server()
            print("👋 Supervisor exited cleanly.")


def main() -> None:
    supervisor = PiRobotSupervisor()
    supervisor.run()


if __name__ == "__main__":
    main()
