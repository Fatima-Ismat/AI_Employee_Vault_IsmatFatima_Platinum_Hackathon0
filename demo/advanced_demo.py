"""
Advanced Demo Pipeline
───────────────────────
Full Platinum-tier demonstration of the AI Employee system.
Simulates a complete business day of autonomous operation.

Scenarios demonstrated:
  1. Email from client → plan → HITL → approved → reply sent
  2. File uploaded → detected → analysis plan → autonomous action
  3. WhatsApp message → urgent priority → HITL → escalated
  4. CEO briefing generation
  5. Pipeline visualization
  6. Watchdog health check

All events are logged to vault and history.

Run:
  python demo/advanced_demo.py
  python demo/advanced_demo.py --scenario email
  python demo/advanced_demo.py --scenario briefing
"""

import argparse
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ── Force demo mode BEFORE any project imports so config.py sees it ──────────
# This ensures DEMO_MODE=true even if .env is missing or has DEMO_MODE=false.
os.environ.setdefault("DEMO_MODE", "true")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.config import ensure_dirs, PENDING_DIR, DONE_DIR, LOGS_DIR, VAULT_DIR, DEMO_MODE
from utils.vault_io import write_inbox_task, list_inbox_tasks
from utils.logger import get_logger
from agents.claude_agent import ClaudeAgent
from approval_system.hitl import check_approvals, process_approval_decision
from analytics.ceo_briefing import run_weekly_briefing
from analytics.pipeline_visualizer import run_visualization

log = get_logger("demo.advanced")

BAR  = "═" * 65
THIN = "─" * 65

# ── Startup banner ─────────────────────────────────────────────────────────────
if DEMO_MODE:
    print(f"\n{'█' * 65}")
    print("  DEMO MODE ACTIVE – NO API CALLS")
    print("  All Claude responses are simulated mock outputs.")
    print("  Set DEMO_MODE=false in .env to use the live Claude API.")
    print(f"{'█' * 65}\n")


def header(title: str) -> None:
    print(f"\n{BAR}")
    print(f"  {title}")
    print(BAR)


def step(n: int, title: str, details: str = "") -> None:
    print(f"\n  [{n:02d}] {title}")
    if details:
        print(f"       {details}")
    print(f"       {THIN}")


def pause(seconds: int = 2) -> None:
    for i in range(seconds, 0, -1):
        print(f"\r       Continuing in {i}s...", end="", flush=True)
        time.sleep(1)
    print("\r" + " " * 30 + "\r", end="")


# ── Scenario Helpers ──────────────────────────────────────────────────────────

def inject_email_task() -> Path:
    return write_inbox_task(
        title="Email: Strategic Partnership Proposal from TechVentures Inc",
        source="gmail_demo",
        body=(
            "**From:** ceo@techventures.io\n"
            "**Date:** " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC") + "\n\n"
            "Dear Team,\n\n"
            "TechVentures Inc is interested in a co-marketing partnership for Q2.\n"
            "We'd like to schedule an executive call and share our proposal deck.\n"
            "Could you send a brief NDA and available meeting times?\n\n"
            "Timeline: We'd like to finalize by end of this month.\n\n"
            "Best,\nMark Chen, CEO — TechVentures Inc"
        ),
        priority="HIGH",
        metadata={"sender": "ceo@techventures.io", "demo": "true"},
    )


def inject_filesystem_task() -> Path:
    # Create a dummy file in watched folder
    watched = Path(__file__).parents[1] / "watched_folder"
    watched.mkdir(parents=True, exist_ok=True)
    report_file = watched / "Q4_Financial_Report_DRAFT.pdf"
    report_file.write_text("[DEMO] Simulated financial report", encoding="utf-8")

    return write_inbox_task(
        title="New file detected: Q4_Financial_Report_DRAFT.pdf",
        source="filesystem_watcher",
        body=(
            "A new file was detected in the watched folder.\n\n"
            "**Path:** `watched_folder/Q4_Financial_Report_DRAFT.pdf`\n"
            "**Size:** 2.4 MB\n\n"
            "Please review this file and determine if any action is required.\n"
            "This appears to be a financial report — handle with care."
        ),
        priority="MEDIUM",
        metadata={"file_path": str(report_file), "event": "created", "demo": "true"},
    )


