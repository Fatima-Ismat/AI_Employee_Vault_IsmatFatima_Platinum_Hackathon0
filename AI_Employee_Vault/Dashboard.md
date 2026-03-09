# AI Employee Dashboard

> **System:** AI_Employee_Vault_IsmatFatima_Platinum_Hackathon0
> **Tier:** Platinum
> **Engine:** Claude Code (claude-sonnet-4-6)
> **Last Updated:** {{date}}

---

## System Status

| Component | Status |
|-----------|--------|
| Gmail Watcher | Running |
| Filesystem Watcher | Running |
| WhatsApp Watcher | Running |
| Claude Agent | Active |
| HITL Approval | Monitoring |
| Orchestrator Loop | Running |

---

## Task Pipeline

### Inbox
```dataview
TABLE file.mtime AS "Received", source AS "Source", priority AS "Priority"
FROM "Inbox"
SORT file.mtime DESC
```

### Needs Action
```dataview
TABLE file.mtime AS "Queued", assigned_to AS "Assigned"
FROM "Needs_Action"
SORT file.mtime DESC
```

### Pending Approval
```dataview
TABLE file.mtime AS "Submitted", status AS "Status"
FROM "Pending_Approval"
SORT file.mtime DESC
```

### Done (Last 10)
```dataview
TABLE file.mtime AS "Completed", source AS "Source"
FROM "Done"
SORT file.mtime DESC
LIMIT 10
```

---

## Metrics

- **Tasks Today:** 0
- **Approved:** 0
- **Rejected:** 0
- **Completed:** 0
- **Pending Human Review:** 0

---

## Quick Links

- [[Company_Handbook]]
- [[Business_Goals]]
- [Logs](Logs/)
- [Plans](Plans/)

---

## Recent Logs

```dataview
LIST
FROM "Logs"
SORT file.mtime DESC
LIMIT 5
```
