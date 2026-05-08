"use client";

import type { RagResponse, SourceChunk } from "@/types/rag";

interface AnswerCardProps {
  result: RagResponse | null;
  isLoading: boolean;
}

export default function AnswerCard({ result, isLoading }: AnswerCardProps) {
  if (!isLoading && !result) return null;

  return (
    <section className="animate-fade-in-up rounded-2xl border border-gold/20 bg-base-50 p-5">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="font-serif text-sm font-light text-pearl">답변</h2>
        {result && (
          <span className="text-[10px] text-pearl-muted">
            ${result.cost_usd.toFixed(4)} · {result.total_tokens} tokens
          </span>
        )}
      </div>

      {isLoading ? (
        <div className="space-y-2">
          <div className="h-3 w-3/4 animate-pulse rounded bg-stroke" />
          <div className="h-3 w-1/2 animate-pulse rounded bg-stroke" />
          <div className="h-3 w-2/3 animate-pulse rounded bg-stroke" />
        </div>
      ) : result ? (
        <>
          <p className="whitespace-pre-wrap text-[13.5px] leading-[1.8] text-pearl">
            {result.answer}
          </p>

          {/* Timing bar */}
          <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-stroke pt-3">
            {Object.entries(result.timing)
              .filter(([k]) => k !== "total_ms")
              .map(([key, ms]) => (
                <span key={key} className="text-[10px] text-pearl-muted">
                  {key.replace("_ms", "")}{" "}
                  {ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`}
                </span>
              ))}
            <span className="ml-auto text-[10px] font-medium text-pearl-dim">
              총 {(result.timing.total_ms / 1000).toFixed(1)}s
            </span>
          </div>

          {/* Sources */}
          {result.sources.length > 0 && (
            <div className="mt-4 border-t border-stroke pt-4">
              <p className="mb-2 text-[10px] tracking-wider text-pearl-muted uppercase">
                참고 문서 ({result.sources.length}개)
              </p>
              <div className="space-y-2">
                {result.sources.map((s: SourceChunk, i: number) => (
                  <div
                    key={i}
                    className="rounded-lg border border-stroke bg-base-100 px-3 py-2"
                  >
                    <div className="mb-1 flex items-center gap-2">
                      <span className="rounded bg-gold/10 px-1.5 py-0.5 text-[10px] font-bold text-gold">
                        [{i + 1}]
                      </span>
                      <span className="text-[10px] text-pearl-muted">
                        유사도 {(s.score * 100).toFixed(1)}%
                      </span>
                      <span className="text-[10px] text-pearl-muted/50">
                        청크 #{s.index}
                      </span>
                    </div>
                    <p className="line-clamp-3 text-[11px] leading-relaxed text-pearl-dim">
                      {s.text}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      ) : null}
    </section>
  );
}
