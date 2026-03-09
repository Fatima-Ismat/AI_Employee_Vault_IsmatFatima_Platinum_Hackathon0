# Judge Demo Guide

## Hackathon: Personal AI Employee #0
## Project: AI_Employee_Vault_IsmatFatima_Platinum_Hackathon0
## Tier: Platinum

---

## Quick Start (5 Minutes)

```bash
# 1. Install Python deps
pip install -r requirements.txt

# 2. Set API key (minimum required)
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

# 3. Run the full demo
python demo/advanced_demo.py
```

That's it. Watch the terminal and vault folders update in real time.

---

## What the Demo Does (Step by Step)

### Scenario 1: Email → HITL → Approved → Done

| Step | What Happens | Where to See It |
|------|-------------|-----------------|
| 1 | Gmail watcher detects email from TechVentures Inc | `AI_Employee_Vault/Inbox/` |
| 2 | Ralph Wiggum picks up the task | Terminal logs |
| 3 | Claude generates a JSON execution plan | `AI_Employee_Vault/Plans/` |
| 4 | Task flagged as sensitive (external email) | `AI_Employee_Vault/Pending_Approval/` |
| 5 | Demo auto-approves after countdown | `AI_Employee_Vault/Approved/` |
| 6 | email_mcp executes (demo mode) | Terminal output |
| 7 | Task complete | `AI_Employee_Vault/Done/` |

### Scenario 2: File Upload Detection

- File dropped in `watched_folder/`
- Filesystem watcher detects it
- Claude creates plan → task processed

### Scenario 3: WhatsApp Urgent

- CRITICAL priority message injected
- HITL approval triggered
- Approved and executed

### Scenario 4: CEO Briefing

- Reads all Done tasks + logs + goals
- Claude generates executive report
- Written to `AI_Employee_Vault/CEO_Briefing.md`

### Scenario 5: Pipeline Visualization

- Counts tasks per stage
- Generates ASCII diagram + Markdown report
- Saved to `AI_Employee_Vault/Logs/pipeline_report.md`

---

## Prompt History (Judging Evidence)

All Claude prompts and responses are logged to:

```
history/prompts.md     ← Every system/user/assistant prompt
history/agent_runs.md  ← Every execution cycle record
history/approvals.md   ← Every HITL decision
```

Open these files to see exactly what prompts Claude received and how it responded.

---

## Dashboard Demo

### Start Backend

```bash
uvicorn backend.main:app --reload --port 8000
```

### Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Open: `http://localhost:3000`

### What Judges Can Do in the Dashboard

1. **Overview tab** — See live pipeline counts and bar chart
2. **Tasks tab** — Browse all tasks by stage, click for detail
3. **Approvals tab** — Click Approve/Reject to make HITL decisions
4. **Logs tab** — Filter system logs by level/content
5. **CEO Briefing tab** — Read the AI-generated executive report

---

## Obsidian Vault Demo

1. Open Obsidian
2. "Open folder as vault" → select `AI_Employee_Vault/`
3. Install **Dataview** plugin
4. Open `Dashboard.md` for live pipeline view
5. Browse `Plans/` to see Claude's reasoning
6. Browse `Pending_Approval/` to approve tasks manually

---

## Architecture Points to Highlight

| Feature | Score Factor | Where |
|---------|-------------|-------|
| Claude as reasoning engine | Core requirement | `agents/claude_agent.py` |
| Obsidian vault as memory | Core requirement | `AI_Employee_Vault/` |
| Python watchers (3) | Core requirement | `watchers/` |
| MCP servers (4) | Core requirement | `mcp_servers/` |
| HITL approval | Core requirement | `approval_system/hitl.py` |
| Ralph Wiggum loop | Core requirement | `orchestrator/agent_loop.py` |
| Prompt history | Platinum bonus | `history/prompts.md` |
| CEO briefing | Platinum bonus | `analytics/ceo_briefing.py` |
| Watchdog recovery | Platinum bonus | `watchdog_service/watchdog.py` |
| Frontend dashboard | Platinum bonus | `frontend/` |
| FastAPI backend | Platinum bonus | `backend/main.py` |
| A2A protocol | Platinum bonus | `agents/a2a_protocol.py` |
| Cloud layer | Platinum bonus | `cloud/` |
| Error recovery | Platinum bonus | `resilience/error_recovery.py` |
| Pipeline visualization | Platinum bonus | `analytics/pipeline_visualizer.py` |

---

## Files to Show Judges

1. `README.md` — full architecture overview
2. `history/prompts.md` — Claude prompt audit trail
3. `AI_Employee_Vault/CEO_Briefing.md` — AI executive report
4. `agents/claude_agent.py` — Claude integration
5. `approval_system/hitl.py` — HITL workflow
6. `orchestrator/agent_loop.py` — Autonomous loop

---

## One-Command Demo Reset

```bash
# Clear all vault pipeline folders (fresh demo state)
python -c "
import shutil
from utils.config import INBOX_DIR, NEEDS_ACTION_DIR, PENDING_DIR, DONE_DIR, APPROVED_DIR
for d in [INBOX_DIR, NEEDS_ACTION_DIR, PENDING_DIR, DONE_DIR, APPROVED_DIR]:
    for f in d.glob('*.md'): f.unlink()
print('Demo state reset.')
"
```
