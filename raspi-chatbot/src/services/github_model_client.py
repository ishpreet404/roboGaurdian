"""GitHub Models API client."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

import requests


class GitHubModelClient:
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