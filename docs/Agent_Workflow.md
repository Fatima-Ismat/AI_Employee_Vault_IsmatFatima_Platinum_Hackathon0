# Agent Workflow

## Overview

The Claude Agent (`agents/claude_agent.py`) is the reasoning brain of the system. It uses `claude-sonnet-4-6` via the Anthropic SDK.

---

## Workflow Diagram

```
Task File (Inbox/)
       │
       ▼
 Read task content
       │
       ▼
 Move → Needs_Action/
       │
       ▼
 Call Claude API ──────────────────────► history/prompts.md
       │
       ▼
 Parse JSON plan
       │
       ├─── Plan written → Plans/plan_<id>.md
       │
       ▼
 Is sensitive? ───YES──► Pending_Approval/ ──► Human decision
       │                                              │
       NO                                    approved/rejected
       │                                              │
       ▼                                              ▼
 Execute MCP tools                          Execute or archive
       │
       ▼
 Move → Done/
       │
       ▼
 Log → history/agent_runs.md
```

---

## Claude System Prompt

The agent uses a structured system prompt that instructs Claude to:

1. Understand the task
2. Create a numbered plan
3. Identify MCP tools needed
4. Flag if human approval is required
5. Provide a full draft action

Output is always a JSON object:

```json
{
  "summary": "Brief description",
  "plan": ["Step 1", "Step 2"],
  "tools_required": ["email_mcp"],
  "requires_approval": true,
  "approval_reason": "Sending external email",
  "draft_action": "Full email draft here",
  "priority": "HIGH",
  "estimated_time": "5 minutes"
}
```

---

## Sensitive Action Detection

Two layers:

1. **Claude judgment** — `requires_approval: true` in response JSON
2. **Keyword matching** — `utils/config.py:SENSITIVE_KEYWORDS`

```python
SENSITIVE_KEYWORDS = [
    "send email", "delete", "payment", "financial",
    "schedule meeting", "publish", "share confidential", "external",
]
```

Either layer triggers the HITL flow.

---

## HITL Flow Detail

```
Agent flags sensitive → create_approval_request()
                              │
                    Pending_Approval/approval_<id>.md
                              │
                    [Human opens in Obsidian]
                              │
               status: pending → status: approved
                              │
                    Orchestrator detects in next cycle
                              │
                    process_approved_task() called
                              │
                    MCP tools execute
                              │
                    Task → Done/
```

---

## Prompt History

Every Claude invocation is logged to `history/prompts.md`:

```markdown
---
timestamp: 2026-03-06 10:05:00 UTC
run_id: abc123
task_id: task_xyz
---

### System Prompt
[full system prompt]

### User Prompt
[task content + instruction]

### Claude Response
[full JSON response]
```

This provides complete auditability for hackathon judges.

---

## Error Handling

- Claude API errors: logged, task status set to `failed`
- MCP tool errors: individual tool failures logged, other tools still execute
- JSON parse errors: fallback to minimal plan with `requires_approval: true`
- All errors: written to `AI_Employee_Vault/Logs/YYYY-MM-DD.md`