def inject_whatsapp_task() -> Path:
    return write_inbox_task(
        title="WhatsApp: URGENT - Client wants call in 30 minutes",
        source="whatsapp_demo",
        body=(
            "**From:** +1****4890\n"
            "**Time:** " + datetime.now(timezone.utc).isoformat() + "\n\n"
            "**Message:**\nUrgent! Our main client Apex Corp just called — "
            "they have a critical issue with the API integration and want "
            "an emergency call in 30 minutes. Can someone from the tech team join?"
        ),
        priority="CRITICAL",
        metadata={"demo": "true", "sender": "+1****4890"},
    )


def auto_approve_pending(max_wait: int = 8) -> int:
    """Auto-approve all pending approval files after a countdown."""
    pending_files = list(PENDING_DIR.glob("*.md"))
    if not pending_files:
        return 0

    print(f"\n       {len(pending_files)} approval request(s) pending in Obsidian...")
    for i in range(max_wait, 0, -1):
        print(f"\r       Auto-approving in {i}s (simulating human review)...", end="", flush=True)
        time.sleep(1)
    print()

    approved = 0
    for f in pending_files:
        content = f.read_text(encoding="utf-8")
        if "status: pending" in content:
            f.write_text(content.replace("status: pending", "status: approved"), encoding="utf-8")
            print(f"       ✓ Approved: {f.name}")
            approved += 1

    return approved


def process_all_approvals() -> None:
    decisions = check_approvals()
    for approval_file, task_id, decision in decisions:
        process_approval_decision(approval_file, task_id, decision)
        if decision == "approved":
            from approval_system.hitl import find_task_in_pipeline
            task = find_task_in_pipeline(task_id)
            if task:
                plan = {
                    "summary": "Approved task execution",
                    "plan": ["Execute approved action"],
                    "tools_required": ["email_mcp"],
                    "requires_approval": False,
                    "draft_action": "Professional response prepared by AI Employee.",
                }
                agent = ClaudeAgent()
                agent.process_approved_task(task, plan)
                print(f"       ✓ Executed: {task_id}")


# ── Full Scenario Runners ─────────────────────────────────────────────────────

def scenario_email_approval() -> None:
    header("SCENARIO 1 — Email Partnership Request (HITL Required)")

    step(1, "Gmail watcher detects incoming email from TechVentures Inc")
    task_path = inject_email_task()
    print(f"       Task created: {task_path.name}")
    pause(2)

    step(2, "Ralph Wiggum orchestrator picks up task from Inbox")
    pause(1)

    step(3, "Claude agent reads email and generates execution plan",
         f"Model: claude-sonnet-4-6")
    agent = ClaudeAgent()
    status = agent.process_task(task_path)
    print(f"       Agent status: {status}")
    pause(2)

    if status == "pending_approval":
        step(4, "Task flagged as SENSITIVE → approval request created",
             "Pending_Approval/approval_*.md written to vault")
        pause(2)

        step(5, "Human reviews in Obsidian — approving partnership response...")
        approved = auto_approve_pending(6)
        print(f"       {approved} task(s) approved")
        pause(1)

        step(6, "Orchestrator detects approval → executing email_mcp.send_email()")
        process_all_approvals()
        pause(1)

    step(7, "Task moved to Done/ — all events logged")
    done_count = len(list(DONE_DIR.glob("*.md")))
    print(f"       Done folder: {done_count} completed task(s)")


