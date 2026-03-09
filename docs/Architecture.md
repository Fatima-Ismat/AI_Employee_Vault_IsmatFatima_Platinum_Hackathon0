# Architecture

## System Overview

AI_Employee_Vault_IsmatFatima_Platinum_Hackathon0 is a **Platinum-tier Personal AI Employee** built for Hackathon 0.

The system uses Claude (claude-sonnet-4-6) as its reasoning brain, an Obsidian vault as its persistent memory and task pipeline, Python watchers for event sensing, MCP servers for external tool execution, and a HITL approval layer for human oversight.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                     EXTERNAL EVENT SOURCES                          │
│   Gmail Inbox    WhatsApp Messages    Filesystem Changes            │
└────────┬───────────────┬─────────────────────┬───────────────────  ┘
         │               │                     │
         ▼               ▼                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      WATCHERS (Python)                              │
│  gmail_watcher.py   whatsapp_watcher.py   filesystem_watcher.py    │
│                                                                     │
│  • Poll external sources on schedule                                │
│  • Format events as Markdown task files                             │
│  • Write to AI_Employee_Vault/Inbox/                                │
└───────────────────────────┬─────────────────────────────────────── ┘
                            │  Task Files (Markdown)
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│               OBSIDIAN VAULT  (Memory + Pipeline)                   │
│                                                                     │
│   Inbox/ → Needs_Action/ → Plans/ → Pending_Approval/              │
│                                  ↘ Approved/ → Done/               │
│                                  ↘ Rejected/                        │
│   Logs/   Dashboard.md   Company_Handbook.md   Business_Goals.md   │
└───────────────────────────┬─────────────────────────────────────── ┘
                            │  Read tasks
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│             RALPH WIGGUM ORCHESTRATOR LOOP                          │
│                  orchestrator/agent_loop.py                         │
│                                                                     │
│  while True:                                                        │
│    scan Inbox → invoke Claude Agent                                 │
│    check Pending_Approval → execute approved tasks                  │
│    sleep(LOOP_INTERVAL)                                             │
└───────────────────────────┬─────────────────────────────────────── ┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   CLAUDE AGENT (Reasoning Engine)                   │
│                    agents/claude_agent.py                           │
│                                                                     │
│  Model: claude-sonnet-4-6                                           │
│  • Read task content                                                │
│  • Generate structured JSON plan                                    │
│  • Identify required MCP tools                                      │
│  • Flag sensitive actions for HITL                                  │
│  • Log all prompts to history/prompts.md                            │
└────────┬──────────────────────────────┬─────────────────────────── ┘
         │                              │
         ▼                              ▼
┌─────────────────────┐    ┌────────────────────────────────────────┐
│   MCP TOOL SERVERS  │    │        HITL APPROVAL SYSTEM            │
│                     │    │       approval_system/hitl.py          │
│  • email_mcp.py     │    │                                        │
│  • browser_mcp.py   │    │  • Creates Pending_Approval/ files     │
│  • calendar_mcp.py  │    │  • Human changes status field          │
│  • filesystem_mcp.py│    │  • Agent detects approved/rejected     │
└─────────────────────┘    └────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PROMPT HISTORY LOGGER                            │
│                                                                     │
│  history/prompts.md      — every Claude prompt + response          │
│  history/agent_runs.md   — every loop execution record             │
│  history/approvals.md    — every HITL decision                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Responsibilities

| Component | File | Responsibility |
|-----------|------|----------------|
| Gmail Watcher | `watchers/gmail_watcher.py` | Poll Gmail IMAP, create Inbox tasks |
| Filesystem Watcher | `watchers/filesystem_watcher.py` | Monitor directory changes |
| WhatsApp Watcher | `watchers/whatsapp_watcher.py` | Poll WhatsApp API |
| Claude Agent | `agents/claude_agent.py` | Reason, plan, execute |
| Orchestrator | `orchestrator/agent_loop.py` | Drive pipeline continuously |
| HITL System | `approval_system/hitl.py` | Manage approval workflow |
| Email MCP | `mcp_servers/email_mcp.py` | Send/receive emails |
| Browser MCP | `mcp_servers/browser_mcp.py` | Web fetch, search |
| Calendar MCP | `mcp_servers/calendar_mcp.py` | Create/list/delete events |
| Filesystem MCP | `mcp_servers/filesystem_mcp.py` | File read/write |
| Prompt Logger | `utils/prompt_logger.py` | History audit trail |
| Vault I/O | `utils/vault_io.py` | Read/write/move task files |
| Config | `utils/config.py` | Centralized settings |

---

## Data Flow

1. **Event detected** by a watcher
2. **Task file created** in `Inbox/` (Markdown with YAML frontmatter)
3. **Orchestrator** picks it up in the next loop cycle
4. **Claude Agent** reads task, calls Claude API, generates plan
5. **Plan saved** to `Plans/plan_<id>.md`
6. If **sensitive**: approval request created in `Pending_Approval/`
7. **Human** opens Obsidian, changes `status: pending` → `status: approved`
8. **Orchestrator** detects approval, calls `process_approved_task()`
9. **MCP tools** execute the plan
10. Task moved to `Done/`
11. All prompts and run metadata saved to `history/`
