"""
Self-Healing Watchdog System
──────────────────────────────
Monitors the orchestrator loop and all watcher processes.
Detects crashes, stalled tasks, and resource issues.
Automatically restarts processes and logs all recovery events.

Output log: AI_Employee_Vault/Logs/watchdog_log.md

Run:
  python -m watchdog_service.watchdog
"""

import os
import signal
import subprocess
import sys
import time
import psutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.config import LOGS_DIR, INBOX_DIR, NEEDS_ACTION_DIR, LOOP_INTERVAL
from utils.logger import get_logger

log = get_logger("watchdog")

WATCHDOG_LOG = LOGS_DIR / "watchdog_log.md"
STALL_THRESHOLD_MINUTES = 15   # Flag task as stalled after N minutes in Needs_Action
CHECK_INTERVAL = 30            # Seconds between watchdog checks
MAX_RESTART_ATTEMPTS = 3


MONITORED_PROCESSES = [
    {
        "name":    "ralph-wiggum",
        "module":  "orchestrator.agent_loop",
        "pid_key": "orchestrator_pid",
    },
    {
        "name":    "gmail-watcher",
        "module":  "watchers.gmail_watcher",
        "pid_key": "gmail_pid",
    },
    {
        "name":    "filesystem-watcher",
        "module":  "watchers.filesystem_watcher",
        "pid_key": "filesystem_pid",
    },
]

