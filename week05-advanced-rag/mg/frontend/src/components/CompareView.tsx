"use client";

import type { CompareResult } from "@/types/rag";
import PipelineViz from "./PipelineViz";
import AnswerCard from "./AnswerCard";

interface Props {
  result: CompareResult | null;
  isLoading: boolean;
  labelA: string;
  labelB: string;
}

export default function CompareView({ result, isLoading, labelA, labelB }: Props) {
  if (!result && !isLoading) return null;

  const stepsA = result?.basic.steps ?? null;
  const stepsB = result?.advanced.steps ?? null;

  const showSummary = result && !isLoading;
  const timeDiff = showSummary
    ? result.advanced.timing.total_ms - result.basic.timing.total_ms
    : 0;
  const costDiff = showSummary
    ? result.advanced.cost_usd - result.basic.cost_usd
    : 0;

  return (
    <div className="animate-fade-in-up space-y-4">
      {/* Summary bar */}
      {showSummary && (
        <div className="flex items-center justify-center gap-6 rounded-xl border border-stroke bg-base-50 px-6 py-3">
          <div className="text-center">
            <p className="text-[10px] uppercase tracking-wider text-pearl-muted">
              시간 차이
            </p>
            <p className="text-sm font-medium text-pearl-dim">
              {timeDiff > 0 ? "+" : ""}
              {timeDiff >= 1000
                ? `${(timeDiff / 1000).toFixed(1)}s`
                : `${timeDiff}ms`}
            </p>
          </div>
          <div className="h-6 w-px bg-stroke" />
          <div className="text-center">
            <p className="text-[10px] uppercase tracking-wider text-pearl-muted">
              비용 차이
            </p>
            <p className="text-sm font-medium text-pearl-dim">
              {costDiff > 0 ? "+" : ""}${costDiff.toFixed(4)}
            </p>
          </div>
          <div className="h-6 w-px bg-stroke" />
          <div className="text-center">
            <p className="text-[10px] uppercase tracking-wider text-pearl-muted">
              소스 변화
            </p>
            <p className="text-sm font-medium text-pearl-dim">
              {result.basic.sources.map((s) => s.index).join(",")}{" "}
              <span className="text-pearl-muted">→</span>{" "}
              {result.advanced.sources.map((s) => s.index).join(",")}
            </p>
          </div>
        </div>
      )}

      {/* Pipeline comparison */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="mb-2 text-xs text-pearl-muted">{labelA} Pipeline</p>
          <PipelineViz steps={stepsA} isLoading={isLoading} />
        </div>
        <div>
          <p className="mb-2 text-xs text-pearl-muted">{labelB} Pipeline</p>
          <PipelineViz steps={stepsB} isLoading={isLoading} />
        </div>
      </div>

      {/* Answers side by side */}
      <div className="grid grid-cols-2 gap-4">
        <AnswerCard
          result={result?.basic ?? null}
          isLoading={isLoading}
          variant="basic"
          label={labelA}
        />
        <AnswerCard
          result={result?.advanced ?? null}
          isLoading={isLoading}
          variant="advanced"
          label={labelB}
        />
      </div>
    </div>
  );
}
