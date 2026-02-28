"use client";

import { useEffect } from "react";
import { useVectorSearch } from "@/hooks/useVectorSearch";
import DocumentInput from "@/components/DocumentInput";
import EmbeddingPanel from "@/components/EmbeddingPanel";
import QuestionInput from "@/components/QuestionInput";
import ComparePanel from "@/components/ComparePanel";
import StatsBar from "@/components/StatsBar";
import VectorViz from "@/components/VectorViz";
import CollectionInfo from "@/components/CollectionInfo";

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
    memoryResult,
    vectordbResult,
    isSearching,
    search,
    vizData,
    collections,
    fetchCollections,
    deleteCollection,
    selectCollection,
  } = useVectorSearch();

  useEffect(() => {
    fetchSamples();
    fetchCollections();
  }, [fetchSamples, fetchCollections]);

  const hasResults = memoryResult || vectordbResult;

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
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="font-serif text-2xl font-light tracking-wide text-pearl">
              Why Vector DB?
            </h1>
            <p className="mt-0.5 text-[11px] tracking-wide text-pearl-muted">
              인메모리 vs Vector DB 검색을 직접 비교해보세요
            </p>
          </div>
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            disabled={isEmbedding || isSearching}
            className="appearance-none rounded-xl border border-stroke bg-base-50 px-3.5 py-1.5 pr-8 text-xs text-pearl-dim transition-all hover:border-stroke-hover focus:border-gold-dim focus:outline-none disabled:opacity-30"
          >
            <option value="gpt-4o-mini">GPT-4o Mini</option>
            <option value="gpt-4o">GPT-4o</option>
          </select>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-5xl space-y-6 px-6 py-8">
        {/* Step 1: Document Input */}
        <DocumentInput
          document={document}
          setDocument={setDocument}
          samples={samples}
          onLoadSample={loadSample}
          disabled={isEmbedding || isSearching}
        />

        {/* Step 2: Embedding */}
        <EmbeddingPanel
          onEmbed={embedDocument}
          embedResult={embedResult}
          isEmbedding={isEmbedding}
          hasDocument={document.length > 0}
        />

        {/* Collections — moved up so user can select before asking */}
        <CollectionInfo
          collections={collections}
          activeCollection={embedResult?.collection_name ?? null}
          onSelect={selectCollection}
          onDelete={deleteCollection}
        />

        {/* Step 3: Question */}
        <QuestionInput
          onSubmit={search}
          disabled={isSearching}
          hasDocument={true}
          hasCollection={!!embedResult}
        />

        {/* Stats Bar — only when both results exist for comparison */}
        {memoryResult && vectordbResult && (
          <StatsBar
            memoryResult={memoryResult}
            vectordbResult={vectordbResult}
          />
        )}

        {/* Compare Panel */}
        <ComparePanel
          memoryResult={memoryResult}
          vectordbResult={vectordbResult}
          isLoading={isSearching}
          hasDocument={document.length > 0}
        />

        {/* Vector Visualization */}
        {vizData && vectordbResult && (
          <VectorViz
            vizData={vizData}
            usedChunks={vectordbResult.used_chunks}
          />
        )}

      </main>
    </div>
  );
}
