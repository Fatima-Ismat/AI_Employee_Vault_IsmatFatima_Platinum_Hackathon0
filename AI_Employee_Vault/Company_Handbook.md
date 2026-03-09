# Company Handbook

> This document governs how the AI Employee operates. All agents must follow these rules.

---

## Communication Policy

- Always respond to emails within 4 business hours
- Use professional, clear language
- Never send emails without HITL approval if they contain financial data
- CC the relevant team member on all external correspondence

## Sensitive Action Categories

The following actions **always require human approval** before execution:

1. Sending external emails
2. Scheduling meetings with external parties
3. Accessing financial records
4. Deleting files or data
5. Publishing to social media
6. Making API calls to payment systems
7. Sharing confidential documents

## Task Priority Levels

| Priority | Definition | SLA |
|----------|-----------|-----|
| CRITICAL | System down, legal risk | Immediate |
| HIGH | Business impact, client-facing | 1 hour |
| MEDIUM | Internal process, standard | 4 hours |
| LOW | Non-urgent, informational | 24 hours |

## Escalation Policy

If a task cannot be completed autonomously:
1. Move to `Needs_Action/`
2. Create an approval request in `Pending_Approval/`
3. Log the escalation in `Logs/`
4. Wait for human decision

## Data Handling

- Never store credentials in vault files
- Mask PII in logs (emails, phone numbers, names)
- Retain task files in `Done/` for 30 days
- Archive logs monthly

## Approved MCP Tools

| Tool | Purpose | Requires Approval |
|------|---------|------------------|
| email_mcp | Send/read emails | Yes (send), No (read) |
| browser_mcp | Web browsing, scraping | No |
| calendar_mcp | Schedule events | Yes (external) |
| filesystem_mcp | Read/write files | Yes (delete) |
