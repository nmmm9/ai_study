"use client";

import type { EmbedResult } from "@/types/vector";

interface EmbeddingPanelProps {
  onEmbed: () => void;
  embedResult: EmbedResult | null;
  isEmbedding: boolean;
  hasDocument: boolean;
}

function StatCell({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-stroke bg-base-100 px-3 py-2 text-center">
      <p className="text-[10px] text-pearl-muted">{label}</p>
      <p className="mt-0.5 truncate text-xs font-medium text-gold">{value}</p>
    </div>
  );
}

export default function EmbeddingPanel({
  onEmbed,
  embedResult,
  isEmbedding,
  hasDocument,
}: EmbeddingPanelProps) {
  const isCached = embedResult && embedResult.total_time_ms === 0;

  return (
    <div className="animate-fade-in-up rounded-2xl border border-stroke bg-base-50 p-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-xs font-medium tracking-widest uppercase text-pearl-dim">
            벡터 임베딩
          </h2>
          {embedResult && (
            <span className="rounded-full bg-good/10 px-2.5 py-0.5 text-[10px] text-good">
              {isCached ? "이미 저장됨" : "저장 완료"}
            </span>
          )}
        </div>
        <button
          onClick={onEmbed}
          disabled={!hasDocument || isEmbedding}
          className="rounded-xl bg-gold px-5 py-2 text-sm font-medium text-base transition-all hover:bg-gold-dim disabled:cursor-not-allowed disabled:opacity-25"
        >
          {isEmbedding ? (
            <span className="flex items-center gap-2">
              <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-base/30 border-t-base" />
              임베딩 중...
            </span>
          ) : embedResult ? (
            "다시 임베딩"
          ) : (
            "임베딩 저장"
          )}
        </button>
      </div>

      {embedResult && (
        <div className="mt-4 grid grid-cols-5 gap-3">
          <StatCell label="컬렉션" value={embedResult.collection_name} />
          <StatCell label="청크 수" value={`${embedResult.chunk_count}개`} />
          <StatCell label="차원" value={`${embedResult.dimension}D`} />
          <StatCell
            label="시간"
            value={
              isCached
                ? "캐시"
                : `${(embedResult.total_time_ms / 1000).toFixed(1)}s`
            }
          />
          <StatCell
            label="비용"
            value={
              isCached ? "$0" : `$${embedResult.embed_cost.toFixed(4)}`
            }
          />
        </div>
      )}
    </div>
  );
}
