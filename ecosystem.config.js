/**
 * PM2 Ecosystem Configuration — Platinum Tier
 * ──────────────────────────────────────────────
 * Manages all AI Employee processes as persistent background daemons.
 *
 * Usage:
 *   pm2 start ecosystem.config.js    # Start all
 *   pm2 stop all                     # Stop all
 *   pm2 restart all                  # Restart all
 *   pm2 monit                        # Live monitoring dashboard
 *   pm2 logs                         # Tail all logs
 *   pm2 logs ralph-wiggum            # Tail specific process
 */

const BASE = {
  cwd:          __dirname,
  interpreter:  "none",
  watch:        false,
  autorestart:  true,
  max_restarts: 10,
  restart_delay: 5000,
  env: { PYTHONUNBUFFERED: "1" },
};

module.exports = {
  apps: [

    // ── Ralph Wiggum Orchestrator (primary) ─────────────────────────────────
    {
      ...BASE,
      name:       "ralph-wiggum",
      script:     "python",
      args:       "-m orchestrator.agent_loop",
      log_file:   "logs/pm2/ralph-wiggum.log",
      error_file: "logs/pm2/ralph-wiggum-error.log",
      time:       true,
    },

    // ── Watchers ──────────────────────────────────────────────────────────────
    {
      ...BASE,
      name:         "gmail-watcher",
      script:       "python",
      args:         "-m watchers.gmail_watcher",
      restart_delay: 10000,
      log_file:     "logs/pm2/gmail-watcher.log",
      error_file:   "logs/pm2/gmail-watcher-error.log",
      time:         true,
    },
    {
      ...BASE,
      name:       "filesystem-watcher",
      script:     "python",
      args:       "-m watchers.filesystem_watcher",
      log_file:   "logs/pm2/filesystem-watcher.log",
      error_file: "logs/pm2/filesystem-watcher-error.log",
      time:       true,
    },
    {
      ...BASE,
      name:         "whatsapp-watcher",
      script:       "python",
      args:         "-m watchers.whatsapp_watcher",
      restart_delay: 10000,
      log_file:     "logs/pm2/whatsapp-watcher.log",
      error_file:   "logs/pm2/whatsapp-watcher-error.log",
      time:         true,
    },

    // ── Watchdog ──────────────────────────────────────────────────────────────
    {
      ...BASE,
      name:       "watchdog",
      script:     "python",
      args:       "-m watchdog_service.watchdog",
      log_file:   "logs/pm2/watchdog.log",
      error_file: "logs/pm2/watchdog-error.log",
      time:       true,
    },

    // ── System Health Monitor ─────────────────────────────────────────────────
    {
      ...BASE,
      name:       "health-monitor",
      script:     "python",
      args:       "-m monitoring.system_health",
      log_file:   "logs/pm2/health-monitor.log",
      error_file: "logs/pm2/health-monitor-error.log",
      time:       true,
    },

    // ── Error Recovery ────────────────────────────────────────────────────────
    {
      ...BASE,
      name:       "error-recovery",
      script:     "python",
      args:       "-m resilience.error_recovery --loop",
      log_file:   "logs/pm2/error-recovery.log",
      error_file: "logs/pm2/error-recovery-error.log",
      time:       true,
    },

    // ── FastAPI Backend ───────────────────────────────────────────────────────
    {
      ...BASE,
      name:       "backend-api",
      script:     "uvicorn",
      args:       "backend.main:app --host 0.0.0.0 --port 8000",
      log_file:   "logs/pm2/backend-api.log",
      error_file: "logs/pm2/backend-api-error.log",
      time:       true,
    },

    // ── Cloud Sync Manager (optional — comment out if not using cloud) ─────────
    // {
    //   ...BASE,
    //   name:         "cloud-sync",
    //   script:       "python",
    //   args:         "-m cloud.sync_manager",
    //   restart_delay: 15000,
    //   log_file:     "logs/pm2/cloud-sync.log",
    //   error_file:   "logs/pm2/cloud-sync-error.log",
    //   time:         true,
    // },

    // ── Frontend (via Next.js — use only if not serving separately) ────────────
    // {
    //   name:       "frontend",
    //   script:     "npm",
    //   args:       "run start",
    //   cwd:        __dirname + "/frontend",
    //   interpreter: "none",
    //   watch:      false,
    //   env: { PORT: "3000", NODE_ENV: "production" },
    //   log_file:   "logs/pm2/frontend.log",
    //   error_file: "logs/pm2/frontend-error.log",
    //   time:       true,
    // },
  ],
};
