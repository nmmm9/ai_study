"use client";

import { useEffect, useRef } from "react";
import { useChat } from "@/hooks/useChat";
import Sidebar from "@/components/Sidebar";
import ChatMessage from "@/components/ChatMessage";
import ChatInput from "@/components/ChatInput";

export default function Home() {
  const {
    sessions, activeSession, isStreaming, isUploading, samples, model,
    setModel, fetchSamples, initDefault, newSession, switchSession,
    deleteSession, uploadFile, addSampleToSession, sendMessage, stopStreaming, editMessage,
  } = useChat();

  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchSamples();
    initDefault();
  }, [fetchSamples, initDefault]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [activeSession.messages]);

  const hasCollections = activeSession.collections.length > 0;

  return (
    <div className="flex h-screen">
      <Sidebar
        sessions={sessions}
        activeSession={activeSession}
        samples={samples}
        model={model}
        isUploading={isUploading}
        onNewSession={newSession}
        onSwitchSession={switchSession}
        onDeleteSession={deleteSession}
        onUploadFile={uploadFile}
        onAddSample={addSampleToSession}
        onSetModel={setModel}
      />

      <div className="flex flex-1 flex-col bg-base">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto">
          {activeSession.messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center px-6">
              <p className="mb-1 text-[11px] uppercase tracking-[0.3em] text-pearl-muted/40">
                Hybrid Search + Reranking
              </p>
              <h2 className="mb-3 font-serif text-4xl font-light tracking-tight text-pearl">
                무엇이든 물어보세요
              </h2>
              <p className="mb-2 text-sm text-pearl-muted">
                {activeSession.fileNames.join(", ")} 기반으로 답변합니다
              </p>
              <p className="mb-10 text-[11px] text-pearl-muted/50">
                사이드바에서 파일을 추가하면 해당 문서도 함께 검색합니다
              </p>
              {hasCollections && (
                <div className="grid max-w-xl grid-cols-2 gap-2.5">
                  {[
                    "스타트업이란 무엇인가?",
                    "투자 유치는 어떤 단계로 진행돼?",
                    "사업계획서에 꼭 들어가야 할 내용은?",
                    "법인 설립은 어떻게 해?",
                  ].map((q) => (
                    <button
                      key={q}
                      onClick={() => sendMessage(q)}
                      className="rounded-xl border border-stroke/60 px-5 py-3.5 text-left text-[13px] leading-snug text-pearl-dim/80 transition-all hover:border-gold/30 hover:text-pearl-dim"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div>
              {activeSession.messages.map((msg) => (
                <ChatMessage
                  key={msg.id}
                  message={msg}
                  onEdit={msg.role === "user" && !isStreaming ? editMessage : undefined}
                />
              ))}
              <div ref={bottomRef} className="h-4" />
            </div>
          )}
        </div>

        <ChatInput
          onSend={sendMessage}
          onStop={stopStreaming}
          isStreaming={isStreaming}
          disabled={!hasCollections}
        />
      </div>
    </div>
  );
}
