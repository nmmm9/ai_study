"use client";

import { useRef, useState } from "react";

type Step    = { tool: string; input: string };
type Message = { role: "user" | "ai"; content: string; steps?: Step[] };

const SUGGESTIONS = [
  "이번주 가장 주목할 레포 하나만 추천해줘",
  "AI 트렌드가 지난번과 비교해서 어떻게 달라졌어?",
  "보안 관련 레포만 정리해줘",
  "이 트렌드가 6개월 후에도 계속될까?",
];

const TOOL_LABEL: Record<string, string> = {
  search_trend_history:  "🔍 과거 트렌드 검색",
  get_recent_trends:     "📅 최근 트렌드 조회",
  search_repo_analysis:  "📦 레포 분석 검색",
};

export default function ChatPanel({ report }: { report: any }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input,    setInput]    = useState("");
  const [loading,  setLoading]  = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const send = async (text: string) => {
    const q = text.trim();
    if (!q || loading) return;
    const next: Message[] = [...messages, { role: "user", content: q }];
    setMessages(next);
    setInput("");
    setLoading(true);
    try {
      const res  = await fetch("http://localhost:8000/api/chat", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: q, report }),
      });
      const data = await res.json();
      setMessages([...next, { role: "ai", content: data.reply, steps: data.steps ?? [] }]);
    } catch {
      setMessages([...next, { role: "ai", content: "오류가 발생했어요. 다시 시도해주세요." }]);
    } finally {
      setLoading(false);
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
    }
  };

  return (
    <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5">
      <h2 className="text-lg font-bold mb-1 text-[#c9d1d9]">💬 Agentic RAG 채팅</h2>
      <p className="text-xs text-[#8b949e] mb-4">에이전트가 스스로 판단해서 과거 데이터를 검색합니다</p>

      {messages.length === 0 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {SUGGESTIONS.map((s) => (
            <button key={s} onClick={() => send(s)}
              className="text-xs bg-[#21262d] hover:bg-[#30363d] text-[#8b949e] rounded-full px-3 py-1.5 transition">
              {s}
            </button>
          ))}
        </div>
      )}

      {messages.length > 0 && (
        <div className="space-y-4 mb-4 max-h-96 overflow-y-auto pr-1">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              {m.role === "ai" ? (
                <div className="max-w-[85%] space-y-2">
                  {(m.steps ?? []).length > 0 && (
                    <div className="bg-[#0d1117] border border-[#30363d] rounded-lg p-3 text-xs space-y-1">
                      <p className="text-[#58a6ff] font-semibold mb-1">🤖 에이전트 사고 과정 ({m.steps!.length}회 도구 호출)</p>
                      {m.steps!.map((s, j) => (
                        <div key={j} className="flex items-start gap-2 text-[#8b949e]">
                          <span className="text-[#3fb950] shrink-0">{TOOL_LABEL[s.tool] ?? s.tool}</span>
                          <span className="truncate opacity-70">← {s.input}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  <div className="bg-[#21262d] rounded-lg px-4 py-3 text-xs text-[#c9d1d9] whitespace-pre-wrap leading-relaxed">
                    <span className="font-bold text-[#58a6ff] block mb-1">AI</span>
                    {m.content}
                  </div>
                </div>
              ) : (
                <div className="max-w-[80%] bg-[#1c2d40] rounded-lg px-4 py-2 text-xs text-[#c9d1d9] whitespace-pre-wrap leading-relaxed">
                  {m.content}
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-[#21262d] rounded-lg px-4 py-2 text-xs text-[#8b949e]">에이전트 추론 중...</div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      )}

      <div className="flex gap-2">
        <input value={input} onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send(input)}
          placeholder="과거 데이터와 비교해서 물어보세요..."
          className="flex-1 bg-[#0d1117] border border-[#30363d] rounded-lg px-3 py-2 text-sm text-white placeholder-[#484f58] focus:outline-none focus:border-[#58a6ff]"
          disabled={loading} />
        <button onClick={() => send(input)} disabled={loading || !input.trim()}
          className="bg-[#238636] hover:bg-[#2ea043] disabled:opacity-50 text-white text-sm font-semibold px-4 rounded-lg transition">
          전송
        </button>
      </div>
    </div>
  );
}
