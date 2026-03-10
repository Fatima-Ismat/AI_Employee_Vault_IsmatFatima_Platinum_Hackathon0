import { useEffect, useState } from "react";
import Head from "next/head";
import Layout from "../components/Layout";
import StatusCard from "../components/StatusCard";
import PipelineBoard from "../components/PipelineBoard";
import TaskList from "../components/TaskList";
import ApprovalQueue from "../components/ApprovalQueue";
import LogViewer from "../components/LogViewer";
import CeoBriefing from "../components/CeoBriefing";
import PipelineChart from "../components/PipelineChart";
import JudgeEvidence from "../components/JudgeEvidence";
import { api } from "../lib/api";
import type { SystemStatus, PipelineStats } from "../lib/types";

export default function Dashboard() {
  const [status, setStatus]     = useState<SystemStatus | null>(null);
  const [pipeline, setPipeline] = useState<PipelineStats | null>(null);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState<string | null>(null);
  const [tab, setTab]           = useState<"overview" | "tasks" | "approvals" | "logs" | "briefing" | "evidence">("overview");

  const refresh = async () => {
    try {
      const [statusData, pipelineData] = await Promise.all([
        api.getSystemStatus(),
        api.getPipelineStats(),
      ]);
      setStatus(statusData);
      setPipeline(pipelineData);
      setError(null);
    } catch (e: any) {
      setError(e.message || "Failed to connect to backend API");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 15_000);
    return () => clearInterval(interval);
  }, []);

  const counts = status?.pipeline ?? {};

  return (
    <>
      <Head>
        <title>AI Employee Vault — Dashboard</title>
        <meta name="description" content="Platinum AI Employee Dashboard" />
      </Head>

      <Layout>
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">
              AI Employee Vault
            </h1>
            <p className="text-sm text-slate-400 mt-0.5">
              IsmatFatima · Platinum Tier · Personal AI Employee Hackathon 0
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-xs text-slate-400 bg-surface-card border border-surface-border rounded-lg px-3 py-1.5">
              <span className={`pulse-dot ${error ? "bg-red-500 glow-red" : "bg-emerald-400 glow-green"}`} />
              {error ? "Disconnected" : "Live"}
            </div>
            <button
              onClick={refresh}
              className="text-xs px-3 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-white transition-colors"
            >
              Refresh
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-950/50 border border-red-800 rounded-xl text-red-300 text-sm">
            <strong>Backend Unreachable:</strong> {error}
            <br />
            <span className="text-red-400/70">Start the API: <code className="font-mono">uvicorn backend.main:app --reload --port 8000</code></span>
          </div>
        )}

        {/* Status Cards Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3 mb-8">
          {[
            { label: "Inbox",            key: "inbox",            color: "blue" },
            { label: "In Progress",      key: "needs_action",     color: "yellow" },
            { label: "Plans",            key: "plans",            color: "purple" },
            { label: "Pending Approval", key: "pending_approval", color: "orange" },
            { label: "Approved",         key: "approved",         color: "green" },
            { label: "Rejected",         key: "rejected",         color: "red" },
            { label: "Done",             key: "done",             color: "emerald" },
          ].map(({ label, key, color }) => (
            <StatusCard
              key={key}
              label={label}
              value={loading ? "…" : String(counts[key as keyof typeof counts] ?? 0)}
              color={color as any}
            />
          ))}
        </div>

        {/* Tab navigation */}
        <div className="flex gap-1 mb-6 bg-surface-card border border-surface-border rounded-xl p-1 w-fit">
          {(["overview", "tasks", "approvals", "logs", "briefing", "evidence"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium capitalize transition-all ${
                tab === t
                  ? t === "evidence"
                    ? "bg-yellow-600 text-white shadow"
                    : "bg-brand-600 text-white shadow"
                  : t === "evidence"
                    ? "text-yellow-400 hover:text-yellow-200 hover:bg-yellow-900/30 border border-yellow-700/40"
                    : "text-slate-400 hover:text-slate-200 hover:bg-surface-hover"
              }`}
            >
              {t === "briefing" ? "CEO Briefing" : t === "evidence" ? "🏆 Judge Evidence" : t}
            </button>
          ))}
        </div>

        {/* Tab content */}
        {tab === "overview" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <PipelineChart pipeline={pipeline} loading={loading} />
            <PipelineBoard counts={counts} loading={loading} />
          </div>
        )}
        {tab === "tasks"     && <TaskList />}
        {tab === "approvals" && <ApprovalQueue onRefresh={refresh} />}
        {tab === "logs"      && <LogViewer />}
        {tab === "briefing"  && <CeoBriefing />}
        {tab === "evidence"  && <JudgeEvidence />}
      </Layout>
    </>
  );
}
