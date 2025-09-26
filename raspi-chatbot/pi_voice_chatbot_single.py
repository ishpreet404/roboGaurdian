#!/usr/bin/env python3
"""Self-contained Raspberry Pi voice chatbot with reminder scheduler and API-friendly service.

This module now exposes a :class:`VoiceChatbotService` that can be imported by
other applications (for example, the Flask camera server) while still offering a
CLI entry point for quick tests. The chatbot speaks in Hindi (Devanagari script)
by default and uses the GitHub Models API for responses.

Usage (CLI):
    python3 pi_voice_chatbot_single.py

Usage (import):
    from pi_voice_chatbot_single import VoiceChatbotService
    service = VoiceChatbotService()
    service.process_text("नमस्ते")
    service.add_reminder("पानी पीना है", remind_at="2025-09-26T18:00:00")
"""
from __future__ import annotations

import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:  # Prefer python-dotenv when installed for .env parsing support.
    from dotenv import load_dotenv as _dotenv_load  # type: ignore
except Exception:  # pragma: no cover - fallback applies when dependency missing
    _dotenv_load = None  # type: ignore

import requests  # type: ignore
import pyttsx3  # type: ignore


# ---------------------------------------------------------------------------
# Environment helpers
# ---------------------------------------------------------------------------
def _load_dotenv(dotenv_path: Optional[str] = None) -> bool:
    if callable(_dotenv_load) and _dotenv_load is not _load_dotenv:
        return bool(_dotenv_load(dotenv_path))

    path = Path(dotenv_path or ".env")
    if not path.exists():
        return False

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key:
            os.environ.setdefault(key, value.strip().strip('"\''))
    return True


