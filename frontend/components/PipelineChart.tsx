import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell,
} from "recharts";

const COLORS = ["#3b82f6","#f59e0b","#a855f7","#f97316","#22c55e","#ef4444","#10b981"];
const LABELS: Record<string, string> = {
  inbox:            "Inbox",
  needs_action:     "In Progress",
  plans:            "Plans",
  pending_approval: "Pending",
  approved:         "Approved",
  rejected:         "Rejected",
  done:             "Done",
};

interface Props {
  pipeline: { counts?: Record<string, number>; completion_rate?: number } | null;
  loading: boolean;
}

export default function PipelineChart({ pipeline, loading }: Props) {
  const data = pipeline?.counts
    ? Object.entries(pipeline.counts).map(([key, value], i) => ({
        name:  LABELS[key] || key,
        value,
        color: COLORS[i % COLORS.length],
      }))
    : [];

  return (
    <div className="card animate-fade-in">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-white">Pipeline Distribution</h2>
        {pipeline && (
          <span className="badge bg-emerald-900/40 text-emerald-300 border border-emerald-800/50">
            {pipeline.completion_rate}% completion
          </span>
        )}
      </div>

      {loading ? (
        <div className="h-48 flex items-center justify-center text-slate-500 text-sm">Loading…</div>
      ) : (
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={data} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2a40" />
            <XAxis dataKey="name" tick={{ fill: "#64748b", fontSize: 10 }} />
            <YAxis tick={{ fill: "#64748b", fontSize: 10 }} />
            <Tooltip
              contentStyle={{ background: "#161625", border: "1px solid #2a2a40", borderRadius: 8, fontSize: 12 }}
              labelStyle={{ color: "#e2e8f0" }}
              cursor={{ fill: "#1e1e30" }}
            />
            <Bar dataKey="value" radius={[4, 4, 0, 0]}>
              {data.map((entry, i) => (
                <Cell key={i} fill={entry.color} fillOpacity={0.85} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
