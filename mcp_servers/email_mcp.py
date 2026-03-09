"""
Email MCP Server
────────────────
Model Context Protocol tool for sending and reading emails.

Production: Replace stub implementations with real SMTP/IMAP calls.
Demo mode: Logs actions without actually sending emails.
"""

import smtplib
import os
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from utils.logger import get_logger

log = get_logger("mcp.email")

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("GMAIL_USER", "")
SMTP_PASS = os.getenv("GMAIL_APP_PASSWORD", "")
DEMO_MODE = not (SMTP_USER and SMTP_PASS)


# ── Public MCP Tool Functions ─────────────────────────────────────────────────

def send_email(
    to: str,
    subject: str,
    body: str,
    cc: Optional[str] = None,
    html: bool = False,
) -> dict:
    """
    Send an email via SMTP.

    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body (plain text or HTML)
        cc: Optional CC address
        html: If True, send as HTML

    Returns:
        {"success": bool, "message": str}
    """
    if DEMO_MODE:
        log.info(f"[DEMO] Would send email to={to} subject='{subject}'")
        log.info(f"[DEMO] Body preview: {body[:100]}...")
        return {"success": True, "message": f"[DEMO] Email logged (not sent) to {to}"}

    try:
        msg = MIMEMultipart("alternative" if html else "mixed")
        msg["From"]    = SMTP_USER
        msg["To"]      = to
        msg["Subject"] = subject
        if cc:
            msg["Cc"] = cc

        content_type = "html" if html else "plain"
        msg.attach(MIMEText(body, content_type))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            recipients = [to] + ([cc] if cc else [])
            server.sendmail(SMTP_USER, recipients, msg.as_string())

        log.info(f"Email sent to {to}: {subject}")
        return {"success": True, "message": f"Email sent to {to}"}

    except Exception as e:
        log.error(f"Failed to send email: {e}")
        return {"success": False, "message": str(e)}


def read_emails(
    folder: str = "INBOX",
    limit: int = 10,
    unread_only: bool = True,
) -> list[dict]:
    """
    Read emails from inbox.

    Returns:
        List of email dicts with keys: id, subject, sender, date, body
    """
    if DEMO_MODE:
        log.info(f"[DEMO] Would read {limit} emails from {folder}")
        return [
            {
                "id": "demo_001",
                "subject": "Partnership Proposal",
                "sender": "partner@example.com",
                "date": datetime.now(timezone.utc).isoformat(),
                "body": "Hi, we'd like to explore a partnership opportunity...",
            }
        ]

    import imaplib, email as email_lib
    results = []
    try:
        with imaplib.IMAP4_SSL("imap.gmail.com") as imap:
            imap.login(SMTP_USER, SMTP_PASS)
            imap.select(folder)
            criteria = "UNSEEN" if unread_only else "ALL"
            _, data = imap.search(None, criteria)
            ids = data[0].split()[-limit:]
            for eid in ids:
                _, msg_data = imap.fetch(eid, "(RFC822)")
                msg = email_lib.message_from_bytes(msg_data[0][1])
                results.append({
                    "id": eid.decode(),
                    "subject": msg.get("Subject", ""),
                    "sender": msg.get("From", ""),
                    "date": msg.get("Date", ""),
                    "body": "",  # Omit for brevity
                })
    except Exception as e:
        log.error(f"Failed to read emails: {e}")

    return results


def draft_reply(
    original_subject: str,
    original_body: str,
    context: str = "",
) -> str:
    """
    Return a draft reply string (calls Claude agent in production).
    Stub: returns a template reply.
    """
    return (
        f"Thank you for your email regarding '{original_subject}'.\n\n"
        f"I have reviewed your message and will get back to you shortly.\n\n"
        f"Best regards,\nAI Employee"
    )
