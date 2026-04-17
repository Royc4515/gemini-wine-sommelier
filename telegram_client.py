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

        import urllib.error
        import re

        # Escape unhandled <, >, & to satisfy Telegram HTML parser constraints
        safe_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        # Convert Gemini's **bold** Markdown to <b>...</b>
        safe_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', safe_text, flags=re.DOTALL)
        # Convert Gemini's *italic* to <i>...</i>
        safe_text = re.sub(r'(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)', r'<i>\1</i>', safe_text, flags=re.DOTALL)
        # Convert Markdown `# Headers` to bold HTML lines
        safe_text = re.sub(r'^#+\s+(.*)', r'<b>\1</b>', safe_text, flags=re.MULTILINE)

        payload_dict = {
            "chat_id": chat_id,
            "text": safe_text,
            "parse_mode": "HTML",
        }

        def _send(data: dict):
            req = urllib.request.Request(
                url=f"{self.api_url}/sendMessage",
                data=json.dumps(data).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode("utf-8"))

        try:
            return _send(payload_dict)
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            if "can't parse entities" in error_body.lower() or "bad request" in error_body.lower():
                # Fallback: remove parse_mode
                payload_dict.pop("parse_mode", None)
                try:
                    return _send(payload_dict)
                except urllib.error.HTTPError as inner_e:
                    inner_body = inner_e.read().decode('utf-8')
                    raise Exception(f"Telegram API Error (Fallback): {inner_e.code} - {inner_body}") from inner_e
            else:
                raise Exception(f"Telegram API Error: {e.code} - {error_body}") from e
