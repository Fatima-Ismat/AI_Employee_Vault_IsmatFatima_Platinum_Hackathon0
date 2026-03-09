"""
CEO AI Weekly Briefing System
──────────────────────────────
Analyzes completed tasks, logs, and business goals to generate
an executive briefing report using Claude.

Output: AI_Employee_Vault/CEO_Briefing.md

Run:
  python -m analytics.ceo_briefing
  or via the orchestrator on a weekly schedule
"""

import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Make project root importable when run directly
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.config import (
    ANTHROPIC_API_KEY, CLAUDE_MODEL, MAX_TOKENS, DEMO_MODE,
    DONE_DIR, LOGS_DIR, VAULT_DIR,
)

if not DEMO_MODE:
    import anthropic
from utils.logger import get_logger
from utils.prompt_logger import log_prompt

log = get_logger("analytics.ceo_briefing")

CEO_BRIEFING_PATH = VAULT_DIR / "CEO_Briefing.md"
BUSINESS_GOALS_PATH = VAULT_DIR / "Business_Goals.md"

CEO_SYSTEM_PROMPT = """You are an elite AI Chief of Staff preparing an executive briefing for the CEO.
Your analysis must be sharp, data-driven, and actionable.

You will receive:
- A summary of tasks completed this week
- System logs and error patterns
- Business goals from the company handbook
- Key metrics

Generate a structured CEO briefing with these exact sections:
1. Executive Summary (3-4 sentences, high-level overview)
2. Revenue & Business Insights (inferred from tasks and communications)
3. Completed Work (key accomplishments, prioritized by impact)
4. Problems Detected (errors, failures, bottlenecks)
5. Opportunities Identified (patterns, growth areas, automation possibilities)
6. AI Recommendations (3-5 concrete action items for next week)

Be concise, confident, and CEO-ready. Use business language.
Format output as clean Markdown."""


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _week_start() -> datetime:
    now = datetime.now(timezone.utc)
    return now - timedelta(days=now.weekday())


def collect_completed_tasks(days: int = 7) -> list[dict]:
    """Read all task files from Done/ modified in the last N days."""
    DONE_DIR.mkdir(parents=True, exist_ok=True)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    tasks = []

    for f in DONE_DIR.glob("*.md"):
        try:
            mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff:
                continue
            content = f.read_text(encoding="utf-8")
            title = _extract_field(content, "title") or f.stem
            source = _extract_field(content, "source") or "unknown"
            priority = _extract_field(content, "priority") or "MEDIUM"
            tasks.append({
                "title":    title,
                "source":   source,
                "priority": priority,
                "file":     f.name,
                "completed_at": mtime.strftime("%Y-%m-%d %H:%M UTC"),
            })
        except Exception:
            pass

    return tasks


def collect_log_summary(days: int = 7) -> str:
    """Read recent log files and produce a summary string."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    lines = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    for log_file in sorted(LOGS_DIR.glob("*.md")):
        try:
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff:
                continue
            content = log_file.read_text(encoding="utf-8")
            lines.append(f"=== {log_file.stem} ===\n{content[:1500]}")
        except Exception:
            pass

    return "\n\n".join(lines) if lines else "No logs found for the period."


def collect_business_goals() -> str:
    """Read the Business_Goals.md file."""
    if BUSINESS_GOALS_PATH.exists():
        return BUSINESS_GOALS_PATH.read_text(encoding="utf-8")[:2000]
    return "Business goals not configured."


def collect_history_stats() -> dict:
    """Aggregate stats from history files."""
    from utils.config import HISTORY_DIR, AGENT_RUNS_LOG, APPROVALS_LOG
    stats = {
        "total_runs":       0,
        "successful_runs":  0,
        "failed_runs":      0,
        "total_approvals":  0,
        "approved":         0,
        "rejected":         0,
        "hitl_required":    0,
    }
    try:
        if AGENT_RUNS_LOG.exists():
            content = AGENT_RUNS_LOG.read_text(encoding="utf-8")
            stats["total_runs"]      = content.count("status:")
            stats["successful_runs"] = content.count("status: success")
            stats["failed_runs"]     = content.count("status: failed")
            stats["hitl_required"]   = content.count("hitl_required: true")

        if APPROVALS_LOG.exists():
            content = APPROVALS_LOG.read_text(encoding="utf-8")
            stats["total_approvals"] = content.count("decision:")
            stats["approved"]        = content.count("decision: approved")
            stats["rejected"]        = content.count("decision: rejected")
    except Exception:
        pass
    return stats


def generate_briefing(client, run_id: str) -> str:
    """Call Claude (or mock) to generate the CEO briefing. Returns Markdown string."""
    tasks = collect_completed_tasks()
    log_summary = collect_log_summary()
    goals = collect_business_goals()
    stats = collect_history_stats()

    task_summary = json.dumps(tasks, indent=2) if tasks else "No tasks completed this week."

    user_prompt = f"""Generate a CEO Weekly Briefing for the week of {_week_start().strftime('%B %d, %Y')}.

