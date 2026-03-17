"use client";

import { useEffect, useState } from "react";
import { useAdvancedRag } from "@/hooks/useAdvancedRag";
import { RAG_MODES } from "@/types/rag";
import type { RagMode } from "@/types/rag";
import DocumentInput from "@/components/DocumentInput";
import CollectionPanel from "@/components/CollectionPanel";
import ModeCard from "@/components/ModeCard";

const MODE_DETAILS: Record<
  string,
  { pipeline: string; colorClass: { text: string; bg: string; border: string } }
> = {
  basic: {
    pipeline: "Embed → Search → Generate",
    colorClass: { text: "text-info", bg: "bg-info/15", border: "border-info/30" },
  },
  hyde: {
    pipeline: "HyDE → Embed → Search → Generate",
    colorClass: { text: "text-purple", bg: "bg-purple/15", border: "border-purple/30" },
  },
  rerank: {
    pipeline: "Embed → Wide Search → Rerank → Generate",
    colorClass: { text: "text-good", bg: "bg-good/15", border: "border-good/30" },
  },
  advanced: {
    pipeline: "HyDE → Embed → Wide Search → Rerank → Generate",
    colorClass: { text: "text-gold", bg: "bg-gold/15", border: "border-gold/30" },
  },
  hybrid: {
    pipeline: "Embed + BM25 → RRF 병합 → Generate",
    colorClass: { text: "text-gold-dim", bg: "bg-gold/10", border: "border-gold-dim/30" },
  },
  multi_query: {
    pipeline: "질문 변형 → 다중 Embed → 다중 Search → Generate",
    colorClass: { text: "text-info", bg: "bg-info/15", border: "border-info/30" },
  },
  self_rag: {
    pipeline: "Judge → Search → Generate → Evaluate → (Regen)",
    colorClass: { text: "text-purple", bg: "bg-purple/15", border: "border-purple/30" },
  },
  crag: {
    pipeline: "Search → Evaluate → (Refine → Re-search) → Generate",
    colorClass: { text: "text-bad", bg: "bg-bad/15", border: "border-bad/30" },
  },
  adaptive: {
    pipeline: "Classify → (자동 선택 파이프라인 실행)",
    colorClass: { text: "text-pearl-dim", bg: "bg-pearl/10", border: "border-pearl-muted/30" },
  },
};

export default function Home() {
  const {
    document,
    setDocument,
    selectedModel,
    setSelectedModel,
    samples,
    fetchSamples,
    loadSample,
    embedResult,
    isEmbedding,
    embedDocument,
    collections,
    fetchCollections,
    selectCollection,
    deleteCollection,
    results,
    runningModes,
    currentQuestion,
    setCurrentQuestion,
    runMode,
  } = useAdvancedRag();

  const [question, setQuestion] = useState("");

  useEffect(() => {
    fetchSamples();
    fetchCollections();
  }, [fetchSamples, fetchCollections]);

  const handleRunAll = () => {
    if (!question.trim() || !embedResult) return;
    setCurrentQuestion(question);
    RAG_MODES.forEach((m) => {
      runMode(m.value as RagMode, question);
    });
  };

  const handleRunSingle = (mode: RagMode) => {
    const q = question.trim() || currentQuestion;
    if (!q) return;
    if (!currentQuestion) setCurrentQuestion(q);
    runMode(mode, q);
  };

  const anyRunning = runningModes.size > 0;

  return (
    <div className="relative min-h-screen bg-base">
      <div
        className="pointer-events-none absolute -top-60 left-1/2 h-[400px] w-[600px] -translate-x-1/2 rounded-full opacity-[0.04]"
        style={{
          background: "radial-gradient(ellipse, #C9A96E, transparent 70%)",
        }}
      />

      {/* Header */}
      <header className="glass sticky top-0 z-10 border-b border-stroke">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="font-serif text-2xl font-light tracking-wide text-pearl">
              Advanced RAG
            </h1>
            <p className="mt-0.5 text-[11px] tracking-wide text-pearl-muted">
              9가지 RAG 파이프라인 비교 데모
            </p>
          </div>
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            disabled={isEmbedding || anyRunning}
            className="appearance-none rounded-xl border border-stroke bg-base-50 px-3.5 py-1.5 pr-8 text-xs text-pearl-dim transition-all hover:border-stroke-hover focus:border-gold-dim focus:outline-none disabled:opacity-30"
          >
            <option value="gpt-4o-mini">GPT-4o Mini</option>
            <option value="gpt-4o">GPT-4o</option>
          </select>
        </div>
      </header>

      <main className="mx-auto max-w-7xl space-y-6 px-6 py-8">
        <DocumentInput
          document={document}
          setDocument={setDocument}
          samples={samples}
          onLoadSample={loadSample}
          disabled={isEmbedding || anyRunning}
        />

        <CollectionPanel
          collections={collections}
          activeCollection={embedResult?.collection_name ?? null}
          embedResult={embedResult}
          isEmbedding={isEmbedding}
          hasDocument={document.length > 0}
          onEmbed={embedDocument}
          onSelect={selectCollection}
          onDelete={deleteCollection}
        />

        {/* Question + Run All */}
        {!!embedResult && (
          <div className="flex gap-3">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.nativeEvent.isComposing) {
                  e.preventDefault();
                  handleRunAll();
                }
              }}
              placeholder="질문을 입력하세요..."
              disabled={anyRunning}
              className="flex-1 rounded-xl border border-stroke bg-base-50 px-4 py-3 text-sm text-pearl-dim placeholder:text-pearl-muted/40 transition-all hover:border-stroke-hover focus:border-gold-dim focus:outline-none disabled:opacity-30"
            />
            <button
              onClick={handleRunAll}
              disabled={!question.trim() || anyRunning}
              className="rounded-xl bg-gold/15 px-5 py-3 text-sm font-medium text-gold transition-all hover:bg-gold/25 disabled:opacity-30 disabled:cursor-not-allowed whitespace-nowrap"
            >
              전체 실행
            </button>
          </div>
        )}

        {/* 9 Mode Cards Grid */}
        {!!embedResult && (
          <div className="grid grid-cols-3 gap-4">
            {RAG_MODES.map((m) => {
              const detail = MODE_DETAILS[m.value];
              return (
                <ModeCard
                  key={m.value}
                  mode={m.value}
                  label={m.label}
                  desc={m.desc}
                  pipeline={detail.pipeline}
                  colorClass={detail.colorClass}
                  result={results[m.value] ?? null}
                  isRunning={runningModes.has(m.value)}
                  hasCollection={!!embedResult}
                  hasQuestion={!!(question.trim() || currentQuestion)}
                  onRun={() => handleRunSingle(m.value as RagMode)}
                />
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
