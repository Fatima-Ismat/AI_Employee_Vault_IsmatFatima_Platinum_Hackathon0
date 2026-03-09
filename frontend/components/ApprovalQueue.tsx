import { useEffect, useState } from "react";
import { CheckCircle, XCircle, Clock, AlertTriangle } from "lucide-react";
import { api } from "../lib/api";
import type { PendingApproval } from "../lib/types";

interface Props {
  onRefresh?: () => void;
}

export default function ApprovalQueue({ onRefresh }: Props) {
  const [pending, setPending]   = useState<PendingApproval[]>([]);
  const [loading, setLoading]   = useState(true);
  const [deciding, setDeciding] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const data = await api.getPendingApprovals();
      setPending(data.pending);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const decide = async (filename: string, decision: "approved" | "rejected") => {
    setDeciding(filename);
    try {
      await api.decideApproval(filename, decision);
      await load();
      onRefresh?.();
    } catch (e) {
      alert("Failed to submit decision. Check the backend API.");
    } finally {
      setDeciding(null);
    }
  };

  return (
    <div className="animate-fade-in">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <AlertTriangle size={14} className="text-orange-400" />
          Pending Approvals
          {pending.length > 0 && (
            <span className="badge bg-orange-900/50 text-orange-300 border border-orange-800">
              {pending.length}
            </span>
          )}
        </h2>
        <button
          onClick={load}
          className="text-xs text-slate-400 hover:text-white transition-colors"
        >
          Refresh
        </button>
      </div>

      {loading && (
        <div className="card text-slate-500 text-sm text-center py-8">Loading…</div>
      )}

      {!loading && pending.length === 0 && (
        <div className="card text-center py-12">
          <CheckCircle size={32} className="text-emerald-500 mx-auto mb-3" />
          <p className="text-slate-400 text-sm">No pending approvals.</p>
          <p className="text-slate-600 text-xs mt-1">All tasks are moving through the pipeline.</p>
        </div>
      )}

      <div className="space-y-4">
        {pending.map(item => (
          <div
            key={item.filename}
            className="card border-orange-900/50 animate-slide-up"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-2">
                  <Clock size={12} className="text-orange-400" />
                  <span className="text-xs text-orange-300 font-medium">Awaiting Human Decision</span>
                </div>
                <p className="text-sm font-medium text-white mb-1">
                  Task: <code className="text-brand-300 font-mono text-xs">{item.task_id}</code>
                </p>
                <p className="text-xs text-slate-500 mb-3">
                  Requested: {item.requested_at}
                </p>
                <pre className="text-xs text-slate-400 bg-surface-hover rounded-lg p-3 overflow-x-auto max-h-32 font-mono leading-relaxed">
                  {item.preview.slice(0, 400)}…
                </pre>
              </div>
            </div>

            <div className="flex gap-3 mt-4 pt-4 border-t border-surface-border">
              <button
                onClick={() => decide(item.filename, "approved")}
                disabled={!!deciding}
                className="flex-1 flex items-center justify-center gap-2 py-2 rounded-lg bg-emerald-900/50 hover:bg-emerald-800/60 border border-emerald-800 text-emerald-300 text-sm font-medium transition-all disabled:opacity-50"
              >
                <CheckCircle size={14} />
                {deciding === item.filename ? "Processing…" : "Approve"}
              </button>
              <button
                onClick={() => decide(item.filename, "rejected")}
                disabled={!!deciding}
                className="flex-1 flex items-center justify-center gap-2 py-2 rounded-lg bg-red-900/50 hover:bg-red-800/60 border border-red-800 text-red-300 text-sm font-medium transition-all disabled:opacity-50"
              >
                <XCircle size={14} />
                Reject
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
