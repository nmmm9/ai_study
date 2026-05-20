"use client";

import { useRef, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Step    = { tool: string; input: string };
type Message = { role: "user" | "ai"; content: string; steps?: Step[] };

const TOOL_LABELS: Record<string, string> = {
  search_trend_history:  "과거 트렌드 검색",
  search_repo_analysis:  "레포 분석 검색",
  get_recent_trends:     "최근 트렌드 조회",
};

const SUGGESTIONS = [
  "이번주 가장 주목할 레포 하나만 뽑아줘",
  "지난 분석과 비교해서 뭐가 달라졌어?",
  "AI 관련 레포 이전에도 나왔던 게 있어?",
  "보안 관련 트렌드 최근 흐름은?",
];

export default function ChatPanel({ report }: { report: any }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input,    setInput]    = useState("");
  const [loading,  setLoading]  = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const send = async (text: string) => {
    const question = text.trim();
    if (!question || loading) return;

    const next = [...messages, { role: "user" as const, content: question }];
    setMessages(next);
    setInput("");
    setLoading(true);

    try {
      const res  = await fetch(`${API}/api/chat`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ message: question, report }),
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
      <div className="flex items-center gap-2 mb-3">
        <h2 className="text-lg font-bold text-[#c9d1d9]">💬 Agentic RAG 채팅</h2>
        <span className="text-xs bg-[#1c2d40] text-[#58a6ff] border border-[#1f6feb] rounded-full px-2 py-0.5">
          과거 분석 자동 검색
        </span>
      </div>

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
        <div className="space-y-3 mb-4 max-h-96 overflow-y-auto">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[85%] space-y-1.5`}>
                {/* 에이전트 도구 호출 단계 표시 */}
                {m.role === "ai" && m.steps && m.steps.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-1">
                    {m.steps.map((s, j) => (
                      <span key={j} className="text-xs bg-[#0d1117] border border-[#30363d] text-[#484f58] rounded px-2 py-0.5">
                        🔍 {TOOL_LABELS[s.tool] ?? s.tool}{s.input ? `: "${s.input}"` : ""}
                      </span>
                    ))}
                  </div>
                )}
                <div className={`rounded-lg px-4 py-2 text-xs whitespace-pre-wrap leading-relaxed ${
                  m.role === "user"
                    ? "bg-[#1c2d40] text-[#c9d1d9]"
                    : "bg-[#21262d] text-[#8b949e]"
                }`}>
                  {m.role === "ai" && <span className="font-bold text-[#58a6ff] block mb-1">AI</span>}
                  {m.content}
                </div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-[#21262d] rounded-lg px-4 py-2 text-xs text-[#8b949e]">
                <span className="animate-pulse">RAG 검색 중...</span>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      )}

      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send(input)}
          placeholder="과거 트렌드 포함해서 질문하면 에이전트가 직접 검색해요..."
          className="flex-1 bg-[#0d1117] border border-[#30363d] rounded-lg px-3 py-2 text-sm text-white placeholder-[#484f58] focus:outline-none focus:border-[#58a6ff]"
          disabled={loading}
        />
        <button onClick={() => send(input)} disabled={loading || !input.trim()}
          className="bg-[#238636] hover:bg-[#2ea043] disabled:opacity-50 text-white text-sm font-semibold px-4 rounded-lg transition">
          전송
        </button>
      </div>
    </div>
  );
}
