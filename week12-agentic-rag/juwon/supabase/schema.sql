-- ============================================================
-- Week 12: Agentic RAG - Supabase Schema
-- Supabase 대시보드 → SQL Editor에서 실행하세요
-- ============================================================

-- pgvector 활성화
create extension if not exists vector;

-- ── 트렌드 분석 리포트 테이블 ─────────────────────────────────
create table if not exists trend_reports (
  id                uuid        primary key default gen_random_uuid(),
  created_at        timestamptz default now(),
  language          text        default '전체',
  period            text        default 'weekly',
  repos             jsonb       default '[]',
  language_stats    jsonb       default '{}',
  top_topics        jsonb       default '{}',
  analysis_ai       text        default '',
  analysis_web      text        default '',
  analysis_sec      text        default '',
  supervisor_report text        default '',
  critic_feedback   text        default '',
  judge_decision    text        default '',
  debate_history    jsonb       default '[]',
  embedding         vector(1536)
);

-- 최신순 조회 인덱스
create index if not exists trend_reports_created_at_idx
  on trend_reports (created_at desc);

-- pgvector HNSW 인덱스 (코사인 유사도)
create index if not exists trend_reports_embedding_idx
  on trend_reports using hnsw (embedding vector_cosine_ops);

-- ── 키워드 구독 테이블 ────────────────────────────────────────
create table if not exists keyword_subscriptions (
  id         uuid        primary key default gen_random_uuid(),
  keyword    text        not null unique,
  created_at timestamptz default now()
);

-- ── pgvector 시맨틱 검색 함수 ─────────────────────────────────
create or replace function search_trend_reports(
  query_embedding vector(1536),
  match_count     int default 3
)
returns table (
  id                uuid,
  created_at        timestamptz,
  language          text,
  period            text,
  repos             jsonb,
  language_stats    jsonb,
  top_topics        jsonb,
  analysis_ai       text,
  analysis_web      text,
  analysis_sec      text,
  supervisor_report text,
  judge_decision    text,
  similarity        float
)
language sql stable
as $$
  select
    id, created_at, language, period,
    repos, language_stats, top_topics,
    analysis_ai, analysis_web, analysis_sec,
    supervisor_report, judge_decision,
    1 - (embedding <=> query_embedding) as similarity
  from trend_reports
  where embedding is not null
  order by embedding <=> query_embedding
  limit match_count;
$$;