def _env(key: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(key)
    if value is None or value == "":
        return default
    return value


def _env_bool(key: str, default: bool = False) -> bool:
    raw = _env(key)
    if raw is None:
        return default

    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _prepare_for_speech(text: str) -> str:
    """Strip conversational markdown so the TTS engine sounds natural."""

    if not text:
        return text

    cleaned = text
    cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"__(.*?)__", r"\1", cleaned)
    cleaned = re.sub(r"\*(.*?)\*", r"\1", cleaned)
    cleaned = re.sub(r"_(.*?)_", r"\1", cleaned)
    cleaned = re.sub(r"`{1,3}(.*?)`{1,3}", r"\1", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", cleaned)
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", cleaned)
    cleaned = re.sub(r"<[^>]+>", "", cleaned)
    cleaned = re.sub(r"^\s*[-*+]\s+", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"^\s*#+\s+", "", cleaned, flags=re.MULTILINE)
    cleaned = cleaned.replace("**", "").replace("__", "")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


# ---------------------------------------------------------------------------
# GitHub Models client and conversation state
# ---------------------------------------------------------------------------
class GitHubModelClient:
    """Small helper around the GitHub Models chat completions endpoint."""

    def __init__(
        self,
        endpoint: str,
        model: str,
        api_key: str,
        *,
        request_timeout: int = 30,
        temperature: float = 0.7,
        max_tokens: int = 600,
    ) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.request_timeout = request_timeout
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._session = requests.Session()

    def get_chat_completion(self, messages: Iterable[Dict[str, str]], **overrides: Any) -> str:
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": list(messages),
            "temperature": overrides.get("temperature", self.temperature),
            "max_tokens": overrides.get("max_tokens", self.max_tokens),
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        url = f"{self.endpoint}/chat/completions"
        response = self._session.post(
            url,
            headers=headers,
            json=payload,
            timeout=self.request_timeout,
        )

        if response.status_code != 200:
            try:
                error_detail = response.json()
            except ValueError:
                error_detail = {"message": response.text}
            raise RuntimeError(
                f"GitHub Models API error ({response.status_code}): {error_detail}"
            )

        data = response.json()
        choices: List[Dict[str, Any]] = data.get("choices", [])
        if not choices:
            raise RuntimeError("GitHub Models API returned no choices.")

        message: Optional[Dict[str, Any]] = choices[0].get("message")
        if not message or "content" not in message:
            raise RuntimeError("GitHub Models API response missing message content.")

        return str(message["content"]).strip()


class StateStore:
    """In-memory conversation history storage."""

    def __init__(self) -> None:
        self._state: Dict[str, Any] = {}

    def save_state(self, conversation_id: str, state_data: Any) -> None:
        self._state[conversation_id] = state_data

    def load_state(self, conversation_id: str, *, default: Optional[Any] = None) -> Any:
        return self._state.get(conversation_id, default)

    def clear_state(self, conversation_id: str) -> None:
        self._state.pop(conversation_id, None)

    def list_conversations(self) -> Iterable[str]:
        return self._state.keys()


Message = Dict[str, str]


class ConvoManager:
    """High-level conversation manager for chat-based interactions."""

    def __init__(
        self,
        state_store: StateStore,
        github_model_client: GitHubModelClient,
        *,
        conversation_id: str = "default",
        system_prompt: str = "You are a helpful assistant.",
        history_limit: int = 20,
    ) -> None:
        self.state_store = state_store
        self.github_model_client = github_model_client
        self.conversation_id = conversation_id
        self.system_prompt = system_prompt
        self.history_limit = max(2, history_limit)

        stored_messages = self.state_store.load_state(conversation_id, default=None)
        if stored_messages:
            self.messages: List[Message] = list(stored_messages)
        else:
            self.messages = [{"role": "system", "content": self.system_prompt}]

    def process_input(self, user_input: str) -> str:
        self._log("User", user_input)
        self.messages.append({"role": "user", "content": user_input})
        self._trim_history()

        assistant_reply = self.github_model_client.get_chat_completion(self.messages)
        self.messages.append({"role": "assistant", "content": assistant_reply})
        self._trim_history()

        self._persist()
        self._log("Chatbot", assistant_reply)
        return assistant_reply

    def _trim_history(self) -> None:
        system = self.messages[0]
        recent = self.messages[-self.history_limit :]
        self.messages = [system, *recent]

    def _persist(self) -> None:
        self.state_store.save_state(self.conversation_id, self.messages)

    @staticmethod
    def _log(speaker: str, message: str) -> None:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {speaker}: {message}")

    def add_assistant_message(self, content: str) -> None:
        if not content:
            return
        self.messages.append({"role": "assistant", "content": content})
        self._trim_history()
        self._persist()


# ---------------------------------------------------------------------------
# Bluetooth & speech helpers
# ---------------------------------------------------------------------------
class BluetoothSpeaker:
    """Thin wrapper around pyttsx3 with optional Bluetooth automation."""

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

    def _resolve_mac(self) -> Optional[str]:
        if not self.speaker_identifier:
            return None

        if ":" in self.speaker_identifier:
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

    def speak(self, text: str) -> None:
        if not text:
            return

        self._engine.say(text)
        self._engine.runAndWait()

    def set_voice(self, language_code: Optional[str] = None) -> None:
        if not language_code:
            return

        language_code = language_code.lower()
        normalized = language_code.replace("-", "_")
        parts = normalized.split("_", 1)
        base_lang = parts[0]
        region = parts[1] if len(parts) > 1 else None

        keywords: List[str] = []

        def _add_keyword(value: Optional[str]) -> None:
            if value and value not in keywords:
                keywords.append(value)

        _add_keyword(normalized)
        _add_keyword(normalized.replace("_", "-"))
        _add_keyword(base_lang)
        _add_keyword(region)

        if base_lang == "hi":
            for extra in ("hin", "hindi", "भारतीय", "india", "indian"):
                _add_keyword(extra)
        elif base_lang == "en":
            for extra in ("en_in", "en-gb", "indian", "india"):
                _add_keyword(extra)

        selected_voice = None
        voices = self._engine.getProperty("voices")
        for voice in voices:
            languages = [
                lang.decode("utf-8", "ignore") if isinstance(lang, bytes) else str(lang)
                for lang in voice.languages
            ]
            haystack = {
                voice.id.lower(),
                voice.name.lower() if hasattr(voice, "name") else "",
                *[lang.lower() for lang in languages],
            }

            if any(
                keyword in entry
                for keyword in keywords
                for entry in haystack
            ):
                selected_voice = voice.id
                break

        if selected_voice:
            self._engine.setProperty("voice", selected_voice)
            print(f"🗣️  Using voice: {selected_voice}")
        else:
            print("ℹ️  Could not find a voice matching the requested language; using default voice.")

    def is_connected(self) -> bool:
        return self._connected

    def __enter__(self) -> "BluetoothSpeaker":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.disconnect()
        self._engine.stop()
        return False


# ---------------------------------------------------------------------------
# Reminder scheduling
# ---------------------------------------------------------------------------
@dataclass
class Reminder:
    id: str
    message: str
    remind_at: datetime
    created_at: datetime
    voice_note: Optional[str] = None
    delivered: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "message": self.message,
            "remind_at": self.remind_at.isoformat(),
            "created_at": self.created_at.isoformat(),
            "voice_note": self.voice_note,
            "delivered": self.delivered,
        }


