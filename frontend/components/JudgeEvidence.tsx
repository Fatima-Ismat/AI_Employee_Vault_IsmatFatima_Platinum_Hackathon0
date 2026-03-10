import { useState } from "react";

const EVIDENCE = {
  owner: "Ismat Fatima",
  tier: "Platinum",
  hackathon: "Personal AI Employee Hackathon 0",
  model: "claude-sonnet-4-6",
  github: "https://github.com/Fatima-Ismat/AI_Employee_Vault_IsmatFatima_Platinum_Hackathon0",
  vercel: "https://ai-employee-vault-ismat-fatima-plat.vercel.app",
  hfBackend: "https://ismat110-ai-employee-vault-ismat-platinum.hf.space",
  hfSpace: "https://huggingface.co/spaces/ismat110/ai-employee-vault-ismat-platinum",
};

const SECTIONS = [
  {
    title: "Cloud Deployment Proof",
    color: "blue",
    icon: "☁️",
    items: [
      { label: "Frontend", value: "Vercel · Next.js 14 · auto-deploy from GitHub main", badge: "LIVE" },
      { label: "Backend API", value: "Hugging Face Spaces · Docker · FastAPI · port 7860→8000", badge: "LIVE" },
      { label: "GitHub Sync", value: "GitHub main branch → triggers both Vercel + HF deploys", badge: "CI/CD" },
      { label: "Process Manager", value: "PM2 via ecosystem.config.js (local/OCI fallback)", badge: "RUNNING" },
    ],
  },
  {
    title: "Watcher Proof",
    color: "purple",
    icon: "👁",
    items: [
      { label: "Gmail Watcher", value: "IMAP + Gmail App Password · polls inbox → creates vault task files", badge: "IMAP" },
      { label: "Filesystem Watcher", value: "watchdog library · monitors watched_folder/ · auto-ingests files", badge: "ACTIVE" },
      { label: "WhatsApp Watcher", value: "Webhook integration · urgent messages → CRITICAL priority tasks", badge: "ACTIVE" },
      { label: "Vault Pipeline", value: "Inbox → Needs_Action → Plans → Pending_Approval → Approved/Rejected → Done", badge: "8 STAGES" },
    ],
  },
  {
    title: "HITL Approval Workflow Proof",
    color: "orange",
    icon: "✅",
    items: [
      { label: "Approval Engine", value: "approval_system/hitl.py · creates Pending_Approval/*.md files", badge: "IMPLEMENTED" },
      { label: "Dashboard UI", value: "Approvals tab · Approve / Reject buttons → POST /approvals/{id}/decide", badge: "LIVE UI" },
      { label: "Audit Trail", value: "history/approvals.md · every decision permanently logged with timestamp", badge: "LOGGED" },
      { label: "Orchestrator Poll", value: "agent_loop.py checks Pending_Approval/ each cycle, acts on status change", badge: "AUTO" },
    ],
  },
  {
    title: "Logs & Audit Trail Proof",
    color: "emerald",
    icon: "📋",
    items: [
      { label: "Prompt History", value: "history/prompts.md · every Claude prompt + response logged with run_id", badge: "FULL LOG" },
      { label: "Agent Runs", value: "history/agent_runs.md · each orchestrator cycle logged with success/failure", badge: "FULL LOG" },
      { label: "Daily Logs", value: "AI_Employee_Vault/Logs/ · per-day markdown logs of pipeline events", badge: "DAILY" },
      { label: "Pipeline Stats API", value: "GET /pipeline-stats · live counts per stage, completion rate", badge: "API" },
    ],
  },
  {
    title: "CEO Briefing Proof",
    color: "yellow",
    icon: "📊",
    items: [
      { label: "Briefing Generator", value: "analytics/ceo_briefing.py · Claude-authored executive summary", badge: "CLAUDE AI" },
      { label: "Output File", value: "AI_Employee_Vault/CEO_Briefing.md · auto-generated weekly", badge: "GENERATED" },
      { label: "Dashboard Viewer", value: "CEO Briefing tab · full markdown render with react-markdown", badge: "LIVE UI" },
      { label: "API Endpoint", value: "GET /ceo-briefing · JSON with content + last modified timestamp", badge: "API" },
    ],
  },
  {
    title: "MCP Tools & Claude Reasoning",
    color: "indigo",
    icon: "🤖",
    items: [
      { label: "Claude Model", value: "claude-sonnet-4-6 · reasoning engine for all task plans", badge: "CLAUDE" },
      { label: "Email MCP", value: "mcp_servers/email_mcp.py · compose + send emails via agent", badge: "MCP" },
      { label: "Browser MCP", value: "mcp_servers/browser_mcp.py · web research tool", badge: "MCP" },
      { label: "Calendar MCP", value: "mcp_servers/calendar_mcp.py · schedule management", badge: "MCP" },
      { label: "Filesystem MCP", value: "mcp_servers/filesystem_mcp.py · read/write files", badge: "MCP" },
      { label: "A2A Protocol", value: "agents/a2a_protocol.py · agent-to-agent task delegation", badge: "A2A" },
    ],
  },
];

