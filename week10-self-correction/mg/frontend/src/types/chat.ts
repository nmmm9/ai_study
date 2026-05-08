export type AgentNode =
  | "supervisor"
  | "shopping"
  | "lifestyle"
  | "sports"
  | "news"
  | "finance"
  | "government"
  | "education"
  | "info"
  | "writer"
  | "critic";

export type NodeStatus = "idle" | "active" | "done";

export interface AgentEvent {
  type:
    | "node_start"
    | "node_end"
    | "edge"
    | "supervisor_decision"
    | "tool_call"
    | "tool_result"
    | "token"
    | "writer_iteration"
    | "revision_start"
    | "critic_score"
    | "done";
  data: Record<string, unknown>;
}

export interface ToolTrace {
  domain: string;
  tool: string;
  args?: Record<string, unknown>;
  result?: string;
}

export interface AgentTrace {
  node: AgentNode;
  status: NodeStatus;
  startedAt?: number;
  endedAt?: number;
  summary?: string;
  tools: ToolTrace[];
}

export interface CriticReport {
  score: number;
  passed: boolean;
  issues: string[];
  suggestions: string[];
  iteration: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  traces?: AgentTrace[];
  plan?: string[];
  reasoning?: string;
  isStreaming?: boolean;
  critiques?: CriticReport[];
  iterations?: number;
  finalScore?: number;
}

export interface GraphMeta {
  nodes: { id: string; label: string; type: string; desc: string }[];
  edges: { from: string; to: string; loop?: boolean }[];
  config?: { pass_threshold: number; max_revisions: number };
}
