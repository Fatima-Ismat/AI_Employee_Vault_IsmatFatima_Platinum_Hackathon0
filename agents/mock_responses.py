"""
Demo Mode — Mock Claude Responses
───────────────────────────────────
When DEMO_MODE=true all Claude API calls are replaced with realistic
pre-built responses so the full pipeline runs without any paid credits.

Every public function here mirrors exactly what the real Claude API
would return, keeping the architecture unchanged.

All responses are clearly stamped:
  [Demo Mode / Simulated Claude Response]
"""

import json
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


# ── Keyword → plan templates ──────────────────────────────────────────────────

_PLAN_TEMPLATES: list[tuple[list[str], dict]] = [
    # Email / partnership
    (["email", "partnership", "proposal", "reply", "respond"],
     {
         "summary": "Draft and send a professional reply to the incoming email",
         "plan": [
             "Step 1: Read and analyse the incoming email content",
             "Step 2: Draft a professional reply acknowledging the request",
             "Step 3: Route draft through HITL approval (external email policy)",
             "Step 4: Send approved reply via email_mcp",
             "Step 5: Log communication to Done/ and history/",
         ],
         "tools_required": ["email_mcp"],
         "requires_approval": True,
         "approval_reason": "Sending external email requires human sign-off per Company_Handbook policy",
         "draft_action": (
             "Dear Partner,\n\n"
             "Thank you for reaching out. We have reviewed your proposal and are "
             "excited about the potential synergies between our organisations.\n\n"
             "We would be delighted to schedule an introductory call this week. "
             "I will have the relevant team member send over a calendar invite "
             "along with our standard NDA for your review.\n\n"
             "Looking forward to exploring this opportunity together.\n\n"
             "Best regards,\nAI Employee (on behalf of the team)"
         ),
         "priority": "HIGH",
         "estimated_time": "5 minutes",
     }),

    # File / document
    (["file", "document", "report", "upload", "pdf", "draft"],
     {
         "summary": "Review newly detected file and determine required action",
         "plan": [
             "Step 1: Identify file type and context from metadata",
             "Step 2: Check sensitivity level (financial / legal / public)",
             "Step 3: If sensitive, route to HITL approval",
             "Step 4: Log file details to filesystem_mcp output folder",
             "Step 5: Notify relevant stakeholder via email_mcp if required",
         ],
         "tools_required": ["filesystem_mcp"],
         "requires_approval": True,
         "approval_reason": "File contains 'financial' keyword — requires human review before action",
         "draft_action": "File has been catalogued and flagged for review. See agent_outputs/ for details.",
         "priority": "MEDIUM",
         "estimated_time": "3 minutes",
     }),

    # WhatsApp / urgent / meeting
    (["whatsapp", "urgent", "call", "meeting", "schedule", "client"],
     {
         "summary": "Respond to urgent WhatsApp message and schedule emergency call",
         "plan": [
             "Step 1: Acknowledge the urgency and log the request",
             "Step 2: Check calendar availability via calendar_mcp",
             "Step 3: Propose two available time slots",
             "Step 4: Request HITL approval before booking external meeting",
             "Step 5: Send calendar invite once approved",
         ],
         "tools_required": ["calendar_mcp", "email_mcp"],
         "requires_approval": True,
         "approval_reason": "Scheduling external meeting requires human confirmation",
         "draft_action": (
             "Acknowledged your urgent message. "
             "I am checking availability and will send a calendar invite within the next 10 minutes. "
             "Proposed slots: Today 3 PM or 4 PM UTC."
         ),
         "priority": "HIGH",
         "estimated_time": "4 minutes",
     }),

    # Invoice / payment / financial
    (["invoice", "payment", "financial", "billing", "cost"],
     {
         "summary": "Process incoming financial request and route for approval",
         "plan": [
             "Step 1: Extract invoice details (amount, vendor, due date)",
             "Step 2: Cross-reference with approved vendor list",
             "Step 3: Flag for finance team review — HITL required",
             "Step 4: Draft acknowledgement email to sender",
             "Step 5: Log to financial tracking in filesystem_mcp",
         ],
         "tools_required": ["email_mcp", "filesystem_mcp"],
         "requires_approval": True,
         "approval_reason": "Financial transaction requires explicit human authorisation",
         "draft_action": (
             "Thank you for submitting invoice. "
             "It has been received and is pending approval from our finance team. "
             "Expected processing time: 2-3 business days."
         ),
         "priority": "HIGH",
         "estimated_time": "6 minutes",
     }),
]

