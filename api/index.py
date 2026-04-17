"""
api/webhook.py — Routing Layer (Vercel Entrypoint)

Handles incoming Telegram webhook POST requests using Python's native
``BaseHTTPRequestHandler`` — no Flask/FastAPI needed.
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler

# Allow imports from the project root (one level up from api/)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sommelier_ai import SommelierAI  # noqa: E402
from telegram_client import TelegramClient  # noqa: E402
from wine_inventory import WineInventory  # noqa: E402


class handler(BaseHTTPRequestHandler):
    """Vercel serverless handler for the Telegram webhook."""

    # ------------------------------------------------------------------
    # POST  /api/webhook
    # ------------------------------------------------------------------
    def do_POST(self):
        # --- Security: validate Telegram secret token ---
        expected_secret = os.environ.get("TELEGRAM_SECRET_TOKEN", "")
        incoming_secret = self.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if expected_secret and incoming_secret != expected_secret:
            self._respond(401, "Unauthorized")
            return

        # --- Read body ---
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            update = json.loads(body)
        except (json.JSONDecodeError, ValueError):
            self._respond(400, "Bad Request")
            return

        # --- Extract message ---
        message = update.get("message")
        if not message:
            self._respond(200, "OK — no message")
            return

        # --- Safety: ignore non-text messages ---
        text = message.get("text")
        if not text:
            self._respond(200, "OK — non-text ignored")
            return

        # --- Authorization: restrict to allowed user ---
        chat_id = message["chat"]["id"]
        allowed_user_id = os.environ.get("ALLOWED_USER_ID", "")
        if allowed_user_id and str(chat_id) != allowed_user_id:
            self._respond(200, "OK — unauthorized user")
            return

        # --- Execute flow ---
        try:
            inventory = WineInventory()
            inventory_text = inventory.get_formatted_inventory()

            ai = SommelierAI()
            answer = ai.ask(user_message=text, inventory_context=inventory_text)

            telegram = TelegramClient()
            telegram.send_message(chat_id=chat_id, text=answer)
        except Exception as exc:
            # Best-effort error notification to the user
            try:
                TelegramClient().send_message(
                    chat_id=chat_id,
                    text=f"⚠️ שגיאה פנימית: {exc}",
                )
            except Exception:
                pass

        self._respond(200, "OK")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _respond(self, status_code: int, message: str):
        self.send_response(status_code)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(message.encode("utf-8"))
