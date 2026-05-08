"use client";

import type { PipelineStep } from "@/types/rag";

interface PipelineVizProps {
  steps: PipelineStep[] | null;
  isLoading: boolean;
}

const ALL_STEPS = ["embed", "search", "generate"];
const STEP_LABELS: Record<string, string> = {
  embed: "임베딩",
  search: "벡터 검색",
  generate: "LLM 생성",
};

export default function PipelineViz({ steps, isLoading }: PipelineVizProps) {
  if (!steps && !isLoading) return null;

  const stepMap = steps ? new Map(steps.map((s) => [s.name, s])) : null;

  return (
    <section className="animate-fade-in-up rounded-2xl border border-stroke bg-base-50 p-5">
      <h2 className="mb-4 font-serif text-sm font-light text-pearl">
        파이프라인 단계
      </h2>

      <div className="flex items-center justify-center gap-1">
        {ALL_STEPS.map((name, i) => {
          const step = stepMap?.get(name);
          const isActive = !!step;

          return (
            <div key={name} className="flex items-center">
              {i > 0 && (
                <div className="mx-1 h-px w-6 bg-stroke-hover" />
              )}
              <div
                className={`group relative flex items-center justify-center rounded-lg border px-4 py-2 text-xs transition-all ${
                  isLoading
                    ? "animate-pulse border-stroke bg-base-100 text-pearl-muted"
                    : isActive
                      ? "border-gold/20 bg-gold/10 text-gold"
                      : "border-stroke bg-base-100 text-pearl-muted"
                }`}
              >
                {STEP_LABELS[name] || name}
                {isActive && (
                  <span className="ml-2 text-[10px] opacity-60">
                    {step.time_ms >= 1000
                      ? `${(step.time_ms / 1000).toFixed(1)}s`
                      : `${step.time_ms}ms`}
                  </span>
                )}

                {step?.detail && (
                  <div className="pointer-events-none absolute top-full left-1/2 z-20 mt-2 w-56 -translate-x-1/2 rounded-lg border border-stroke bg-base-50 p-2.5 text-[10px] leading-relaxed text-pearl-dim opacity-0 shadow-lg transition-opacity group-hover:pointer-events-auto group-hover:opacity-100">
                    {step.detail}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
