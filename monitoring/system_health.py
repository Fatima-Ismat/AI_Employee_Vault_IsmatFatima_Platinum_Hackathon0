"""
System Health Monitor
──────────────────────
Continuously monitors system resources, process states, and pipeline health.
Writes a live health report to AI_Employee_Vault/Logs/system_health.md.

Run:
  python -m monitoring.system_health
  or include as a FastAPI background task
"""

import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from utils.config import (
    LOGS_DIR, INBOX_DIR, NEEDS_ACTION_DIR, PENDING_DIR,
    DONE_DIR, REJECTED_DIR, HISTORY_DIR,
)
from utils.logger import get_logger

log = get_logger("monitoring.health")

HEALTH_REPORT_PATH = LOGS_DIR / "system_health.md"
CHECK_INTERVAL     = 60   # seconds


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _count_files(folder: Path, pattern: str = "*.md") -> int:
    if not folder.exists():
        return 0
    return sum(1 for _ in folder.glob(pattern) if not _.name.startswith("."))


def check_pipeline_health() -> dict:
    """Count tasks in each pipeline stage."""
    return {
        "inbox":            _count_files(INBOX_DIR),
        "needs_action":     _count_files(NEEDS_ACTION_DIR),
        "pending_approval": _count_files(PENDING_DIR),
        "done":             _count_files(DONE_DIR),
        "rejected":         _count_files(REJECTED_DIR),
    }


def check_system_resources() -> dict:
    """Gather CPU, memory, disk metrics."""
    if not PSUTIL_AVAILABLE:
        return {"note": "psutil not installed — install with: pip install psutil"}

    cpu   = psutil.cpu_percent(interval=1)
    mem   = psutil.virtual_memory()
    disk  = psutil.disk_usage("/")

    return {
        "cpu_percent":        cpu,
        "memory_percent":     mem.percent,
        "memory_available_gb": round(mem.available / 1e9, 2),
        "disk_percent":       disk.percent,
        "disk_free_gb":       round(disk.free / 1e9, 2),
    }


def check_error_rate() -> dict:
    """Count errors in recent logs."""
    error_count   = 0
    warning_count = 0
    if not LOGS_DIR.exists():
        return {"errors": 0, "warnings": 0}

    for log_file in sorted(LOGS_DIR.glob("*.md"))[-3:]:  # Last 3 days
        try:
            content = log_file.read_text(encoding="utf-8")
            error_count   += content.count("**ERROR**")
            warning_count += content.count("**WARNING**")
        except Exception:
            pass

    return {"errors": error_count, "warnings": warning_count}


def check_agent_run_stats() -> dict:
    """Parse agent_runs.md for recent performance."""
    from utils.config import AGENT_RUNS_LOG
    if not AGENT_RUNS_LOG.exists():
        return {"total": 0, "success": 0, "failed": 0}

    content = AGENT_RUNS_LOG.read_text(encoding="utf-8")
    return {
        "total":   content.count("status:"),
        "success": content.count("status: success"),
        "failed":  content.count("status: failed"),
        "pending": content.count("status: pending_approval"),
    }


def compute_overall_status(resources: dict, pipeline: dict, errors: dict) -> str:
    """Compute a single status string: healthy | degraded | critical."""
    if not PSUTIL_AVAILABLE:
        return "unknown"

    cpu  = resources.get("cpu_percent", 0)
    mem  = resources.get("memory_percent", 0)
    disk = resources.get("disk_percent", 0)
    errs = errors.get("errors", 0)
    inbox = pipeline.get("inbox", 0)

    if cpu > 95 or mem > 95 or disk > 95:
        return "critical"
    if cpu > 80 or mem > 80 or errs > 10 or inbox > 30:
        return "degraded"
    return "healthy"


def generate_health_report(
    resources: dict, pipeline: dict, errors: dict, agent_stats: dict
) -> str:
    ts = _now()
    status = compute_overall_status(resources, pipeline, errors)
    status_icon = {"healthy": "✅", "degraded": "⚠️", "critical": "🔥", "unknown": "❓"}.get(status, "❓")

    cpu  = resources.get("cpu_percent",        "?")
    mem  = resources.get("memory_percent",     "?")
    disk = resources.get("disk_percent",       "?")
    mem_gb = resources.get("memory_available_gb", "?")
    disk_gb = resources.get("disk_free_gb",    "?")

    runs_total   = agent_stats.get("total",   0)
    runs_success = agent_stats.get("success", 0)
    runs_failed  = agent_stats.get("failed",  0)
    success_rate = round(runs_success / max(runs_total, 1) * 100, 1)

    return f"""# System Health Report

> **Status:** {status_icon} `{status.upper()}`
> **Generated:** {ts}
> **Auto-refreshed every {CHECK_INTERVAL}s**

---

## System Resources

| Metric | Value | Status |
|--------|-------|--------|
| CPU Usage | {cpu}% | {"⚠️" if isinstance(cpu, (int,float)) and cpu > 80 else "✅"} |
| Memory Usage | {mem}% ({mem_gb} GB free) | {"⚠️" if isinstance(mem, (int,float)) and mem > 80 else "✅"} |
| Disk Usage | {disk}% ({disk_gb} GB free) | {"⚠️" if isinstance(disk, (int,float)) and disk > 85 else "✅"} |

---

## Task Pipeline

| Stage | Count | Health |
|-------|-------|--------|
| Inbox | {pipeline.get('inbox', 0)} | {"⚠️ Overflow" if pipeline.get('inbox', 0) > 20 else "✅"} |
| Needs Action | {pipeline.get('needs_action', 0)} | {"⚠️ Stalled?" if pipeline.get('needs_action', 0) > 10 else "✅"} |
| Pending Approval | {pipeline.get('pending_approval', 0)} | {"⏳ Waiting" if pipeline.get('pending_approval', 0) > 0 else "✅"} |
| Done | {pipeline.get('done', 0)} | ✅ |
| Rejected | {pipeline.get('rejected', 0)} | {"⚠️" if pipeline.get('rejected', 0) > 5 else "✅"} |

---

## Agent Performance

| Metric | Value |
|--------|-------|
| Total Runs | {runs_total} |
| Successful | {runs_success} |
| Failed | {runs_failed} |
| Success Rate | {success_rate}% |

---

## Error Summary (Last 3 Days)

| Type | Count |
|------|-------|
| Errors | {errors.get('errors', 0)} |
| Warnings | {errors.get('warnings', 0)} |

---

*Updated: {ts}*
"""


def run_health_monitor(single_check: bool = False) -> dict:
    """Run health checks. If single_check=True, run once and return. Otherwise loop."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    while True:
        resources   = check_system_resources()
        pipeline    = check_pipeline_health()
        errors      = check_error_rate()
        agent_stats = check_agent_run_stats()

        report = generate_health_report(resources, pipeline, errors, agent_stats)
        HEALTH_REPORT_PATH.write_text(report, encoding="utf-8")

        status = compute_overall_status(resources, pipeline, errors)
        log.info(f"Health check: {status.upper()} — Inbox:{pipeline.get('inbox',0)} Done:{pipeline.get('done',0)}")

        result = {
            "status": status,
            "resources": resources,
            "pipeline": pipeline,
            "errors": errors,
            "agent_stats": agent_stats,
            "timestamp": _now(),
        }

        if single_check:
            return result

        time.sleep(CHECK_INTERVAL)

    return {}


if __name__ == "__main__":
    run_health_monitor()
