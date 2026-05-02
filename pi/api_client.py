import json
import threading
import time
from typing import Callable, List, Optional

import requests

try:
    import websocket
except ImportError:  # pragma: no cover
    websocket = None


class BackendClient:
    def __init__(self, base_url: str, ws_url: Optional[str] = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.ws_url = ws_url
        self.ws_app = None
        self.ws_thread = None
        self.on_command: Optional[Callable[[dict], None]] = None
        self._connected = False

    def start(self) -> None:
        if websocket is None or not self.ws_url:
            return

        def on_open(ws):
            self._connected = True
            hello = {"type": "hello", "data": {"role": "pi"}}
            ws.send(json.dumps(hello))

        def on_close(ws, *_):
            self._connected = False

        def on_message(ws, message):
            try:
                payload = json.loads(message)
            except json.JSONDecodeError:
                return
            if payload.get("type") == "command" and self.on_command:
                self.on_command(payload.get("data") or {})

        self.ws_app = websocket.WebSocketApp(
            self.ws_url,
            on_open=on_open,
            on_close=on_close,
            on_message=on_message,
        )

        self.ws_thread = threading.Thread(target=self._run_ws, daemon=True)
        self.ws_thread.start()

    def _run_ws(self) -> None:
        while True:
            try:
                self.ws_app.run_forever(ping_interval=25, ping_timeout=10)
            except Exception:
                pass
            time.sleep(2)

    def send_ws(self, msg_type: str, data: dict) -> None:
        if not self._connected or not self.ws_app:
            return
        try:
            self.ws_app.send(json.dumps({"type": msg_type, "data": data}))
        except Exception:
            self._connected = False

    def post_json(self, path: str, payload: dict) -> None:
        url = f"{self.base_url}{path}"
        try:
            requests.post(url, json=payload, timeout=2.5)
        except Exception:
            pass

    def send_telemetry(self, telemetry: dict) -> None:
        self.post_json("/api/telemetry", telemetry)
        self.send_ws("telemetry", telemetry)

    def send_path(self, points: List[dict]) -> None:
        self.post_json("/api/path", {"points": points})
        self.send_ws("path", {"points": points})

    def send_victims(self, victims: List[dict]) -> None:
        self.post_json("/api/victims", victims)
        self.send_ws("victims", victims)

    def send_alert(self, alert: dict) -> None:
        self.post_json("/api/alerts", alert)
        self.send_ws("alert", alert)
