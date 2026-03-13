export interface SampleInfo {
  id: string;
  title: string;
  length: number;
}

export interface CollectionItem {
  name: string;
  count: number;
}

export interface EmbedResult {
  collection_name: string;
  chunk_count: number;
  dimension: number;
  embed_time_ms: number;
  store_time_ms: number;
  total_time_ms: number;
  embed_cost: number;
}

export interface PipelineStep {
  name: string;
  label: string;
  time_ms: number;
  detail?: string;
}

export interface SourceChunk {
  index: number;
  text: string;
  score: number;
  rerank_score?: number;
}

export interface RagResponse {
  answer: string;
  sources: SourceChunk[];
  steps: PipelineStep[];
  timing: Record<string, number>;
  cost_usd: number;
  total_tokens: number;
  mode: string;
  hyde_query?: string;
}

export interface CompareResult {
  basic: RagResponse;
  advanced: RagResponse;
}