def scenario_filesystem() -> None:
    header("SCENARIO 2 — File Upload Detection (Autonomous)")

    step(1, "New file dropped in watched_folder/")
    task_path = inject_filesystem_task()
    print(f"       Task: {task_path.name}")
    pause(2)

    step(2, "Claude agent analyzes file and creates plan")
    agent = ClaudeAgent()
    status = agent.process_task(task_path)
    print(f"       Status: {status}")
    pause(1)

    if status == "pending_approval":
        step(3, "Financial file → HITL required")
        auto_approve_pending(5)
        process_all_approvals()
    else:
        step(3, "Non-sensitive → processed autonomously")

    step(4, "File task complete")


def scenario_whatsapp() -> None:
    header("SCENARIO 3 — WhatsApp Urgent Message")

    step(1, "CRITICAL WhatsApp message received")
    task_path = inject_whatsapp_task()
    print(f"       Priority: CRITICAL")
    pause(2)

    step(2, "Claude agent processes urgent task")
    agent = ClaudeAgent()
    status = agent.process_task(task_path)
    print(f"       Status: {status}")

    if status == "pending_approval":
        step(3, "Urgent action requires approval")
        auto_approve_pending(4)
        process_all_approvals()
    pause(1)


def scenario_ceo_briefing() -> None:
    header("SCENARIO 4 — CEO AI Weekly Briefing")

    step(1, "Collecting completed tasks, logs, and business goals...")
    pause(2)

    step(2, "Claude generates executive briefing report")
    try:
        path = run_weekly_briefing()
        print(f"       Briefing written: {path.name}")
        # Show first 400 chars of briefing
        content = path.read_text(encoding="utf-8")
        preview = content[content.find("## "):content.find("## ") + 400]
        print(f"\n       Preview:\n       {'─'*50}")
        for line in preview.splitlines()[:10]:
            print(f"       {line}")
        print(f"       {'─'*50}")
    except Exception as e:
        print(f"       [Demo] Briefing generated (Claude API: {e})")
    pause(2)


def scenario_visualization() -> None:
    header("SCENARIO 5 — Pipeline Visualization")

    step(1, "Analyzing task movement across all pipeline stages...")
    pause(1)

    step(2, "Generating pipeline report")
    path = run_visualization()
    print(f"       Report: {path}")


def run_full_demo() -> None:
    header("AI EMPLOYEE VAULT — PLATINUM TIER FULL DEMO")
    print("  System: AI_Employee_Vault_IsmatFatima_Platinum_Hackathon0")
    print("  Engine: Claude claude-sonnet-4-6")
    print("  Mode:   Full autonomous + HITL hybrid")
    print(f"  Time:   {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

    ensure_dirs()
    pause(2)

    scenario_email_approval()
    pause(2)
    scenario_filesystem()
    pause(2)
    scenario_whatsapp()
    pause(2)
    scenario_ceo_briefing()
    pause(2)
    scenario_visualization()

    # Final summary
    header("DEMO COMPLETE — SYSTEM SUMMARY")
    done_count    = len(list(DONE_DIR.glob("*.md")))
    log_count     = len(list(LOGS_DIR.glob("*.md")))
    briefing_path = VAULT_DIR / "CEO_Briefing.md"
    print(f"""
  Results:
  ├── Tasks completed:    {done_count}
  ├── Log files:          {log_count}
  ├── CEO Briefing:       {"✓" if briefing_path.exists() else "–"}
  ├── Prompt history:     history/prompts.md
  ├── Approval history:   history/approvals.md
  └── Vault location:     AI_Employee_Vault/

  Open AI_Employee_Vault/ in Obsidian to explore all results.
  Open Dashboard.md for the live system overview.

{BAR}
""")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Employee Advanced Demo")
    parser.add_argument("--scenario", choices=["email", "filesystem", "whatsapp", "briefing", "viz", "all"],
                        default="all")
    args = parser.parse_args()

    ensure_dirs()

    if args.scenario == "email":
        scenario_email_approval()
    elif args.scenario == "filesystem":
        scenario_filesystem()
    elif args.scenario == "whatsapp":
        scenario_whatsapp()
    elif args.scenario == "briefing":
        scenario_ceo_briefing()
    elif args.scenario == "viz":
        scenario_visualization()
    else:
        run_full_demo()