class ReminderManager:
    """Background scheduler that triggers callbacks when reminders become due."""

    def __init__(self, on_due: callable) -> None:
        self._on_due = on_due
        self._reminders: Dict[str, Reminder] = {}
        self._lock = threading.Lock()
        self._event = threading.Event()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def add_reminder(
        self,
        message: str,
        remind_at: datetime,
        *,
        voice_note: Optional[str] = None,
    ) -> Reminder:
        reminder = Reminder(
            id=str(uuid.uuid4()),
            message=message.strip(),
            remind_at=remind_at,
            created_at=datetime.utcnow(),
            voice_note=voice_note.strip() if voice_note else None,
        )
        with self._lock:
            self._reminders[reminder.id] = reminder
            self._event.set()
        return reminder

    def remove_reminder(self, reminder_id: str) -> Optional[Reminder]:
        with self._lock:
            removed = self._reminders.pop(reminder_id, None)
            if removed:
                self._event.set()
            return removed

    def list_reminders(self) -> List[Reminder]:
        with self._lock:
            return sorted(self._reminders.values(), key=lambda item: item.remind_at)

    def stop(self) -> None:
        self._stop.set()
        self._event.set()
        if self._thread.is_alive():
            self._thread.join(timeout=1.5)

    def _next_pending(self) -> Optional[Reminder]:
        with self._lock:
            pending = [r for r in self._reminders.values() if not r.delivered]
            if not pending:
                return None
            return min(pending, key=lambda item: item.remind_at)

    def _mark_delivered(self, reminder_id: str) -> Optional[Reminder]:
        with self._lock:
            reminder = self._reminders.get(reminder_id)
            if reminder:
                reminder.delivered = True
            return reminder

    def _run(self) -> None:
        while not self._stop.is_set():
            reminder = self._next_pending()
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

            try:
                self._on_due(delivered)
            finally:
                self._event.set()


