"""
Gmail Watcher
─────────────
Polls a Gmail inbox via IMAP, detects unread emails, and writes
task files into AI_Employee_Vault/Inbox/.

Setup:
  1. Enable IMAP in Gmail settings
  2. Create an App Password (Google Account → Security → App Passwords)
  3. Set GMAIL_USER and GMAIL_APP_PASSWORD in .env
"""

import email
import imaplib
import re
from datetime import datetime, timezone
from email.header import decode_header

from utils.config import GMAIL_USER, GMAIL_APP_PASSWORD, GMAIL_POLL_INTERVAL
from utils.logger import get_logger
from utils.vault_io import write_inbox_task
from watchers.base_watcher import BaseWatcher

log = get_logger("watcher.gmail")

IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993

_SEEN_IDS: set[str] = set()


def _decode_mime_words(s: str) -> str:
    parts = decode_header(s)
    decoded = []
    for part, enc in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return "".join(decoded)


def _mask_email(address: str) -> str:
    """Mask PII in email addresses for logs."""
    return re.sub(r"(?<=.{2}).(?=.*@)", "*", address)


def _extract_body(msg: email.message.Message) -> str:
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            cd = str(part.get("Content-Disposition", ""))
            if ct == "text/plain" and "attachment" not in cd:
                payload = part.get_payload(decode=True)
                if payload:
                    body = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                    break
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            body = payload.decode(msg.get_content_charset() or "utf-8", errors="replace")
    return body.strip()[:2000]  # cap at 2000 chars


class GmailWatcher(BaseWatcher):
    """Poll Gmail IMAP and create Inbox tasks for unread emails."""

    def __init__(self) -> None:
        super().__init__("gmail", poll_interval=GMAIL_POLL_INTERVAL)

    def poll(self) -> None:
        if not GMAIL_USER or not GMAIL_APP_PASSWORD:
            self.log.warning("Gmail credentials not set — running in DEMO mode")
            self._demo_inject()
            return

        with imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT) as imap:
            imap.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            imap.select("INBOX")
            _, data = imap.search(None, "UNSEEN")
            email_ids = data[0].split()

            for eid in email_ids:
                eid_str = eid.decode()
                if eid_str in _SEEN_IDS:
                    continue
                _SEEN_IDS.add(eid_str)

                _, msg_data = imap.fetch(eid, "(RFC822)")
                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw)

                subject = _decode_mime_words(msg.get("Subject", "(no subject)"))
                sender  = _decode_mime_words(msg.get("From", "unknown"))
                date    = msg.get("Date", datetime.now(timezone.utc).isoformat())
                body    = _extract_body(msg)

                self.log.info(f"New email from {_mask_email(sender)}: {subject}")

                write_inbox_task(
                    title=f"Email: {subject}",
                    source="gmail",
                    body=f"**From:** {sender}\n**Date:** {date}\n\n{body}",
                    priority=self._infer_priority(subject, body),
                    metadata={"sender": sender, "email_id": eid_str},
                )

    def _infer_priority(self, subject: str, body: str) -> str:
        text = (subject + " " + body).lower()
        if any(w in text for w in ["urgent", "critical", "asap", "emergency"]):
            return "HIGH"
        if any(w in text for w in ["invoice", "payment", "legal", "contract"]):
            return "HIGH"
        return "MEDIUM"

    def _demo_inject(self) -> None:
        """Inject a fake email task for demo/testing without real credentials."""
        import random
        subjects = [
            "Partnership proposal from Acme Corp",
            "Invoice #1042 due Friday",
            "Urgent: Server downtime report needed",
        ]
        subject = random.choice(subjects)
        write_inbox_task(
            title=f"Email: {subject}",
            source="gmail_demo",
            body=f"**From:** demo@example.com\n\nThis is a simulated email for demo purposes.\nSubject: {subject}",
            priority="MEDIUM",
            metadata={"demo": "true"},
        )
        self.log.info(f"[DEMO] Injected email task: {subject}")
        # Only inject once per run to avoid flooding
        self._demo_injected = True
        self.poll = self._poll_noop  # type: ignore

    def _poll_noop(self) -> None:
        pass


if __name__ == "__main__":
    watcher = GmailWatcher()
    watcher.start()
