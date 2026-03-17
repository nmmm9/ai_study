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
  generated_queries?: string[];
  self_eval?: { score: number; grounded: boolean; feedback: string };
  corrective_action?: string | null;
  eval_verdict?: string;
  selected_pipeline?: string;
  complexity?: string;
}

export interface CompareResult {
  basic: RagResponse;
  advanced: RagResponse;
}

export const RAG_MODES = [
  { value: "basic", label: "Basic RAG", desc: "Embed → Search → Generate" },
  { value: "hyde", label: "HyDE", desc: "가상 문서 임베딩 검색" },
  { value: "rerank", label: "Rerank", desc: "LLM 리랭킹" },
  { value: "advanced", label: "Advanced", desc: "HyDE + Rerank" },
  { value: "hybrid", label: "Hybrid", desc: "벡터 + BM25 검색" },
  { value: "multi_query", label: "Multi-Query", desc: "질문 변형 다중 검색" },
  { value: "self_rag", label: "Self-RAG", desc: "자체 평가 + 재생성" },
  { value: "crag", label: "CRAG", desc: "검색 품질 교정" },
  { value: "adaptive", label: "Adaptive", desc: "복잡도별 자동 라우팅" },
] as const;

export type RagMode = (typeof RAG_MODES)[number]["value"];
