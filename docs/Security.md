# Security

## Credentials

**Never commit credentials to the repository.**

All secrets are loaded from `.env` via `python-dotenv`. The `.env` file is in `.gitignore`.

Use `.env.example` as a template:
```bash
cp .env.example .env
# Fill in your values
```

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | Anthropic API key | Yes |
| `GMAIL_USER` | Gmail address | For Gmail watcher |
| `GMAIL_APP_PASSWORD` | Gmail App Password (not account password) | For Gmail watcher |
| `WHATSAPP_API_URL` | WhatsApp Business API URL | For WhatsApp watcher |
| `WHATSAPP_API_KEY` | WhatsApp Bearer token | For WhatsApp watcher |
| `GOOGLE_CALENDAR_CREDENTIALS_PATH` | Path to Google OAuth JSON | For Calendar MCP |
| `WATCH_PATH` | Directory to monitor | For Filesystem watcher |

---

## PII Protection

- Email addresses are masked in logs: `jo**@example.com`
- Phone numbers are masked in logs: `+1****7890`
- Task body content is never logged to console — only to vault Logs

---

## Filesystem Sandboxing

The Filesystem MCP only writes to `agent_outputs/` by default.
Delete operations require `require_in_output=True` (default).

```python
# This is blocked:
delete_file("/etc/hosts")  # Outside output dir

# This is allowed:
delete_file("output_task123.txt")  # Inside output dir
```

---

## HITL as a Security Layer

Sensitive actions are never executed without human approval:
- Sending emails
- Scheduling external meetings
- Accessing financial data
- Deleting files
- Publishing content

The approval file must be manually edited in Obsidian — there is no programmatic auto-approval.

---

## API Key Rotation

If credentials are compromised:
1. Revoke the compromised key immediately
2. Generate a new key
3. Update `.env`
4. Restart services

---

## Audit Trail

All agent actions are logged to:
- `history/prompts.md` — full prompt/response pairs
- `history/agent_runs.md` — execution records
- `history/approvals.md` — approval decisions
- `AI_Employee_Vault/Logs/YYYY-MM-DD.md` — daily system logs

These files are the complete audit trail for security review.
