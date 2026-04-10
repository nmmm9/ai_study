export interface ThinkingStep {
  step: string;
  detail: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceChunk[];
  thinking?: ThinkingStep[];
  isStreaming?: boolean;
}

export interface SourceChunk {
  index: number;
  text: string;
  score: number;
  source?: string;
}

export interface ChatSession {
  id: string;
  name: string;
  messages: ChatMessage[];
  collections: string[];  // attached collections (base + uploaded files)
  fileNames: string[];    // display names of attached files
  createdAt: number;
}

export interface SampleInfo {
  id: string;
  title: string;
  length: number;
}

export interface CollectionItem {
  name: string;
  count: number;
}
