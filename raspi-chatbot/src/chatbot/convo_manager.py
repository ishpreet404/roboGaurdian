from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from .state_store import StateStore
from ..services.github_model_client import GitHubModelClient


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

    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    def _trim_history(self) -> None:
        # Keep the system prompt plus the latest ``history_limit`` exchanges
        system = self.messages[0]
        recent = self.messages[-self.history_limit :]
        self.messages = [system, *recent]

    def _persist(self) -> None:
        self.state_store.save_state(self.conversation_id, self.messages)

    @staticmethod
    def _log(speaker: str, message: str) -> None:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {speaker}: {message}")