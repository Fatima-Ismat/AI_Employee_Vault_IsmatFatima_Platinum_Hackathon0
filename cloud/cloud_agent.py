"""
Cloud AI Employee Agent
────────────────────────
Cloud-mode agent that monitors a shared/remote vault (S3, GCS, or mounted path),
processes Inbox tasks, prepares drafts, and creates approval requests.

Sensitive actions are delegated back to the local agent via the message bus.

Architecture:
  Cloud Agent                  Local Agent
       │                            │
       ├─── read shared Inbox ──────┤
       ├─── generate plan  ─────────┤
       ├─── sensitive? ─────────────┼──► Pending_Approval/ (local HITL)
       ├─── safe actions ───────────┼──► Execute directly
       └─── sync Done ─────────────┘

Configuration (.env):
  CLOUD_VAULT_PATH   Path to shared/mounted vault (local path or mount point)
  CLOUD_AGENT_ID     Unique ID for this cloud agent instance
  CLOUD_SYNC_INTERVAL Seconds between sync cycles
"""

import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.config import (
    ANTHROPIC_API_KEY, CLAUDE_MODEL, MAX_TOKENS, DEMO_MODE,
    INBOX_DIR, NEEDS_ACTION_DIR, DONE_DIR, PENDING_DIR, PLANS_DIR,
)

if not DEMO_MODE:
    import anthropic
from utils.logger import get_logger
from utils.prompt_logger import log_prompt, log_agent_run
from utils.vault_io import write_plan, move_task, update_task_status, now_utc, read_task
from approval_system.hitl import is_sensitive_task, create_approval_request

log = get_logger("cloud.agent")

CLOUD_VAULT_PATH    = Path(os.getenv("CLOUD_VAULT_PATH", str(Path(__file__).parents[1] / "AI_Employee_Vault")))
CLOUD_AGENT_ID      = os.getenv("CLOUD_AGENT_ID", f"cloud-agent-{str(uuid.uuid4())[:6]}")
CLOUD_SYNC_INTERVAL = int(os.getenv("CLOUD_SYNC_INTERVAL", "30"))

CLOUD_SYSTEM_PROMPT = """You are a cloud-deployed AI Employee agent.
You work remotely, processing tasks from a shared vault.
For sensitive actions (emails, payments, external comms), always set requires_approval: true.
For safe actions (summaries, drafts, read-only analysis), you may proceed autonomously.

Always output structured JSON:
{
  "summary": "...",
  "plan": ["step1", "step2"],
  "tools_required": ["email_mcp"],
  "requires_approval": true,
  "approval_reason": "...",
  "draft_action": "...",
  "cloud_executable": false,
  "priority": "MEDIUM"
}

Set cloud_executable: true only for tasks you can complete without MCP tools
(summarization, drafting, analysis, classification)."""


