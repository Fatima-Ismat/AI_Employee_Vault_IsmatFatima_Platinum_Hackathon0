"""
Centralized configuration loader for the AI Employee system.
Reads from .env and provides typed access to all settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=False)  # env vars already in os.environ take priority

# ── Repository root ────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parents[1]

# ── Vault paths ────────────────────────────────────────────────────────────────
VAULT_DIR         = ROOT_DIR / "AI_Employee_Vault"
INBOX_DIR         = VAULT_DIR / "Inbox"
NEEDS_ACTION_DIR  = VAULT_DIR / "Needs_Action"
PLANS_DIR         = VAULT_DIR / "Plans"
PENDING_DIR       = VAULT_DIR / "Pending_Approval"
APPROVED_DIR      = VAULT_DIR / "Approved"
REJECTED_DIR      = VAULT_DIR / "Rejected"
DONE_DIR          = VAULT_DIR / "Done"
LOGS_DIR          = VAULT_DIR / "Logs"

# ── History paths ──────────────────────────────────────────────────────────────
HISTORY_DIR       = ROOT_DIR / "history"
PROMPTS_LOG       = HISTORY_DIR / "prompts.md"
AGENT_RUNS_LOG    = HISTORY_DIR / "agent_runs.md"
APPROVALS_LOG     = HISTORY_DIR / "approvals.md"

# ── Demo mode — defaults to true; set DEMO_MODE=false for live API calls ──────
DEMO_MODE = os.getenv("DEMO_MODE", "true").strip().lower() in ("true", "1", "yes")

# ── Anthropic / Claude ─────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL      = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
MAX_TOKENS        = int(os.getenv("MAX_TOKENS", "8096"))

# ── Gmail ──────────────────────────────────────────────────────────────────────
GMAIL_USER        = os.getenv("GMAIL_USER", "")
GMAIL_APP_PASSWORD= os.getenv("GMAIL_APP_PASSWORD", "")
GMAIL_POLL_INTERVAL = int(os.getenv("GMAIL_POLL_INTERVAL", "60"))  # seconds

# ── WhatsApp ───────────────────────────────────────────────────────────────────
WHATSAPP_API_URL  = os.getenv("WHATSAPP_API_URL", "")
WHATSAPP_API_KEY  = os.getenv("WHATSAPP_API_KEY", "")

# ── Orchestrator ───────────────────────────────────────────────────────────────
LOOP_INTERVAL     = int(os.getenv("LOOP_INTERVAL", "10"))          # seconds
MAX_RETRIES       = int(os.getenv("MAX_RETRIES", "3"))

# ── Sensitive action keywords (triggers HITL) ──────────────────────────────────
SENSITIVE_KEYWORDS = [
    "send email",
    "delete",
    "payment",
    "financial",
    "schedule meeting",
    "publish",
    "share confidential",
    "external",
]

def ensure_dirs() -> None:
    """Create all vault and history directories if they don't exist."""
    dirs = [
        INBOX_DIR, NEEDS_ACTION_DIR, PLANS_DIR, PENDING_DIR,
        APPROVED_DIR, REJECTED_DIR, DONE_DIR, LOGS_DIR, HISTORY_DIR,
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
