"""
Vault I/O helpers — read, write, and move task files through the pipeline.
All task files are Markdown with YAML-style frontmatter.
"""

import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from utils.config import (
    INBOX_DIR, NEEDS_ACTION_DIR, PLANS_DIR, PENDING_DIR,
    APPROVED_DIR, REJECTED_DIR, DONE_DIR,
)
from utils.logger import get_logger

log = get_logger(__name__)


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def generate_task_id() -> str:
    return str(uuid.uuid4())[:8]


# Characters forbidden in Windows filenames: < > : " / \ | ? *
# Plus control characters (0x00-0x1f) and the literal dot-only names.
_WIN_ILLEGAL = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize_filename(name: str, max_len: int = 50) -> str:
    """Return a Windows-safe filename fragment from an arbitrary string.

    Replaces every character that is illegal on Windows (or on any major OS)
    with an underscore, collapses consecutive underscores, and trims to
    *max_len* characters so the full path stays well under MAX_PATH.
    """
    safe = _WIN_ILLEGAL.sub("_", name)          # replace illegal chars
    safe = re.sub(r"_+", "_", safe)              # collapse runs of _
    safe = safe.strip("_. ")                     # trim leading/trailing junk
    return safe[:max_len] or "task"


def write_inbox_task(
    title: str,
    source: str,
    body: str,
    priority: str = "MEDIUM",
    metadata: Optional[dict] = None,
) -> Path:
    """Write a new task file into the Inbox and return its path."""
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    task_id = generate_task_id()
    ts = now_utc()
    safe_title = sanitize_filename(title.replace(" ", "_"))
    filename = f"{task_id}_{safe_title}.md"
    filepath = INBOX_DIR / filename

    meta_lines = ""
    if metadata:
        for k, v in metadata.items():
            meta_lines += f"{k}: {v}\n"

    content = f"""---
task_id: {task_id}
title: {title}
source: {source}
priority: {priority}
status: inbox
created_at: {ts}
{meta_lines}---

# Task: {title}

**Source:** {source}
**Priority:** {priority}
**Created:** {ts}

---

## Description

{body}

---

## Agent Notes

<!-- Populated by Claude agent -->

## Plan Reference

<!-- Link to Plans/ file -->
"""
    filepath.write_text(content, encoding="utf-8")
    log.info(f"Task written to Inbox: {filename}")
    return filepath


def move_task(src_path: Path, dest_dir: Path) -> Path:
    """Move a task file to a different pipeline stage directory."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / src_path.name
    shutil.move(str(src_path), str(dest_path))
    log.info(f"Moved {src_path.name} → {dest_dir.name}/")
    return dest_path


def update_task_status(task_path: Path, new_status: str) -> None:
    """Rewrite the status: field in a task file's frontmatter."""
    content = task_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    updated = []
    for line in lines:
        if line.startswith("status:"):
            updated.append(f"status: {new_status}")
        else:
            updated.append(line)
    task_path.write_text("\n".join(updated), encoding="utf-8")


def read_task(task_path: Path) -> str:
    return task_path.read_text(encoding="utf-8")


def list_inbox_tasks() -> list[Path]:
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(
        [p for p in INBOX_DIR.iterdir() if p.suffix == ".md"],
        key=lambda p: p.stat().st_ctime,
    )


def list_approved_tasks() -> list[Path]:
    APPROVED_DIR.mkdir(parents=True, exist_ok=True)
    return [p for p in APPROVED_DIR.iterdir() if p.suffix == ".md"]


def list_rejected_tasks() -> list[Path]:
    REJECTED_DIR.mkdir(parents=True, exist_ok=True)
    return [p for p in REJECTED_DIR.iterdir() if p.suffix == ".md"]


def write_plan(task_id: str, plan_content: str) -> Path:
    """Write a plan file into Plans/."""
    PLANS_DIR.mkdir(parents=True, exist_ok=True)
    plan_path = PLANS_DIR / f"plan_{task_id}.md"
    plan_path.write_text(plan_content, encoding="utf-8")
    log.info(f"Plan written: plan_{task_id}.md")
    return plan_path
