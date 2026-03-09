"""
Human-in-the-Loop (HITL) Approval System
─────────────────────────────────────────
Manages sensitive-action approval workflow through the Obsidian vault.

Workflow:
  1. Agent detects sensitive action → create_approval_request()
  2. File written to Pending_Approval/ with status: pending
  3. Human opens file in Obsidian and changes status to approved/rejected
  4. Orchestrator calls check_approvals() to detect decisions
  5. Agent executes (approved) or logs rejection (rejected)
"""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from utils.config import (
    SENSITIVE_KEYWORDS, PENDING_DIR, APPROVED_DIR, REJECTED_DIR,
    NEEDS_ACTION_DIR,
)
from utils.logger import get_logger
from utils.prompt_logger import log_approval
from utils.vault_io import now_utc, move_task

log = get_logger("hitl")


def is_sensitive_task(task_content: str) -> bool:
    """Return True if the task content contains sensitive keywords."""
    lower = task_content.lower()
    return any(keyword in lower for keyword in SENSITIVE_KEYWORDS)


def create_approval_request(
    task_path: Path,
    task_id: str,
    plan: dict,
    run_id: str = "",
) -> Path:
    """
    Write an approval request file to Pending_Approval/.
    Returns the path of the created approval file.
    """
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    approval_id = str(uuid.uuid4())[:8]
    ts = now_utc()

    steps_md = "\n".join(
        f"- [ ] {step}" for step in plan.get("plan", ["Review and approve"])
    )
    tools_md = ", ".join(plan.get("tools_required", [])) or "none"

    content = f"""---
approval_id: {approval_id}
task_id: {task_id}
run_id: {run_id}
requested_at: {ts}
status: pending
---

# Approval Request: {task_id}

**Requested:** {ts}
**Approval ID:** `{approval_id}`

> **To approve:** Change `status: pending` to `status: approved`
> **To reject:** Change `status: pending` to `status: rejected`
> Optionally add a `rejection_reason:` field below the frontmatter.

---

## Task Summary

{plan.get("summary", "No summary available")}

## Proposed Execution Plan

{steps_md}

## Tools That Will Be Used

{tools_md}

## Reason Approval Required

{plan.get("approval_reason", "Sensitive action detected")}

## Draft Action

```
{plan.get("draft_action", "")}
```

---

## Human Decision

<!-- Change status above to: approved | rejected -->
<!-- Add notes here if needed -->
"""
    approval_path = PENDING_DIR / f"approval_{approval_id}_{task_id[:20]}.md"
    approval_path.write_text(content, encoding="utf-8")
    log.info(f"Approval request created: {approval_path.name}")
    return approval_path


def check_approvals() -> list[tuple[Path, str, str]]:
    """
    Scan Pending_Approval/ for files with status: approved or rejected.
    Returns list of (file_path, task_id, decision) tuples.
    """
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    results = []

    for approval_file in PENDING_DIR.glob("*.md"):
        content = approval_file.read_text(encoding="utf-8")
        status = _extract_frontmatter_field(content, "status")
        task_id = _extract_frontmatter_field(content, "task_id")

        if status in ("approved", "rejected"):
            results.append((approval_file, task_id or approval_file.stem, status))
            log.info(f"Approval decision found: {approval_file.name} → {status}")

    return results


def process_approval_decision(
    approval_file: Path,
    task_id: str,
    decision: str,
) -> None:
    """
    Move approval file to Approved/ or Rejected/ and log the decision.
    """
    requested_at = _extract_frontmatter_field(
        approval_file.read_text(encoding="utf-8"), "requested_at"
    ) or ""
    approval_id = _extract_frontmatter_field(
        approval_file.read_text(encoding="utf-8"), "approval_id"
    ) or str(uuid.uuid4())[:8]

    content = approval_file.read_text(encoding="utf-8")
    action_description = _extract_section(content, "Draft Action")

    if decision == "approved":
        dest = APPROVED_DIR
    else:
        dest = REJECTED_DIR

    dest.mkdir(parents=True, exist_ok=True)
    move_task(approval_file, dest)

    log_approval(
        task_id=task_id,
        decision=decision,
        action_description=action_description,
        approval_id=approval_id,
        requested_at=requested_at,
        decided_at=now_utc(),
    )
    log.info(f"Approval {decision}: task={task_id}")


def find_task_in_pipeline(task_id: str) -> Optional[Path]:
    """Search Needs_Action and Pending_Approval for the task file."""
    for folder in (NEEDS_ACTION_DIR, PENDING_DIR):
        folder.mkdir(parents=True, exist_ok=True)
        for f in folder.glob("*.md"):
            if task_id in f.stem:
                return f
    return None


def _extract_frontmatter_field(content: str, field: str) -> str:
    """Extract a YAML frontmatter field value."""
    for line in content.splitlines():
        if line.startswith(f"{field}:"):
            return line.split(":", 1)[1].strip()
    return ""


def _extract_section(content: str, section_title: str) -> str:
    """Extract text under a markdown heading."""
    lines = content.splitlines()
    in_section = False
    result = []
    for line in lines:
        if line.strip().startswith("##") and section_title in line:
            in_section = True
            continue
        if in_section:
            if line.strip().startswith("##"):
                break
            result.append(line)
    return "\n".join(result).strip()