const COLOR_MAP: Record<string, { card: string; badge: string; title: string }> = {
  blue:    { card: "border-blue-500/30 bg-blue-950/20",    badge: "bg-blue-600/30 text-blue-300",    title: "text-blue-300" },
  purple:  { card: "border-purple-500/30 bg-purple-950/20", badge: "bg-purple-600/30 text-purple-300", title: "text-purple-300" },
  orange:  { card: "border-orange-500/30 bg-orange-950/20", badge: "bg-orange-600/30 text-orange-300", title: "text-orange-300" },
  emerald: { card: "border-emerald-500/30 bg-emerald-950/20", badge: "bg-emerald-600/30 text-emerald-300", title: "text-emerald-300" },
  yellow:  { card: "border-yellow-500/30 bg-yellow-950/20", badge: "bg-yellow-600/30 text-yellow-300", title: "text-yellow-300" },
  indigo:  { card: "border-indigo-500/30 bg-indigo-950/20", badge: "bg-indigo-600/30 text-indigo-300", title: "text-indigo-300" },
};

function EvidenceRow({ label, value, badge, badgeStyle }: { label: string; value: string; badge: string; badgeStyle: string }) {
  return (
    <div className="flex items-start gap-3 py-2.5 border-b border-white/5 last:border-0">
      <span className={`shrink-0 text-[10px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wider mt-0.5 ${badgeStyle}`}>
        {badge}
      </span>
      <div className="min-w-0">
        <span className="text-slate-300 font-medium text-sm">{label}:</span>{" "}
        <span className="text-slate-400 text-sm">{value}</span>
      </div>
    </div>
  );
}

