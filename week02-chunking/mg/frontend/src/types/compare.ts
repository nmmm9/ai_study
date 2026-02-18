export interface SampleInfo {
  id: string;
  title: string;
  length: number;
}

export interface Stats {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  time_ms: number;
  cost_usd: number;
  document_tokens: number;
}

export interface RawResult {
  answer: string | null;
  error?: string;
  message?: string;
  stats: Stats;
}

export interface ScoredChunk {
  index: number;
  text: string;
  score: number;
  start: number;
  end: number;
}

export interface ChunkedResult {
  answer: string;
  stats: Stats;
  chunks: {
    total_count: number;
    used: ScoredChunk[];
  };
}
