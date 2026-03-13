"use client";

import { useEffect } from "react";
import { useAdvancedRag } from "@/hooks/useAdvancedRag";
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
              Basic vs Advanced RAG 비교 데모 — HyDE + Reranking
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

        <QuestionInput
          onSubmit={compare}
          disabled={isComparing}
          hasCollection={!!embedResult}
        />

        {/* Method info */}
        {!!embedResult && !compareResult && !isComparing && (
          <div className="rounded-xl border border-stroke bg-base-50 p-5">
            <p className="mb-3 text-xs font-medium text-pearl-dim">
              비교 방식
            </p>
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-lg border border-pearl-muted/20 bg-base-100 p-4">
                <p className="mb-1 text-sm font-medium text-pearl-dim">
                  Basic RAG
                </p>
                <p className="text-xs text-pearl-muted">
                  질문 임베딩 → 벡터 검색 (Top-5) → LLM 생성
                </p>
              </div>
              <div className="rounded-lg border border-gold/30 bg-gold/5 p-4">
                <p className="mb-1 text-sm font-medium text-gold">
                  Advanced RAG (HyDE + Reranking)
                </p>
                <p className="text-xs text-pearl-muted">
                  HyDE 생성 → 가상 문서 임베딩 → 벡터 검색 (Top-20) → LLM
                  리랭킹 → Top-5 → LLM 생성
                </p>
              </div>
            </div>
          </div>
        )}

        <CompareView result={compareResult} isLoading={isComparing} />
      </main>
    </div>
  );
}
