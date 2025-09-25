"""Console-driven Raspberry Pi chatbot with Bluetooth speaker playback.

This entry point wires together the conversation manager, GitHub Models API
client, and Bluetooth text-to-speech helper.  It expects configuration to be
supplied via environment variables (see ``config/settings.example.env``).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional, Tuple

# Ensure the project packages are importable when running this file directly.
if __package__ in {None, ""}:  # pragma: no cover - runtime environment setup
    current_dir = Path(__file__).resolve().parent
    candidate_paths = [current_dir, current_dir.parent]
    for candidate in candidate_paths:
        candidate_str = str(candidate)
        if candidate.exists() and candidate_str not in sys.path:
            sys.path.insert(0, candidate_str)

from dotenv import load_dotenv

from audio.bluetooth_speaker import BluetoothSpeaker
from chatbot.convo_manager import ConvoManager
from chatbot.state_store import StateStore
from services.github_model_client import GitHubModelClient


def _env(key: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(key)
    if value is None or value == "":
        return default
    return value


def build_app() -> Tuple[ConvoManager, BluetoothSpeaker]:
    load_dotenv()

    token = _env("GITHUB_TOKEN")
    if not token:
        raise SystemExit(
            "Missing GITHUB_TOKEN environment variable. "
            "Visit https://github.com/settings/tokens to generate a token and"
            " store it securely (never commit it to source control)."
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

    return (
        ConvoManager(
            state_store,
            github_client,
            conversation_id=conversation_id,
            system_prompt="You are a helpful assistant running on a Raspberry Pi.",
        ),
        speaker,
    )


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
            except Exception as err:  # pragma: no cover - interactive handling
                print(f"🚨 Error while contacting GitHub Models API: {err}")
                continue

            print(f"Assistant: {reply}")
            speaker.speak(reply)
    except KeyboardInterrupt:
        print("\n🔚 Keyboard interrupt received. Shutting down…")
    finally:
        if 'speaker' in locals():
            speaker.disconnect()


if __name__ == "__main__":
    main()
