"""Telegram Bot API client."""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TelegramResponse:
    ok: bool
    description: str = ""


class TelegramBotClient:
    """Send simple Telegram bot messages."""

    def __init__(self, token: str, timeout: int = 10) -> None:
        self.token = token
        self.timeout = timeout

    def send_message(self, chat_id: str, text: str) -> TelegramResponse:
        payload = json.dumps({"chat_id": chat_id, "text": text}).encode("utf-8")
        request = urllib.request.Request(
            f"https://api.telegram.org/bot{self.token}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        return TelegramResponse(
            ok=bool(data.get("ok")),
            description=data.get("description", ""),
        )
