"""
telegram_client.py — Integration Layer

Lightweight Telegram Bot API wrapper using only ``urllib.request``.
"""

import json
import os
import urllib.request


class TelegramClient:
    """Sends messages via the Telegram Bot API."""

    BASE_URL = "https://api.telegram.org"

    def __init__(self):
        token: str = os.environ["TELEGRAM_BOT_TOKEN"]
        self.api_url = f"{self.BASE_URL}/bot{token}"

    def send_message(self, chat_id: int | str, text: str) -> dict:
        """Send a text message to *chat_id*.

        Long messages are automatically truncated to Telegram's 4096 char limit.
        Returns the parsed JSON response from the API.
        """
        max_length = 4096
        if len(text) > max_length:
            text = text[: max_length - 3] + "..."

        payload = json.dumps({
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
        }).encode("utf-8")

        request = urllib.request.Request(
            url=f"{self.api_url}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
