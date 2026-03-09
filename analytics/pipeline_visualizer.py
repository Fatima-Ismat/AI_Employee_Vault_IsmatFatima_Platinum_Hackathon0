"""
Task Pipeline Visualizer
─────────────────────────
Generates a visual ASCII + Markdown diagram of task movement
through the pipeline. Reads all vault folders and produces stats.

Output:
  AI_Employee_Vault/Logs/pipeline_report.md
  Printed to console as ASCII art

Run:
  python -m analytics.pipeline_visualizer
"""

import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.config import (
    VAULT_DIR, INBOX_DIR, NEEDS_ACTION_DIR, PLANS_DIR,
    PENDING_DIR, APPROVED_DIR, REJECTED_DIR, DONE_DIR, LOGS_DIR,
)
from utils.logger import get_logger

log = get_logger("analytics.pipeline_visualizer")

REPORT_PATH = LOGS_DIR / "pipeline_report.md"

STAGES = [
    ("Inbox",            INBOX_DIR),
    ("Needs_Action",     NEEDS_ACTION_DIR),
    ("Plans",            PLANS_DIR),
    ("Pending_Approval", PENDING_DIR),
    ("Approved",         APPROVED_DIR),
    ("Rejected",         REJECTED_DIR),
    ("Done",             DONE_DIR),
]


def count_tasks(folder: Path) -> int:
    if not folder.exists():
        return 0
    return sum(1 for f in folder.glob("*.md") if not f.name.startswith("."))


def collect_source_breakdown() -> Counter:
    """Count tasks by source across all folders."""
    counter: Counter = Counter()
    for _, folder in STAGES:
        if not folder.exists():
            continue
        for f in folder.glob("*.md"):
            try:
                content = f.read_text(encoding="utf-8")
                for line in content.splitlines():
                    if line.startswith("source:"):
                        source = line.split(":", 1)[1].strip()
                        counter[source] += 1
                        break
            except Exception:
                pass
    return counter


def collect_priority_breakdown() -> Counter:
    """Count tasks by priority across Done folder."""
    counter: Counter = Counter()
    if DONE_DIR.exists():
        for f in DONE_DIR.glob("*.md"):
            try:
                content = f.read_text(encoding="utf-8")
                for line in content.splitlines():
                    if line.startswith("priority:"):
                        p = line.split(":", 1)[1].strip()
                        counter[p] += 1
                        break
            except Exception:
                pass
    return counter


def render_ascii_pipeline(counts: dict) -> str:
    """Render a horizontal ASCII pipeline diagram."""
    stages = ["Inbox", "Needs_Action", "Pending_Approval", "Done", "Rejected"]
    boxes = []
    for stage in stages:
        n = counts.get(stage, 0)
        label = f"{stage}\n[{n:>3}]"
        width = max(len(stage), 7) + 4
        top    = "┌" + "─" * width + "┐"
        middle = "│" + f" {stage} ".center(width) + "│"
        count  = "│" + f"  [{n}]  ".center(width) + "│"
        bottom = "└" + "─" * width + "┘"
        boxes.append((top, middle, count, bottom))

    arrows = "  ──►  "
    lines = ["", ""]
    for i, (top, mid, cnt, bot) in enumerate(boxes):
        sep = arrows if i < len(boxes) - 1 else ""
        lines[0] = lines[0] if lines[0] else ""

    # Build line-by-line
    rows = [[], [], [], []]
    for i, (top, mid, cnt, bot) in enumerate(boxes):
        arrow = "  ──►  " if i < len(boxes) - 1 else ""
        rows[0].append(top + (" " * len(arrow)))
        rows[1].append(mid + (arrow if i < len(boxes) - 1 else ""))
        rows[2].append(cnt + (" " * len(arrow)))
        rows[3].append(bot + (" " * len(arrow)))

    return "\n".join("".join(r) for r in rows)


def generate_report() -> str:
    """Build the full pipeline report as Markdown."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    counts = {stage: count_tasks(folder) for stage, folder in STAGES}
    total = sum(counts.values())
    sources = collect_source_breakdown()
    priorities = collect_priority_breakdown()

    completion_rate = (
        round(counts["Done"] / max(total - counts["Inbox"], 1) * 100, 1)
        if total > 0 else 0
    )
    approval_rate = (
        round(counts["Approved"] / max(counts["Approved"] + counts["Rejected"], 1) * 100, 1)
        if (counts["Approved"] + counts["Rejected"]) > 0 else 0
    )

    ascii_diagram = render_ascii_pipeline(counts)

    source_table = "\n".join(
        f"| {src} | {cnt} |" for src, cnt in sources.most_common()
    ) or "| — | — |"

    priority_table = "\n".join(
        f"| {p} | {cnt} |" for p, cnt in sorted(priorities.items())
    ) or "| — | — |"

    # Bar chart for pipeline stages
    bar_chart = ""
    max_count = max(counts.values()) or 1
    for stage, count in counts.items():
        bar_len = int(count / max_count * 30)
        bar = "█" * bar_len + "░" * (30 - bar_len)
        bar_chart += f"  {stage:<20} {bar} {count}\n"

    report = f"""# Task Pipeline Report

> **Generated:** {ts}
> **Total Tasks Tracked:** {total}

---

## Pipeline Overview (ASCII)

```
{ascii_diagram}
```

---

## Stage Counts

| Stage | Count | % of Total |
|-------|-------|-----------|
"""
    for stage, count in counts.items():
        pct = round(count / max(total, 1) * 100, 1)
        report += f"| {stage} | {count} | {pct}% |\n"

    report += f"""
---

## Pipeline Bar Chart

```
{bar_chart}```

---

## Key Metrics

| Metric | Value |
|--------|-------|
| Task Completion Rate | {completion_rate}% |
| HITL Approval Rate | {approval_rate}% |
| Tasks in Inbox | {counts['Inbox']} |
| Tasks Done | {counts['Done']} |
| Tasks Rejected | {counts['Rejected']} |

---

## Task Sources

| Source | Count |
|--------|-------|
{source_table}

---

## Priority Distribution (Completed Tasks)

| Priority | Count |
|----------|-------|
{priority_table}
"""
    return report


def run_visualization() -> Path:
    """Generate and write the pipeline report."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    report = generate_report()
    REPORT_PATH.write_text(report, encoding="utf-8")
    log.info(f"Pipeline report written: {REPORT_PATH}")

    # Also print ASCII overview to console
    counts = {stage: count_tasks(folder) for stage, folder in STAGES}
    print("\n" + render_ascii_pipeline(counts) + "\n")
    print(f"Full report: {REPORT_PATH}")
    return REPORT_PATH


if __name__ == "__main__":
    run_visualization()
