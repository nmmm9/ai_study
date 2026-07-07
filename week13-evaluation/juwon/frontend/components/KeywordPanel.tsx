"use client";

import { useEffect, useState } from "react";

export default function KeywordPanel() {
  const [keywords, setKeywords] = useState<string[]>([]);
  const [input,    setInput]    = useState("");
  const [msg,      setMsg]      = useState<string | null>(null);

  const load = () =>
    fetch("http://localhost:8000/api/keywords")
      .then((r) => r.json())
      .then((d) => setKeywords(d.keywords ?? []))
      .catch(() => {});

  useEffect(() => { load(); }, []);

  const add = async () => {
    const kw = input.trim().toLowerCase();
    if (!kw) return;
    setMsg(null);
    const res  = await fetch("http://localhost:8000/api/keywords", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ keyword: kw }),
    });
    const data = await res.json();
    if (res.ok) { setKeywords(data.keywords ?? []); setInput(""); }
    else setMsg(data.detail ?? "추가 실패");
  };

  const remove = async (kw: string) => {
    const res  = await fetch(`http://localhost:8000/api/keywords/${encodeURIComponent(kw)}`, { method: "DELETE" });
    const data = await res.json();
    setKeywords(data.keywords ?? []);
  };

  return (
    <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5">
      <h2 className="text-lg font-bold mb-1 text-[#c9d1d9]">🔔 키워드 구독</h2>
      <p className="text-xs text-[#8b949e] mb-4">등록한 키워드가 트렌딩 레포에 나타나면 이메일로 알림을 받습니다</p>
      <div className="flex gap-2 mb-4">
        <input value={input} onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && add()}
          placeholder="키워드 입력 (예: llm, rust, wasm)"
          className="flex-1 bg-[#0d1117] border border-[#30363d] rounded-lg px-3 py-2 text-sm text-white placeholder-[#484f58] focus:outline-none focus:border-[#58a6ff]" />
        <button onClick={add} disabled={!input.trim()}
          className="bg-[#238636] hover:bg-[#2ea043] disabled:opacity-50 text-white text-sm font-semibold px-4 rounded-lg transition">
          추가
        </button>
      </div>
      {msg && <p className="text-xs text-[#f78166] mb-3">{msg}</p>}
      {keywords.length === 0 ? (
        <p className="text-xs text-[#484f58] text-center py-6">등록된 키워드가 없습니다</p>
      ) : (
        <div className="flex flex-wrap gap-2">
          {keywords.map((kw) => (
            <span key={kw} className="flex items-center gap-1.5 bg-[#1c2d40] border border-[#1f6feb] text-[#58a6ff] rounded-full px-3 py-1 text-xs">
              {kw}
              <button onClick={() => remove(kw)} className="text-[#8b949e] hover:text-[#f78166] transition leading-none">×</button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
