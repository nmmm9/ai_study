"use client";

import { useEffect, useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

type StatEntry = { date: string; languages: Record<string, number> };

const COLORS = ["#58a6ff", "#3fb950", "#f78166", "#d2a8ff", "#ffa657", "#79c0ff", "#56d364"];

export default function TrendChart() {
  const [stats,   setStats]   = useState<StatEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8000/api/history/stats")
      .then((r) => r.json())
      .then((d) => setStats(d ?? []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5">
      <p className="text-xs text-[#8b949e]">차트 로딩 중...</p>
    </div>
  );

  if (stats.length === 0) return (
    <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5">
      <h2 className="text-lg font-bold mb-2 text-[#c9d1d9]">📈 언어 트렌드 변화</h2>
      <p className="text-xs text-[#484f58] text-center py-8">분석을 실행하면 차트가 표시됩니다.</p>
    </div>
  );

  const langSet = new Set<string>();
  stats.forEach((s) => Object.keys(s.languages).forEach((l) => langSet.add(l)));
  const langs = Array.from(langSet).slice(0, 7);

  const chartData = stats.map((s) => ({
    date: s.date.slice(5),
    ...Object.fromEntries(langs.map((l) => [l, s.languages[l] ?? 0])),
  }));

  return (
    <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5">
      <h2 className="text-lg font-bold mb-4 text-[#c9d1d9]">📈 언어 트렌드 변화</h2>
      {chartData.length === 1 ? (
        <>
          <div className="flex gap-3 flex-wrap">
            {langs.map((l, i) => (
              <div key={l} className="bg-[#0d1117] border border-[#30363d] rounded-lg px-4 py-3 text-center">
                <p className="text-xs text-[#8b949e]">{l}</p>
                <p className="text-xl font-bold mt-1" style={{ color: COLORS[i % COLORS.length] }}>
                  {(chartData[0] as any)[l] ?? 0}개
                </p>
              </div>
            ))}
          </div>
          <p className="text-xs text-[#484f58] mt-3">분석을 더 실행하면 날짜별 추이 그래프로 바뀝니다.</p>
        </>
      ) : (
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={chartData} margin={{ top: 4, right: 16, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#21262d" />
            <XAxis dataKey="date" tick={{ fill: "#8b949e", fontSize: 11 }} />
            <YAxis tick={{ fill: "#8b949e", fontSize: 11 }} />
            <Tooltip contentStyle={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8 }} labelStyle={{ color: "#c9d1d9" }} />
            <Legend wrapperStyle={{ fontSize: 11, color: "#8b949e" }} />
            {langs.map((l, i) => (
              <Line key={l} type="monotone" dataKey={l} stroke={COLORS[i % COLORS.length]} strokeWidth={2} dot={false} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
