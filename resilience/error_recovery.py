"""
Error Recovery System
──────────────────────
Detects failed and stalled tasks, retries them with exponential backoff,
and moves permanently broken tasks to a recovery folder for human review.

Responsibilities:
  • Retry failed tasks (up to MAX_RECOVERY_RETRIES)
  • Move stuck Needs_Action tasks back to Inbox if stalled > threshold
  • Archive broken tasks to AI_Employee_Vault/Recovery/
  • Log all recovery events

Run:
  python -m resilience.error_recovery        # One-shot scan
  python -m resilience.error_recovery --loop # Continuous monitoring
"""

import sys
import time
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.config import (
    VAULT_DIR, INBOX_DIR, NEEDS_ACTION_DIR, DONE_DIR, LOGS_DIR,
)
from utils.logger import get_logger
from utils.vault_io import move_task, update_task_status, now_utc, read_task

log = get_logger("resilience.recovery")

RECOVERY_DIR      = VAULT_DIR / "Recovery"
RECOVERY_LOG      = LOGS_DIR / "recovery_log.md"
STALL_THRESHOLD   = int(__import__("os").getenv("STALL_THRESHOLD_MINUTES", "15"))
MAX_RECOVERY_RETRIES = int(__import__("os").getenv("MAX_RECOVERY_RETRIES", "3"))
RECOVERY_INTERVAL = 120   # seconds between recovery scans


def _now() -> str:
    return now_utc()


def _write_recovery_log(event: str, level: str = "INFO") -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    icons = {"INFO": "ℹ️", "RETRY": "🔄", "ARCHIVED": "📦", "ERROR": "❌", "OK": "✅"}
    icon = icons.get(level, "•")
    line = f"\n- `{_now()}` {icon} **{level}** — {event}"
    with open(RECOVERY_LOG, "a", encoding="utf-8") as f:
        f.write(line)


def _extract_retry_count(content: str) -> int:
    for line in content.splitlines():
        if line.startswith("retry_count:"):
            try:
                return int(line.split(":", 1)[1].strip())
            except ValueError:
                pass
    return 0


def _increment_retry_count(task_path: Path) -> int:
    content = task_path.read_text(encoding="utf-8")
    count = _extract_retry_count(content) + 1
    lines = content.splitlines()
    updated = []
    found = False
    for line in lines:
        if line.startswith("retry_count:"):
            updated.append(f"retry_count: {count}")
            found = True
        else:
            updated.append(line)
    if not found:
        # Insert after status: line
        result = []
        for line in updated:
            result.append(line)
            if line.startswith("status:"):
                result.append(f"retry_count: {count}")
        updated = result
    task_path.write_text("\n".join(updated), encoding="utf-8")
    return count


def find_stalled_tasks(threshold_minutes: int = STALL_THRESHOLD) -> list[Path]:
    """Find tasks stuck in Needs_Action beyond the stall threshold."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=threshold_minutes)
    NEEDS_ACTION_DIR.mkdir(parents=True, exist_ok=True)
    stalled = []
    for f in NEEDS_ACTION_DIR.glob("*.md"):
        if f.name.startswith("."):
            continue
        try:
            mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff:
                stalled.append(f)
        except Exception:
            pass
    return stalled


def retry_stalled_task(task_path: Path) -> str:
    """Retry a stalled task by moving it back to Inbox."""
    count = _increment_retry_count(task_path)

    if count > MAX_RECOVERY_RETRIES:
        # Too many retries → archive
        result = archive_broken_task(task_path, reason=f"Exceeded {MAX_RECOVERY_RETRIES} retry attempts")
        return "archived"

    # Move back to Inbox for reprocessing
    update_task_status(task_path, "retrying")
    new_path = move_task(task_path, INBOX_DIR)
    msg = f"Stalled task retried (attempt {count}/{MAX_RECOVERY_RETRIES}): {task_path.name}"
    log.warning(msg)
    _write_recovery_log(msg, "RETRY")
    return "retried"


def archive_broken_task(task_path: Path, reason: str = "") -> Path:
    """Move an unrecoverable task to Recovery/ folder."""
    RECOVERY_DIR.mkdir(parents=True, exist_ok=True)
    dest = RECOVERY_DIR / task_path.name

    # Append failure note to task file
    try:
        content = task_path.read_text(encoding="utf-8")
        content += f"\n\n---\n\n## Recovery Archive\n\n**Archived:** {_now()}\n**Reason:** {reason}\n"
        task_path.write_text(content, encoding="utf-8")
    except Exception:
        pass

    update_task_status(task_path, "archived")
    shutil.move(str(task_path), str(dest))

    msg = f"Task archived to Recovery/: {task_path.name} — {reason}"
    log.error(msg)
    _write_recovery_log(msg, "ARCHIVED")
    return dest


def scan_and_recover() -> dict:
    """
    Run one recovery scan cycle.
    Returns summary of actions taken.
    """
    RECOVERY_DIR.mkdir(parents=True, exist_ok=True)

    stalled = find_stalled_tasks()
    retried  = 0
    archived = 0

    for task in stalled:
        action = retry_stalled_task(task)
        if action == "retried":
            retried += 1
        elif action == "archived":
            archived += 1

    recovery_count = sum(1 for _ in RECOVERY_DIR.glob("*.md"))

    summary = {
        "stalled_found": len(stalled),
        "retried":       retried,
        "archived":      archived,
        "recovery_total": recovery_count,
        "timestamp":     _now(),
    }

    if stalled:
        log.info(f"Recovery scan: found={len(stalled)} retried={retried} archived={archived}")
        _write_recovery_log(
            f"Recovery scan — stalled={len(stalled)} retried={retried} archived={archived}", "OK"
        )

    return summary


def run_recovery_loop() -> None:
    """Continuous recovery monitoring loop."""
    if not RECOVERY_LOG.exists():
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        RECOVERY_LOG.write_text(
            "# Recovery Log\n\n> Automatic error recovery events.\n\n",
            encoding="utf-8",
        )
    log.info(f"Error recovery monitor active (interval={RECOVERY_INTERVAL}s)")
    while True:
        try:
            scan_and_recover()
        except Exception as e:
            log.error(f"Recovery scan error: {e}")
        time.sleep(RECOVERY_INTERVAL)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--loop", action="store_true", help="Run as continuous monitor")
    args = parser.parse_args()

    if args.loop:
        run_recovery_loop()
    else:
        result = scan_and_recover()
        print(f"Recovery scan complete: {result}")
