import { useEffect, useState } from "react";
import { Terminal, RefreshCw } from "lucide-react";
import { api } from "../lib/api";

const LEVEL_COLOR: Record<string, string> = {
  ERROR:    "text-red-400",
  WARNING:  "text-yellow-400",
  INFO:     "text-blue-400",
  DEBUG:    "text-slate-500",
  RECOVERY: "text-emerald-400",
  CRITICAL: "text-red-300",
};

function parseLevel(line: string): string {
  for (const level of Object.keys(LEVEL_COLOR)) {
    if (line.includes(level)) return level;
  }
  return "INFO";
}

export default function LogViewer() {
  const [logs,    setLogs]    = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter,  setFilter]  = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const data = await api.getLogs(100);
      setLogs(data.logs.map((l: any) => l.raw || l.content || ""));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const filtered = filter
    ? logs.filter(l => l.toLowerCase().includes(filter.toLowerCase()))
    : logs;

  return (
    <div className="animate-fade-in">
      <div className="flex items-center justify-between mb-4 gap-3">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <Terminal size={14} className="text-slate-400" />
          System Logs
        </h2>
        <div className="flex items-center gap-2 flex-1 max-w-sm">
          <input
            type="text"
            placeholder="Filter logs…"
            value={filter}
            onChange={e => setFilter(e.target.value)}
            className="flex-1 bg-surface-card border border-surface-border rounded-lg px-3 py-1.5 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-brand-700"
          />
          <button
            onClick={load}
            className="p-1.5 rounded-lg bg-surface-card border border-surface-border text-slate-400 hover:text-white transition-colors"
          >
            <RefreshCw size={13} />
          </button>
        </div>
      </div>

      <div className="card bg-[#0a0a12] font-mono text-xs h-[500px] overflow-y-auto">
        {loading && (
          <div className="text-slate-500 text-center py-8">Loading logs…</div>
        )}
        {!loading && filtered.length === 0 && (
          <div className="text-slate-600 text-center py-8">No log entries found.</div>
        )}
        <div className="space-y-0.5">
          {filtered.slice().reverse().map((line, i) => {
            const level = parseLevel(line);
            const color = LEVEL_COLOR[level] || "text-slate-400";
            return (
              <div key={i} className="flex gap-2 px-2 py-0.5 hover:bg-surface-hover rounded leading-5">
                <span className={`${color} shrink-0`}>[{level}]</span>
                <span className="text-slate-300 break-all">{line.replace(/^-\s+/, "")}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
