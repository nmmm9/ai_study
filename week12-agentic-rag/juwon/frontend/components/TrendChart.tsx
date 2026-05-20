"use client";

import { useEffect, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from "recharts";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const COLORS = ["#58a6ff", "#3fb950", "#f78166", "#d2a8ff", "#ffa657", "#79c0ff"];

export default function TrendChart() {
  const [data,    setData]    = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [langs,   setLangs]   = useState<string[]>([]);

  useEffect(() => {
    fetch(`${API}/api/history/stats`)
      .then((r) => r.json())
      .then((stats: any[]) => {
        if (!stats.length) return;

        // 등장한 모든 언어 수집
        const langSet = new Set<string>();
        stats.forEach((s) => Object.keys(s.language_stats ?? {}).forEach((l) => langSet.add(l)));
        const topLangs = [...langSet].slice(0, 6);
        setLangs(topLangs);

        // recharts용 데이터 변환
        const chartData = stats.map((s) => ({
          date: s.date,
          ...Object.fromEntries(topLangs.map((l) => [l, s.language_stats?.[l] ?? 0])),
        }));
        setData(chartData);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5">
      <p className="text-xs text-[#8b949e]">차트 로딩 중...</p>
    </div>
  );

  if (!data.length) return (
    <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5">
      <h2 className="text-lg font-bold mb-2 text-[#c9d1d9]">📈 트렌드 변화</h2>
      <p className="text-xs text-[#484f58]">분석을 2회 이상 실행하면 차트가 표시됩니다.</p>
    </div>
  );

  return (
    <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5">
      <h2 className="text-lg font-bold mb-4 text-[#c9d1d9]">📈 언어별 트렌드 변화</h2>
      <ResponsiveContainer width="100%" height={240}>
        <LineChart data={data} margin={{ top: 4, right: 16, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#21262d" />
          <XAxis dataKey="date" tick={{ fill: "#8b949e", fontSize: 11 }} />
          <YAxis tick={{ fill: "#8b949e", fontSize: 11 }} />
          <Tooltip
            contentStyle={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8 }}
            labelStyle={{ color: "#c9d1d9" }}
            itemStyle={{ color: "#8b949e" }}
          />
          <Legend wrapperStyle={{ fontSize: 12, color: "#8b949e" }} />
          {langs.map((lang, i) => (
            <Line
              key={lang}
              type="monotone"
              dataKey={lang}
              stroke={COLORS[i % COLORS.length]}
              strokeWidth={2}
              dot={{ r: 3 }}
              activeDot={{ r: 5 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