## Completed Tasks This Week ({len(tasks)} total)

```json
{task_summary}
```

## System Performance Metrics

- Total Agent Runs: {stats['total_runs']}
- Successful: {stats['successful_runs']}
- Failed: {stats['failed_runs']}
- Tasks Requiring Human Approval: {stats['hitl_required']}
- Approvals Granted: {stats['approved']}
- Approvals Rejected: {stats['rejected']}

## Business Goals

{goals}

## System Logs (Last 7 Days)

{log_summary[:2000]}

---

Please produce the complete CEO briefing now."""

    if DEMO_MODE:
        from agents.mock_responses import mock_ceo_briefing
        briefing_content = mock_ceo_briefing(tasks, stats)
        log_prompt(
            system_prompt=CEO_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            assistant_response=briefing_content,
            task_id="ceo_briefing",
            run_id=run_id,
        )
        return briefing_content

    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS,
            system=CEO_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        briefing_content = response.content[0].text

        log_prompt(
            system_prompt=CEO_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            assistant_response=briefing_content,
            task_id="ceo_briefing",
            run_id=run_id,
        )
        return briefing_content

    except Exception as e:
        log.error(f"Claude API error during CEO briefing: {e}")
        return _generate_template_briefing(tasks, stats)


def _generate_template_briefing(tasks: list[dict], stats: dict) -> str:
    """Fallback template briefing when Claude API is unavailable."""
    ts = _now_utc()
    task_list = "\n".join(
        f"- [{t['priority']}] {t['title']} (via {t['source']})" for t in tasks
    ) or "- No tasks completed this week"

    return f"""## Executive Summary

The AI Employee system processed {stats['total_runs']} tasks this week with a
{stats['successful_runs']}/{stats['total_runs']} success rate.
{stats['hitl_required']} tasks required human approval, demonstrating effective
risk governance. System operated autonomously with minimal intervention required.

## Revenue & Business Insights

- {len(tasks)} business tasks completed autonomously
- Email and communication handling fully automated
- Estimated time saved: {len(tasks) * 15} minutes of manual work

## Completed Work

{task_list}

## Problems Detected

- Failed tasks: {stats['failed_runs']} (review Logs/ for details)

## Opportunities Identified

- Consider automating repetitive task patterns identified in Inbox
- Approval rate {stats['approved']}/{stats['total_approvals']} suggests refining sensitivity thresholds

## AI Recommendations

1. Review and resolve {stats['failed_runs']} failed tasks
2. Expand watcher coverage to additional communication channels
3. Refine HITL thresholds based on approval patterns

---
*Generated by AI Employee — {ts}*"""


def write_ceo_briefing(content: str) -> Path:
    """Write the briefing to the vault."""
    ts = _now_utc()
    week_str = _week_start().strftime("%B %d, %Y")

    mode_label = f"{CLAUDE_MODEL} [Demo Mode — simulated]" if DEMO_MODE else CLAUDE_MODEL
    full_content = f"""# CEO AI Weekly Briefing
### Week of {week_str}

> **Generated:** {ts}
> **Model:** {mode_label}
> **System:** AI_Employee_Vault_IsmatFatima_Platinum_Hackathon0

---

{content}

---

*This briefing was generated automatically by the AI Employee analytics system.*
*All data sourced from AI_Employee_Vault/Done/, Logs/, and history/ directories.*
"""
    CEO_BRIEFING_PATH.parent.mkdir(parents=True, exist_ok=True)
    CEO_BRIEFING_PATH.write_text(full_content, encoding="utf-8")
    log.info(f"CEO Briefing written: {CEO_BRIEFING_PATH}")
    return CEO_BRIEFING_PATH


def run_weekly_briefing() -> Path:
    """Full pipeline: collect data → call Claude (or mock) → write briefing."""
    import uuid
    run_id = str(uuid.uuid4())[:8]
    log.info(f"Starting CEO Weekly Briefing generation... (demo_mode={DEMO_MODE})")

    client = None if DEMO_MODE else anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    content = generate_briefing(client, run_id)
    path = write_ceo_briefing(content)

    log.info(f"CEO Briefing complete: {path}")
    return path


def _extract_field(content: str, field: str) -> str:
    for line in content.splitlines():
        if line.startswith(f"{field}:"):
            return line.split(":", 1)[1].strip()
    return ""


if __name__ == "__main__":
    result = run_weekly_briefing()
    print(f"Briefing written to: {result}")
