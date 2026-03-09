export interface Task {
  id: string;
  filename: string;
  stage: string;
  title: string;
  source: string;
  priority: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  status: string;
  created_at: string;
  preview?: string;
  full_content?: string;
}

export interface SystemStatus {
  status: string;
  timestamp: string;
  pipeline: Record<string, number>;
  vault_exists: boolean;
  history_exists: boolean;
  briefing_exists: boolean;
}

export interface PipelineStats {
  counts: Record<string, number>;
  total: number;
  completion_rate: number;
  timestamp: string;
}

export interface PendingApproval {
  filename: string;
  approval_id: string;
  task_id: string;
  requested_at: string;
  preview: string;
}

export interface LogEntry {
  date: string;
  raw: string;
  content: string;
}

export interface CeoBriefing {
  exists: boolean;
  content: string | null;
  size: number;
  modified: string;
  message?: string;
}

export type PriorityColor = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
export type StageColor    = "blue" | "yellow" | "purple" | "orange" | "green" | "red" | "emerald";
