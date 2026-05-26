"use client";

import { useEffect, useRef } from "react";
import { useChat } from "@/hooks/useChat";
import ChatMessage from "@/components/ChatMessage";
import ChatInput from "@/components/ChatInput";
import AgentGraph from "@/components/AgentGraph";
import SessionSidebar from "@/components/SessionSidebar";

const EXAMPLES = [
  "서울 날씨 + 어제 KBO 결과 + 강남구 맛집까지 한 번에",
  "삼성전자 주가 + 관련 최신 뉴스 + 같은 업종 종목 비교",
  "타이레놀 안전 정보 + 인근 약국 검색 + 회수 이력 확인",
  "부산 LH 청약 공고 + 부산 주차장 + 부산 날씨",
  "어제 KBO + KBL + LCK 결과 종합",
  "에어팟 프로 가격 비교 + '딥러닝' 도서 검색 + 긱뉴스 최신 AI 글",
];

export default function Home() {
  const {
    messages, isStreaming, model, setModel,
    sendMessage, stopStreaming, graphState,
    threadId, sessions, newChat, loadThread, deleteSession,
  } = useChat();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex h-screen bg-base">
      {/* Session sidebar */}
      <div className="w-[230px] flex-shrink-0 border-r border-stroke/30 bg-base-50/20">
        <SessionSidebar
          sessions={sessions}
          activeThreadId={threadId}
          onSelect={loadThread}
          onNew={newChat}
          onDelete={deleteSession}
        />
      </div>

      {/* Main chat area */}
      <div className="flex flex-1 flex-col min-w-0">
        <header className="flex items-center justify-between border-b border-stroke/30 px-6 py-3">
          <div>
            <h1 className="text-[15px] font-semibold tracking-tight text-pearl">
              K-Agent
              <span className="text-purple text-[11px] font-normal ml-1.5">Plan-and-Execute</span>
            </h1>
            <p className="text-[10px] text-pearl-muted/60">Planner → Executor ⇄ Replanner → Writer ⇄ Critic</p>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="appearance-none rounded-lg bg-base-200/40 px-3 py-1.5 text-[12px] text-pearl-dim focus:outline-none"
              title="auto = Supervisor에 nano, Agent/Writer에 mini (균형 모드)"
            >
              <option value="auto">Auto (균형: nano + mini)</option>
              <option value="gpt-5.5-nano">5.5-nano (전부)</option>
              <option value="gpt-5.5-mini">5.5-mini (전부)</option>
              <option value="gpt-5.5">5.5 (고품질)</option>
              <option value="gpt-5-mini">5-mini (레거시)</option>
              <option value="gpt-4o-mini">4o-mini (8주차 호환)</option>
            </select>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center px-6">
              <p className="mb-1 text-[11px] uppercase tracking-[0.3em] text-pearl-muted/40">Plan-and-Execute · Multi-step</p>
              <h2 className="mb-3 font-serif text-4xl font-light tracking-tight text-pearl">K-Agent</h2>
              <p className="mb-2 text-sm text-pearl-muted">Planner가 질문을 단계별 plan으로 분해하고 Executor가 차례로 실행</p>
              <p className="mb-1 text-[11px] text-pearl-muted/50">매 step 후 Replanner가 continue / revise / finish 결정</p>
              <p className="mb-10 text-[11px] text-pearl-muted/50">최종 답변은 Writer + Critic 으로 검수 (10주차 재사용)</p>
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

      {/* Graph sidebar */}
      <div className="w-[420px] flex-shrink-0 border-l border-stroke/30 bg-base-50/30">
        <AgentGraph state={graphState} isStreaming={isStreaming} />
      </div>
    </div>
  );
}
