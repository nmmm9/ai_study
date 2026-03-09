"use client";

import type { EmbedResult, CollectionItem } from "@/types/rag";

interface CollectionPanelProps {
  collections: CollectionItem[];
  activeCollection: string | null;
  embedResult: EmbedResult | null;
  isEmbedding: boolean;
  hasDocument: boolean;
  onEmbed: () => void;
  onSelect: (name: string, count: number) => void;
  onDelete: (name: string) => void;
}

export default function CollectionPanel({
  collections,
  activeCollection,
  embedResult,
  isEmbedding,
  hasDocument,
  onEmbed,
  onSelect,
  onDelete,
}: CollectionPanelProps) {
  return (
    <section className="animate-fade-in-up rounded-2xl border border-stroke bg-base-50 p-5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="font-serif text-sm font-light text-pearl">
          컬렉션 관리
        </h2>
        <button
          onClick={onEmbed}
          disabled={!hasDocument || isEmbedding}
          className="rounded-xl bg-gold px-4 py-1.5 text-xs font-medium text-base transition-all hover:bg-gold-bright active:scale-95 disabled:opacity-30"
        >
          {isEmbedding ? (
            <span className="flex items-center gap-1.5">
              <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-base border-t-transparent" />
              임베딩 중...
            </span>
          ) : embedResult && embedResult.total_time_ms === 0 ? (
            "이미 저장됨"
          ) : (
            "새 문서 임베딩"
          )}
        </button>
      </div>

      {/* Embed stats */}
      {embedResult && embedResult.total_time_ms > 0 && (
        <div className="mb-4 flex flex-wrap gap-3 rounded-lg border border-gold/10 bg-gold/5 px-3 py-2">
          <span className="text-[10px] text-pearl-muted">
            {embedResult.collection_name}
          </span>
          <span className="text-[10px] text-pearl-muted">
            {embedResult.chunk_count}개 청크
          </span>
          <span className="text-[10px] text-pearl-muted">
            {(embedResult.total_time_ms / 1000).toFixed(1)}s
          </span>
        </div>
      )}

      {/* Collection list */}
      {collections.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-[10px] tracking-wider text-pearl-muted uppercase">
            저장된 컬렉션 (클릭하여 선택)
          </p>
          {collections.map((c) => (
            <div
              key={c.name}
              onClick={() => onSelect(c.name, c.count)}
              className={`flex cursor-pointer items-center justify-between rounded-lg border px-3 py-2 transition-all ${
                c.name === activeCollection
                  ? "border-gold/30 bg-gold/5"
                  : "border-stroke bg-base-100 hover:border-stroke-hover"
              }`}
            >
              <div className="flex items-center gap-2">
                {c.name === activeCollection && (
                  <span className="text-[10px] text-gold">●</span>
                )}
                <span className="text-xs text-pearl">{c.name}</span>
                <span className="text-[10px] text-pearl-muted">
                  {c.count}개
                </span>
              </div>
              <div className="flex items-center gap-2">
                {c.name === activeCollection && (
                  <span className="text-[10px] text-gold">선택됨</span>
                )}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(c.name);
                  }}
                  className="text-[10px] text-bad/60 hover:text-bad"
                >
                  삭제
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {collections.length === 0 && !embedResult && (
        <p className="text-center text-xs text-pearl-muted">
          문서를 입력하고 임베딩하여 컬렉션을 만드세요
        </p>
      )}
    </section>
  );
}
