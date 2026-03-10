import axios from "axios";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "https://ismat110-ai-employee-vault-ismat-platinum.hf.space";

const client = axios.create({ baseURL: BASE_URL, timeout: 10_000 });

export const api = {
  getSystemStatus:    () => client.get("/system-status").then(r => r.data),
  getPipelineStats:   () => client.get("/pipeline-stats").then(r => r.data),
  getTasks:           (params?: Record<string, string>) =>
                        client.get("/tasks", { params }).then(r => r.data),
  getTask:            (id: string) => client.get(`/tasks/${id}`).then(r => r.data),
  getLogs:            (limit = 50) => client.get("/logs", { params: { limit } }).then(r => r.data),
  getPendingApprovals:() => client.get("/approvals/pending").then(r => r.data),
  getApprovals:       () => client.get("/approvals").then(r => r.data),
  decideApproval:     (filename: string, decision: string, reason?: string) =>
                        client.post(`/approvals/${filename}/decide`, { decision, reason }).then(r => r.data),
  getCeoBriefing:     () => client.get("/ceo-briefing").then(r => r.data),
  getAnalytics:       () => client.get("/analytics").then(r => r.data),
  injectTask:         (title: string, body: string, source = "dashboard", priority = "MEDIUM") =>
                        client.post("/tasks/inject", { title, body, source, priority }).then(r => r.data),
  getPromptHistory:   (limit = 10) => client.get("/prompt-history", { params: { limit } }).then(r => r.data),
};
