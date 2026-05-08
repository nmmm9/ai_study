"use client";

import { useEffect, useRef } from "react";
import { useChat } from "@/hooks/useChat";
import ChatMessage from "@/components/ChatMessage";
import ChatInput from "@/components/ChatInput";
import AgentGraph from "@/components/AgentGraph";
import SessionSidebar from "@/components/SessionSidebar";

const EXAMPLES = [
  "오늘 서울 날씨 + 미세먼지 어때?",
  "삼성전자 주가 알려줘",
  "긱뉴스 최신글 + KBO 어제 결과",
  "강남구 생활쓰레기 배출 요일",
  "타이레놀 안전 정보 + 부산 LH 공고",
  "에어팟 프로 가격 비교 + 도서 '딥러닝' 검색",
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
              <span className="text-purple text-[11px] font-normal ml-1.5">LangGraph Multi-Agent + Memory</span>
            </h1>
            <p className="text-[10px] text-pearl-muted/60">Supervisor → Domain Agents → Writer · Checkpointer 메모리</p>
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
              <p className="mb-1 text-[11px] uppercase tracking-[0.3em] text-pearl-muted/40">LangGraph Multi-Agent + Checkpointer</p>
              <h2 className="mb-3 font-serif text-4xl font-light tracking-tight text-pearl">K-Agent</h2>
              <p className="mb-2 text-sm text-pearl-muted">Supervisor가 질문을 분석해 도메인 전문 에이전트로 라우팅</p>
              <p className="mb-1 text-[11px] text-pearl-muted/50">오른쪽 그래프에서 에이전트 간 흐름이 실시간으로 표시됩니다</p>
              <p className="mb-10 text-[11px] text-pearl-muted/50">왼쪽 사이드바에서 이전 대화를 이어갈 수 있습니다 (LangGraph Checkpointer)</p>
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
