"use client";

import type { CollectionItem, EmbedResult } from "@/types/rag";

interface Props {
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
}: Props) {
  return (
    <section className="animate-fade-in-up rounded-2xl border border-stroke bg-base-50 p-5">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-medium tracking-wide text-pearl-dim">
          2. 벡터 컬렉션
        </h2>
        <button
          onClick={onEmbed}
          disabled={!hasDocument || isEmbedding}
          className="rounded-xl bg-gold/10 px-4 py-2 text-xs font-medium text-gold transition-all hover:bg-gold/20 disabled:opacity-30"
        >
          {isEmbedding ? "임베딩 중..." : "임베딩 저장"}
        </button>
      </div>

      {embedResult && (
        <div className="mt-3 flex flex-wrap gap-3 text-xs text-pearl-muted">
          <span>
            컬렉션:{" "}
            <span className="text-gold">{embedResult.collection_name}</span>
          </span>
          <span>{embedResult.chunk_count}개 청크</span>
          {embedResult.total_time_ms > 0 && (
            <span>{embedResult.total_time_ms}ms</span>
          )}
        </div>
      )}

      {collections.length > 0 && (
        <div className="mt-4 flex flex-wrap gap-2">
          {collections.map((c) => (
            <div
              key={c.name}
              className={`flex items-center gap-2 rounded-lg border px-3 py-1.5 text-xs transition-all ${
                activeCollection === c.name
                  ? "border-gold/40 bg-gold/8 text-gold"
                  : "border-stroke bg-base-100 text-pearl-muted hover:border-stroke-hover"
              }`}
            >
              <button onClick={() => onSelect(c.name, c.count)}>
                {c.name}{" "}
                <span className="opacity-60">({c.count})</span>
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(c.name);
                }}
                className="ml-1 text-pearl-muted hover:text-bad"
              >
                x
              </button>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
