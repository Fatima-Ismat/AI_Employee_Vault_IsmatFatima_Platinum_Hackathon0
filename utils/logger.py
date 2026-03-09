"""
Structured logging utility.
Writes to both console and AI_Employee_Vault/Logs/.
"""

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from utils.config import LOGS_DIR


def _get_log_file() -> Path:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return LOGS_DIR / f"{today}.md"


class VaultMarkdownHandler(logging.Handler):
    """Appends log records to a daily Markdown file in the Vault Logs folder."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            LOGS_DIR.mkdir(parents=True, exist_ok=True)
            log_file = _get_log_file()
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            level_icon = {
                "DEBUG":    "🔍",
                "INFO":     "ℹ️",
                "WARNING":  "⚠️",
                "ERROR":    "❌",
                "CRITICAL": "🔥",
            }.get(record.levelname, "•")
            line = f"\n- `{ts}` {level_icon} **{record.levelname}** [{record.name}] {self.format(record)}"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            self.handleError(record)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)-8s %(name)s — %(message)s", "%H:%M:%S"))

    # Vault markdown handler
    vh = VaultMarkdownHandler()
    vh.setLevel(logging.DEBUG)
    vh.setFormatter(logging.Formatter("%(message)s"))

    logger.addHandler(ch)
    logger.addHandler(vh)
    return logger
