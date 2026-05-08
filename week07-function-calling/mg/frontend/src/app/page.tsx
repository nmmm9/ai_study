"use client";

import { useEffect, useRef } from "react";
import { useChat } from "@/hooks/useChat";
import ChatMessage from "@/components/ChatMessage";
import ChatInput from "@/components/ChatInput";

const EXAMPLES = [
  "내 택배 어디야? 운송장 6123456789",
  "오늘 미세먼지 어때?",
  "이번 주 로또 당첨번호?",
  "어제 KBO 야구 결과 알려줘",
  "강남역 근처 맛집 추천",
  "지금 몇시야?",
];

export default function Home() {
  const { messages, isStreaming, model, setModel, sendMessage, stopStreaming, clearChat } = useChat();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex h-screen flex-col bg-base">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-stroke/30 px-6 py-3">
        <div>
          <h1 className="text-[15px] font-semibold tracking-tight text-pearl">K-Agent</h1>
          <p className="text-[10px] text-pearl-muted/60">한국 생활 AI 에이전트 — 18개 도구</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="appearance-none rounded-lg bg-base-200/40 px-3 py-1.5 text-[12px] text-pearl-dim focus:outline-none"
          >
            <option value="gpt-4o-mini">GPT-4o Mini</option>
            <option value="gpt-4o">GPT-4o</option>
          </select>
          <button
            onClick={clearChat}
            className="rounded-md px-2.5 py-1 text-[11px] text-pearl-muted hover:bg-base-200 hover:text-pearl-dim"
          >
            새 채팅
          </button>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center px-6">
            <p className="mb-1 text-[11px] uppercase tracking-[0.3em] text-pearl-muted/40">
              Function Calling Agent
            </p>
            <h2 className="mb-3 font-serif text-4xl font-light tracking-tight text-pearl">
              K-Agent
            </h2>
            <p className="mb-10 text-sm text-pearl-muted">
              택배 추적, 미세먼지, 야구, 맛집, 로또, 법률... 뭐든 물어보세요
            </p>
            <div className="grid max-w-xl grid-cols-2 gap-2.5">
              {EXAMPLES.map((q) => (
                <button
                  key={q}
                  onClick={() => sendMessage(q)}
                  className="rounded-xl border border-stroke/60 px-5 py-3.5 text-left text-[13px] leading-snug text-pearl-dim/80 transition-all hover:border-gold/30 hover:text-pearl-dim"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div>
            {messages.map((msg) => (
              <ChatMessage key={msg.id} message={msg} />
            ))}
            <div ref={bottomRef} className="h-4" />
          </div>
        )}
      </div>

      <ChatInput onSend={sendMessage} onStop={stopStreaming} isStreaming={isStreaming} />
    </div>
  );
}
