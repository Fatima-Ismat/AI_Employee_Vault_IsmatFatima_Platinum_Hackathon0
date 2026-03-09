import { useEffect, useState } from "react";
import { Inbox, Clock, CheckCircle, XCircle, AlertCircle } from "lucide-react";
import { api } from "../lib/api";
import type { Task } from "../lib/types";

const PRIORITY_STYLES: Record<string, string> = {
  CRITICAL: "bg-red-900/50 text-red-300 border-red-800",
  HIGH:     "bg-orange-900/50 text-orange-300 border-orange-800",
  MEDIUM:   "bg-blue-900/50 text-blue-300 border-blue-800",
  LOW:      "bg-slate-800 text-slate-400 border-slate-700",
};

const STAGE_ICON: Record<string, JSX.Element> = {
  inbox:            <Inbox size={12} />,
  needs_action:     <Clock size={12} />,
  done:             <CheckCircle size={12} />,
  rejected:         <XCircle size={12} />,
  pending_approval: <AlertCircle size={12} />,
};

export default function TaskList() {
  const [tasks,    setTasks]    = useState<Task[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [filter,   setFilter]   = useState<string>("all");
  const [selected, setSelected] = useState<Task | null>(null);

  const STAGES = ["all","inbox","needs_action","pending_approval","approved","rejected","done"];

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const params = filter !== "all" ? { stage: filter } : undefined;
        const data = await api.getTasks(params);
        setTasks(data.tasks);
      } finally {
        setLoading(false);
      }
    })();
  }, [filter]);

  return (
    <div className="animate-fade-in">
      {/* Filter tabs */}
      <div className="flex gap-1 mb-4 flex-wrap">
        {STAGES.map(s => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            className={`px-3 py-1 rounded-lg text-xs font-medium capitalize transition-all ${
              filter === s
                ? "bg-brand-600 text-white"
                : "bg-surface-card border border-surface-border text-slate-400 hover:text-slate-200"
            }`}
          >
            {s.replace("_", " ")}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Task list */}
        <div className="space-y-2">
          {loading && (
            <div className="card text-slate-500 text-sm text-center py-8">Loading tasks…</div>
          )}
          {!loading && tasks.length === 0 && (
            <div className="card text-slate-500 text-sm text-center py-8">No tasks in this stage.</div>
          )}
          {!loading && tasks.map(task => (
            <div
              key={task.id}
              onClick={() => setSelected(task)}
              className={`card cursor-pointer transition-all hover:border-brand-700 ${
                selected?.id === task.id ? "border-brand-600 glow-brand" : ""
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">{task.title}</p>
                  <div className="flex items-center gap-2 mt-1.5">
                    <span className={`badge border ${PRIORITY_STYLES[task.priority] || PRIORITY_STYLES.MEDIUM}`}>
                      {task.priority}
                    </span>
                    <span className="flex items-center gap-1 text-xs text-slate-500">
                      {STAGE_ICON[task.stage] ?? null}
                      {task.stage.replace("_", " ")}
                    </span>
                    <span className="text-xs text-slate-600">{task.source}</span>
                  </div>
                </div>
                <span className="text-xs text-slate-600 whitespace-nowrap">
                  {task.created_at?.split(" ")[0] || ""}
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Task detail */}
        <div className="card h-fit max-h-[600px] overflow-y-auto">
          {selected ? (
            <>
              <h3 className="text-sm font-semibold text-white mb-3">{selected.title}</h3>
              <div className="flex gap-2 mb-4 flex-wrap">
                <span className={`badge border ${PRIORITY_STYLES[selected.priority]}`}>{selected.priority}</span>
                <span className="badge bg-surface-hover border-surface-border text-slate-400">{selected.stage}</span>
                <span className="badge bg-surface-hover border-surface-border text-slate-400">{selected.source}</span>
              </div>
              <pre className="text-xs text-slate-300 whitespace-pre-wrap font-mono leading-relaxed">
                {selected.preview || "No preview available"}
              </pre>
            </>
          ) : (
            <div className="text-slate-500 text-sm text-center py-12">
              Select a task to view details
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
