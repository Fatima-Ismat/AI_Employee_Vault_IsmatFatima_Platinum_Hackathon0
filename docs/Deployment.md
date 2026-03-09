# Deployment

## Local Development

### Prerequisites

- Python 3.11+
- pip
- (Optional) PM2 for process management: `npm install -g pm2`
- (Optional) Obsidian desktop app for vault visualization

### Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd AI_Employee_Vault_IsmatFatima_Platinum_Hackathon0

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and fill in your ANTHROPIC_API_KEY at minimum

# 5. Run the orchestrator (starts the full pipeline)
python -m orchestrator.agent_loop
```

### Running Individual Components

```bash
# Run only the Gmail watcher
python -m watchers.gmail_watcher

# Run only the filesystem watcher
python -m watchers.filesystem_watcher

# Run only the WhatsApp watcher
python -m watchers.whatsapp_watcher

# Run the agent on a specific task file
python -c "
from agents.claude_agent import ClaudeAgent
from pathlib import Path
agent = ClaudeAgent()
agent.process_task(Path('AI_Employee_Vault/Inbox/your_task.md'))
"
```

---

## PM2 Process Manager

PM2 runs all components as background daemons with auto-restart.

```bash
# Install PM2
npm install -g pm2

# Start all processes
pm2 start ecosystem.config.js

# Monitor
pm2 monit

# View logs
pm2 logs

# Stop all
pm2 stop all

# Restart
pm2 restart all

# Save process list (survives reboot)
pm2 save
pm2 startup
```

---

## Demo Run (No Credentials)

The system runs in demo mode when credentials are not set.
Watchers inject simulated tasks automatically.

```bash
# Only ANTHROPIC_API_KEY is needed for demo
echo "ANTHROPIC_API_KEY=your-key-here" > .env

# Start the loop — demo tasks will be injected automatically
python -m orchestrator.agent_loop
```

Watch the vault:
- `AI_Employee_Vault/Inbox/` — new tasks appear
- `AI_Employee_Vault/Plans/` — Claude's plans
- `AI_Employee_Vault/Pending_Approval/` — tasks awaiting approval
- `AI_Employee_Vault/Done/` — completed tasks
- `history/prompts.md` — full Claude prompt logs

---

## Opening the Vault in Obsidian

1. Open Obsidian
2. Click "Open folder as vault"
3. Select `AI_Employee_Vault/`
4. Install the Dataview plugin for live dashboard queries
5. Open `Dashboard.md`

---

## Production Considerations

- Run behind a reverse proxy (nginx) if exposing any HTTP endpoints
- Use environment-specific `.env` files (`.env.production`)
- Set up log rotation for `AI_Employee_Vault/Logs/`
- Back up `history/` regularly — it is your audit trail
- Monitor PM2 with `pm2-logrotate` plugin
