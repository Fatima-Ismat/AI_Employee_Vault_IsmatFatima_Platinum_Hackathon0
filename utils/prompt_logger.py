"""
Prompt history logger — appends every Claude prompt and response to history/prompts.md
and every agent run summary to history/agent_runs.md.
Provides full auditability for hackathon judges.
"""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from utils.config import PROMPTS_LOG, AGENT_RUNS_LOG, APPROVALS_LOG, HISTORY_DIR


def _ensure_history() -> None:
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def log_prompt(
    system_prompt: str,
    user_prompt: str,
    assistant_response: str,
    task_id: str = "",
    run_id: str = "",
) -> None:
    """Append a full prompt/response triplet to history/prompts.md."""
    _ensure_history()
    run_id = run_id or str(uuid.uuid4())[:8]
    entry = f"""
---
timestamp: {_now()}
run_id: {run_id}
task_id: {task_id}
---

### System Prompt

```
{system_prompt}
```

### User Prompt

```
{user_prompt}
```

### Claude Response

```
{assistant_response}
```

"""
    with open(PROMPTS_LOG, "a", encoding="utf-8") as f:
        f.write(entry)


def log_agent_run(
    task_id: str,
    status: str,
    summary: str,
    tools_used: Optional[list[str]] = None,
    hitl_required: bool = False,
    run_id: str = "",
    started_at: str = "",
    completed_at: str = "",
) -> None:
    """Append an agent run record to history/agent_runs.md."""
    _ensure_history()
    run_id = run_id or str(uuid.uuid4())[:8]
    tools_str = ", ".join(tools_used) if tools_used else "none"
    entry = f"""
---
run_id: {run_id}
started_at: {started_at or _now()}
completed_at: {completed_at or _now()}
task_id: {task_id}
status: {status}
tools_used: [{tools_str}]
hitl_required: {str(hitl_required).lower()}
---

{summary}

"""
    with open(AGENT_RUNS_LOG, "a", encoding="utf-8") as f:
        f.write(entry)


def log_approval(
    task_id: str,
    decision: str,
    action_description: str,
    reason: str = "",
    approval_id: str = "",
    requested_at: str = "",
    decided_at: str = "",
) -> None:
    """Append an approval decision to history/approvals.md."""
    _ensure_history()
    approval_id = approval_id or str(uuid.uuid4())[:8]
    entry = f"""
---
approval_id: {approval_id}
task_id: {task_id}
requested_at: {requested_at or _now()}
decided_at: {decided_at or _now()}
decision: {decision}
decided_by: human
reason: {reason}
---

{action_description}

"""
    with open(APPROVALS_LOG, "a", encoding="utf-8") as f:
        f.write(entry)
