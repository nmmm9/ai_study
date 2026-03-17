"use client";

import type { PipelineStep } from "@/types/rag";

const STEP_COLORS: Record<string, string> = {
  hyde: "border-purple/50 bg-purple/8 text-purple",
  embed: "border-info/50 bg-info/8 text-info",
  search: "border-gold/50 bg-gold/8 text-gold",
  rerank: "border-good/50 bg-good/8 text-good",
  generate: "border-pearl/30 bg-pearl/5 text-pearl-dim",
  bm25: "border-orange-400/50 bg-orange-400/8 text-orange-400",
  rrf: "border-gold/50 bg-gold/8 text-gold",
  multi_query: "border-info/50 bg-info/8 text-info",
  judge: "border-purple/50 bg-purple/8 text-purple",
  evaluate: "border-gold/50 bg-gold/8 text-gold",
  regenerate: "border-good/50 bg-good/8 text-good",
  refine: "border-orange-400/50 bg-orange-400/8 text-orange-400",
  re_search: "border-gold/50 bg-gold/8 text-gold",
  classify: "border-purple/50 bg-purple/8 text-purple",
};

function formatTime(ms: number): string {
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`;
}

interface Props {
  steps: PipelineStep[] | null;
  isLoading: boolean;
}

export default function PipelineViz({ steps, isLoading }: Props) {
  if (!steps && !isLoading) return null;

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {isLoading && !steps ? (
        <div className="flex items-center gap-1.5">
          {["embed", "search", "generate"].map((name, i) => (
            <div key={name} className="flex items-center gap-1.5">
              {i > 0 && (
                <span className="text-xs text-pearl-muted">→</span>
              )}
              <div className="h-7 w-16 animate-pulse rounded-lg bg-base-200" />
            </div>
          ))}
        </div>
      ) : (
        steps?.map((step, i) => (
          <div key={step.name + i} className="flex items-center gap-1.5">
            {i > 0 && (
              <span className="text-xs text-pearl-muted">→</span>
            )}
            <div
              className={`rounded-lg border px-2.5 py-1 text-[11px] font-medium ${
                STEP_COLORS[step.name] ?? "border-stroke bg-base-100 text-pearl-muted"
              }`}
              title={step.detail ?? step.label}
            >
              {step.label}
              <span className="ml-1.5 opacity-60">{formatTime(step.time_ms)}</span>
            </div>
          </div>
        ))
      )}
    </div>
  );
}
