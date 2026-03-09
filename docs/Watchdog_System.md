# Watchdog System

## Overview

The self-healing watchdog monitors all AI Employee processes and automatically recovers from crashes.

**File:** `watchdog/watchdog.py`
**Log:** `AI_Employee_Vault/Logs/watchdog_log.md`

## Capabilities

| Feature | Detail |
|---------|--------|
| Process monitoring | Checks subprocess liveness every 30s |
| Auto-restart | Restarts crashed processes (up to 3 attempts) |
| Stall detection | Flags tasks stuck in Needs_Action > 15 minutes |
| Inbox overflow | Warns if Inbox > 20 tasks |
| Resource monitoring | CPU, memory, disk usage via psutil |
| Health summaries | Written every 10 check cycles |

## Monitored Processes

- `ralph-wiggum` (orchestrator/agent_loop.py)
- `gmail-watcher` (watchers/gmail_watcher.py)
- `filesystem-watcher` (watchers/filesystem_watcher.py)

## Usage Modes

### Standalone (manages its own processes)
```bash
python -m watchdog.watchdog
```

### Alongside PM2 (monitor-only mode)
```bash
# Start processes with PM2
pm2 start ecosystem.config.js

# Start watchdog in monitor-only mode (no process management)
python -m watchdog.watchdog  # set start_processes=False
```

## Log Format

```
- `2026-03-06 10:15:00 UTC` ✅ RECOVERY — Process started: ralph-wiggum (PID 12345)
- `2026-03-06 10:45:00 UTC` ⚠️ WARN — Stalled tasks detected (2): task_abc.md, task_xyz.md
- `2026-03-06 11:00:00 UTC` ❌ ERROR — Process CRASHED: gmail-watcher (exit code 1)
- `2026-03-06 11:00:05 UTC` ✅ RECOVERY — Restarting gmail-watcher (attempt 1/3)
```

## Configuration

```env
# No special config needed — uses LOOP_INTERVAL from main .env
```

## psutil Requirement

```bash
pip install psutil
```

Resource monitoring (CPU/memory/disk) is skipped gracefully if psutil is not installed.
