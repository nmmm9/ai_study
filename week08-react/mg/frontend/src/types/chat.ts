export interface ReActStep {
  type: "thought" | "action" | "observation";
  round: number;
  text?: string;
  tool?: string;
  arguments?: Record<string, unknown>;
  result?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  steps?: ReActStep[];
  isStreaming?: boolean;
}
