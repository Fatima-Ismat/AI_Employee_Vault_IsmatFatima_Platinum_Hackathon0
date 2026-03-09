# CEO Briefing System

## Overview

The CEO AI Weekly Briefing System automatically generates an executive report by analyzing all completed tasks, system logs, and business goals.

**Output:** `AI_Employee_Vault/CEO_Briefing.md`

## How It Works

```
1. Collect completed tasks from Done/ (last 7 days)
2. Collect system logs from Logs/ (last 7 days)
3. Read Business_Goals.md
4. Parse agent run statistics from history/agent_runs.md
5. Call Claude with structured business analysis prompt
6. Write formatted briefing to CEO_Briefing.md
7. Log the prompt/response to history/prompts.md
```

## Report Sections

| Section | Content |
|---------|---------|
| Executive Summary | 3-4 sentence overview |
| Revenue & Business Insights | Inferred from task patterns |
| Completed Work | Prioritized accomplishments |
| Problems Detected | Errors, failures, bottlenecks |
| Opportunities Identified | Patterns, automation possibilities |
| AI Recommendations | 3-5 concrete action items |

## Run Manually

```bash
python -m analytics.ceo_briefing
```

## Schedule Weekly (cron)

```bash
# Add to crontab (every Monday at 9am)
0 9 * * 1 cd /path/to/repo && python -m analytics.ceo_briefing
```

## Fallback

If the Claude API is unavailable, a template-based briefing is generated using raw metrics only (no LLM required).

## Dashboard Integration

The CEO Briefing tab in the frontend dashboard reads and renders the briefing as formatted Markdown with syntax highlighting.
