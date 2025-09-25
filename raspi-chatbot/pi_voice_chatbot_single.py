#!/usr/bin/env python3
"""Self-contained Raspberry Pi voice chatbot using the GitHub Models API.

This single-file script bundles the core logic that previously lived across
multiple modules in the ``raspi-chatbot`` project. Drop it onto a Raspberry Pi,
update the environment variables (either via ``.env`` or the shell), and run it
with Python 3.10+.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:  # Prefer python-dotenv when installed for full .env parsing support.
    from dotenv import load_dotenv as _load_dotenv  # type: ignore
except Exception:  # pragma: no cover - fallback applies when dependency missing
    def _load_dotenv(dotenv_path: Optional[str] = None) -> bool:
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
else:  # Successful import, wrap for consistent signature.
    def _load_dotenv(dotenv_path: Optional[str] = None) -> bool:
        return bool(_load_dotenv(dotenv_path))

import requests  # type: ignore
import pyttsx3  # type: ignore


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------
def _env(key: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(key)
    if value is None or value == "":
        return default
    return value


# ---------------------------------------------------------------------------
# GitHub Models client
# ---------------------------------------------------------------------------
class GitHubModelClient:
    """Very small helper around the GitHub Models chat completions endpoint."""

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


# ---------------------------------------------------------------------------
# Conversation state store
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Conversation manager
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Bluetooth speaker helper
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


# ---------------------------------------------------------------------------
# Application wiring
# ---------------------------------------------------------------------------
def build_app() -> Tuple[ConvoManager, BluetoothSpeaker]:
    _load_dotenv()

    token = _env("GITHUB_TOKEN")
    if not token:
        raise SystemExit(
            "Missing GITHUB_TOKEN environment variable. "
            "Visit https://github.com/settings/tokens to generate a token and "
            "store it securely (never commit it to source control)."
        )

    endpoint = _env("GITHUB_MODELS_ENDPOINT", "https://models.github.ai/inference")
    model = _env("GITHUB_MODEL", "openai/gpt-4o-mini")
    conversation_id = _env("CONVERSATION_ID", "pi-console")
    temperature = float(_env("TEMPERATURE", "0.7"))
    max_tokens = int(_env("MAX_RESPONSE_TOKENS", "600"))
    speech_rate = int(_env("SPEECH_RATE", "175"))
    language = _env("LANGUAGE", "en")
    speaker_identifier = _env("BLUETOOTH_DEVICE_IDENTIFIER")

    speaker = BluetoothSpeaker(speaker_identifier, voice_rate=speech_rate)
    speaker.set_voice(language)
    speaker.connect()

    state_store = StateStore()
    github_client = GitHubModelClient(
        endpoint,
        model,
        token,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    convo_manager = ConvoManager(
        state_store,
        github_client,
        conversation_id=conversation_id,
        system_prompt="You are a helpful assistant running on a Raspberry Pi.",
    )

    return convo_manager, speaker


def main() -> None:
    try:
        convo_manager, speaker = build_app()
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

    print("🤖 Raspberry Pi Chatbot ready. Type 'exit' to quit.")

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
                reply = convo_manager.process_input(user_input)
            except Exception as err:
                print(f"🚨 Error while contacting GitHub Models API: {err}")
                continue

            print(f"Assistant: {reply}")
            speaker.speak(reply)
    except KeyboardInterrupt:
        print("\n🔚 Keyboard interrupt received. Shutting down…")
    finally:
        if "speaker" in locals():
            speaker.disconnect()


if __name__ == "__main__":
    main()
