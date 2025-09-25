"""In-memory conversation state store.

The store keeps a mapping of ``conversation_id`` → arbitrary serialisable data.
This lightweight implementation is sufficient for command-line usage; in a
production deployment you could swap it with Redis, SQLite, or another
persistent backend by implementing the same interface.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, Optional


class StateStore:
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