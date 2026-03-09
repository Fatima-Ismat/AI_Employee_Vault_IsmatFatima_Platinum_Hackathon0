import { ArrowRight } from "lucide-react";

const STAGES = [
  { key: "inbox",            label: "Inbox",     color: "text-blue-400"   },
  { key: "needs_action",     label: "Working",   color: "text-yellow-400" },
  { key: "pending_approval", label: "Approval",  color: "text-orange-400" },
  { key: "done",             label: "Done",      color: "text-emerald-400"},
];

interface Props {
  counts: Record<string, number>;
  loading: boolean;
}

export default function PipelineBoard({ counts, loading }: Props) {
  return (
    <div className="card animate-fade-in">
      <h2 className="text-sm font-semibold text-white mb-5">Task Pipeline Flow</h2>

      {loading ? (
        <div className="h-48 flex items-center justify-center text-slate-500 text-sm">Loading…</div>
      ) : (
        <div className="flex items-center justify-between gap-2 mt-4">
          {STAGES.map((stage, i) => (
            <div key={stage.key} className="flex items-center gap-2 flex-1">
              <div className="flex-1 bg-surface-hover border border-surface-border rounded-xl p-4 text-center">
                <div className={`text-2xl font-bold font-mono ${stage.color}`}>
                  {counts[stage.key] ?? 0}
                </div>
                <div className="text-xs text-slate-500 mt-1">{stage.label}</div>
              </div>
              {i < STAGES.length - 1 && (
                <ArrowRight size={14} className="text-slate-600 flex-shrink-0" />
              )}
            </div>
          ))}
        </div>
      )}

      <div className="mt-5 pt-4 border-t border-surface-border">
        <div className="flex justify-between text-xs text-slate-500">
          <span>Rejected: <span className="text-red-400 font-mono">{counts["rejected"] ?? 0}</span></span>
          <span>Approved: <span className="text-green-400 font-mono">{counts["approved"] ?? 0}</span></span>
          <span>Total: <span className="text-white font-mono">
            {Object.values(counts).reduce((a, b) => a + b, 0)}
          </span></span>
        </div>
      </div>
    </div>
  );
}
