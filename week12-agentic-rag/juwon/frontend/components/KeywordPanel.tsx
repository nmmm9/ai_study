"use client";

import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function KeywordPanel({ matches }: { matches?: any[] }) {
  const [keywords, setKeywords] = useState<string[]>([]);
  const [input,    setInput]    = useState("");
  const [saving,   setSaving]   = useState(false);

  const fetchKeywords = () =>
    fetch(`${API}/api/keywords`)
      .then((r) => r.json())
      .then((d) => setKeywords(d.keywords ?? []))
      .catch(() => {});

  useEffect(() => { fetchKeywords(); }, []);

  const add = async () => {
    const kw = input.trim().toLowerCase();
    if (!kw || saving) return;
    setSaving(true);
    try {
      const res = await fetch(`${API}/api/keywords`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ keyword: kw }),
      });
      const data = await res.json();
      setKeywords(data.keywords ?? []);
      setInput("");
    } catch {
    } finally {
      setSaving(false);
    }
  };

  const remove = async (kw: string) => {
    try {
      const res = await fetch(`${API}/api/keywords/${encodeURIComponent(kw)}`, { method: "DELETE" });
      const data = await res.json();
      setKeywords(data.keywords ?? []);
    } catch {}
  };

  return (
    <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4 space-y-3">
      <p className="text-xs font-bold text-[#c9d1d9]">🔔 키워드 구독</p>
      <p className="text-xs text-[#484f58]">등록한 키워드가 트렌딩에 뜨면 이메일로 알려드려요.</p>

      {/* 입력 */}
      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && add()}
          placeholder="rust, llm, wasm..."
          className="flex-1 bg-[#0d1117] border border-[#30363d] rounded px-2 py-1.5 text-xs text-white placeholder-[#484f58] focus:outline-none focus:border-[#58a6ff]"
          disabled={saving}
        />
        <button onClick={add} disabled={saving || !input.trim()}
          className="bg-[#238636] hover:bg-[#2ea043] disabled:opacity-50 text-white text-xs font-semibold px-3 rounded transition">
          추가
        </button>
      </div>

      {/* 등록된 키워드 */}
      {keywords.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {keywords.map((kw) => (
            <span key={kw}
              className="flex items-center gap-1 bg-[#21262d] border border-[#30363d] text-[#c9d1d9] text-xs rounded-full px-2.5 py-1">
              {kw}
              <button onClick={() => remove(kw)} className="text-[#484f58] hover:text-[#f78166] transition">✕</button>
            </span>
          ))}
        </div>
      )}

      {/* 이번 분석 매칭 결과 */}
      {matches && matches.length > 0 && (
        <div className="border-t border-[#30363d] pt-3">
          <p className="text-xs text-[#3fb950] font-bold mb-1.5">✅ 이번 분석 매칭 {matches.length}건</p>
          <div className="space-y-1">
            {matches.map((m, i) => (
              <div key={i} className="text-xs text-[#8b949e]">
                <span className="text-[#ffa657] font-semibold">{m.keyword}</span>
                {" → "}
                <a href={m.repo.url} target="_blank" rel="noreferrer"
                  className="text-[#58a6ff] hover:underline">{m.repo.name}</a>
                {" "}(⭐{m.repo.stars?.toLocaleString()})
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
