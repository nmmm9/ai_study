"use client";

import { useEffect } from "react";
import { useRagPipeline } from "@/hooks/useRagPipeline";
import DocumentInput from "@/components/DocumentInput";
import CollectionPanel from "@/components/CollectionPanel";
import QuestionInput from "@/components/QuestionInput";
import PipelineViz from "@/components/PipelineViz";
import AnswerCard from "@/components/AnswerCard";
import ChatPanel from "@/components/ChatPanel";

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
    ragResult,
    isSearching,
    search,
    chatMessages,
    chatSources,
    isChatting,
    sendChatMessage,
    clearChat,
    collections,
    fetchCollections,
    selectCollection,
    deleteCollection,
  } = useRagPipeline();

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
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="font-serif text-2xl font-light tracking-wide text-pearl">
              RAG Pipeline
            </h1>
            <p className="mt-0.5 text-[11px] tracking-wide text-pearl-muted">
              기본 RAG 파이프라인 & 문서 기반 챗봇
            </p>
          </div>
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            disabled={isEmbedding || isSearching || isChatting}
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
          disabled={isEmbedding || isSearching || isChatting}
        />

        {/* Step 2: Collection Management */}
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

        {/* Step 3: Single Q&A */}
        <QuestionInput
          onSubmit={search}
          disabled={isSearching}
          hasCollection={!!embedResult}
        />

        {/* Pipeline Steps */}
        <PipelineViz
          steps={ragResult?.steps ?? null}
          isLoading={isSearching}
        />

        {/* Answer + Sources */}
        <AnswerCard result={ragResult} isLoading={isSearching} />

        {/* Divider */}
        {embedResult && (
          <div className="flex items-center gap-4 py-2">
            <div className="h-px flex-1 bg-stroke" />
            <span className="text-[10px] tracking-widest text-pearl-muted uppercase">
              챗봇 모드
            </span>
            <div className="h-px flex-1 bg-stroke" />
          </div>
        )}

        {/* Step 4: Chat */}
        {embedResult && (
          <ChatPanel
            messages={chatMessages}
            latestSources={chatSources}
            isChatting={isChatting}
            hasCollection={!!embedResult}
            onSend={sendChatMessage}
            onClear={clearChat}
          />
        )}
      </main>
    </div>
  );
}
