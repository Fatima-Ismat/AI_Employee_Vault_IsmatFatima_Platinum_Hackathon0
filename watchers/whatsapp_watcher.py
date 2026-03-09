"""
WhatsApp Watcher
────────────────
Polls a WhatsApp Business API webhook or a local message queue
and writes tasks into AI_Employee_Vault/Inbox/.

Production:
  Use Meta WhatsApp Business API and set WHATSAPP_API_URL + WHATSAPP_API_KEY in .env

Demo mode:
  Runs without credentials and injects simulated messages.
"""

import json
import re
import time
from datetime import datetime, timezone
from typing import Any

import requests

from utils.config import WHATSAPP_API_URL, WHATSAPP_API_KEY, LOOP_INTERVAL
from utils.logger import get_logger
from utils.vault_io import write_inbox_task
from watchers.base_watcher import BaseWatcher

log = get_logger("watcher.whatsapp")

_PROCESSED_IDS: set[str] = set()


def _mask_phone(number: str) -> str:
    return re.sub(r"\d(?=\d{4})", "*", number)


class WhatsAppWatcher(BaseWatcher):
    """Poll WhatsApp Business API for new messages and create Inbox tasks."""

    def __init__(self) -> None:
        super().__init__("whatsapp", poll_interval=LOOP_INTERVAL)
        self._demo_mode = not (WHATSAPP_API_URL and WHATSAPP_API_KEY)
        if self._demo_mode:
            self.log.warning("WhatsApp credentials not set — running in DEMO mode")

    def poll(self) -> None:
        if self._demo_mode:
            self._demo_poll()
            return

        headers = {
            "Authorization": f"Bearer {WHATSAPP_API_KEY}",
            "Content-Type": "application/json",
        }
        try:
            resp = requests.get(
                f"{WHATSAPP_API_URL}/messages",
                headers=headers,
                timeout=10,
            )
            resp.raise_for_status()
            messages: list[dict[str, Any]] = resp.json().get("messages", [])

            for msg in messages:
                msg_id = msg.get("id", "")
                if msg_id in _PROCESSED_IDS:
                    continue
                _PROCESSED_IDS.add(msg_id)

                sender = msg.get("from", "unknown")
                text   = msg.get("text", {}).get("body", "")
                ts     = msg.get("timestamp", datetime.now(timezone.utc).isoformat())

                self.log.info(f"WhatsApp message from {_mask_phone(sender)}")
                write_inbox_task(
                    title=f"WhatsApp message from {_mask_phone(sender)}",
                    source="whatsapp",
                    body=(
                        f"**From:** {sender}\n"
                        f"**Time:** {ts}\n\n"
                        f"**Message:**\n{text}"
                    ),
                    priority=self._infer_priority(text),
                    metadata={"message_id": msg_id, "sender": sender},
                )
        except requests.RequestException as e:
            self.log.error(f"WhatsApp API error: {e}")
            raise

    def _infer_priority(self, text: str) -> str:
        lower = text.lower()
        if any(w in lower for w in ["urgent", "asap", "emergency", "help"]):
            return "HIGH"
        return "MEDIUM"

    def _demo_poll(self) -> None:
        """Inject one simulated WhatsApp message per cycle for demo."""
        import random
        messages = [
            ("+1234567890", "Hey, can you confirm the meeting tomorrow at 3pm?"),
            ("+0987654321", "Urgent: client wants updated proposal by EOD"),
            ("+1122334455", "Please send me the Q4 report when ready"),
        ]
        sender, text = random.choice(messages)
        write_inbox_task(
            title=f"WhatsApp: {text[:40]}...",
            source="whatsapp_demo",
            body=(
                f"**From:** {_mask_phone(sender)}\n"
                f"**Time:** {datetime.now(timezone.utc).isoformat()}\n\n"
                f"**Message:**\n{text}"
            ),
            priority=self._infer_priority(text),
            metadata={"demo": "true", "sender": sender},
        )
        self.log.info(f"[DEMO] Injected WhatsApp message from {_mask_phone(sender)}")
        # Only once per demo run
        self._demo_mode = False
        self.poll = self._poll_noop  # type: ignore

    def _poll_noop(self) -> None:
        pass


if __name__ == "__main__":
    watcher = WhatsAppWatcher()
    watcher.start()
