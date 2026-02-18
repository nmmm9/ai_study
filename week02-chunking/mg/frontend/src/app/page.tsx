"use client";

import { useEffect } from "react";
import { useCompare } from "@/hooks/useCompare";
import DocumentInput from "@/components/DocumentInput";
import QuestionInput from "@/components/QuestionInput";
import ComparePanel from "@/components/ComparePanel";
import StatsBar from "@/components/StatsBar";
import ChunkViewer from "@/components/ChunkViewer";

export default function Home() {
  const {
    document,
    setDocument,
    selectedModel,
    setSelectedModel,
    samples,
    fetchSamples,
    loadSample,
    rawResult,
    chunkedResult,
    isLoading,
    compare,
  } = useCompare();

  useEffect(() => {
    fetchSamples();
  }, [fetchSamples]);

  const hasResults = rawResult && chunkedResult;

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
              Why Chunking?
            </h1>
            <p className="mt-0.5 text-[11px] tracking-wide text-pearl-muted">
              청킹의 필요성을 직접 비교해보세요
            </p>
          </div>
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            disabled={isLoading}
            className="appearance-none rounded-xl border border-stroke bg-base-50 px-3.5 py-1.5 pr-8 text-xs text-pearl-dim transition-all hover:border-stroke-hover focus:border-gold-dim focus:outline-none disabled:opacity-30"
          >
            <option value="gpt-4o-mini">GPT-4o Mini</option>
            <option value="gpt-4o">GPT-4o</option>
          </select>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-5xl space-y-6 px-6 py-8">
        {/* Document Input */}
        <DocumentInput
          document={document}
          setDocument={setDocument}
          samples={samples}
          onLoadSample={loadSample}
          disabled={isLoading}
        />

        {/* Question Input */}
        <QuestionInput
          onSubmit={compare}
          disabled={isLoading}
          hasDocument={document.length > 0}
        />

        {/* Stats Bar */}
        {hasResults && !rawResult.error && (
          <StatsBar
            rawStats={rawResult.stats}
            chunkedStats={chunkedResult.stats}
          />
        )}

        {/* Compare Panel */}
        <ComparePanel
          rawResult={rawResult}
          chunkedResult={chunkedResult}
          isLoading={isLoading}
        />

        {/* Chunk Viewer */}
        {chunkedResult && (
          <ChunkViewer
            totalChunks={chunkedResult.chunks.total_count}
            usedChunks={chunkedResult.chunks.used}
          />
        )}
      </main>
    </div>
  );
}
