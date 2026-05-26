"use client";

import { useEffect, useRef } from "react";
import { useChat } from "@/hooks/useChat";
import ChatMessage from "@/components/ChatMessage";
import ChatInput from "@/components/ChatInput";
import AgentGraph from "@/components/AgentGraph";
import SessionSidebar from "@/components/SessionSidebar";
import DocumentPanel from "@/components/DocumentPanel";

const EXAMPLES = [
  "업로드한 문서에서 핵심 내용 3가지 요약",
  "이 문서에 OpenAI 가 언급된 부분 찾아줘",
  "문서 기반으로 설명 + 서울 날씨도 같이",
  "삼성전자 주가 + 관련 최신 뉴스",
  "타이레놀 안전 정보 + 회수 이력 확인",
  "어제 KBO + KBL 결과 종합",
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
      <div className="w-[210px] flex-shrink-0 border-r border-stroke/30 bg-base-50/20">
        <SessionSidebar
          sessions={sessions}
          activeThreadId={threadId}
          onSelect={loadThread}
          onNew={newChat}
          onDelete={deleteSession}
        />
      </div>

      {/* Documents sidebar */}
      <div className="w-[220px] flex-shrink-0 border-r border-stroke/30 bg-base-50/30">
        <DocumentPanel />
      </div>

      {/* Main chat area */}
      <div className="flex flex-1 flex-col min-w-0">
        <header className="flex items-center justify-between border-b border-stroke/30 px-6 py-3">
          <div>
            <h1 className="text-[15px] font-semibold tracking-tight text-pearl">
              K-Agent
              <span className="text-purple text-[11px] font-normal ml-1.5">Agentic RAG</span>
            </h1>
            <p className="text-[10px] text-pearl-muted/60">Plan-Execute + Retriever 자기 평가 루프 + Critic</p>
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
              <p className="mb-1 text-[11px] uppercase tracking-[0.3em] text-pearl-muted/40">Agentic RAG · Self-Eval Retrieval</p>
              <h2 className="mb-3 font-serif text-4xl font-light tracking-tight text-pearl">K-Agent</h2>
              <p className="mb-2 text-sm text-pearl-muted">문서를 업로드하면 LLM 이 검색을 직접 운영합니다</p>
              <p className="mb-1 text-[11px] text-pearl-muted/50">쿼리 재작성 + 결과 자기 평가 (1~5점) + 점수 부족 시 재검색</p>
              <p className="mb-10 text-[11px] text-pearl-muted/50">답변에는 인용 마커 [1], [2] 가 자동으로 붙습니다</p>
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

      {/* Graph sidebar (오른쪽) */}
      <div className="w-[440px] flex-shrink-0 border-l border-stroke/30 bg-base-50/30">
        <AgentGraph state={graphState} isStreaming={isStreaming} />
      </div>
    </div>
  );
}
