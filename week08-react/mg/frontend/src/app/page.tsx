"use client";

import { useEffect, useRef, useMemo } from "react";
import { useChat } from "@/hooks/useChat";
import ChatMessage from "@/components/ChatMessage";
import ChatInput from "@/components/ChatInput";
import ToolCharacters from "@/components/ToolCharacters";

const EXAMPLES = [
  "독산점에 피크닉 매트 재고 있어?",
  "이번 주 로또 당첨번호?",
  "안양 미세먼지 어때?",
  "어제 KBO 야구 결과",
  "강남역 근처 맛집 추천",
  "훈민정음 조선왕조실록에서 찾아줘",
];

export default function Home() {
  const { messages, isStreaming, model, setModel, sendMessage, stopStreaming, clearChat } = useChat();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Extract currently active tools from the latest assistant message
  const activeTools = useMemo(() => {
    const lastAssistant = [...messages].reverse().find(m => m.role === "assistant" && m.isStreaming);
    if (!lastAssistant?.steps) return [];
    // Get tools from action steps that don't have a corresponding observation yet
    const actionTools = lastAssistant.steps
      .filter(s => s.type === "action")
      .map(s => s.tool || "");
    const observedTools = lastAssistant.steps
      .filter(s => s.type === "observation")
      .map(s => s.tool || "");
    // Currently active = last action tool if no observation yet
    const unobserved = actionTools.filter((t, i) => i >= observedTools.length);
    // Also include recently observed (for dance animation)
    const recent = actionTools.slice(-2);
    return [...new Set([...unobserved, ...recent])];
  }, [messages]);

  return (
    <div className="flex h-screen bg-base">
      {/* Main chat area */}
      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-stroke/30 px-6 py-3">
          <div>
            <h1 className="text-[15px] font-semibold tracking-tight text-pearl">
              K-Agent <span className="text-purple text-[11px] font-normal ml-1.5">ReAct</span>
            </h1>
            <p className="text-[10px] text-pearl-muted/60">Thought → Action → Observation → Answer</p>
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
            <button onClick={clearChat} className="rounded-md px-2.5 py-1 text-[11px] text-pearl-muted hover:bg-base-200">새 채팅</button>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center px-6">
              <p className="mb-1 text-[11px] uppercase tracking-[0.3em] text-pearl-muted/40">ReAct Agent</p>
              <h2 className="mb-3 font-serif text-4xl font-light tracking-tight text-pearl">K-Agent</h2>
              <p className="mb-2 text-sm text-pearl-muted">AI의 추론 과정을 실시간으로 확인하세요</p>
              <p className="mb-10 text-[11px] text-pearl-muted/50">질문하면 오른쪽 캐릭터가 무대로 나와 춤을 춥니다</p>
              <div className="grid max-w-xl grid-cols-2 gap-2.5">
                {EXAMPLES.map((q) => (
                  <button
                    key={q}
                    onClick={() => sendMessage(q)}
                    className="rounded-xl border border-stroke/60 px-5 py-3.5 text-left text-[13px] leading-snug text-pearl-dim/80 hover:border-gold/30 hover:text-pearl-dim transition-all"
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

      {/* Character sidebar */}
      <div className="w-[220px] border-l border-stroke/30 bg-base-50/30">
        <ToolCharacters activeTools={activeTools} />
      </div>
    </div>
  );
}
