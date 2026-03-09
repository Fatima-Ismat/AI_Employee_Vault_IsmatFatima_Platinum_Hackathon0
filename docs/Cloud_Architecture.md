# Cloud Architecture

## Hybrid Design

The system operates in a **local-first, cloud-optional** architecture:

- **Local**: Watchers, Claude agent, HITL approval, MCP tool execution
- **Cloud**: Remote inbox monitoring, safe task processing, vault sync

See `cloud/deployment.md` for full deployment guide.

## Components

| File | Role |
|------|------|
| `cloud/cloud_agent.py` | Cloud-mode agent — processes safe tasks remotely |
| `cloud/sync_manager.py` | Bidirectional vault sync (local ↔ S3/GCS/local mirror) |
| `cloud/deployment.md` | Deployment instructions |

## Cloud Agent Decision Logic

```
Task received by cloud agent
         │
         ▼
  Is it sensitive? ──YES──► Create HITL approval → write to Pending_Approval/
         │                   Local agent handles after human approves
         NO
         │
         ▼
  Is it cloud-executable? ──YES──► Execute autonomously (summarize, draft, classify)
         │
         NO
         │
         ▼
  Write delegation message → agents/messages/
  Local agent picks up via A2A protocol
```

## Sync Backends

| Backend | Config | Notes |
|---------|--------|-------|
| Local mirror | `SYNC_BACKEND=local` | For demo/dev |
| AWS S3 | `SYNC_BACKEND=s3` + `S3_BUCKET=...` | Production |
| GCS | `SYNC_BACKEND=gcs` + `GCS_BUCKET=...` | Production |

## A2A Protocol Integration

Cloud agent uses `agents/a2a_protocol.py` to delegate tasks:

```python
send_delegation(
    from_agent="cloud-agent-01",
    to_agent="local-agent",
    task_id=task_id,
    plan=plan,
    reason="Requires local MCP tools",
)
```

Local agent polls `agents/messages/` and processes delegations.
