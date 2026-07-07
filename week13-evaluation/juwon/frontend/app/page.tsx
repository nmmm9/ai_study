"use client";

import { useState } from "react";
import AgentCard from "@/components/AgentCard";
import ChatPanel from "@/components/ChatPanel";
import DebateTimeline from "@/components/DebateTimeline";
import EvaluationPanel from "@/components/EvaluationPanel";
import KeywordPanel from "@/components/KeywordPanel";
import Markdown from "@/components/Markdown";
import MyGithubPanel from "@/components/MyGithubPanel";
import RepoList from "@/components/RepoList";
import TrendPredictionPanel from "@/components/TrendPredictionPanel";
import SchedulePanel from "@/components/SchedulePanel";
import TrendChart from "@/components/TrendChart";
import TrendComparison from "@/components/TrendComparison";

const LANGUAGES = ["전체", "Python", "JavaScript", "TypeScript", "Rust", "Go", "Java", "C++"];
const PERIODS: Record<string, string> = { "오늘": "daily", "이번 주": "weekly", "이번 달": "monthly" };
type Tab = "analyze" | "chat" | "history" | "keywords" | "mygithub" | "evaluate" | "predict";

export default function Home() {
  const [tab,      setTab]      = useState<Tab>("analyze");
  const [language, setLanguage] = useState("전체");
  const [period,   setPeriod]   = useState("이번 주");
  const [loading,  setLoading]  = useState(false);
  const [report,   setReport]   = useState<any>(null);
  const [emailStatus,   setEmailStatus]   = useState<string | null>(null);
  const [githubStatus,  setGithubStatus]  = useState<string | null>(null);
  const [emailLoading,  setEmailLoading]  = useState(false);
  const [githubLoading, setGithubLoading] = useState(false);

  const handleAnalyze = async () => {
    setLoading(true);
    setEmailStatus(null);
    setGithubStatus(null);
    try {
      const res = await fetch("http://localhost:8000/api/analyze", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ language: language === "전체" ? "" : language, period: PERIODS[period] }),
      });
      const data = await res.json();
      setReport(data);
      if (data.keyword_matches?.length > 0)
        alert(`🔔 구독 키워드 감지됨: ${data.keyword_matches.join(", ")}`);
    } catch {
      alert("분석 실패: 백엔드 서버가 실행 중인지 확인해주세요.");
    } finally {
      setLoading(false);
    }
  };

  const handleEmail = async () => {
    if (!report) return;
    setEmailLoading(true); setEmailStatus(null);
    try {
      const res  = await fetch("http://localhost:8000/api/notify/email", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ judge_decision: report.judge_decision ?? "", language: report.language ?? "전체", period: report.period ?? "weekly" }),
      });
      const data = await res.json();
      setEmailStatus(res.ok ? "✅ " + data.message : "❌ " + data.detail);
    } catch { setEmailStatus("❌ 메일 전송 실패"); }
    finally { setEmailLoading(false); }
  };

  const handleGithub = async () => {
    if (!report) return;
    setGithubLoading(true); setGithubStatus(null);
    try {
      const res  = await fetch("http://localhost:8000/api/notify/github", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ judge_decision: report.judge_decision ?? "", language: report.language ?? "전체", period: report.period ?? "weekly" }),
      });
      const data = await res.json();
      setGithubStatus(res.ok ? "✅ " + data.message : "❌ " + data.detail);
    } catch { setGithubStatus("❌ GitHub 업로드 실패"); }
    finally { setGithubLoading(false); }
  };

  const TABS: { key: Tab; label: string }[] = [
    { key: "analyze",  label: "🔍 트렌드 분석" },
    { key: "chat",     label: "💬 Agentic 채팅" },
    { key: "history",  label: "📚 히스토리" },
    { key: "keywords", label: "🔔 키워드 구독" },
    { key: "mygithub", label: "🧑‍💻 내 GitHub" },
    { key: "evaluate", label: "🧪 평가" },
    { key: "predict",  label: "📈 트렌드 예측" },
  ];

  return (
    <main className="min-h-screen bg-[#0d1117] text-white">
      {/* 헤더 */}
      <div className="border-b border-[#21262d] px-8 py-5">
        <h1 className="text-2xl font-bold text-[#58a6ff]">GitHub Tech Trend Analyzer</h1>
        <p className="text-sm text-[#8b949e] mt-1">Agentic RAG · Multi-Agent Debate · RAGAS 평가 — Week 13</p>
      </div>

      {/* 탭 */}
      <div className="border-b border-[#21262d] px-8 flex gap-6">
        {TABS.map(({ key, label }) => (
          <button key={key} onClick={() => setTab(key)}
            className={`py-3 text-sm font-medium border-b-2 transition ${
              tab === key ? "border-[#58a6ff] text-[#58a6ff]" : "border-transparent text-[#8b949e] hover:text-[#c9d1d9]"
            }`}>
            {label}
          </button>
        ))}
      </div>

      {/* ── 트렌드 분석 ── */}
      {tab === "analyze" && (
        <div className="flex gap-6 p-8">
          <div className="w-56 shrink-0 space-y-4">
            <div>
              <label className="text-xs text-[#8b949e] mb-1 block">언어 필터</label>
              <select value={language} onChange={(e) => setLanguage(e.target.value)}
                className="w-full bg-[#161b22] border border-[#30363d] rounded-lg px-3 py-2 text-sm text-white">
                {LANGUAGES.map((l) => <option key={l}>{l}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-[#8b949e] mb-1 block">기간</label>
              <select value={period} onChange={(e) => setPeriod(e.target.value)}
                className="w-full bg-[#161b22] border border-[#30363d] rounded-lg px-3 py-2 text-sm text-white">
                {Object.keys(PERIODS).map((p) => <option key={p}>{p}</option>)}
              </select>
            </div>
            <button onClick={handleAnalyze} disabled={loading}
              className="w-full bg-[#238636] hover:bg-[#2ea043] disabled:opacity-50 text-white font-semibold py-2 rounded-lg text-sm transition">
              {loading ? "분석 중..." : "🔍 분석 시작"}
            </button>
            <SchedulePanel />
          </div>

          <div className="flex-1 space-y-6">
            {!report && !loading && (
              <div className="text-center text-[#8b949e] mt-20">
                <p className="text-4xl mb-4">📊</p>
                <p>왼쪽에서 설정 후 분석 시작 버튼을 눌러주세요</p>
                <p className="text-xs mt-2 text-[#484f58]">전문가 에이전트가 과거 데이터를 RAG로 참조하며 분석합니다</p>
              </div>
            )}
            {report && (
              <>
                {report.keyword_matches?.length > 0 && (
                  <div className="bg-[#1c2d1c] border border-[#3fb950] rounded-lg px-4 py-3 text-sm text-[#3fb950]">
                    🔔 구독 키워드 감지: <strong>{report.keyword_matches.join(", ")}</strong>
                  </div>
                )}
                <div className="grid grid-cols-3 gap-4">
                  {[
                    { label: "수집된 레포", value: `${report.repos?.length ?? 0}개` },
                    { label: "1위 언어",    value: Object.keys(report.language_stats ?? {})[0] ?? "-" },
                    { label: "분석 기간",   value: ({ daily:"오늘", weekly:"이번 주", monthly:"이번 달" } as any)[report.period] ?? "-" },
                  ].map((m) => (
                    <div key={m.label} className="bg-[#161b22] border border-[#30363d] rounded-lg p-4">
                      <p className="text-xs text-[#8b949e]">{m.label}</p>
                      <p className="text-xl font-bold mt-1">{m.value}</p>
                    </div>
                  ))}
                </div>
                <RepoList repos={report.repos ?? []} />
                <TrendComparison comparison={report.comparison} />
                <div>
                  <h2 className="text-lg font-bold mb-1 text-[#c9d1d9]">🤖 전문가 에이전트 분석</h2>
                  <p className="text-xs text-[#8b949e] mb-3">각 에이전트가 과거 데이터를 RAG로 참조한 후 분석 (Week 12 기능)</p>
                  <div className="grid grid-cols-3 gap-4">
                    <AgentCard title="AI/ML 전문가" icon="🧠" content={report.analysis_ai  ?? ""} color="blue" />
                    <AgentCard title="웹/앱 전문가" icon="🌐" content={report.analysis_web ?? ""} color="green" />
                    <AgentCard title="보안 전문가"  icon="🔒" content={report.analysis_sec ?? ""} color="yellow" />
                  </div>
                </div>
                <DebateTimeline history={report.debate_history ?? []} />
                <div className="bg-[#161b22] border border-[#58a6ff] rounded-xl overflow-hidden">
                  <div className="flex items-center gap-2 px-5 py-3 bg-[#1c2d40] border-b border-[#58a6ff]">
                    <span className="text-sm font-bold text-[#58a6ff]">⚖️ Judge 최종 결론</span>
                  </div>
                  <div className="px-5 py-4"><Markdown content={report.judge_decision ?? ""} /></div>
                </div>
                <div className="flex gap-3">
                  <button onClick={handleEmail} disabled={emailLoading}
                    className="flex-1 bg-[#1c2d40] hover:bg-[#1f3a52] disabled:opacity-50 border border-[#58a6ff] text-[#58a6ff] font-semibold py-3 rounded-lg text-sm transition">
                    {emailLoading ? "전송 중..." : "📧 메일로 전송"}
                  </button>
                  <button onClick={handleGithub} disabled={githubLoading}
                    className="flex-1 bg-[#1a2d1a] hover:bg-[#1e3620] disabled:opacity-50 border border-[#3fb950] text-[#3fb950] font-semibold py-3 rounded-lg text-sm transition">
                    {githubLoading ? "업로드 중..." : "📁 GitHub에 올리기"}
                  </button>
                </div>
                {(emailStatus || githubStatus) && (
                  <div className="space-y-1">
                    {emailStatus  && <p className="text-xs text-[#8b949e]">{emailStatus}</p>}
                    {githubStatus && <p className="text-xs text-[#8b949e]">{githubStatus}</p>}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}

      {/* ── Agentic 채팅 ── */}
      {tab === "chat" && (
        <div className="p-8">
          {report ? (
            <ChatPanel report={report} />
          ) : (
            <div className="text-center text-[#8b949e] mt-20">
              <p className="text-4xl mb-4">💬</p>
              <p>먼저 트렌드 분석 탭에서 분석을 실행해주세요</p>
            </div>
          )}
        </div>
      )}

      {/* ── 히스토리 ── */}
      {tab === "history" && (
        <div className="p-8 space-y-6">
          <TrendChart />
          <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-5">
            <h2 className="text-lg font-bold mb-4 text-[#c9d1d9]">📚 분석 히스토리</h2>
            <HistoryList />
          </div>
        </div>
      )}

      {/* ── 키워드 구독 ── */}
      {tab === "keywords" && (
        <div className="p-8 max-w-xl"><KeywordPanel /></div>
      )}

      {/* ── 내 GitHub ── */}
      {tab === "mygithub" && (
        <div className="p-8 max-w-4xl">
          {report ? (
            <MyGithubPanel report={report} />
          ) : (
            <div className="text-center text-[#8b949e] mt-20">
              <p className="text-4xl mb-4">🧑‍💻</p>
              <p>먼저 트렌드 분석 탭에서 분석을 실행해주세요</p>
            </div>
          )}
        </div>
      )}

      {/* ── 평가 ── */}
      {tab === "evaluate" && (
        <div className="p-8 max-w-4xl"><EvaluationPanel /></div>
      )}

      {/* ── 트렌드 예측 ── */}
      {tab === "predict" && (
        <div className="p-8 max-w-4xl"><TrendPredictionPanel /></div>
      )}
    </main>
  );
}

function HistoryList() {
  const [list,    setList]    = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const PERIOD_KR: Record<string, string> = { daily: "오늘", weekly: "이번 주", monthly: "이번 달" };

  useState(() => {
    fetch("http://localhost:8000/api/history")
      .then((r) => r.json())
      .then((d) => setList(Array.isArray(d) ? d : []))
      .catch(() => {})
      .finally(() => setLoading(false));
  });

  if (loading) return <p className="text-xs text-[#8b949e]">로딩 중...</p>;
  if (list.length === 0) return <p className="text-xs text-[#484f58]">저장된 기록이 없습니다.</p>;

  return (
    <div className="space-y-2">
      {list.map((item, i) => {
        const date = item.created_at?.slice(0, 16).replace("T", " ");
        const lang = item.language || "전체";
        const p    = PERIOD_KR[item.period] ?? item.period;
        return (
          <details key={i} className="bg-[#0d1117] border border-[#21262d] rounded-lg px-4 py-3 cursor-pointer">
            <summary className="text-xs text-[#8b949e] list-none flex justify-between">
              <span>{date}  |  {lang}  |  {p}</span>
              <span>레포 {item.repos?.length ?? 0}개</span>
            </summary>
            <div className="mt-3 text-xs text-[#c9d1d9]">
              <p className="text-[#58a6ff] font-semibold mb-1">상위 레포</p>
              <p className="text-[#8b949e] mb-2">{item.repos?.slice(0, 5).map((r: any) => r.name).join(" · ")}</p>
              <p className="text-[#58a6ff] font-semibold mb-1">Judge 결론</p>
              <p className="whitespace-pre-wrap">{item.judge_decision?.slice(0, 300)}...</p>
            </div>
          </details>
        );
      })}
    </div>
  );
}
