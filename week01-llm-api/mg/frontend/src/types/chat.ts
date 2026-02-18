export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  usage?: TokenUsage;
  timestamp: number;
}

export interface TokenUsage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
}

export interface ModelInfo {
  id: string;
  name: string;
  provider: "openai" | "anthropic";
}

export interface SSEEvent {
  content: string;
  done: boolean;
  usage?: TokenUsage;
}
