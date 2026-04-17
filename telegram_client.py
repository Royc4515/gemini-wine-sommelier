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

        Messages longer than 4000 chars are split into multiple sequential
        messages so the user always receives the full response.
        Returns the parsed JSON response from the last chunk sent.
        """
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

        # Split into ≤4000-char chunks (safe margin below 4096)
        chunk_size = 4000
        chunks = [safe_text[i:i + chunk_size] for i in range(0, len(safe_text), chunk_size)]

        def _send(data: dict):
            req = urllib.request.Request(
                url=f"{self.api_url}/sendMessage",
                data=json.dumps(data).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode("utf-8"))

        last_result = None
        for chunk in chunks:
            payload_dict = {
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "HTML",
            }
            try:
                last_result = _send(payload_dict)
            except urllib.error.HTTPError as e:
                error_body = e.read().decode("utf-8")
                if "can't parse entities" in error_body.lower() or "bad request" in error_body.lower():
                    # Fallback: send without parse_mode
                    payload_dict.pop("parse_mode", None)
                    try:
                        last_result = _send(payload_dict)
                    except urllib.error.HTTPError as inner_e:
                        inner_body = inner_e.read().decode('utf-8')
                        raise Exception(f"Telegram API Error (Fallback): {inner_e.code} - {inner_body}") from inner_e
                else:
                    raise Exception(f"Telegram API Error: {e.code} - {error_body}") from e

        return last_result
