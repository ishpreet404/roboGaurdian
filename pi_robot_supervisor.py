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
import threading
from contextlib import suppress
from typing import Optional

import pi_voice_chatbot_single as voice_chatbot

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
        # build_app may raise SystemExit on missing env or return either
        # (convo_manager, speaker, disconnect_on_exit) or (convo_manager, speaker)
        try:
            result = voice_chatbot.build_app()
        except SystemExit as exc:  # expected when env/config is missing
            print(f"⚠️ Voice chatbot startup error: {exc}")
            return
        except Exception as exc:  # unexpected errors
            print(f"⚠️ Unexpected error while initializing voice chatbot: {exc}")
            return

        # Normalize return value to (convo_manager, speaker, disconnect_on_exit)
        disconnect_on_exit = False
        if isinstance(result, tuple):
            if len(result) == 3:
                convo_manager, speaker, disconnect_on_exit = result
            elif len(result) == 2:
                convo_manager, speaker = result
                disconnect_on_exit = False
            else:
                print("⚠️ build_app() returned unexpected number of values. Aborting voice console.")
                return
        else:
            print("⚠️ build_app() did not return a tuple. Aborting voice console.")
            return

        intro = (
            "नमस्ते! मैं Chirpy हूँ। सिस्टम तैयार है और कैमरा सर्वर बैकग्राउंड में चल रहा है। \n"
            "रोबोट को नियंत्रित करने या पूछताछ करने के लिए हिंदी में बात कीजिए। \n"
            "कमान्ड: 'exit' या Ctrl+C से बाहर निकलें।"
        )
        print(f"Assistant: {intro}")
        speaker.speak(voice_chatbot._prepare_for_speech(intro))

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
                    reply = convo_manager.process_input(user_input)
                except Exception as exc:  # noqa: BLE001 - surface helpful error
                    print(f"🚨 GitHub Models API error: {exc}")
                    continue

                print(f"Assistant: {reply}")
                speaker.speak(voice_chatbot._prepare_for_speech(reply))
        except KeyboardInterrupt:
            print("\n🔚 Keyboard interrupt received. Shutting down supervisor…")
        finally:
            if disconnect_on_exit:
                speaker.disconnect()
            speaker._engine.stop()  # type: ignore[attr-defined]

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
