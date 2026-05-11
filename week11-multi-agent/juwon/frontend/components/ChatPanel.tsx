"use client";

import { useRef, useState } from "react";

type Message = {
  role:    "user" | "ai";
  content: string;
};

const SUGGESTIONS = [
  "이번주 가장 주목할 레포 하나만 뽑아줘",
  "보안 관련 레포만 정리해줘",
  "비전공자도 이해할 수 있게 쉽게 설명해줘",
  "이 트렌드가 내년에도 계속될까?",
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
      const res = await fetch("http://localhost:8000/api/chat", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ message: question, report }),
      });
      const data = await res.json();
      setMessages([...next, { role: "ai", content: data.reply }]);
    } catch {
      setMessages([...next, { role: "ai", content: "오류가 발생했어요. 다시 시도해주세요." }]);
    } finally {
      setLoading(false);
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
    }
  };

  return (
    <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5">
      <h2 className="text-lg font-bold mb-3 text-[#c9d1d9]">💬 분석 결과에 대해 질문하기</h2>

      {/* 추천 질문 */}
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

      {/* 대화 목록 */}
      {messages.length > 0 && (
        <div className="space-y-3 mb-4 max-h-80 overflow-y-auto">
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[80%] rounded-lg px-4 py-2 text-xs whitespace-pre-wrap leading-relaxed ${
                m.role === "user"
                  ? "bg-[#1c2d40] text-[#c9d1d9]"
                  : "bg-[#21262d] text-[#8b949e]"
              }`}>
                {m.role === "ai" && <span className="font-bold text-[#58a6ff] block mb-1">AI</span>}
                {m.content}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-[#21262d] rounded-lg px-4 py-2 text-xs text-[#8b949e]">
                답변 작성 중...
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      )}

      {/* 입력창 */}
      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send(input)}
          placeholder="분석 결과에 대해 궁금한 것을 물어보세요..."
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
