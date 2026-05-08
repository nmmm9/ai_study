"use client";

import { useState, useRef, useEffect } from "react";
import type { ChatMessage, RagResponse, SourceChunk } from "@/types/rag";

interface ChatPanelProps {
  messages: ChatMessage[];
  latestSources: RagResponse | null;
  isChatting: boolean;
  hasCollection: boolean;
  onSend: (message: string) => void;
  onClear: () => void;
}

export default function ChatPanel({
  messages,
  latestSources,
  isChatting,
  hasCollection,
  onSend,
  onClear,
}: ChatPanelProps) {
  const [input, setInput] = useState("");
  const [showSources, setShowSources] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, isChatting]);

  const handleSubmit = () => {
    if (input.trim() && !isChatting && hasCollection) {
      onSend(input.trim());
      setInput("");
    }
  };

  return (
    <section className="animate-fade-in-up rounded-2xl border border-stroke bg-base-50">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-stroke px-5 py-3">
        <div>
          <h2 className="font-serif text-sm font-light text-pearl">
            RAG 챗봇
          </h2>
          <p className="text-[10px] text-pearl-muted">
            문서 기반 멀티턴 대화
          </p>
        </div>
        <div className="flex items-center gap-2">
          {latestSources && (
            <button
              onClick={() => setShowSources(!showSources)}
              className="rounded-lg border border-stroke px-2.5 py-1 text-[10px] text-pearl-muted transition-all hover:border-gold/30 hover:text-pearl"
            >
              {showSources ? "소스 숨기기" : "소스 보기"}
            </button>
          )}
          {messages.length > 0 && (
            <button
              onClick={onClear}
              className="rounded-lg border border-stroke px-2.5 py-1 text-[10px] text-bad/60 transition-all hover:border-bad/30 hover:text-bad"
            >
              초기화
            </button>
          )}
        </div>
      </div>

      <div className="flex">
        {/* Chat area */}
        <div className={`flex flex-1 flex-col ${showSources ? "border-r border-stroke" : ""}`}>
          {/* Messages */}
          <div
            ref={scrollRef}
            className="flex-1 space-y-3 overflow-y-auto px-5 py-4"
            style={{ maxHeight: "400px", minHeight: "200px" }}
          >
            {messages.length === 0 && !isChatting && (
              <div className="flex h-full items-center justify-center py-12">
                <p className="text-xs text-pearl-muted/50">
                  {hasCollection
                    ? "문서에 대해 질문해보세요"
                    : "먼저 컬렉션을 선택하세요"}
                </p>
              </div>
            )}

            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-2.5 ${
                    msg.role === "user"
                      ? "rounded-br-md bg-gold/15 text-pearl"
                      : "rounded-bl-md border border-stroke bg-base-100 text-pearl-dim"
                  }`}
                >
                  <p className="whitespace-pre-wrap text-[13px] leading-[1.7]">
                    {msg.content}
                  </p>
                </div>
              </div>
            ))}

            {isChatting && (
              <div className="flex justify-start">
                <div className="rounded-2xl rounded-bl-md border border-stroke bg-base-100 px-4 py-3">
                  <div className="flex items-center gap-1.5">
                    <div className="h-1.5 w-1.5 animate-pulse rounded-full bg-gold" />
                    <div className="h-1.5 w-1.5 animate-pulse rounded-full bg-gold" style={{ animationDelay: "0.2s" }} />
                    <div className="h-1.5 w-1.5 animate-pulse rounded-full bg-gold" style={{ animationDelay: "0.4s" }} />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <div className="border-t border-stroke px-5 py-3">
            {latestSources && (
              <div className="mb-2 flex flex-wrap items-center gap-3">
                <span className="text-[10px] text-pearl-muted">
                  마지막 응답: ${latestSources.cost_usd.toFixed(4)} ·{" "}
                  {latestSources.total_tokens} tokens ·{" "}
                  {(latestSources.timing.total_ms / 1000).toFixed(1)}s
                </span>
              </div>
            )}
            <div className="flex gap-3">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
                placeholder={
                  hasCollection
                    ? "메시지를 입력하세요..."
                    : "먼저 컬렉션을 선택하세요"
                }
                disabled={isChatting || !hasCollection}
                className="flex-1 rounded-xl border border-stroke bg-base px-4 py-2.5 text-sm text-pearl placeholder:text-pearl-muted/50 focus:border-gold-dim focus:outline-none disabled:opacity-30"
              />
              <button
                onClick={handleSubmit}
                disabled={isChatting || !input.trim() || !hasCollection}
                className="rounded-xl bg-gold px-5 py-2.5 text-xs font-medium text-base transition-all hover:bg-gold-bright active:scale-95 disabled:opacity-30"
              >
                {isChatting ? (
                  <span className="flex items-center gap-1.5">
                    <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-base border-t-transparent" />
                  </span>
                ) : (
                  "전송"
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Sources sidebar */}
        {showSources && latestSources && (
          <div className="w-72 overflow-y-auto px-4 py-4" style={{ maxHeight: "500px" }}>
            <p className="mb-2 text-[10px] tracking-wider text-pearl-muted uppercase">
              참고 문서 ({latestSources.sources.length}개)
            </p>
            <div className="space-y-2">
              {latestSources.sources.map((s: SourceChunk, i: number) => (
                <div
                  key={i}
                  className="rounded-lg border border-stroke bg-base-100 px-3 py-2"
                >
                  <div className="mb-1 flex items-center gap-2">
                    <span className="rounded bg-gold/10 px-1.5 py-0.5 text-[10px] font-bold text-gold">
                      [{i + 1}]
                    </span>
                    <span className="text-[10px] text-pearl-muted">
                      {(s.score * 100).toFixed(1)}%
                    </span>
                  </div>
                  <p className="line-clamp-4 text-[10px] leading-relaxed text-pearl-dim">
                    {s.text}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
