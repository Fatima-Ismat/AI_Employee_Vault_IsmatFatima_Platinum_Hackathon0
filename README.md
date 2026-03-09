---
title: AI Employee Vault Ismat Platinum
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# AI Employee Vault — IsmatFatima — Platinum Tier
### Personal AI Employee Hackathon 0

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14%2B-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![Claude Agents](https://img.shields.io/badge/Claude-Sonnet%204.6-CC785C?style=for-the-badge&logo=anthropic&logoColor=white)](https://www.anthropic.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Hackathon](https://img.shields.io/badge/Hackathon-Platinum%20Tier-FFD700?style=for-the-badge&logo=trophy&logoColor=black)](https://github.com/Fatima-Ismat/AI_Employee_Vault_IsmatFatima_Platinum_Hackathon0)

> **Project Owner:** Ismat Fatima &nbsp;|&nbsp; **Hackathon:** AI Employee Vault – Platinum Tier

A **production-grade autonomous AI employee system** powered by **Claude (claude-sonnet-4-6)**, featuring a modern Next.js dashboard, FastAPI backend, self-healing watchdog, CEO AI briefings, cloud deployment layer, and full Human-in-the-Loop approval workflow.

---

## Full Architecture

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                   EXTERNAL EVENT SOURCES
         Gmail       WhatsApp       Filesystem       API/Webhook
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
        gmail_         whatsapp_   filesystem_
        watcher        watcher     watcher
              └───────────┬───────────┘
                          │  Markdown task files
                          ▼
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                  OBSIDIAN VAULT  (Memory + Pipeline)

  Inbox → Needs_Action → Plans → Pending_Approval
                                ↘ Approved → Done
                                ↘ Rejected
                                ↘ Recovery  (error recovery)

  Dashboard.md  Company_Handbook.md  Business_Goals.md  CEO_Briefing.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                          │
                          ▼
           ┌──────────────────────────────┐
           │  RALPH WIGGUM ORCHESTRATOR   │ ◄── Watchdog monitors
           │  orchestrator/agent_loop.py  │
           └──────────────┬───────────────┘
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
        CLAUDE AGENT   HITL         ERROR RECOVERY
        agents/        approval_    resilience/
        claude_agent   system/      error_recovery
             │         hitl.py
    ┌────────┼────────────────┐
    ▼        ▼        ▼       ▼
email_  browser_  calendar_ filesystem_
mcp     mcp       mcp       mcp
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  SUPPORT SYSTEMS               CLOUD LAYER

  analytics/                cloud/cloud_agent.py
  ceo_briefing.py            cloud/sync_manager.py
  pipeline_visualizer.py     agents/a2a_protocol.py

  watchdog_service/watchdog.py       MONITORING
  resilience/recovery.py     monitoring/system_health.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  DASHBOARD                       AUDIT TRAIL

  Next.js (frontend/)         history/prompts.md
  FastAPI (backend/)          history/agent_runs.md
  http://localhost:3000       history/approvals.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Feature Matrix — Platinum Tier

### Core Requirements

| Feature | File |
|---------|------|
| Claude as reasoning engine | `agents/claude_agent.py` |
| Obsidian vault memory (8 stages) | `AI_Employee_Vault/` |
| Gmail watcher | `watchers/gmail_watcher.py` |
| Filesystem watcher | `watchers/filesystem_watcher.py` |
| WhatsApp watcher | `watchers/whatsapp_watcher.py` |
| Email MCP | `mcp_servers/email_mcp.py` |
| Browser MCP | `mcp_servers/browser_mcp.py` |
| Calendar MCP | `mcp_servers/calendar_mcp.py` |
| Filesystem MCP | `mcp_servers/filesystem_mcp.py` |
| HITL approval workflow | `approval_system/hitl.py` |
| Ralph Wiggum autonomous loop | `orchestrator/agent_loop.py` |
| Prompt history logging | `history/prompts.md` |

### Platinum Bonus Features

| Feature | File |
|---------|------|
| CEO AI Weekly Briefing | `analytics/ceo_briefing.py` |
| Pipeline visualization + ASCII | `analytics/pipeline_visualizer.py` |
| Self-healing watchdog | `watchdog_service/watchdog.py` |
| Error recovery system | `resilience/error_recovery.py` |
| System health monitor | `monitoring/system_health.py` |
| FastAPI backend (10 endpoints) | `backend/main.py` |
| Next.js + Tailwind dashboard | `frontend/` |
| Cloud agent (S3/GCS/local) | `cloud/cloud_agent.py` |
| Vault sync manager | `cloud/sync_manager.py` |
| A2A agent communication | `agents/a2a_protocol.py` |
| Advanced demo (5 scenarios) | `demo/advanced_demo.py` |
| PM2 process management | `ecosystem.config.js` |

---

## Repository Structure

```
AI_Employee_Vault_IsmatFatima_Platinum_Hackathon0/
├── AI_Employee_Vault/         Obsidian vault (memory + pipeline)
│   ├── Dashboard.md
│   ├── Company_Handbook.md
│   ├── Business_Goals.md
│   ├── CEO_Briefing.md        (auto-generated weekly)
│   ├── Inbox/  Needs_Action/  Plans/  Pending_Approval/
│   ├── Approved/  Rejected/  Done/  Recovery/
│   └── Logs/  (daily logs, watchdog, health, pipeline report)
├── history/                   Prompt audit trail (judge proof)
│   ├── prompts.md
│   ├── agent_runs.md
│   └── approvals.md
├── watchers/                  Event detection
├── agents/                    Claude reasoning + A2A
├── orchestrator/              Ralph Wiggum loop
├── approval_system/           HITL workflow
├── mcp_servers/               Tool integrations (4)
├── analytics/                 CEO briefing + pipeline viz
├── watchdog/                  Self-healing monitor
├── monitoring/                System health checks
├── resilience/                Error recovery
├── cloud/                     Cloud deployment layer
├── backend/                   FastAPI REST API
├── frontend/                  Next.js dashboard
├── demo/                      Demo scripts
├── utils/                     Shared utilities
└── docs/                      Full documentation (10 files)
```

---

## Demo Mode (Zero API Cost)

Run the entire pipeline — all 5 scenarios, HITL approval, CEO briefing, pipeline visualization — **without any Anthropic API key or paid credits**.

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy env (DEMO_MODE=true is already set)
cp .env.example .env

# 3. Run the full demo
python demo/advanced_demo.py
```

All Claude responses are replaced with realistic keyword-matched mock outputs, clearly stamped `[Demo Mode / Simulated Claude Response]`. Every pipeline stage, vault folder, prompt log, HITL approval, and history file works identically to live mode.

To switch to live Claude API, edit `.env`:
```env
DEMO_MODE=false
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

---

## Quick Start

### 1. Install

```bash
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# DEMO_MODE=true by default — no API key needed
# Set ANTHROPIC_API_KEY and DEMO_MODE=false for live Claude
```

### 3. Full Demo (No External Credentials Needed)

```bash
python demo/advanced_demo.py
```

Runs 5 scenarios: email HITL, file detection, WhatsApp urgent, CEO briefing, pipeline viz.

### 4. Start Full System

```bash
# PM2 (all watchers + orchestrator)
pm2 start ecosystem.config.js
pm2 monit

# Or direct Python
python -m orchestrator.agent_loop
```

### 5. Start Dashboard

```bash
# Terminal 1 — Backend API
uvicorn backend.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend && npm install && npm run dev

# Open: http://localhost:3000
```

### 6. Open Vault in Obsidian

1. Obsidian → Open folder as vault → `AI_Employee_Vault/`
2. Install **Dataview** plugin
3. Open `Dashboard.md`

---

## HITL Approval Flow

```
Agent flags sensitive action
         │
Pending_Approval/approval_xyz.md created
         │
Human opens in Obsidian (or Dashboard UI)
         │
status: pending  →  status: approved
         │
Orchestrator detects in next cycle
         │
MCP tool executes  →  Done/
```

---

## Demo Scenarios

| # | Scenario | Key Features |
|---|----------|-------------|
| 1 | Email partnership request | Gmail watcher → Claude plan → HITL → email_mcp |
| 2 | File upload detection | Filesystem watcher → autonomous analysis |
| 3 | WhatsApp urgent | CRITICAL priority → HITL escalation |
| 4 | CEO AI briefing | Claude executive report from task history |
| 5 | Pipeline visualization | ASCII diagram + Markdown stats report |

---

## Prompt History (Judge Proof)

```
history/prompts.md
──────────────────
timestamp: 2026-03-06 10:01:23 UTC
run_id: abc123
task_id: task_xyz

System Prompt:  [full system prompt]
User Prompt:    [task content + instruction]
Claude Response: {"summary": "...", "plan": [...], ...}
```

All prompts, agent runs, and approval decisions are permanently logged.

---

## Screenshots

> Run `python demo/advanced_demo.py` and open `http://localhost:3000`

Dashboard features:
- Live pipeline stage counters (7 stages)
- Bar chart visualization
- Task list with filtering
- Approval queue with Approve/Reject buttons
- Log terminal with level filtering
- CEO briefing markdown viewer

---

## Hackathon Tier: Platinum

This implementation covers all core requirements plus every Platinum-tier bonus:
autonomous loop, HITL, MCP tools, Obsidian vault, Claude reasoning, prompt history,
CEO briefing, frontend dashboard, FastAPI backend, watchdog, cloud layer, A2A protocol,
error recovery, pipeline visualization, and PM2 process management.

---

## Gmail Watcher Integration

Gmail Watcher monitors unread Gmail messages using IMAP and a Gmail App Password. It polls the inbox and converts unread emails into AI Employee Inbox tasks.

```
Gmail Inbox (unread)
       │
       ▼
GmailWatcher.poll()   ← IMAP over SSL (imap.gmail.com:993)
       │
       ▼
Email parsed (subject, sender, body)
       │
       ▼
Priority inferred (urgent/invoice keywords → HIGH)
       │
       ▼
write_inbox_task() → AI_Employee_Vault/Inbox/
       │
       ▼
Orchestrator picks up on next cycle
```

**Setup:** Enable IMAP in Gmail settings → create a Gmail App Password (Google Account → Security → App Passwords) → set in `.env`:
```env
GMAIL_USER=your@gmail.com
GMAIL_APP_PASSWORD=your-app-password
```

---

## Future Roadmap

| Feature | Status |
|---------|--------|
| Slack watcher integration | Planned |
| Gmail OAuth full flow | In Progress |
| Multi-agent task delegation (A2A) | Implemented |
| Vector memory (embeddings) | Planned |
| Mobile dashboard (PWA) | Planned |
| Webhook ingest endpoint | Planned |
| Multi-tenant vault support | Planned |
| LLM-agnostic model switcher | Planned |

---

## Cloud Deployment

The system is deployed on Oracle Cloud Infrastructure (OCI):

- **Backend API:** `http://141.145.155.147:8000`
- **Dashboard:** `http://141.145.155.147:3000`
- **Process Manager:** PM2 (`ecosystem.config.js`)

```bash
# Deploy on cloud server
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

---

## Author

**Ismat Fatima**
Personal AI Employee Hackathon 0 — Platinum Tier
Model: claude-sonnet-4-6
GitHub: [Fatima-Ismat](https://github.com/Fatima-Ismat/AI_Employee_Vault_IsmatFatima_Platinum_Hackathon0)