_process_registry: dict[str, subprocess.Popen] = {}
_restart_counts:   dict[str, int] = {}
_shutdown = False


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _write_watchdog_log(event: str, level: str = "INFO") -> None:
    """Append an event to the watchdog log file."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    icons = {"INFO": "ℹ️", "WARN": "⚠️", "ERROR": "❌", "RECOVERY": "✅", "CRITICAL": "🔥"}
    icon = icons.get(level, "•")
    line = f"\n- `{_now()}` {icon} **{level}** — {event}"
    with open(WATCHDOG_LOG, "a", encoding="utf-8") as f:
        f.write(line)


def _is_process_alive(proc: subprocess.Popen) -> bool:
    """Check if a subprocess is still running."""
    try:
        return proc.poll() is None
    except Exception:
        return False


def _is_pid_alive(pid: int) -> bool:
    """Check if an OS-level PID is alive."""
    try:
        return psutil.pid_exists(pid) and psutil.Process(pid).status() != psutil.STATUS_ZOMBIE
    except Exception:
        return False


def start_process(proc_def: dict) -> Optional[subprocess.Popen]:
    """Start a monitored process and register it."""
    name = proc_def["name"]
    module = proc_def["module"]
    try:
        proc = subprocess.Popen(
            [sys.executable, "-m", module],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        _process_registry[name] = proc
        msg = f"Process started: {name} (PID {proc.pid})"
        log.info(msg)
        _write_watchdog_log(msg, "RECOVERY")
        return proc
    except Exception as e:
        msg = f"Failed to start {name}: {e}"
        log.error(msg)
        _write_watchdog_log(msg, "ERROR")
        return None


def restart_process(proc_def: dict) -> bool:
    """Restart a crashed process if under the restart limit."""
    name = proc_def["name"]
    _restart_counts[name] = _restart_counts.get(name, 0) + 1

    if _restart_counts[name] > MAX_RESTART_ATTEMPTS:
        msg = f"CRITICAL: {name} has crashed {_restart_counts[name]} times — giving up restart"
        log.error(msg)
        _write_watchdog_log(msg, "CRITICAL")
        return False

    msg = f"Restarting {name} (attempt {_restart_counts[name]}/{MAX_RESTART_ATTEMPTS})"
    log.warning(msg)
    _write_watchdog_log(msg, "WARN")

    # Kill existing if zombie
    old = _process_registry.get(name)
    if old:
        try:
            old.terminate()
            old.wait(timeout=5)
        except Exception:
            pass

    new_proc = start_process(proc_def)
    if new_proc:
        _restart_counts[name] = 0  # Reset on successful restart
        return True
    return False


def check_stalled_tasks() -> list[str]:
    """Find tasks stuck in Needs_Action beyond the stall threshold."""
    stalled = []
    threshold = datetime.now(timezone.utc) - timedelta(minutes=STALL_THRESHOLD_MINUTES)

    NEEDS_ACTION_DIR.mkdir(parents=True, exist_ok=True)
    for f in NEEDS_ACTION_DIR.glob("*.md"):
        try:
            mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
            if mtime < threshold:
                stalled.append(f.name)
        except Exception:
            pass

    if stalled:
        msg = f"Stalled tasks detected ({len(stalled)}): {', '.join(stalled[:3])}"
        log.warning(msg)
        _write_watchdog_log(msg, "WARN")

    return stalled


def check_inbox_overflow() -> int:
    """Warn if Inbox has an unusually large number of tasks."""
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    count = sum(1 for _ in INBOX_DIR.glob("*.md"))
    if count > 20:
        msg = f"Inbox overflow detected: {count} tasks pending"
        log.warning(msg)
        _write_watchdog_log(msg, "WARN")
    return count


def check_system_resources() -> dict:
    """Check CPU and memory usage."""
    try:
        cpu_pct = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        metrics = {
            "cpu_percent":  cpu_pct,
            "mem_percent":  mem.percent,
            "disk_percent": disk.percent,
        }

        if cpu_pct > 90:
            _write_watchdog_log(f"High CPU usage: {cpu_pct}%", "WARN")
        if mem.percent > 85:
            _write_watchdog_log(f"High memory usage: {mem.percent}%", "WARN")
        if disk.percent > 90:
            _write_watchdog_log(f"High disk usage: {disk.percent}%", "WARN")

        return metrics
    except Exception as e:
        log.debug(f"Resource check error (non-critical): {e}")
        return {}


def write_health_summary(metrics: dict, stalled: list, inbox_count: int) -> None:
    """Write a brief status summary to the watchdog log."""
    cpu  = metrics.get("cpu_percent", "?")
    mem  = metrics.get("mem_percent", "?")
    disk = metrics.get("disk_percent", "?")
    running = [n for n, p in _process_registry.items() if _is_process_alive(p)]
    dead    = [n for n, p in _process_registry.items() if not _is_process_alive(p)]

    summary = (
        f"Health check — Running: [{', '.join(running) or 'none'}] | "
        f"Dead: [{', '.join(dead) or 'none'}] | "
        f"Inbox: {inbox_count} | Stalled: {len(stalled)} | "
        f"CPU: {cpu}% | MEM: {mem}% | Disk: {disk}%"
    )
    _write_watchdog_log(summary, "INFO")


def run_watchdog(start_processes: bool = False) -> None:
    """
    Main watchdog loop.

    Args:
        start_processes: If True, start all monitored processes on launch.
                         Set to False when running alongside PM2.
    """
    global _shutdown

    # Initialize watchdog log
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    if not WATCHDOG_LOG.exists():
        WATCHDOG_LOG.write_text(
            "# Watchdog Log\n\n> Self-healing monitor for AI Employee system.\n\n",
            encoding="utf-8",
        )

    _write_watchdog_log("Watchdog started", "INFO")
    log.info(f"Watchdog active — checking every {CHECK_INTERVAL}s")

    def _handle_signal(sig, frame):
        global _shutdown
        _shutdown = True
        _write_watchdog_log("Watchdog stopping (signal received)", "INFO")
        log.info("Watchdog shutting down")

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    # Optionally start all processes
    if start_processes:
        for proc_def in MONITORED_PROCESSES:
            start_process(proc_def)
        time.sleep(2)

    cycle = 0
    while not _shutdown:
        cycle += 1

        # Check each monitored process
        for proc_def in MONITORED_PROCESSES:
            name = proc_def["name"]
            proc = _process_registry.get(name)
            if proc is None:
                continue  # Not managed by this watchdog instance
            if not _is_process_alive(proc):
                msg = f"Process CRASHED: {name} (exit code {proc.returncode})"
                log.error(msg)
                _write_watchdog_log(msg, "ERROR")
                restart_process(proc_def)

        # Check task pipeline health
        stalled     = check_stalled_tasks()
        inbox_count = check_inbox_overflow()
        metrics     = check_system_resources()

        if cycle % 10 == 0:  # Every 10 cycles write a health summary
            write_health_summary(metrics, stalled, inbox_count)

        time.sleep(CHECK_INTERVAL)

    _write_watchdog_log("Watchdog stopped cleanly", "INFO")
    log.info("Watchdog stopped")


if __name__ == "__main__":
    # When run directly: start all processes and watch them
    run_watchdog(start_processes=True)
