import type { SearchResult } from "@/types/vector";

interface AnswerCardProps {
  title: string;
  result: SearchResult | null;
  variant: "memory" | "vectordb";
  isLoading: boolean;
}

export default function AnswerCard({
  title,
  result,
  variant,
  isLoading,
}: AnswerCardProps) {
  const borderColor =
    variant === "memory" ? "border-bad/20" : "border-good/20";
  const tagColor =
    variant === "memory" ? "bg-bad/10 text-bad" : "bg-good/10 text-good";

  return (
    <div
      className={`animate-fade-in-up flex flex-1 flex-col rounded-2xl border ${borderColor} bg-base-50 p-5`}
    >
      {/* Header */}
      <div className="mb-3 flex items-center justify-between">
        <span
          className={`rounded-full px-2.5 py-0.5 text-[10px] font-medium tracking-wider uppercase ${tagColor}`}
        >
          {title}
        </span>
      </div>

      {/* Content */}
      <div className="flex-1">
        {isLoading ? (
          <div className="space-y-2">
            <div className="h-3 w-3/4 animate-pulse rounded bg-stroke" />
            <div className="h-3 w-1/2 animate-pulse rounded bg-stroke" />
            <div className="h-3 w-2/3 animate-pulse rounded bg-stroke" />
          </div>
        ) : result ? (
          <p className="whitespace-pre-wrap text-[13.5px] leading-[1.8] text-pearl">
            {result.answer}
          </p>
        ) : null}
      </div>

      {/* Timing breakdown */}
      {result && !isLoading && (
        <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-stroke pt-3">
          <span className="text-[10px] text-pearl-muted">
            임베딩 {(result.timing.embed_ms / 1000).toFixed(1)}s
          </span>
          <span className="text-[10px] text-pearl-muted">
            검색 {result.timing.search_ms}ms
          </span>
          <span className="text-[10px] text-pearl-muted">
            LLM {(result.timing.llm_ms / 1000).toFixed(1)}s
          </span>
          <span className="ml-auto text-[10px] font-medium text-pearl-dim">
            총 {(result.timing.total_ms / 1000).toFixed(1)}s
          </span>
        </div>
      )}
    </div>
  );
}
