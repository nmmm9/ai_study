"use client";

import type { RagResponse } from "@/types/rag";

interface Props {
  result: RagResponse | null;
  isLoading: boolean;
  variant: "basic" | "advanced";
}

const VARIANT_STYLES = {
  basic: {
    border: "border-pearl-muted/20",
    badge: "bg-pearl/10 text-pearl-dim",
    label: "Basic RAG",
  },
  advanced: {
    border: "border-gold/30",
    badge: "bg-gold/15 text-gold",
    label: "Advanced RAG",
  },
};

export default function AnswerCard({ result, isLoading, variant }: Props) {
  const style = VARIANT_STYLES[variant];

  return (
    <div
      className={`flex flex-col rounded-2xl border bg-base-50 ${style.border}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-stroke px-5 py-3">
        <span className={`rounded-lg px-2.5 py-1 text-xs font-medium ${style.badge}`}>
          {style.label}
        </span>
        {result && (
          <div className="flex gap-3 text-[11px] text-pearl-muted">
            <span>${result.cost_usd.toFixed(4)}</span>
            <span>{result.total_tokens} tokens</span>
            <span>{result.timing.total_ms}ms</span>
          </div>
        )}
      </div>

      {/* Body */}
      <div className="flex-1 p-5">
        {isLoading ? (
          <div className="space-y-3">
            <div className="h-4 w-3/4 animate-pulse rounded bg-base-200" />
            <div className="h-4 w-full animate-pulse rounded bg-base-200" />
            <div className="h-4 w-2/3 animate-pulse rounded bg-base-200" />
          </div>
        ) : result ? (
          <>
            {/* HyDE preview */}
            {result.hyde_query && (
              <div className="mb-4 rounded-xl border border-purple/20 bg-purple/5 p-3">
                <p className="mb-1 text-[11px] font-medium text-purple">
                  HyDE 가상 답변
                </p>
                <p className="text-xs leading-relaxed text-pearl-muted line-clamp-3">
                  {result.hyde_query}
                </p>
              </div>
            )}

            {/* Answer */}
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-pearl-dim">
              {result.answer}
            </p>

            {/* Sources */}
            {result.sources.length > 0 && (
              <div className="mt-4 space-y-2">
                <p className="text-[11px] font-medium text-pearl-muted">
                  참조 소스 ({result.sources.length})
                </p>
                {result.sources.map((s, i) => (
                  <div
                    key={i}
                    className="rounded-lg border border-stroke bg-base-100 p-3"
                  >
                    <div className="mb-1 flex items-center gap-2">
                      <span className="rounded bg-base-200 px-1.5 py-0.5 text-[10px] font-medium text-pearl-muted">
                        [{s.index}]
                      </span>
                      <span className="text-[11px] text-gold">
                        유사도 {(s.score * 100).toFixed(1)}%
                      </span>
                      {s.rerank_score != null && (
                        <span className="text-[11px] text-good">
                          리랭크 {(s.rerank_score * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>
                    <p className="text-xs leading-relaxed text-pearl-muted line-clamp-2">
                      {s.text}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </>
        ) : (
          <p className="text-sm text-pearl-muted">
            질문을 입력하면 결과가 여기에 표시됩니다
          </p>
        )}
      </div>
    </div>
  );
}
