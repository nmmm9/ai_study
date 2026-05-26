export type AgentNode =
  | "supervisor"
  | "planner"
  | "executor"
  | "replanner"
  | "shopping"
  | "lifestyle"
  | "sports"
  | "news"
  | "finance"
  | "government"
  | "education"
  | "info"
  | "documents"
  | "writer"
  | "critic";

export type NodeStatus = "idle" | "active" | "done";

export type StepStatus = "pending" | "active" | "done" | "skipped";

export type ReplanAction = "continue" | "revise" | "finish";

export interface PlanStep {
  id: number;
  domain: string | null;
  task: string;
  status?: StepStatus;
  tool_count?: number;
  results_summary?: string;
}

export interface ReplanRecord {
  step_id: number;
  action: ReplanAction;
  reasoning: string;
  new_plan?: PlanStep[];
}

export interface AgentEvent {
  type:
    | "node_start"
    | "node_end"
    | "edge"
    | "plan_created"
    | "step_start"
    | "step_done"
    | "replan_decision"
    | "tool_call"
    | "tool_result"
    | "token"
    | "writer_iteration"
    | "revision_start"
    | "critic_score"
    | "retrieval_round"
    | "retrieval_result"
    | "retrieval_eval"
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

export interface RetrievedChunk {
  doc_name: string;
  page: number | null;
  score: number;
  text_snippet?: string;
  text?: string;
}

export interface RetrievalRound {
  round: number;
  query: string;
  chunks: RetrievedChunk[];
  score: number;
  reasoning: string;
  alternative_query?: string;
}

export interface DocumentInfo {
  doc_id: string;
  doc_name: string;
  chunks: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  traces?: AgentTrace[];
  plan?: PlanStep[];
  planReasoning?: string;
  replans?: ReplanRecord[];
  reasoning?: string;
  isStreaming?: boolean;
  critiques?: CriticReport[];
  iterations?: number;
  finalScore?: number;
  retrievalRounds?: RetrievalRound[];
}

export interface GraphMeta {
  nodes: { id: string; label: string; type: string; desc: string }[];
  edges: { from: string; to: string; loop?: boolean }[];
  config?: { pass_threshold: number; max_revisions: number; max_replan?: number };
}
