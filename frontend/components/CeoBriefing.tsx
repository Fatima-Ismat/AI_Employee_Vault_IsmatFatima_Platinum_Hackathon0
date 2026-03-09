import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { FileText, RefreshCw, AlertCircle } from "lucide-react";
import { api } from "../lib/api";
import type { CeoBriefing } from "../lib/types";

export default function CeoBriefingView() {
  const [briefing, setBriefing] = useState<CeoBriefing | null>(null);
  const [loading,  setLoading]  = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const data = await api.getCeoBriefing();
      setBriefing(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="animate-fade-in">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <FileText size={14} className="text-brand-400" />
          CEO AI Weekly Briefing
        </h2>
        <button
          onClick={load}
          className="p-1.5 rounded-lg bg-surface-card border border-surface-border text-slate-400 hover:text-white transition-colors"
        >
          <RefreshCw size={13} />
        </button>
      </div>

      {loading && (
        <div className="card text-slate-500 text-sm text-center py-12">Loading briefing…</div>
      )}

      {!loading && (!briefing?.exists) && (
        <div className="card text-center py-12">
          <AlertCircle size={32} className="text-orange-400 mx-auto mb-3" />
          <p className="text-slate-300 text-sm font-medium">No briefing generated yet</p>
          <p className="text-slate-500 text-xs mt-2">
            {briefing?.message || "Run: python -m analytics.ceo_briefing"}
          </p>
          <code className="mt-3 inline-block text-xs bg-surface-hover border border-surface-border rounded px-3 py-1.5 text-brand-300">
            python -m analytics.ceo_briefing
          </code>
        </div>
      )}

      {!loading && briefing?.exists && briefing.content && (
        <div className="card max-h-[680px] overflow-y-auto">
          <div className="flex items-center gap-3 mb-4 pb-4 border-b border-surface-border">
            <div className="text-xs text-slate-500">
              Last updated: {briefing.modified ? new Date(briefing.modified).toLocaleString() : "Unknown"}
            </div>
            <span className="badge bg-brand-900/40 text-brand-300 border border-brand-800">
              {Math.round(briefing.size / 1024)}KB
            </span>
          </div>
          <div className="prose prose-invert prose-sm max-w-none
            prose-headings:text-white prose-headings:font-semibold
            prose-p:text-slate-300 prose-p:leading-relaxed
            prose-strong:text-white prose-strong:font-semibold
            prose-code:text-brand-300 prose-code:bg-surface-hover prose-code:px-1 prose-code:rounded
            prose-li:text-slate-300
            prose-table:text-sm prose-th:text-slate-400 prose-td:text-slate-300
            prose-hr:border-surface-border
          ">
            <ReactMarkdown>{briefing.content}</ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}
