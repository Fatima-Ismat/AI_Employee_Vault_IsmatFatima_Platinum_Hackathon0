"""
Ralph Wiggum — Autonomous Agent Loop
──────────────────────────────────────
The orchestrator that continuously drives the AI Employee pipeline.

Named after Ralph Wiggum from The Simpsons — runs forever, processes
everything that appears, never gets tired, never complains.

Loop behavior:
  1. Scan Inbox for new tasks
  2. For each task, invoke ClaudeAgent.process_task()
  3. Check Pending_Approval for human decisions
  4. Execute approved tasks immediately
  5. Log rejections and archive
  6. Sleep and repeat

Run:
  python -m orchestrator.agent_loop
  or via PM2: pm2 start ecosystem.config.js
"""

import signal
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from agents.claude_agent import ClaudeAgent
from approval_system.hitl import (
    check_approvals,
    find_task_in_pipeline,
    process_approval_decision,
)
from utils.config import LOOP_INTERVAL, DONE_DIR, REJECTED_DIR
from utils.logger import get_logger
from utils.vault_io import (
    list_inbox_tasks,
    move_task,
    now_utc,
    update_task_status,
    read_task,
)
from utils.prompt_logger import log_agent_run

log = get_logger("orchestrator.ralph")

_SHUTDOWN = False


def _handle_signal(sig, frame):
    global _SHUTDOWN
    log.info("Shutdown signal received — finishing current cycle then stopping")
    _SHUTDOWN = True


signal.signal(signal.SIGINT, _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


def process_inbox() -> int:
    """Process all tasks currently in Inbox. Returns number of tasks handled."""
    tasks = list_inbox_tasks()
    if not tasks:
        return 0

    log.info(f"Found {len(tasks)} task(s) in Inbox")
    count = 0
    for task_path in tasks:
        if _SHUTDOWN:
            break
        try:
            agent = ClaudeAgent()
            status = agent.process_task(task_path)
            log.info(f"Task {task_path.name} → {status}")
            count += 1
        except Exception as e:
            log.error(f"Failed to process {task_path.name}: {e}")
    return count


def process_pending_approvals() -> int:
    """Check for human approval decisions and execute/archive accordingly."""
    decisions = check_approvals()
    if not decisions:
        return 0

    count = 0
    for approval_file, task_id, decision in decisions:
        try:
            process_approval_decision(approval_file, task_id, decision)

            if decision == "approved":
                task_path = find_task_in_pipeline(task_id)
                if task_path and task_path.exists():
                    # Re-read and re-parse plan for execution
                    from utils.vault_io import PLANS_DIR
                    from utils.config import PLANS_DIR as PD
                    plan_file = PD / f"plan_{task_id}.md"
                    # Build a minimal plan dict from the approval file content
                    plan = _extract_plan_from_approval(approval_file if approval_file.exists()
                                                        else _find_archived_approval(task_id))
                    agent = ClaudeAgent()
                    agent.process_approved_task(task_path, plan)
                else:
                    log.warning(f"Approved task file not found for task_id={task_id}")

            elif decision == "rejected":
                task_path = find_task_in_pipeline(task_id)
                if task_path and task_path.exists():
                    update_task_status(task_path, "rejected")
                    move_task(task_path, REJECTED_DIR)
                    log_agent_run(
                        task_id=task_id,
                        status="rejected",
                        summary="Task was rejected by human reviewer.",
                        hitl_required=True,
                        run_id=str(uuid.uuid4())[:8],
                        started_at=now_utc(),
                        completed_at=now_utc(),
                    )
                    log.info(f"Task rejected and archived: {task_id}")

            count += 1
        except Exception as e:
            log.error(f"Error processing approval for {task_id}: {e}")

    return count


def _find_archived_approval(task_id: str) -> Path:
    from utils.config import APPROVED_DIR, REJECTED_DIR
    for folder in (APPROVED_DIR, REJECTED_DIR):
        for f in folder.glob("*.md"):
            if task_id in f.stem:
                return f
    return Path("/dev/null")


def _extract_plan_from_approval(approval_file: Path) -> dict:
    """Build a minimal plan dict from an approval file for re-execution."""
    if not approval_file.exists():
        return {"summary": "Approved task", "plan": [], "tools_required": [], "draft_action": ""}
    content = approval_file.read_text(encoding="utf-8")
    # Extract Draft Action section
    draft = ""
    in_draft = False
    for line in content.splitlines():
        if "## Draft Action" in line:
            in_draft = True
            continue
        if in_draft and line.startswith("##"):
            break
        if in_draft:
            draft += line + "\n"
    return {
        "summary": "Approved task execution",
        "plan": ["Execute approved action"],
        "tools_required": [],
        "requires_approval": False,
        "draft_action": draft.strip().strip("`"),
    }


def run_loop() -> None:
    """Ralph Wiggum main loop — runs until SIGTERM/SIGINT."""
    log.info("=" * 60)
    log.info("Ralph Wiggum Autonomous Agent Loop — STARTED")
    log.info(f"Loop interval: {LOOP_INTERVAL}s")
    log.info("=" * 60)

    cycle = 0
    while not _SHUTDOWN:
        cycle += 1
        log.info(f"--- Cycle {cycle} | {now_utc()} ---")

        try:
            inbox_count = process_inbox()
            approval_count = process_pending_approvals()

            if inbox_count == 0 and approval_count == 0:
                log.info("Nothing to do — sleeping...")
        except Exception as e:
            log.error(f"Unhandled error in loop cycle {cycle}: {e}")

        if not _SHUTDOWN:
            time.sleep(LOOP_INTERVAL)

    log.info("Ralph Wiggum loop stopped cleanly.")


if __name__ == "__main__":
    run_loop()
