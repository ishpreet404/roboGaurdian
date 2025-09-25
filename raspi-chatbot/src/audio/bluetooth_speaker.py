"""Bluetooth speaker helper utilities tailored for Raspberry Pi deployments.

The implementation prefers using the system's default audio sink once the
speaker is connected. When a Bluetooth device identifier is supplied we
attempt to establish the connection through ``bluetoothctl`` so that text-to-
speech playback is routed to the paired speaker.
"""
from __future__ import annotations

import shutil
import subprocess
import time
from typing import Optional

import pyttsx3


class BluetoothSpeaker:
    """Thin wrapper around ``pyttsx3`` with optional Bluetooth automation."""

    def __init__(
        self,
        speaker_identifier: Optional[str] = None,
        *,
        voice_rate: int = 175,
        voice_volume: float = 1.0,
    ) -> None:
        self.speaker_identifier = speaker_identifier
        self.voice_rate = voice_rate
        self.voice_volume = max(0.0, min(voice_volume, 1.0))
        self._engine = pyttsx3.init()
        self._engine.setProperty("rate", self.voice_rate)
        self._engine.setProperty("volume", self.voice_volume)
        self._bluetoothctl = shutil.which("bluetoothctl")
        self._connected = False

    # ------------------------------------------------------------------
    # Bluetooth helpers
    # ------------------------------------------------------------------
    def _resolve_mac(self) -> Optional[str]:
        """Resolve a user-friendly name to a MAC address if possible."""

        if not self.speaker_identifier:
            return None

        if ":" in self.speaker_identifier:
            # Already looks like a MAC address
            return self.speaker_identifier

        if not self._bluetoothctl:
            return None

        try:
            result = subprocess.run(
                [self._bluetoothctl, "devices"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return None

        for line in result.stdout.splitlines():
            parts = line.strip().split(" ", 2)
            if len(parts) == 3 and parts[2] == self.speaker_identifier:
                return parts[1]

        return None

    def connect(self, *, timeout: int = 10) -> bool:
        """Attempt to connect to the configured Bluetooth speaker."""

        if not self.speaker_identifier:
            print("🔊 Using default audio output (no Bluetooth identifier supplied).")
            self._connected = True
            return True

        mac = self._resolve_mac()
        if not mac:
            print(
                "⚠️  Unable to resolve Bluetooth device. Ensure the speaker is paired "
                "and provide either its MAC address or the exact advertised name."
            )
            return False

        if not self._bluetoothctl:
            print("⚠️  bluetoothctl not found. Install bluez-utils or connect manually.")
            return False

        try:
            subprocess.run(
                [self._bluetoothctl, "connect", mac],
                check=True,
                timeout=timeout,
                capture_output=True,
                text=True,
            )
            # Give PulseAudio/ALSA a moment to switch sinks
            time.sleep(1.0)
            self._connected = True
            print(f"✅ Connected to Bluetooth speaker ({mac}).")
            return True
        except subprocess.TimeoutExpired:
            print("⚠️  bluetoothctl connect command timed out.")
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.strip() if exc.stderr else "unknown error"
            print(f"⚠️  Failed to connect to Bluetooth speaker: {stderr}")

        return False

    def disconnect(self) -> None:
        """Disconnect the Bluetooth speaker if we connected it."""

        if not self.speaker_identifier or not self._bluetoothctl or not self._connected:
            return

        mac = self._resolve_mac()
        if not mac:
            return

        try:
            subprocess.run(
                [self._bluetoothctl, "disconnect", mac],
                check=True,
                timeout=5,
                capture_output=True,
                text=True,
            )
            print(f"🔌 Disconnected Bluetooth speaker ({mac}).")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass
        finally:
            self._connected = False

    # ------------------------------------------------------------------
    # Speech synthesis helpers
    # ------------------------------------------------------------------
    def speak(self, text: str) -> None:
        """Convert text to speech via ``pyttsx3``."""

        if not text:
            return

        self._engine.say(text)
        self._engine.runAndWait()

    def set_voice(self, language_code: Optional[str] = None) -> None:
        """Attempt to switch voice based on a language code (e.g. ``en``)."""

        if not language_code:
            return

        language_code = language_code.lower()
        for voice in self._engine.getProperty("voices"):
            languages = [
                lang.decode("utf-8", "ignore") if isinstance(lang, bytes) else lang
                for lang in voice.languages
            ]
            if any(language_code in lang.lower() for lang in languages):
                self._engine.setProperty("voice", voice.id)
                break

    def is_connected(self) -> bool:
        return self._connected

    def __enter__(self) -> "BluetoothSpeaker":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.disconnect()
        self._engine.stop()
        return False