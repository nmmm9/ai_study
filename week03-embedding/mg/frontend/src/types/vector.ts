export interface SampleInfo {
  id: string;
  title: string;
  length: number;
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

export interface TimingBreakdown {
  embed_ms: number;
  search_ms: number;
  llm_ms: number;
  total_ms: number;
}

export interface ScoredChunk {
  index: number;
  text: string;
  score: number;
}

export interface SearchResult {
  answer: string;
  timing: TimingBreakdown;
  cost_usd: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  used_chunks: ScoredChunk[];
  chunk_count: number;
}

export interface VizPoint {
  x: number;
  y: number;
  index: number;
  text_preview: string;
}

export interface Point2D {
  x: number;
  y: number;
}

export interface VizData {
  points: VizPoint[];
  query_point: Point2D | null;
}

export interface CollectionItem {
  name: string;
  count: number;
}
