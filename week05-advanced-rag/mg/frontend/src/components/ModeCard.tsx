"use client";

import type { RagResponse } from "@/types/rag";
import PipelineViz from "./PipelineViz";

interface Props {
  mode: string;
  label: string;
  desc: string;
  pipeline: string;
  colorClass: { text: string; bg: string; border: string };
  result: RagResponse | null;
  isRunning: boolean;
  hasCollection: boolean;
  hasQuestion: boolean;
  onRun: () => void;
}

export default function ModeCard({
  label,
  desc,
  pipeline,
  colorClass,
  result,
  isRunning,
  hasCollection,
  hasQuestion,
  onRun,
}: Props) {
  const canRun = hasCollection && hasQuestion && !isRunning;

  return (
    <div
      className={`group relative flex flex-col rounded-2xl border bg-base-50 transition-all ${
        result ? colorClass.border : "border-stroke hover:border-stroke-hover"
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-stroke px-4 py-3">
        <div>
          <p className={`text-sm font-medium ${colorClass.text}`}>{label}</p>
          <p className="text-[11px] text-pearl-muted">{desc}</p>
        </div>
        <button
          onClick={onRun}
          disabled={!canRun}
          className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-all ${
            canRun
              ? `${colorClass.bg} ${colorClass.text} hover:opacity-80`
              : "bg-base-200 text-pearl-muted/50 cursor-not-allowed"
          }`}
        >
          {isRunning ? (
            <span className="flex items-center gap-1.5">
              <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent" />
              실행 중
            </span>
          ) : (
            "실행"
          )}
        </button>
      </div>

      {/* Pipeline flow */}
      <div className="px-4 py-2 border-b border-stroke/50">
        <p className="text-[10px] font-mono text-pearl-muted/70">{pipeline}</p>
      </div>

      {/* Result */}
      <div className="flex-1 p-4">
        {isRunning ? (
          <div className="space-y-2">
            <div className="h-3 w-3/4 animate-pulse rounded bg-base-200" />
            <div className="h-3 w-full animate-pulse rounded bg-base-200" />
            <div className="h-3 w-1/2 animate-pulse rounded bg-base-200" />
          </div>
        ) : result ? (
          <div className="animate-fade-in-up space-y-3">
            <PipelineViz steps={result.steps} isLoading={false} />

            {/* Stats */}
            <div className="flex gap-3 text-[11px] text-pearl-muted">
              <span>{result.timing.total_ms}ms</span>
              <span>${result.cost_usd.toFixed(4)}</span>
              <span>{result.total_tokens} tok</span>
            </div>

            {/* Mode-specific info */}
            {result.hyde_query && (
              <div className="rounded-lg border border-purple/20 bg-purple/5 px-3 py-2">
                <p className="text-[10px] font-medium text-purple">HyDE 가상 답변</p>
                <p className="text-[11px] text-pearl-muted line-clamp-2">{result.hyde_query}</p>
              </div>
            )}
            {result.generated_queries && result.generated_queries.length > 0 && (
              <div className="rounded-lg border border-info/20 bg-info/5 px-3 py-2">
                <p className="text-[10px] font-medium text-info">질문 변형</p>
                {result.generated_queries.map((q, i) => (
                  <p key={i} className="text-[11px] text-pearl-muted">{i + 1}. {q}</p>
                ))}
              </div>
            )}
            {result.self_eval && (
              <div className="rounded-lg border border-gold/20 bg-gold/5 px-3 py-2">
                <p className="text-[10px] font-medium text-gold">
                  자체 평가: {result.self_eval.score}/10
                  {result.self_eval.grounded ? " (근거 O)" : " (근거 X)"}
                </p>
              </div>
            )}
            {result.eval_verdict && (
              <div className={`rounded-lg border px-3 py-2 ${
                result.eval_verdict === "CORRECT" ? "border-good/20 bg-good/5" :
                result.eval_verdict === "AMBIGUOUS" ? "border-gold/20 bg-gold/5" :
                "border-bad/20 bg-bad/5"
              }`}>
                <p className={`text-[10px] font-medium ${
                  result.eval_verdict === "CORRECT" ? "text-good" :
                  result.eval_verdict === "AMBIGUOUS" ? "text-gold" : "text-bad"
                }`}>
                  문서 품질: {result.eval_verdict}
                  {result.corrective_action && " → 교정 수행"}
                </p>
              </div>
            )}
            {result.complexity && result.selected_pipeline && (
              <div className="rounded-lg border border-purple/20 bg-purple/5 px-3 py-2">
                <p className="text-[10px] font-medium text-purple">
                  {result.complexity} → {result.selected_pipeline}
                </p>
              </div>
            )}

            {/* Answer */}
            <p className="whitespace-pre-wrap text-xs leading-relaxed text-pearl-dim line-clamp-6">
              {result.answer}
            </p>

            {/* Sources */}
            <div className="flex flex-wrap gap-1">
              {result.sources.map((s, i) => (
                <span
                  key={i}
                  className="rounded bg-base-200 px-1.5 py-0.5 text-[10px] text-pearl-muted"
                  title={s.text.slice(0, 100)}
                >
                  [{s.index}] {(s.score * 100).toFixed(0)}%
                  {s.rerank_score != null && ` R:${(s.rerank_score * 100).toFixed(0)}%`}
                </span>
              ))}
            </div>
          </div>
        ) : (
          <p className="text-xs text-pearl-muted/50 text-center py-4">
            질문 입력 후 실행
          </p>
        )}
      </div>
    </div>
  );
}
