"use client";

import { useState } from "react";
import type { ScoredChunk } from "@/types/compare";

interface ChunkViewerProps {
  totalChunks: number;
  usedChunks: ScoredChunk[];
}

export default function ChunkViewer({
  totalChunks,
  usedChunks,
}: ChunkViewerProps) {
  const [expandedChunk, setExpandedChunk] = useState<number | null>(null);

  const usedIndices = new Set(usedChunks.map((c) => c.index));

  return (
    <div className="animate-fade-in-up space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-xs font-medium tracking-widest uppercase text-pearl-dim">
          청크 시각화
        </h2>
        <span className="text-[10px] text-pearl-muted">
          총 {totalChunks}개 청크 중{" "}
          <span className="text-gold">{usedChunks.length}개</span> 사용
        </span>
      </div>

      {/* Chunk blocks */}
      <div className="flex flex-wrap gap-1.5">
        {Array.from({ length: totalChunks }, (_, i) => {
          const isUsed = usedIndices.has(i);
          const chunk = usedChunks.find((c) => c.index === i);
          return (
            <button
              key={i}
              onClick={() =>
                isUsed
                  ? setExpandedChunk(expandedChunk === i ? null : i)
                  : undefined
              }
              className={`h-8 rounded-md text-[10px] font-medium transition-all ${
                isUsed
                  ? "w-14 border border-gold/40 bg-gold/15 text-gold hover:bg-gold/25 cursor-pointer"
                  : "w-8 border border-stroke bg-base-100 text-pearl-muted/40 cursor-default"
              }`}
            >
              {isUsed ? `#${i + 1}` : i + 1}
            </button>
          );
        })}
      </div>

      {/* Expanded chunk detail */}
      {expandedChunk !== null && (
        <div className="rounded-xl border border-gold/20 bg-gold/5 p-4">
          {usedChunks
            .filter((c) => c.index === expandedChunk)
            .map((chunk) => (
              <div key={chunk.index}>
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-xs font-medium text-gold">
                    청크 #{chunk.index + 1}
                  </span>
                  <span className="text-[10px] text-pearl-muted">
                    유사도:{" "}
                    <span className="text-gold">
                      {(chunk.score * 100).toFixed(1)}%
                    </span>
                  </span>
                </div>
                <p className="whitespace-pre-wrap text-xs leading-relaxed text-pearl-dim">
                  {chunk.text}
                </p>
              </div>
            ))}
        </div>
      )}
    </div>
  );
}
