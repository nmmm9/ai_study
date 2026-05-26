"use client";

import { useState, useEffect, useRef } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer,
} from "recharts";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const SYSTEM_LABELS: Record<string, string> = {
  simple_rag:   "Simple RAG (A)",
  advanced_rag: "Advanced RAG (B)",
  agentic_rag:  "Agentic RAG (C)",
};

const SYSTEM_COLORS: Record<string, string> = {
  simple_rag:   "#6366f1",
  advanced_rag: "#22c55e",
  agentic_rag:  "#f59e0b",
};

const METRIC_LABELS: Record<string, string> = {
  faithfulness:      "Faithfulness",
  answer_relevancy:  "Answer Relevancy",
  context_precision: "Context Precision",
  context_recall:    "Context Recall",
};

const METRICS = Object.keys(METRIC_LABELS);

type EvalStatus = { status: string; progress: number; total: number; current_system: string };
type EvalResults = {
  ready: boolean;
  scores?: Record<string, Record<string, number>>;
  records?: Record<string, any[]>;
  ragas_error?: string | null;
};

function scoreColor(v: number) {
  if (v >= 0.8) return "#22c55e";
  if (v >= 0.6) return "#f59e0b";
  return "#ef4444";
}

export default function EvaluationPanel() {
  const [status,  setStatus]  = useState<EvalStatus | null>(null);
  const [results, setResults] = useState<EvalResults | null>(null);
  const [loading, setLoading] = useState(false);
  const [tab,     setTab]     = useState<"scores" | "details">("scores");
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPoll = () => { if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; } };

  const pollStatus = async () => {
    try {
      const res = await fetch(`${API}/api/evaluate/status`);
      const s: EvalStatus = await res.json();
      setStatus(s);
      if (s.status === "done") {
        stopPoll();
        setLoading(false);
        const r = await fetch(`${API}/api/evaluate/results`);
        setResults(await r.json());
      } else if (s.status === "idle") {
        stopPoll();
        setLoading(false);
      }
    } catch { stopPoll(); setLoading(false); }
  };

  const handleStart = async () => {
    setLoading(true);
    setResults(null);
    try {
      await fetch(`${API}/api/evaluate`, { method: "POST" });
      pollRef.current = setInterval(pollStatus, 3000);
    } catch {
      setLoading(false);
    }
  };

  useEffect(() => {
    // 이미 실행 중인지 확인
    fetch(`${API}/api/evaluate/status`)
      .then(r => r.json())
      .then((s: EvalStatus) => {
        setStatus(s);
        if (s.status === "running") {
          setLoading(true);
          pollRef.current = setInterval(pollStatus, 3000);
        } else if (s.status === "done") {
          fetch(`${API}/api/evaluate/results`).then(r => r.json()).then(setResults);
        }
      })
      .catch(() => {});
    return stopPoll;
  }, []);

  // ── 차트 데이터 변환 ──────────────────────────────────────
  const barData = METRICS.map(m => {
    const row: Record<string, any> = { metric: METRIC_LABELS[m] };
    if (results?.scores) {
      Object.entries(results.scores).forEach(([sys, sc]) => {
        row[SYSTEM_LABELS[sys] ?? sys] = sc[m] ?? 0;
      });
    }
    return row;
  });

  const radarData = METRICS.map(m => {
    const row: Record<string, any> = { metric: METRIC_LABELS[m] };
    if (results?.scores) {
      Object.entries(results.scores).forEach(([sys, sc]) => {
        row[SYSTEM_LABELS[sys] ?? sys] = sc[m] ?? 0;
      });
    }
    return row;
  });

  const progress = status?.total ? Math.round((status.progress / status.total) * 100) : 0;

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h2 className="text-lg font-bold text-[#c9d1d9]">RAG 시스템 평가 대시보드</h2>
            <p className="text-sm text-[#8b949e] mt-1">
              Simple RAG · Advanced RAG · Agentic RAG — 20개 질문으로 RAGAS 정량 평가
            </p>
          </div>
          <button
            onClick={handleStart}
            disabled={loading}
            className="bg-[#6366f1] hover:bg-[#4f46e5] disabled:opacity-50 text-white font-semibold px-5 py-2.5 rounded-lg text-sm transition"
          >
            {loading ? "평가 중..." : "▶ 평가 시작"}
          </button>
        </div>

        {/* 진행률 바 */}
        {loading && (
          <div className="mt-4">
            <div className="flex justify-between text-xs text-[#8b949e] mb-1">
              <span>{status?.current_system || "준비 중..."}</span>
              <span>{status?.progress ?? 0} / {status?.total ?? 0} ({progress}%)</span>
            </div>
            <div className="w-full bg-[#21262d] rounded-full h-2">
              <div
                className="bg-[#6366f1] h-2 rounded-full transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="text-xs text-[#8b949e] mt-1">약 5~10분 소요됩니다. 다른 기능은 정상 사용 가능합니다.</p>
          </div>
        )}
      </div>

      {/* 결과 없음 */}
      {!results && !loading && (
        <div className="text-center text-[#8b949e] py-16">
          <p className="text-4xl mb-4">📊</p>
          <p>평가 시작 버튼을 눌러 3개 RAG 시스템의 성능을 비교하세요</p>
        </div>
      )}

      {/* 결과 */}
      {results?.ready && results.scores && (
        <>
          {results.ragas_error && (
            <div className="bg-[#2d1c1c] border border-[#f85149] rounded-lg px-4 py-3 text-sm text-[#f85149]">
              RAGAS 오류: {results.ragas_error} — 점수 없이 답변만 표시됩니다.
            </div>
          )}

          {/* 탭 */}
          <div className="flex gap-2">
            {(["scores", "details"] as const).map(t => (
              <button key={t} onClick={() => setTab(t)}
                className={`px-4 py-1.5 rounded-full text-sm font-medium transition ${
                  tab === t ? "bg-[#6366f1] text-white" : "bg-[#21262d] text-[#8b949e] hover:text-white"
                }`}>
                {t === "scores" ? "점수 비교" : "질문별 상세"}
              </button>
            ))}
          </div>

          {tab === "scores" && (
            <>
              {/* 점수 테이블 */}
              <div className="bg-[#161b22] border border-[#30363d] rounded-xl overflow-hidden">
                <div className="px-5 py-3 border-b border-[#30363d]">
                  <span className="text-sm font-bold text-[#c9d1d9]">RAGAS 메트릭 비교</span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-[#30363d]">
                        <th className="text-left px-5 py-3 text-[#8b949e] font-medium">메트릭</th>
                        {Object.keys(results.scores).map(sys => (
                          <th key={sys} className="px-5 py-3 text-center font-semibold"
                            style={{ color: SYSTEM_COLORS[sys] }}>
                            {SYSTEM_LABELS[sys] ?? sys}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {METRICS.map(m => (
                        <tr key={m} className="border-b border-[#21262d] hover:bg-[#1c2128]">
                          <td className="px-5 py-3 text-[#c9d1d9]">{METRIC_LABELS[m]}</td>
                          {Object.keys(results.scores!).map(sys => {
                            const v = results.scores![sys][m] ?? 0;
                            return (
                              <td key={sys} className="px-5 py-3 text-center font-bold"
                                style={{ color: scoreColor(v) }}>
                                {v ? v.toFixed(3) : "—"}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                      {/* 평균 행 */}
                      <tr className="bg-[#1c2128]">
                        <td className="px-5 py-3 font-bold text-[#c9d1d9]">평균</td>
                        {Object.entries(results.scores).map(([sys, sc]) => {
                          const vals = METRICS.map(m => sc[m] ?? 0).filter(v => v > 0);
                          const avg  = vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
                          return (
                            <td key={sys} className="px-5 py-3 text-center font-bold"
                              style={{ color: scoreColor(avg) }}>
                              {avg ? avg.toFixed(3) : "—"}
                            </td>
                          );
                        })}
                      </tr>
                    </tbody>
                  </table>
                </div>
                <p className="px-5 py-2 text-xs text-[#6b7280]">
                  초록(≥0.8) · 주황(≥0.6) · 빨강(&lt;0.6)
                </p>
              </div>

              {/* 차트 2개 */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5">
                  <p className="text-sm font-bold text-[#c9d1d9] mb-4">메트릭별 비교 (막대)</p>
                  <ResponsiveContainer width="100%" height={260}>
                    <BarChart data={barData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
                      <XAxis dataKey="metric" tick={{ fill: "#8b949e", fontSize: 11 }} />
                      <YAxis domain={[0, 1]} tick={{ fill: "#8b949e", fontSize: 11 }} />
                      <Tooltip contentStyle={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8 }} />
                      <Legend wrapperStyle={{ fontSize: 12 }} />
                      {Object.keys(results.scores).map(sys => (
                        <Bar key={sys} dataKey={SYSTEM_LABELS[sys] ?? sys} fill={SYSTEM_COLORS[sys]} radius={[3,3,0,0]} />
                      ))}
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5">
                  <p className="text-sm font-bold text-[#c9d1d9] mb-4">종합 점수 (레이더)</p>
                  <ResponsiveContainer width="100%" height={260}>
                    <RadarChart data={radarData}>
                      <PolarGrid stroke="#30363d" />
                      <PolarAngleAxis dataKey="metric" tick={{ fill: "#8b949e", fontSize: 11 }} />
                      <PolarRadiusAxis domain={[0, 1]} tick={{ fill: "#8b949e", fontSize: 10 }} />
                      <Tooltip contentStyle={{ background: "#161b22", border: "1px solid #30363d", borderRadius: 8 }} />
                      <Legend wrapperStyle={{ fontSize: 12 }} />
                      {Object.keys(results.scores).map(sys => (
                        <Radar key={sys} name={SYSTEM_LABELS[sys] ?? sys}
                          dataKey={SYSTEM_LABELS[sys] ?? sys}
                          stroke={SYSTEM_COLORS[sys]} fill={SYSTEM_COLORS[sys]} fillOpacity={0.15} />
                      ))}
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </>
          )}

          {tab === "details" && results.records && (
            <div className="bg-[#161b22] border border-[#30363d] rounded-xl overflow-hidden">
              <div className="px-5 py-3 border-b border-[#30363d]">
                <span className="text-sm font-bold text-[#c9d1d9]">질문별 답변 상세</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-[#30363d]">
                      <th className="text-left px-4 py-3 text-[#8b949e]">#</th>
                      <th className="text-left px-4 py-3 text-[#8b949e]">유형</th>
                      <th className="text-left px-4 py-3 text-[#8b949e]">질문</th>
                      {Object.keys(results.records).map(sys => (
                        <th key={sys} className="px-4 py-3 text-center" style={{ color: SYSTEM_COLORS[sys] }}>
                          {SYSTEM_LABELS[sys] ?? sys}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {(results.records[Object.keys(results.records)[0]] ?? []).map((item: any) => (
                      <tr key={item.id} className="border-b border-[#21262d] hover:bg-[#1c2128]">
                        <td className="px-4 py-3 text-[#8b949e]">{item.id}</td>
                        <td className="px-4 py-3">
                          <span className="bg-[#1c2d40] text-[#58a6ff] px-2 py-0.5 rounded-full text-xs">
                            {item.type}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-[#c9d1d9] max-w-xs">{item.question}</td>
                        {Object.keys(results.records!).map(sys => {
                          const rec = results.records![sys].find((r: any) => r.id === item.id);
                          return (
                            <td key={sys} className="px-4 py-3 text-[#8b949e] max-w-xs align-top">
                              {rec?.error
                                ? <span className="text-[#f85149]">오류</span>
                                : <span>{(rec?.answer ?? "").slice(0, 120)}...</span>
                              }
                              {rec?.tool_calls > 0 && (
                                <span className="ml-1 bg-[#2d2006] text-[#f59e0b] text-xs px-1.5 py-0.5 rounded-full">
                                  🔧{rec.tool_calls}
                                </span>
                              )}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