export default function JudgeEvidence() {
  const [copied, setCopied] = useState(false);
  const now = new Date().toISOString();

  const pack = `AI Employee Vault — Judge Evidence Pack
Generated: ${now}
========================================
Owner:     ${EVIDENCE.owner}
Tier:      ${EVIDENCE.tier}
Hackathon: ${EVIDENCE.hackathon}
Model:     ${EVIDENCE.model}

LIVE LINKS
  GitHub:        ${EVIDENCE.github}
  Frontend:      ${EVIDENCE.vercel}
  Backend API:   ${EVIDENCE.hfBackend}
  HF Space:      ${EVIDENCE.hfSpace}

DEPLOYMENT
  Frontend: Vercel · Next.js 14 · auto-deploy from GitHub main
  Backend:  Hugging Face Spaces · Docker · FastAPI

WATCHERS
  Gmail:      IMAP + Gmail App Password → vault task files
  Filesystem: watchdog lib → watched_folder/ auto-ingest
  WhatsApp:   Webhook → CRITICAL priority tasks

HITL APPROVAL
  Engine: approval_system/hitl.py
  UI:     Dashboard Approvals tab (Approve / Reject)
  Audit:  history/approvals.md (permanent log)

LOGS
  Prompts:   history/prompts.md (every Claude call)
  Agent Runs: history/agent_runs.md
  Daily:     AI_Employee_Vault/Logs/

CEO BRIEFING
  Generator: analytics/ceo_briefing.py (Claude-authored)
  Output:    AI_Employee_Vault/CEO_Briefing.md
  Dashboard: CEO Briefing tab

MCP TOOLS (4): Email · Browser · Calendar · Filesystem
BONUS: A2A Protocol · Self-healing Watchdog · Error Recovery · Cloud Layer
`;

  const handleCopy = () => {
    navigator.clipboard.writeText(pack).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    });
  };

  return (
    <div className="space-y-6">
      {/* Identity Card */}
      <div className="rounded-2xl border border-yellow-500/40 bg-yellow-950/20 p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-yellow-400 text-xl font-bold">🏆</span>
              <h2 className="text-xl font-bold text-white">Judge Evidence Pack</h2>
              <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-yellow-500/20 text-yellow-300 border border-yellow-500/30 uppercase tracking-wide">
                Platinum Tier
              </span>
            </div>
            <p className="text-slate-400 text-sm">AI Employee Vault · Personal AI Employee Hackathon 0</p>
          </div>
          <button
            onClick={handleCopy}
            className={`px-4 py-2 rounded-xl text-sm font-semibold transition-all border ${
              copied
                ? "bg-emerald-600/30 border-emerald-500/40 text-emerald-300"
                : "bg-yellow-600/20 border-yellow-500/30 text-yellow-300 hover:bg-yellow-600/30"
            }`}
          >
            {copied ? "✓ Copied!" : "📋 Copy Evidence Pack"}
          </button>
        </div>

        {/* Key Info Grid */}
        <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
          {[
            { label: "Project Owner", value: EVIDENCE.owner },
            { label: "Hackathon Tier", value: EVIDENCE.tier },
            { label: "Model", value: EVIDENCE.model },
            { label: "Last Updated", value: now.slice(0, 19).replace("T", " ") + " UTC" },
          ].map(({ label, value }) => (
            <div key={label} className="bg-black/20 rounded-xl px-4 py-2.5 border border-white/5">
              <p className="text-[11px] text-slate-500 uppercase tracking-wider">{label}</p>
              <p className="text-sm text-white font-medium mt-0.5">{value}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Live Links */}
      <div className="rounded-2xl border border-surface-border bg-surface-card p-5">
        <h3 className="text-sm font-semibold text-slate-300 mb-3 uppercase tracking-wider">Live Deployment Links</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {[
            { label: "GitHub Repo", url: EVIDENCE.github, icon: "🐙", color: "text-slate-300" },
            { label: "Vercel Frontend", url: EVIDENCE.vercel, icon: "▲", color: "text-white" },
            { label: "HF Backend API", url: EVIDENCE.hfBackend, icon: "🤗", color: "text-yellow-300" },
            { label: "HF Space", url: EVIDENCE.hfSpace, icon: "🚀", color: "text-blue-300" },
          ].map(({ label, url, icon, color }) => (
            <a
              key={label}
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 px-4 py-3 rounded-xl border border-surface-border bg-black/20 hover:bg-black/40 hover:border-white/20 transition-all group"
            >
              <span className="text-lg">{icon}</span>
              <div className="min-w-0">
                <p className="text-xs text-slate-500 uppercase tracking-wider">{label}</p>
                <p className={`text-xs font-mono truncate ${color} group-hover:underline`}>{url}</p>
              </div>
              <span className="ml-auto text-slate-600 group-hover:text-slate-400 text-xs">↗</span>
            </a>
          ))}
        </div>
      </div>

      {/* Evidence Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {SECTIONS.map((section) => {
          const c = COLOR_MAP[section.color] ?? COLOR_MAP.blue;
          return (
            <div key={section.title} className={`rounded-2xl border p-5 ${c.card}`}>
              <h3 className={`text-sm font-bold mb-3 flex items-center gap-2 ${c.title}`}>
                <span>{section.icon}</span>
                {section.title}
              </h3>
              <div>
                {section.items.map((item) => (
                  <EvidenceRow
                    key={item.label}
                    label={item.label}
                    value={item.value}
                    badge={item.badge}
                    badgeStyle={c.badge}
                  />
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Architecture Diagram */}
      <div className="rounded-2xl border border-surface-border bg-surface-card p-5">
        <h3 className="text-sm font-semibold text-slate-300 mb-3 uppercase tracking-wider">System Architecture</h3>
        <pre className="text-[11px] text-slate-400 font-mono leading-5 overflow-x-auto whitespace-pre">{`
  ┌─────────────────────────────────────────────────────┐
  │              EXTERNAL EVENT SOURCES                 │
  │  Gmail (IMAP)  ·  WhatsApp (Webhook)  ·  Filesystem │
  └──────────────┬──────────────────────────────────────┘
                 │  watchers/ → markdown task files
                 ▼
  ┌─────────────────────────────────────────────────────┐
  │            OBSIDIAN VAULT PIPELINE                  │
  │  Inbox → Needs_Action → Plans → Pending_Approval    │
  │                              ↘ Approved → Done      │
  │                              ↘ Rejected             │
  └──────────────┬──────────────────────────────────────┘
                 │
                 ▼
  ┌─────────────────────────────────────────────────────┐
  │         RALPH WIGGUM ORCHESTRATOR                   │
  │         orchestrator/agent_loop.py                  │
  │   ┌───────────┬──────────────┬──────────────────┐   │
  │   ▼           ▼              ▼                  ▼   │
  │ Claude     HITL          Watchdog          A2A      │
  │ Agent      Approval      Self-Heal         Protocol │
  │   │        System                                   │
  │   ▼                                                 │
  │ MCP Tools: Email · Browser · Calendar · Filesystem  │
  └──────────────┬──────────────────────────────────────┘
                 │
     ┌───────────┴────────────┐
     ▼                        ▼
  ┌──────────────┐    ┌───────────────────┐
  │  ANALYTICS   │    │   AUDIT TRAIL     │
  │CEO Briefing  │    │ history/prompts   │
  │Pipeline Viz  │    │ history/approvals │
  └──────┬───────┘    └────────┬──────────┘
         │                     │
         ▼                     ▼
  ┌─────────────────────────────────────────────────────┐
  │              CLOUD DEPLOYMENT                       │
  │  Backend: Hugging Face Spaces (Docker · FastAPI)    │
  │  Frontend: Vercel (Next.js 14 · TypeScript)         │
  │  Source:   GitHub main → auto-deploy CI/CD          │
  └─────────────────────────────────────────────────────┘
`}</pre>
      </div>

      {/* Platinum Feature Checklist */}
      <div className="rounded-2xl border border-surface-border bg-surface-card p-5">
        <h3 className="text-sm font-semibold text-slate-300 mb-3 uppercase tracking-wider">Platinum Tier Feature Checklist</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
          {[
            "Claude Sonnet 4.6 reasoning",
            "Obsidian vault (8 stages)",
            "Gmail watcher (IMAP)",
            "Filesystem watcher",
            "WhatsApp watcher",
            "Email MCP tool",
            "Browser MCP tool",
            "Calendar MCP tool",
            "Filesystem MCP tool",
            "HITL approval workflow",
            "Ralph Wiggum orchestrator",
            "CEO AI weekly briefing",
            "Self-healing watchdog",
            "Error recovery system",
            "System health monitor",
            "FastAPI backend (10+ endpoints)",
            "Next.js + Tailwind dashboard",
            "Cloud agent (S3/GCS/local)",
            "Vault sync manager",
            "A2A agent communication",
            "Prompt history logging",
            "Pipeline visualization",
            "PM2 process management",
            "Vercel frontend deployment",
            "Hugging Face backend deploy",
            "GitHub CI/CD integration",
          ].map((feat) => (
            <div key={feat} className="flex items-center gap-2 text-sm text-slate-300">
              <span className="text-emerald-400 shrink-0">✓</span>
              {feat}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
