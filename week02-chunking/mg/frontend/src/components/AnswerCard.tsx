import type { Stats } from "@/types/compare";

interface AnswerCardProps {
  title: string;
  answer: string | null;
  error?: string;
  message?: string;
  variant: "raw" | "chunked";
  stats: Stats | null;
  isLoading: boolean;
}

export default function AnswerCard({
  title,
  answer,
  error,
  message,
  variant,
  stats,
  isLoading,
}: AnswerCardProps) {
  const borderColor = variant === "raw" ? "border-bad/20" : "border-good/20";
  const tagColor =
    variant === "raw"
      ? "bg-bad/10 text-bad"
      : "bg-good/10 text-good";

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
        ) : error ? (
          <div className="rounded-xl border border-bad/20 bg-bad/5 p-4">
            <p className="text-sm font-medium text-bad">토큰 한도 초과</p>
            <p className="mt-1 text-xs text-pearl-dim">{message}</p>
          </div>
        ) : answer ? (
          <p className="whitespace-pre-wrap text-[13.5px] leading-[1.8] text-pearl">
            {answer}
          </p>
        ) : null}
      </div>

      {/* Bottom stats: tokens + time */}
      {stats && !isLoading && !error && (
        <div className="mt-4 flex items-center gap-4 border-t border-stroke pt-3">
          <span className="text-[10px] text-pearl-muted">
            문서 {stats.document_tokens.toLocaleString()} 토큰
          </span>
          <span className="text-[10px] text-pearl-muted">
            총 {stats.total_tokens.toLocaleString()} 토큰
          </span>
          <span className="text-[10px] text-pearl-muted">
            {(stats.time_ms / 1000).toFixed(1)}s
          </span>
        </div>
      )}
    </div>
  );
}
