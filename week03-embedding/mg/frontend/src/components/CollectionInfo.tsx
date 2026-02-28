"use client";

import type { CollectionItem } from "@/types/vector";

interface CollectionInfoProps {
  collections: CollectionItem[];
  activeCollection: string | null;
  onSelect: (name: string, count: number) => void;
  onDelete: (name: string) => void;
}

export default function CollectionInfo({
  collections,
  activeCollection,
  onSelect,
  onDelete,
}: CollectionInfoProps) {
  if (collections.length === 0) return null;

  return (
    <div className="animate-fade-in-up rounded-2xl border border-stroke bg-base-50 p-5">
      <h2 className="mb-3 text-xs font-medium tracking-widest uppercase text-pearl-dim">
        저장된 컬렉션
      </h2>
      <div className="space-y-2">
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
            <div className="flex items-center gap-3">
              {c.name === activeCollection && (
                <span className="text-[10px] text-gold">●</span>
              )}
              <span className="text-xs text-pearl">{c.name}</span>
              <span className="text-[10px] text-pearl-muted">
                {c.count}개 청크
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
                className="text-[10px] text-bad/60 transition-colors hover:text-bad"
              >
                삭제
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