_DEFAULT_PLAN: dict = {
    "summary": "Analyse incoming task and execute appropriate response",
    "plan": [
        "Step 1: Read and classify the incoming task",
        "Step 2: Identify priority and sensitivity level",
        "Step 3: Draft appropriate response or action",
        "Step 4: Log output and update task status",
    ],
    "tools_required": [],
    "requires_approval": False,
    "approval_reason": "",
    "draft_action": "Task has been processed and logged by the AI Employee.",
    "priority": "MEDIUM",
    "estimated_time": "2 minutes",
}


def mock_task_plan(task_content: str) -> str:
    """
    Return a JSON string mimicking a real Claude task-planning response.
    Inspects task_content for keywords to pick the most relevant template.
    """
    lower = task_content.lower()
    chosen = _DEFAULT_PLAN
    for keywords, template in _PLAN_TEMPLATES:
        if any(kw in lower for kw in keywords):
            chosen = template
            break

    payload = {**chosen, "_demo_mode": True}
    response_json = json.dumps(payload, indent=2)

    return (
        f"[Demo Mode / Simulated Claude Response]\n"
        f"Model: claude-sonnet-4-6 (mocked — no API call made)\n"
        f"Timestamp: {_now()}\n\n"
        f"{response_json}"
    )


def mock_ceo_briefing(tasks: list[dict], stats: dict) -> str:
    """
    Return a Markdown string mimicking a real Claude CEO briefing.
    """
    task_count = len(tasks)
    success_rate = (
        round(stats["successful_runs"] / max(stats["total_runs"], 1) * 100, 1)
        if stats["total_runs"] > 0 else 100
    )
    task_bullets = "\n".join(
        f"- **[{t['priority']}]** {t['title']} *(via {t['source']})*"
        for t in tasks
    ) or "- No tasks completed in the reporting window"

    return f"""> **[Demo Mode / Simulated Claude Response]**
> Model: claude-sonnet-4-6 (mocked — no API call made)
> Generated: {_now()}

## Executive Summary

This week the AI Employee system operated at **{success_rate}% efficiency**, processing
**{task_count} tasks** autonomously across email, filesystem, and WhatsApp channels.
Human-in-the-Loop approval was triggered for {stats.get('hitl_required', 0)} high-sensitivity
actions, all of which were reviewed and actioned within SLA. The system demonstrated
consistent performance with zero unrecovered failures.

## Revenue & Business Insights

- **{task_count} business tasks** completed without human initiation
- Estimated **{task_count * 18} minutes** of staff time saved this week
- All external communications routed through HITL — zero compliance breaches
- Partnership and client communications processed within 4-hour SLA target
- Financial requests flagged and escalated correctly 100% of the time

## Completed Work

{task_bullets}

- Agent executed {stats.get('successful_runs', task_count)} successful task runs
- {stats.get('hitl_required', 0)} tasks routed through human approval workflow
- Pipeline maintained clean state: no stale tasks in Needs_Action

## Problems Detected

- Failed runs: **{stats.get('failed_runs', 0)}** — within acceptable threshold (<5%)
- No stalled tasks detected in Needs_Action folder
- No inbox overflow events this week
- All watchers reporting healthy status

## Opportunities Identified

1. **Email volume** trending upward — consider adding a second email watcher instance
2. **WhatsApp urgency** patterns suggest a dedicated escalation pipeline would reduce HITL latency
3. **Filesystem monitoring** could be extended to cloud storage (S3/GCS) for broader coverage
4. Several repetitive task types are candidates for fully autonomous execution (no HITL required)

## AI Recommendations

1. **Expand HITL thresholds** — current approval rate is high; safe to automate standard email replies
2. **Schedule weekly pipeline cleanup** — archive Done/ tasks older than 30 days
3. **Add Slack watcher** — capture internal communication as task source
4. **Enable calendar_mcp** for autonomous meeting scheduling for internal events
5. **Review rejected tasks** — {stats.get('rejected', 0)} rejections may indicate over-triggering of HITL

---
*Simulated executive briefing — architecture identical to live Claude output.*
"""


def mock_cloud_plan(task_content: str, agent_id: str) -> str:
    """
    Return a JSON string for the cloud agent's task plan mock.
    """
    lower = task_content.lower()
    chosen = _DEFAULT_PLAN.copy()
    for keywords, template in _PLAN_TEMPLATES:
        if any(kw in lower for kw in keywords):
            chosen = template.copy()
            break

    # Cloud agent marks safe/simple tasks as cloud_executable
    is_safe = not chosen.get("requires_approval", False)
    payload = {
        **chosen,
        "cloud_executable": is_safe,
        "_demo_mode": True,
        "_agent_id": agent_id,
    }
    response_json = json.dumps(payload, indent=2)

    return (
        f"[Demo Mode / Simulated Claude Response — Cloud Agent: {agent_id}]\n"
        f"Model: claude-sonnet-4-6 (mocked — no API call made)\n"
        f"Timestamp: {_now()}\n\n"
        f"{response_json}"
    )
