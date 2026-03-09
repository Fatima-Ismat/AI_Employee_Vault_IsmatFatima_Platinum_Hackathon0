"""
Claude Agent
────────────
Primary reasoning engine powered by Claude (claude-sonnet-4-6).

Responsibilities:
  1. Read a task from Inbox
  2. Reason about the task using Claude
  3. Generate a structured plan saved to Plans/
  4. Determine if HITL approval is required
  5. Execute MCP tools if approved
  6. Move task through pipeline to Done
  7. Log all prompts and runs to history/

Uses the Anthropic Python SDK directly (not Claude Code CLI).
"""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from utils.config import (
    ANTHROPIC_API_KEY, CLAUDE_MODEL, MAX_TOKENS, SENSITIVE_KEYWORDS,
    NEEDS_ACTION_DIR, DONE_DIR, PENDING_DIR, DEMO_MODE,
)

if not DEMO_MODE:
    import anthropic
from utils.logger import get_logger
from utils.prompt_logger import log_prompt, log_agent_run
from utils.vault_io import (
    read_task, write_plan, move_task, update_task_status, now_utc,
)
from approval_system.hitl import create_approval_request, is_sensitive_task
from mcp_servers.email_mcp import send_email
from mcp_servers.calendar_mcp import create_event
from mcp_servers.filesystem_mcp import write_file

log = get_logger("agent.claude")

SYSTEM_PROMPT = """You are an AI Employee working autonomously on behalf of a business.
You have access to company policies defined in Company_Handbook.md and strategic goals in Business_Goals.md.

Your job when given a task is to:
1. Understand what is being asked
2. Create a clear, numbered execution plan
3. Identify which MCP tools are needed (email_mcp, calendar_mcp, filesystem_mcp, browser_mcp)
4. Flag if human approval is required before executing
5. Provide a draft response or action output

Always output your response in the following JSON structure:
{
  "summary": "One-sentence description of the task",
  "plan": ["Step 1: ...", "Step 2: ...", "Step N: ..."],
  "tools_required": ["email_mcp", "calendar_mcp"],
  "requires_approval": true,
  "approval_reason": "Sending external email requires human sign-off",
  "draft_action": "Full draft of the email/response/action to take",
  "priority": "HIGH | MEDIUM | LOW",
  "estimated_time": "5 minutes"
}

Be concise, professional, and always check if an action could be sensitive before executing."""


