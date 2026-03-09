"""
Demo Script — AI Employee Vault
────────────────────────────────
Demonstrates the full Platinum-tier pipeline without real credentials.

Demo flow:
  1. Simulated email arrives
  2. Watcher creates Inbox task
  3. Claude agent reads task and creates plan
  4. Task requires approval (sensitive: send external email)
  5. Script auto-approves after 5 seconds (simulating human)
  6. Agent executes MCP tool (demo mode)
  7. Task moves to Done
  8. All events logged to history/

Run:
  python demo/run_demo.py
"""

import sys
import time
from pathlib import Path

# Make project root importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.config import ensure_dirs, PENDING_DIR
from utils.vault_io import write_inbox_task, list_inbox_tasks
from utils.logger import get_logger
from agents.claude_agent import ClaudeAgent
from approval_system.hitl import check_approvals, process_approval_decision

log = get_logger("demo")

DEMO_SEPARATOR = "=" * 60


def step(n: int, msg: str) -> None:
    print(f"\n{DEMO_SEPARATOR}")
    print(f"  STEP {n}: {msg}")
    print(DEMO_SEPARATOR)


def main() -> None:
    print(DEMO_SEPARATOR)
    print("  AI Employee Vault — DEMO RUN")
    print("  Hackathon: Personal AI Employee #0")
    print("  Tier: Platinum")
    print(DEMO_SEPARATOR)

    # Ensure all vault directories exist
    ensure_dirs()

    # ── Step 1: Simulate email arrival ────────────────────────────────────────
    step(1, "Simulated email arrives from partner@acme.com")
    task_path = write_inbox_task(
        title="Email: Partnership proposal from Acme Corp",
        source="gmail_demo",
        body=(
            "**From:** partner@acme.com\n"
            "**Date:** 2026-03-06 09:00:00 UTC\n\n"
            "Hi,\n\n"
            "We'd like to explore a strategic partnership with your company. "
            "Could you please send us your partnership deck and schedule a call "
            "this week? We're looking to finalize terms by end of Q1.\n\n"
            "Best regards,\nAcme Corp Business Development"
        ),
        priority="HIGH",
        metadata={"sender": "partner@acme.com", "email_id": "demo_001"},
    )
    print(f"  Task created: {task_path.name}")
    time.sleep(1)

    # ── Step 2: Claude agent processes task ───────────────────────────────────
    step(2, "Claude agent reads task and creates execution plan")
    print("  Calling Claude API...")
    agent = ClaudeAgent()
    status = agent.process_task(task_path)
    print(f"  Agent status: {status}")
    time.sleep(1)

    if status == "pending_approval":
        # ── Step 3: Show pending approval file ───────────────────────────────
        step(3, "Task requires HITL approval — approval request created")
        pending_files = list(PENDING_DIR.glob("*.md"))
        if pending_files:
            approval_file = pending_files[0]
            print(f"  Approval file: {approval_file.name}")
            print(f"  Location: {PENDING_DIR}/")
            print("\n  In production: Human opens this file in Obsidian")
            print("  and changes 'status: pending' to 'status: approved'")

        # ── Step 4: Simulate human approval ──────────────────────────────────
        step(4, "Simulating human approval in 5 seconds...")
        for i in range(5, 0, -1):
            print(f"  Auto-approving in {i}s...", end="\r")
            time.sleep(1)

        if pending_files:
            approval_file = pending_files[0]
            content = approval_file.read_text(encoding="utf-8")
            content = content.replace("status: pending", "status: approved")
            approval_file.write_text(content, encoding="utf-8")
            print(f"\n  Approval file updated: status → approved")

        # ── Step 5: Orchestrator detects approval ─────────────────────────────
        step(5, "Orchestrator detects approval and executes task")
        decisions = check_approvals()
        for approval_file, task_id, decision in decisions:
            process_approval_decision(approval_file, task_id, decision)
            print(f"  Decision processed: {task_id} → {decision}")

            # Find and execute the original task
            from approval_system.hitl import find_task_in_pipeline
            task = find_task_in_pipeline(task_id)
            if task:
                plan = {
                    "summary": "Send partnership acknowledgment email",
                    "plan": ["Draft reply", "Send via email_mcp"],
                    "tools_required": ["email_mcp"],
                    "requires_approval": False,
                    "draft_action": (
                        "Dear Acme Corp,\n\n"
                        "Thank you for reaching out. We'd be happy to explore a partnership. "
                        "I'll send over our partnership deck and will have someone reach out "
                        "to schedule a call this week.\n\n"
                        "Best regards,\nAI Employee"
                    ),
                }
                agent2 = ClaudeAgent()
                final_status = agent2.process_approved_task(task, plan)
                print(f"  Execution status: {final_status}")

    # ── Step 6: Summary ───────────────────────────────────────────────────────
    step(6, "Demo complete — checking pipeline state")
    from utils.config import DONE_DIR, LOGS_DIR
    done_tasks = list(DONE_DIR.glob("*.md"))
    log_files  = list(LOGS_DIR.glob("*.md"))
    print(f"  Tasks in Done/: {len(done_tasks)}")
    print(f"  Log files: {len(log_files)}")
    print(f"  Prompt history: history/prompts.md")
    print(f"  Agent runs: history/agent_runs.md")
    print(f"  Approvals: history/approvals.md")

    print(f"\n{DEMO_SEPARATOR}")
    print("  DEMO COMPLETE")
    print("  Open AI_Employee_Vault/ in Obsidian to explore the results.")
    print(DEMO_SEPARATOR)


if __name__ == "__main__":
    main()