class CloudAgent:
    """Cloud-mode agent — processes tasks and delegates sensitive actions."""

    def __init__(self) -> None:
        self.agent_id = CLOUD_AGENT_ID
        if DEMO_MODE:
            self.client = None
            log.info(f"Cloud Agent running in DEMO MODE: {self.agent_id}")
        else:
            self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        log.info(f"Cloud Agent initialized: {self.agent_id}")

    def scan_inbox(self) -> list[Path]:
        """Return unprocessed tasks from the (possibly remote) Inbox."""
        inbox = CLOUD_VAULT_PATH / "Inbox"
        inbox.mkdir(parents=True, exist_ok=True)
        return sorted(
            [p for p in inbox.glob("*.md") if not p.name.startswith(".")],
            key=lambda p: p.stat().st_ctime,
        )

    def process_task(self, task_path: Path) -> str:
        """Process a single task in cloud mode. Returns status string."""
        run_id = str(uuid.uuid4())[:8]
        started = now_utc()
        task_id = task_path.stem
        content = read_task(task_path)

        log.info(f"[{self.agent_id}] Processing: {task_path.name}")

        # Move to Needs_Action
        needs_action = CLOUD_VAULT_PATH / "Needs_Action"
        needs_action.mkdir(parents=True, exist_ok=True)
        task_path = move_task(task_path, needs_action)
        update_task_status(task_path, "cloud_processing")

        # Call Claude
        user_prompt = f"""[Cloud Agent: {self.agent_id}]

Please analyze and plan the following task:

---
{content}
---

Respond with the JSON structure specified."""

        try:
            if DEMO_MODE:
                from agents.mock_responses import mock_cloud_plan
                response_text = mock_cloud_plan(content, self.agent_id)
            else:
                resp = self.client.messages.create(
                    model=CLAUDE_MODEL,
                    max_tokens=MAX_TOKENS,
                    system=CLOUD_SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                response_text = resp.content[0].text
        except Exception as e:
            log.error(f"Claude API error: {e}")
            return "failed"

        log_prompt(CLOUD_SYSTEM_PROMPT, user_prompt, response_text, task_id, run_id)

        plan = self._parse_plan(response_text)
        plan_content = self._format_plan(task_id, plan, response_text)
        write_plan(task_id, plan_content)

        # Determine execution path
        if is_sensitive_task(content) or plan.get("requires_approval", True):
            # Delegate to local HITL
            pending = CLOUD_VAULT_PATH / "Pending_Approval"
            create_approval_request(task_path, task_id, plan, run_id)
            update_task_status(task_path, "pending_approval")
            move_task(task_path, pending)
            log_agent_run(task_id, "pending_approval",
                          f"Cloud agent delegated to HITL: {task_id}",
                          hitl_required=True, run_id=run_id,
                          started_at=started, completed_at=now_utc())
            log.info(f"Delegated to HITL: {task_id}")
            return "pending_approval"

        if plan.get("cloud_executable", False):
            # Execute cloud-safe action (no MCP tools needed)
            self._execute_cloud_action(plan, task_id)
            done = CLOUD_VAULT_PATH / "Done"
            done.mkdir(parents=True, exist_ok=True)
            update_task_status(task_path, "done")
            move_task(task_path, done)
            log_agent_run(task_id, "success",
                          f"Cloud agent completed autonomously: {plan.get('summary', '')}",
                          run_id=run_id, started_at=started, completed_at=now_utc())
            log.info(f"Cloud task completed: {task_id}")
            return "success"

        # Fallback: delegate to local agent
        self._write_delegation_message(task_id, plan)
        return "delegated"

    def _execute_cloud_action(self, plan: dict, task_id: str) -> None:
        """Execute cloud-safe actions (drafting, summarization, etc.)."""
        draft = plan.get("draft_action", "")
        output_path = CLOUD_VAULT_PATH / "Done" / f"cloud_output_{task_id}.txt"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(draft, encoding="utf-8")
        log.info(f"Cloud action output written: {output_path.name}")

    def _write_delegation_message(self, task_id: str, plan: dict) -> None:
        """Write a delegation message for the local agent."""
        msg_dir = Path(__file__).parents[1] / "cloud" / "messages"
        msg_dir.mkdir(parents=True, exist_ok=True)
        msg = {
            "type":      "delegation",
            "from":      self.agent_id,
            "task_id":   task_id,
            "plan":      plan,
            "timestamp": now_utc(),
        }
        msg_path = msg_dir / f"delegate_{task_id}.json"
        msg_path.write_text(json.dumps(msg, indent=2), encoding="utf-8")
        log.info(f"Delegation message written: {msg_path.name}")

    def _parse_plan(self, text: str) -> dict:
        import re
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {
            "summary": "Cloud task", "plan": [], "tools_required": [],
            "requires_approval": True, "cloud_executable": False,
            "draft_action": text, "priority": "MEDIUM",
        }

    def _format_plan(self, task_id: str, plan: dict, raw: str) -> str:
        steps = "\n".join(f"{i+1}. {s}" for i, s in enumerate(plan.get("plan", [])))
        return f"""# Cloud Plan: {task_id}

**Agent:** {self.agent_id}
**Generated:** {now_utc()}

## Summary
{plan.get("summary", "")}

## Steps
{steps}

## Cloud Executable
{plan.get("cloud_executable", False)}

## Raw Response
```json
{raw}
```
"""

    def run_loop(self) -> None:
        """Continuous cloud processing loop."""
        log.info(f"Cloud Agent loop started (interval={CLOUD_SYNC_INTERVAL}s)")
        while True:
            tasks = self.scan_inbox()
            if tasks:
                log.info(f"Cloud: {len(tasks)} task(s) found")
                for t in tasks:
                    try:
                        self.process_task(t)
                    except Exception as e:
                        log.error(f"Cloud task error: {e}")
            time.sleep(CLOUD_SYNC_INTERVAL)


if __name__ == "__main__":
    CloudAgent().run_loop()
