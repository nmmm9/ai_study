"use client";

import { useEffect, useState } from "react";
import Markdown from "./Markdown";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type HistoryEntry = {
  key:      string;
  language: string;
  period:   string;
  repos:    any[];
  judge_decision: string;
};

const PERIOD_LABEL: Record<string, string> = {
  daily: "오늘", weekly: "이번 주", monthly: "이번 달",
};

export default function HistoryBrowser() {
  const [entries,  setEntries]  = useState<HistoryEntry[]>([]);
  const [selected, setSelected] = useState<HistoryEntry | null>(null);
  const [loading,  setLoading]  = useState(true);

  useEffect(() => {
    fetch(`${API}/api/history`)
      .then((r) => r.json())
      .then((data: Record<string, any>) => {
        const list = Object.entries(data)
          .map(([key, val]) => ({ key, ...val }))
          .sort((a, b) => b.key.localeCompare(a.key));
        setEntries(list);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5">
      <p className="text-xs text-[#8b949e]">히스토리 불러오는 중...</p>
    </div>
  );

  if (!entries.length) return (
    <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5">
      <h2 className="text-lg font-bold mb-2 text-[#c9d1d9]">🗂 분석 히스토리</h2>
      <p className="text-xs text-[#484f58]">아직 저장된 분석이 없습니다.</p>
    </div>
  );

  return (
    <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5">
      <h2 className="text-lg font-bold mb-4 text-[#c9d1d9]">🗂 분석 히스토리</h2>

      <div className="flex gap-4">
        {/* 목록 */}
        <div className="w-52 shrink-0 space-y-1 max-h-64 overflow-y-auto">
          {entries.map((e) => (
            <button
              key={e.key}
              onClick={() => setSelected(e)}
              className={`w-full text-left px-3 py-2 rounded-lg text-xs transition ${
                selected?.key === e.key
                  ? "bg-[#1c2d40] border border-[#58a6ff] text-[#58a6ff]"
                  : "bg-[#21262d] hover:bg-[#30363d] text-[#8b949e]"
              }`}
            >
              <p className="font-semibold truncate">{e.key}</p>
              <p className="text-[#484f58] mt-0.5">
                {e.language || "전체"} · {PERIOD_LABEL[e.period] ?? e.period}
                · {e.repos?.length ?? 0}개
              </p>
            </button>
          ))}
        </div>

        {/* 상세 */}
        <div className="flex-1 min-w-0">
          {selected ? (
            <div className="space-y-3">
              <div className="flex gap-2 text-xs">
                {[
                  { label: "언어", value: selected.language || "전체" },
                  { label: "기간", value: PERIOD_LABEL[selected.period] ?? selected.period },
                  { label: "레포", value: `${selected.repos?.length ?? 0}개` },
                ].map((m) => (
                  <div key={m.label} className="bg-[#0d1117] border border-[#30363d] rounded px-3 py-1.5">
                    <span className="text-[#484f58]">{m.label}: </span>
                    <span className="text-[#c9d1d9] font-semibold">{m.value}</span>
                  </div>
                ))}
              </div>
              <div className="bg-[#0d1117] border border-[#30363d] rounded-lg p-3 max-h-40 overflow-y-auto">
                <p className="text-xs text-[#58a6ff] font-bold mb-1">⚖️ Judge 결론</p>
                <div className="text-xs text-[#8b949e]">
                  <Markdown content={selected.judge_decision ?? ""} />
                </div>
              </div>
            </div>
          ) : (
            <p className="text-xs text-[#484f58] mt-4">왼쪽에서 날짜를 선택하세요.</p>
          )}
        </div>
      </div>
    </div>
  );
}
