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
  | "writer";

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

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  traces?: AgentTrace[];
  plan?: string[];
  reasoning?: string;
  isStreaming?: boolean;
}

export interface GraphMeta {
  nodes: { id: string; label: string; type: string; desc: string }[];
  edges: { from: string; to: string }[];
}
