"use client";

import { useState } from "react";
import RepoList from "@/components/RepoList";
import AgentCard from "@/components/AgentCard";
import DebateTimeline from "@/components/DebateTimeline";
import TrendComparison from "@/components/TrendComparison";
import SchedulePanel from "@/components/SchedulePanel";
import ChatPanel from "@/components/ChatPanel";
import Markdown from "@/components/Markdown";

const LANGUAGES = ["전체", "Python", "JavaScript", "TypeScript", "Rust", "Go", "Java", "C++"];
const PERIODS: Record<string, string> = { "오늘": "daily", "이번 주": "weekly", "이번 달": "monthly" };

export default function Home() {
  const [language, setLanguage] = useState("전체");
  const [period, setPeriod]     = useState("이번 주");
  const [loading, setLoading]         = useState(false);
  const [report, setReport]           = useState<any>(null);
  const [emailStatus, setEmailStatus] = useState<string | null>(null);
  const [githubStatus, setGithubStatus] = useState<string | null>(null);
  const [emailLoading, setEmailLoading]   = useState(false);
  const [githubLoading, setGithubLoading] = useState(false);

  const handleEmail = async () => {
    if (!report) return;
    setEmailLoading(true);
    setEmailStatus(null);
    try {
      const res = await fetch("http://localhost:8000/api/notify/email", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({
          judge_decision: report.judge_decision ?? "",
          language:       report.language ?? "전체",
          period:         report.period   ?? "weekly",
        }),
      });
      const data = await res.json();
      setEmailStatus(res.ok ? "✅ " + data.message : "❌ " + data.detail);
    } catch {
      setEmailStatus("❌ 메일 전송 실패");
    } finally {
      setEmailLoading(false);
    }
  };

  const handleGithub = async () => {
    if (!report) return;
    setGithubLoading(true);
    setGithubStatus(null);
    try {
      const res = await fetch("http://localhost:8000/api/notify/github", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({
          judge_decision: report.judge_decision ?? "",
          language:       report.language ?? "전체",
          period:         report.period   ?? "weekly",
        }),
      });
      const data = await res.json();
      setGithubStatus(res.ok ? "✅ " + data.message : "❌ " + data.detail);
    } catch {
      setGithubStatus("❌ GitHub 업로드 실패");
    } finally {
      setGithubLoading(false);
    }
  };

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/analyze", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({
          language: language === "전체" ? "" : language,
          period:   PERIODS[period],
        }),
      });
      setReport(await res.json());
    } catch {
      alert("분석 실패: 백엔드 서버가 실행 중인지 확인해주세요.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#0d1117] text-white">
      <div className="border-b border-[#21262d] px-8 py-5">
        <h1 className="text-2xl font-bold text-[#58a6ff]">GitHub Tech Trend Analyzer</h1>
        <p className="text-sm text-[#8b949e] mt-1">Multi-Agent Debate 패턴으로 구동되는 트렌드 분석 에이전트</p>
      </div>

      <div className="flex gap-6 p-8">
        {/* 사이드바 */}
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

        {/* 메인 */}
        <div className="flex-1 space-y-6">
          {!report && !loading && (
            <div className="text-center text-[#8b949e] mt-20">
              <p className="text-4xl mb-4">📊</p>
              <p>왼쪽에서 설정 후 분석 시작 버튼을 눌러주세요</p>
            </div>
          )}
          {report && (
            <>
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
                <h2 className="text-lg font-bold mb-3 text-[#c9d1d9]">🤖 전문가 에이전트 분석</h2>
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
                <div className="px-5 py-4">
                  <Markdown content={report.judge_decision ?? ""} />
                </div>
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
              <ChatPanel report={report} />
            </>
          )}
        </div>
      </div>
    </main>
  );
}