class ClaudeAgent:
    """Reason about a single task using Claude and execute the resulting plan."""

    def __init__(self) -> None:
        self.run_id = str(uuid.uuid4())[:8]
        if DEMO_MODE:
            self.client = None
            log.info("ClaudeAgent running in DEMO MODE — no API calls will be made")
        else:
            self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def _call_claude(self, user_prompt: str, task_content: str = "") -> str:
        """Call Claude API or return a mock response in demo mode."""
        if DEMO_MODE:
            from agents.mock_responses import mock_task_plan
            return mock_task_plan(task_content or user_prompt)
        response = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text

    def process_task(self, task_path: Path) -> str:
        """Full pipeline for one task. Returns final status."""
        started_at = now_utc()
        task_content = read_task(task_path)
        task_id = task_path.stem

        log.info(f"Processing task: {task_path.name}")

        # ── Step 1: Move to Needs_Action ──────────────────────────────────────
        task_path = move_task(task_path, NEEDS_ACTION_DIR)
        update_task_status(task_path, "in_progress")

        # ── Step 2: Call Claude ───────────────────────────────────────────────
        user_prompt = f"""Please analyze this task and create an execution plan:

---
{task_content}
---

Respond with the JSON structure specified in your system prompt."""

        try:
            assistant_text = self._call_claude(user_prompt, task_content)
        except Exception as e:
            log.error(f"Claude API error: {e}")
            log_agent_run(
                task_id=task_id,
                status="failed",
                summary=f"Claude API call failed: {e}",
                run_id=self.run_id,
                started_at=started_at,
                completed_at=now_utc(),
            )
            return "failed"

        # ── Step 3: Log prompt history ────────────────────────────────────────
        log_prompt(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            assistant_response=assistant_text,
            task_id=task_id,
            run_id=self.run_id,
        )

        # ── Step 4: Parse plan ────────────────────────────────────────────────
        plan = self._parse_plan(assistant_text)

        # ── Step 5: Write plan file ───────────────────────────────────────────
        plan_content = self._format_plan_md(task_id, task_content, assistant_text, plan)
        write_plan(task_id, plan_content)
        update_task_status(task_path, "planned")

        # ── Step 6: Check if approval needed ─────────────────────────────────
        requires_approval = plan.get("requires_approval", False) or is_sensitive_task(task_content)

        if requires_approval:
            log.info(f"Task requires HITL approval: {task_id}")
            approval_path = create_approval_request(
                task_path=task_path,
                task_id=task_id,
                plan=plan,
                run_id=self.run_id,
            )
            update_task_status(task_path, "pending_approval")
            move_task(task_path, PENDING_DIR)
            log_agent_run(
                task_id=task_id,
                status="pending_approval",
                summary=f"Task requires human approval. Approval file: {approval_path.name}",
                tools_used=plan.get("tools_required", []),
                hitl_required=True,
                run_id=self.run_id,
                started_at=started_at,
                completed_at=now_utc(),
            )
            return "pending_approval"

        # ── Step 7: Execute plan autonomously ─────────────────────────────────
        tools_used = self._execute_plan(plan, task_id)

        # ── Step 8: Move to Done ──────────────────────────────────────────────
        update_task_status(task_path, "done")
        move_task(task_path, DONE_DIR)

        log_agent_run(
            task_id=task_id,
            status="success",
            summary=plan.get("summary", "Task completed successfully"),
            tools_used=tools_used,
            hitl_required=False,
            run_id=self.run_id,
            started_at=started_at,
            completed_at=now_utc(),
        )
        log.info(f"Task completed: {task_id}")
        return "success"

    def process_approved_task(self, task_path: Path, plan: dict) -> str:
        """Execute a task that has received human approval."""
        started_at = now_utc()
        task_id = task_path.stem
        log.info(f"Executing approved task: {task_id}")

        tools_used = self._execute_plan(plan, task_id)
        update_task_status(task_path, "done")
        move_task(task_path, DONE_DIR)

        log_agent_run(
            task_id=task_id,
            status="success",
            summary=f"Approved task executed. Tools: {tools_used}",
            tools_used=tools_used,
            hitl_required=True,
            run_id=self.run_id,
            started_at=started_at,
            completed_at=now_utc(),
        )
        log.info(f"Approved task done: {task_id}")
        return "success"

    def _parse_plan(self, assistant_text: str) -> dict:
        """Extract JSON plan from Claude response, with fallback."""
        import json, re
        # Try to extract JSON block
        match = re.search(r"\{[\s\S]*\}", assistant_text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        # Fallback: return minimal structure
        return {
            "summary": "Task received",
            "plan": ["Review task and take appropriate action"],
            "tools_required": [],
            "requires_approval": True,
            "approval_reason": "Could not parse structured plan — defaulting to approval required",
            "draft_action": assistant_text,
            "priority": "MEDIUM",
        }

    def _format_plan_md(self, task_id: str, task_content: str, raw_response: str, plan: dict) -> str:
        steps = "\n".join(f"{i+1}. {s}" for i, s in enumerate(plan.get("plan", [])))
        tools = ", ".join(plan.get("tools_required", [])) or "none"
        model_label = f"{CLAUDE_MODEL} [Demo Mode — simulated]" if DEMO_MODE else CLAUDE_MODEL
        return f"""# Plan: {task_id}

**Generated:** {now_utc()}
**Model:** {model_label}
**Run ID:** {self.run_id}

---

## Summary

{plan.get("summary", "")}

## Execution Steps

{steps}

## Tools Required

{tools}

## Requires Approval

{plan.get("requires_approval", False)} — {plan.get("approval_reason", "")}

## Draft Action

{plan.get("draft_action", "")}

---

## Raw Claude Response

```json
{raw_response}
```
"""

    def _execute_plan(self, plan: dict, task_id: str) -> list[str]:
        """Execute MCP tool calls based on the plan. Returns list of tools used."""
        tools_used = []
        tools_required = plan.get("tools_required", [])
        draft = plan.get("draft_action", "")

        for tool in tools_required:
            try:
                if tool == "email_mcp":
                    send_email(
                        to="recipient@example.com",
                        subject=f"Re: Task {task_id}",
                        body=draft,
                    )
                    tools_used.append("email_mcp")
                elif tool == "calendar_mcp":
                    create_event(
                        title=f"Task: {task_id}",
                        description=draft,
                        start_time=now_utc(),
                    )
                    tools_used.append("calendar_mcp")
                elif tool == "filesystem_mcp":
                    write_file(
                        filename=f"output_{task_id}.txt",
                        content=draft,
                    )
                    tools_used.append("filesystem_mcp")
            except Exception as e:
                log.error(f"MCP tool {tool} failed: {e}")

        return tools_used
