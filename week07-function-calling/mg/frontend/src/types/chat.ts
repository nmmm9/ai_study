export interface ToolCall {
  name: string;
  arguments: Record<string, unknown>;
  round: number;
}

export interface ToolResult {
  name: string;
  result: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  toolCalls?: ToolCall[];
  toolResults?: ToolResult[];
  isStreaming?: boolean;
}
