"""
AI Employee — FastAPI Backend
──────────────────────────────
REST API that powers the frontend dashboard.
Reads live data from the Obsidian vault and history files.

Run:
  uvicorn backend.main:app --reload --port 8000

Endpoints:
  GET  /                    Health check
  GET  /system-status       Overall system health
  GET  /tasks               All tasks (filterable by stage/source/priority)
  GET  /tasks/{task_id}     Single task detail
  GET  /logs                Recent log entries
  GET  /approvals           Approval history
  GET  /ceo-briefing        Latest CEO briefing content
  POST /approvals/{id}/decide   Approve or reject via API
  GET  /pipeline-stats      Pipeline counts per stage
  GET  /analytics           Business metrics and trends
  POST /tasks/inject        Inject a demo task (for testing)
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from utils.config import (
    VAULT_DIR, INBOX_DIR, NEEDS_ACTION_DIR, PLANS_DIR,
    PENDING_DIR, APPROVED_DIR, REJECTED_DIR, DONE_DIR, LOGS_DIR,
    HISTORY_DIR, AGENT_RUNS_LOG, APPROVALS_LOG, PROMPTS_LOG,
)
from utils.vault_io import write_inbox_task

app = FastAPI(
    title="AI Employee Vault API",
    description="Backend API for AI_Employee_Vault_IsmatFatima_Platinum_Hackathon0",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://141.145.155.147:3000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://ismat110-ai-employee-vault-ismat-platinum.hf.space",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Helpers ───────────────────────────────────────────────────────────────────

STAGE_MAP = {
    "inbox":            INBOX_DIR,
    "needs_action":     NEEDS_ACTION_DIR,
    "plans":            PLANS_DIR,
    "pending_approval": PENDING_DIR,
    "approved":         APPROVED_DIR,
    "rejected":         REJECTED_DIR,
    "done":             DONE_DIR,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _extract_field(content: str, field: str) -> str:
    for line in content.splitlines():
        if line.startswith(f"{field}:"):
            return line.split(":", 1)[1].strip()
    return ""


def _parse_task_file(f: Path, stage: str) -> dict:
    try:
        content = f.read_text(encoding="utf-8")
        return {
            "id":         f.stem,
            "filename":   f.name,
            "stage":      stage,
            "title":      _extract_field(content, "title") or f.stem,
            "source":     _extract_field(content, "source") or "unknown",
            "priority":   _extract_field(content, "priority") or "MEDIUM",
            "status":     _extract_field(content, "status") or stage,
            "created_at": _extract_field(content, "created_at"),
            "preview":    content[content.find("## Description") + 15:][:200].strip()
                          if "## Description" in content else content[:200],
            "size":       f.stat().st_size,
        }
    except Exception:
        return {"id": f.stem, "filename": f.name, "stage": stage, "title": f.stem}


def _count_stage(folder: Path) -> int:
    if not folder.exists():
        return 0
    return sum(1 for f in folder.glob("*.md") if not f.name.startswith("."))


def _read_history_file(path: Path, limit: int = 50) -> list[str]:
    if not path.exists():
        return []
    content = path.read_text(encoding="utf-8")
    # Split by entry separator
    entries = [e.strip() for e in content.split("---") if e.strip() and not e.strip().startswith("#")]
    return entries[-limit:]


# ── Models ────────────────────────────────────────────────────────────────────

class ApprovalDecision(BaseModel):
    decision: str   # "approved" | "rejected"
    reason: Optional[str] = ""


class InjectTaskRequest(BaseModel):
    title: str
    source: str = "api_demo"
    body: str = "Injected via API for demo purposes."
    priority: str = "MEDIUM"


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "service": "AI Employee Vault API",
        "status":  "running",
        "version": "1.0.0",
        "time":    _now(),
    }


@app.get("/system-status")
def system_status():
    """Overall system health and process status."""
    return {
        "status":    "operational",
        "timestamp": _now(),
        "pipeline": {
            stage: _count_stage(folder)
            for stage, folder in STAGE_MAP.items()
        },
        "vault_exists":   VAULT_DIR.exists(),
        "history_exists": HISTORY_DIR.exists(),
        "briefing_exists": (VAULT_DIR / "CEO_Briefing.md").exists(),
    }


@app.get("/tasks")
def list_tasks(
    stage:    Optional[str] = Query(None, description="Filter by stage"),
    source:   Optional[str] = Query(None, description="Filter by source"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    limit:    int           = Query(100, ge=1, le=500),
):
    """Return all tasks across the pipeline, optionally filtered."""
    tasks = []
    stages = {stage: STAGE_MAP[stage]} if stage and stage in STAGE_MAP else STAGE_MAP

    for stage_name, folder in stages.items():
        if not folder.exists():
            continue
        for f in folder.glob("*.md"):
            if f.name.startswith("."):
                continue
            task = _parse_task_file(f, stage_name)
            if source   and task.get("source", "")   != source:
                continue
            if priority and task.get("priority", "") != priority:
                continue
            tasks.append(task)

    tasks.sort(key=lambda t: t.get("created_at", ""), reverse=True)
    return {"tasks": tasks[:limit], "total": len(tasks)}


@app.get("/tasks/{task_id}")
def get_task(task_id: str):
    """Return full content of a specific task."""
    for stage_name, folder in STAGE_MAP.items():
        if not folder.exists():
            continue
        for f in folder.glob("*.md"):
            if f.stem == task_id or task_id in f.stem:
                content = f.read_text(encoding="utf-8")
                task = _parse_task_file(f, stage_name)
                task["full_content"] = content
                return task
    raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")


@app.get("/logs")
def list_logs(limit: int = Query(20, ge=1, le=200)):
    """Return recent log file entries."""
    entries = []
    if not LOGS_DIR.exists():
        return {"logs": []}

    for log_file in sorted(LOGS_DIR.glob("*.md"), reverse=True)[:5]:
        content = log_file.read_text(encoding="utf-8")
        lines = [l.strip() for l in content.splitlines()
                 if l.strip().startswith("-") and "`" in l]
        for line in lines:
            entries.append({
                "date":    log_file.stem,
                "raw":     line,
                "content": line,
            })

    return {"logs": entries[-limit:], "total": len(entries)}


@app.get("/approvals")
def list_approvals():
    """Return approval history from history/approvals.md."""
    entries = _read_history_file(APPROVALS_LOG, limit=50)
    return {"approvals": entries, "total": len(entries)}


@app.get("/approvals/pending")
def list_pending_approvals():
    """Return pending approval files from Pending_Approval/."""
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    pending = []
    for f in PENDING_DIR.glob("*.md"):
        content = f.read_text(encoding="utf-8")
        status  = _extract_field(content, "status")
        if status == "pending":
            pending.append({
                "filename":     f.name,
                "approval_id":  _extract_field(content, "approval_id"),
                "task_id":      _extract_field(content, "task_id"),
                "requested_at": _extract_field(content, "requested_at"),
                "preview":      content[:400],
            })
    return {"pending": pending, "count": len(pending)}


@app.post("/approvals/{filename}/decide")
def decide_approval(filename: str, decision: ApprovalDecision):
    """Approve or reject a pending task via API (simulates human Obsidian edit)."""
    if decision.decision not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="Decision must be 'approved' or 'rejected'")

    approval_file = PENDING_DIR / filename
    if not approval_file.exists():
        raise HTTPException(status_code=404, detail=f"Approval file not found: {filename}")

    content = approval_file.read_text(encoding="utf-8")
    if "status: pending" not in content:
        raise HTTPException(status_code=409, detail="Approval already decided")

    updated = content.replace("status: pending", f"status: {decision.decision}")
    if decision.reason:
        updated += f"\n\n**Decision Reason:** {decision.reason}\n"
    approval_file.write_text(updated, encoding="utf-8")

    return {
        "success":  True,
        "filename": filename,
        "decision": decision.decision,
        "message":  f"Approval {decision.decision} — orchestrator will pick up on next cycle",
    }


@app.get("/ceo-briefing")
def get_ceo_briefing():
    """Return the latest CEO briefing content."""
    briefing_path = VAULT_DIR / "CEO_Briefing.md"
    if not briefing_path.exists():
        return {"exists": False, "content": None, "message": "Run analytics/ceo_briefing.py first"}
    content = briefing_path.read_text(encoding="utf-8")
    return {
        "exists":    True,
        "content":   content,
        "size":      len(content),
        "modified":  datetime.fromtimestamp(
            briefing_path.stat().st_mtime, tz=timezone.utc
        ).isoformat(),
    }


@app.get("/pipeline-stats")
def pipeline_stats():
    """Return task counts per stage for dashboard visualization."""
    counts = {stage: _count_stage(folder) for stage, folder in STAGE_MAP.items()}
    total = sum(counts.values())
    completion_rate = round(counts["done"] / max(total - counts["inbox"], 1) * 100, 1) if total > 0 else 0

    return {
        "counts":          counts,
        "total":           total,
        "completion_rate": completion_rate,
        "timestamp":       _now(),
    }


@app.get("/analytics")
def analytics():
    """Aggregate analytics across the system."""
    from analytics.pipeline_visualizer import collect_source_breakdown, collect_priority_breakdown
    sources    = dict(collect_source_breakdown().most_common(10))
    priorities = dict(collect_priority_breakdown())
    counts     = {stage: _count_stage(folder) for stage, folder in STAGE_MAP.items()}

    # Parse agent runs for success rate
    success, failed, total = 0, 0, 0
    if AGENT_RUNS_LOG.exists():
        content = AGENT_RUNS_LOG.read_text(encoding="utf-8")
        total   = content.count("status:")
        success = content.count("status: success")
        failed  = content.count("status: failed")

    return {
        "pipeline_counts": counts,
        "source_breakdown":   sources,
        "priority_breakdown": priorities,
        "agent_runs": {
            "total":   total,
            "success": success,
            "failed":  failed,
            "success_rate": round(success / max(total, 1) * 100, 1),
        },
        "timestamp": _now(),
    }


@app.post("/tasks/inject")
def inject_task(req: InjectTaskRequest):
    """Inject a task into Inbox (for demo and testing)."""
    path = write_inbox_task(
        title=req.title,
        source=req.source,
        body=req.body,
        priority=req.priority,
        metadata={"injected_via": "api"},
    )
    return {
        "success":  True,
        "filename": path.name,
        "stage":    "inbox",
        "message":  "Task injected — orchestrator will pick up on next cycle",
    }


@app.get("/prompt-history")
def prompt_history(limit: int = Query(10, ge=1, le=100)):
    """Return recent prompt/response pairs from history."""
    entries = _read_history_file(PROMPTS_LOG, limit=limit)
    return {"prompts": entries, "total": len(entries)}