# ---------------------------------------------------------------------------
# Voice chatbot service
# ---------------------------------------------------------------------------
class VoiceChatbotService:
    """High-level service that powers the voice chatbot and reminders."""

    def __init__(self, *, enable_speaker: bool = True) -> None:
        _load_dotenv()

        token = _env("GITHUB_TOKEN")
        if not token:
            raise RuntimeError(
                "Missing GITHUB_TOKEN environment variable. "
                "Visit https://github.com/settings/tokens to generate a token."
            )

        endpoint = _env("GITHUB_MODELS_ENDPOINT", "https://models.github.ai/inference")
        model = _env("GITHUB_MODEL", "openai/gpt-4o-mini")
        conversation_id = _env("CONVERSATION_ID", "pi-console")
        temperature = float(_env("TEMPERATURE", "0.7"))
        max_tokens = int(_env("MAX_RESPONSE_TOKENS", "600"))
        speech_rate = int(_env("SPEECH_RATE", "175"))
        language = _env("LANGUAGE", "hi-in")
        speaker_identifier = _env("BLUETOOTH_DEVICE_IDENTIFIER")
        self.disconnect_on_exit = _env_bool("DISCONNECT_ON_EXIT", False)

        self.voice_enabled = enable_speaker
        self.speaker = BluetoothSpeaker(speaker_identifier, voice_rate=speech_rate)
        self.speaker.set_voice(language)
        self._speaker_ready = False
        if self.voice_enabled:
            self._speaker_ready = self.speaker.connect()

        self._speech_queue: "queue.Queue[Optional[str]]" = queue.Queue()
        self._speech_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self._speech_thread.start()

        state_store = StateStore()
        github_client = GitHubModelClient(
            endpoint,
            model,
            token,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        self.convo_manager = ConvoManager(
            state_store,
            github_client,
            conversation_id=conversation_id,
            system_prompt=(
                "You are Chirpy, the friendly RoboGuardian stationed on a Raspberry Pi. "
                "Always greet users warmly, keep replies upbeat yet concise, and offer "
                "practical help for robotics, safety, and daily assistance. Respond "
                "exclusively in natural Hindi written in Devanagari script—never use "
                "English unless the user explicitly requests a translation."
            ),
        )

        self.reminders = ReminderManager(self._handle_reminder_due)

    # ----------------------------- Speech helpers -------------------------
    def speak_async(self, text: str) -> None:
        if not text:
            return
        if not (self.voice_enabled and self._speaker_ready):
            return
        self._speech_queue.put(_prepare_for_speech(text))

    def _speech_worker(self) -> None:
        while True:
            text = self._speech_queue.get()
            if text is None:
                break
            try:
                self.speaker.speak(text)
            except Exception as exc:  # pragma: no cover - hardware specific
                print(f"⚠️  Failed to speak reminder: {exc}")

    # ----------------------------- Conversation --------------------------
    def process_text(self, user_input: str, *, speak_reply: bool = True) -> Dict[str, Any]:
        cleaned = (user_input or "").strip()
        if not cleaned:
            raise ValueError("Input text is empty.")

        reply = self.convo_manager.process_input(cleaned)
        if speak_reply:
            self.speak_async(reply)

        return {
            "user": cleaned,
            "reply": reply,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_history(self, limit: int = 20) -> List[Dict[str, str]]:
        messages = self.convo_manager.messages[-limit:]
        history: List[Dict[str, str]] = []
        for message in messages:
            if message["role"] == "system":
                continue
            history.append({"role": message["role"], "content": message["content"]})
        return history

    def add_system_note(self, note: str, *, speak: bool = False) -> None:
        cleaned = (note or "").strip()
        if not cleaned:
            return
        self.convo_manager.add_assistant_message(cleaned)
        if speak:
            self.speak_async(cleaned)

    # ----------------------------- Reminders -----------------------------
    @staticmethod
    def _coerce_datetime(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value

        if isinstance(value, (int, float)):
            return datetime.utcnow() + timedelta(seconds=float(value))

        if isinstance(value, str):
            text = value.strip()
            if not text:
                raise ValueError("Reminder time cannot be empty.")

            if text.endswith("Z"):
                text = text[:-1] + "+00:00"
            try:
                dt = datetime.fromisoformat(text)
            except ValueError as exc:
                raise ValueError(
                    "Invalid reminder time. Use ISO format, e.g. 2025-09-26T18:30"
                ) from exc

            if dt.tzinfo:
                return dt.astimezone().replace(tzinfo=None)
            return dt

        raise ValueError("Unsupported reminder time format.")

    def add_reminder(
        self,
        message: str,
        *,
        remind_at: Optional[Any] = None,
        delay_seconds: Optional[float] = None,
        voice_note: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not message or not message.strip():
            raise ValueError("Reminder message cannot be empty.")

        if remind_at is None and delay_seconds is None:
            delay_seconds = 60

        if remind_at is not None:
            remind_dt = self._coerce_datetime(remind_at)
        else:
            remind_dt = datetime.utcnow() + timedelta(seconds=float(delay_seconds))

        reminder = self.reminders.add_reminder(
            message.strip(),
            remind_dt,
            voice_note=voice_note or message,
        )
        return reminder.to_dict()

    def list_reminders(self) -> List[Dict[str, Any]]:
        return [reminder.to_dict() for reminder in self.reminders.list_reminders()]

    def remove_reminder(self, reminder_id: str) -> Optional[Dict[str, Any]]:
        removed = self.reminders.remove_reminder(reminder_id)
        return removed.to_dict() if removed else None

    def _handle_reminder_due(self, reminder: Reminder) -> None:
        announcement = (
            f"स्मरण: {reminder.voice_note or reminder.message}"
        )
        self.speak_async(announcement)
        print(f"🔔 Reminder due ({reminder.remind_at.isoformat()}): {reminder.message}")

    # ----------------------------- Status & cleanup ----------------------
    def status(self) -> Dict[str, Any]:
        return {
            "voice_ready": bool(self._speaker_ready if self.voice_enabled else True),
            "reminders": self.list_reminders(),
        }

    def shutdown(self) -> None:
        self.reminders.stop()
        self._speech_queue.put(None)
        if self.disconnect_on_exit and self.voice_enabled and self._speaker_ready:
            self.speaker.disconnect()


def build_service(*, enable_speaker: bool = True) -> VoiceChatbotService:
    return VoiceChatbotService(enable_speaker=enable_speaker)


def main() -> None:
    try:
        service = VoiceChatbotService()
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    print("🤖 Raspberry Pi Chatbot ready. Type 'exit' to quit.")
    intro_message = (
        "नमस्ते, सत श्री अकाल, हेलो! मैं आपका मित्रवत रोबोट Chirpy हूँ। "
        "आज मैं आपकी कैसे सहायता कर सकता हूँ?"
    )
    print(f"Assistant: {intro_message}")
    service.speak_async(intro_message)

    try:
        while True:
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
            except Exception as err:
                print(f"🚨 Error while contacting GitHub Models API: {err}")
                continue

            print(f"Assistant: {result['reply']}")
    except KeyboardInterrupt:
        print("\n🔚 Keyboard interrupt received. Shutting down…")
    finally:
        service.shutdown()


if __name__ == "__main__":
    main()
