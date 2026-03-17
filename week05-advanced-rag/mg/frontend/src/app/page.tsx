"use client";

import { useEffect } from "react";
import { useAdvancedRag } from "@/hooks/useAdvancedRag";
import { RAG_MODES } from "@/types/rag";
import DocumentInput from "@/components/DocumentInput";
import CollectionPanel from "@/components/CollectionPanel";
import QuestionInput from "@/components/QuestionInput";
import CompareView from "@/components/CompareView";

export default function Home() {
  const {
    document,
    setDocument,
    selectedModel,
    setSelectedModel,
    modeA,
    setModeA,
    modeB,
    setModeB,
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
    compareResult,
    isComparing,
    compare,
  } = useAdvancedRag();

  useEffect(() => {
    fetchSamples();
    fetchCollections();
  }, [fetchSamples, fetchCollections]);

  const modeALabel = RAG_MODES.find((m) => m.value === modeA)?.label ?? modeA;
  const modeBLabel = RAG_MODES.find((m) => m.value === modeB)?.label ?? modeB;

  return (
    <div className="relative min-h-screen bg-base">
      {/* Ambient glow */}
      <div
        className="pointer-events-none absolute -top-60 left-1/2 h-[400px] w-[600px] -translate-x-1/2 rounded-full opacity-[0.04]"
        style={{
          background: "radial-gradient(ellipse, #C9A96E, transparent 70%)",
        }}
      />

      {/* Header */}
      <header className="glass sticky top-0 z-10 border-b border-stroke">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
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
            disabled={isEmbedding || isComparing}
            className="appearance-none rounded-xl border border-stroke bg-base-50 px-3.5 py-1.5 pr-8 text-xs text-pearl-dim transition-all hover:border-stroke-hover focus:border-gold-dim focus:outline-none disabled:opacity-30"
          >
            <option value="gpt-4o-mini">GPT-4o Mini</option>
            <option value="gpt-4o">GPT-4o</option>
          </select>
        </div>
      </header>

      {/* Main */}
      <main className="mx-auto max-w-6xl space-y-6 px-6 py-8">
        <DocumentInput
          document={document}
          setDocument={setDocument}
          samples={samples}
          onLoadSample={loadSample}
          disabled={isEmbedding || isComparing}
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

        {/* Mode selector */}
        {!!embedResult && (
          <div className="rounded-xl border border-stroke bg-base-50 p-5">
            <p className="mb-3 text-xs font-medium text-pearl-dim">
              비교할 파이프라인 선택
            </p>
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <label className="mb-1 block text-[10px] uppercase tracking-wider text-pearl-muted">
                  Left
                </label>
                <select
                  value={modeA}
                  onChange={(e) => setModeA(e.target.value as typeof modeA)}
                  disabled={isComparing}
                  className="w-full appearance-none rounded-lg border border-stroke bg-base-100 px-3 py-2 text-sm text-pearl-dim transition-all hover:border-stroke-hover focus:border-gold-dim focus:outline-none disabled:opacity-30"
                >
                  {RAG_MODES.map((m) => (
                    <option key={m.value} value={m.value}>
                      {m.label} — {m.desc}
                    </option>
                  ))}
                </select>
              </div>
              <span className="mt-5 text-lg font-bold text-gold">VS</span>
              <div className="flex-1">
                <label className="mb-1 block text-[10px] uppercase tracking-wider text-pearl-muted">
                  Right
                </label>
                <select
                  value={modeB}
                  onChange={(e) => setModeB(e.target.value as typeof modeB)}
                  disabled={isComparing}
                  className="w-full appearance-none rounded-lg border border-stroke bg-base-100 px-3 py-2 text-sm text-pearl-dim transition-all hover:border-stroke-hover focus:border-gold-dim focus:outline-none disabled:opacity-30"
                >
                  {RAG_MODES.map((m) => (
                    <option key={m.value} value={m.value}>
                      {m.label} — {m.desc}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        )}

        <QuestionInput
          onSubmit={compare}
          disabled={isComparing}
          hasCollection={!!embedResult}
        />

        <CompareView
          result={compareResult}
          isLoading={isComparing}
          labelA={modeALabel}
          labelB={modeBLabel}
        />
      </main>
    </div>
  );
}
