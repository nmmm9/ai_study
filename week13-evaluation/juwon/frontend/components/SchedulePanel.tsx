"use client";

import { useEffect, useState } from "react";

const HOURS = Array.from({ length: 24 }, (_, i) => i);
const PERIODS: Record<string, string> = { "오늘": "daily", "이번 주": "weekly", "이번 달": "monthly" };

export default function SchedulePanel() {
  const [enabled,  setEnabled]  = useState(false);
  const [hour,     setHour]     = useState(9);
  const [period,   setPeriod]   = useState("daily");
  const [nextRun,  setNextRun]  = useState<string | null>(null);
  const [saving,   setSaving]   = useState(false);
  const [saved,    setSaved]    = useState(false);

  useEffect(() => {
    fetch("http://localhost:8000/api/schedule")
      .then((r) => r.json())
      .then((d) => {
        setEnabled(d.enabled);
        setHour(d.hour);
        setPeriod(d.period);
        setNextRun(d.next_run);
      })
      .catch(() => {});
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    try {
      const res = await fetch("http://localhost:8000/api/schedule", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ enabled, hour, minute: 0, language: "", period }),
      });
      const data = await res.json();
      setNextRun(data.next_run);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {
      alert("저장 실패: 백엔드 서버를 확인해주세요.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-4 space-y-3">
      <p className="text-xs font-bold text-[#c9d1d9]">⏰ 자동 분석 설정</p>

      {/* 토글 */}
      <div className="flex items-center justify-between">
        <span className="text-xs text-[#8b949e]">자동 실행</span>
        <button
          onClick={() => setEnabled(!enabled)}
          className={`w-10 h-5 rounded-full transition-colors ${enabled ? "bg-[#238636]" : "bg-[#30363d]"} relative`}
        >
          <span className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform ${enabled ? "translate-x-5" : "translate-x-0.5"}`} />
        </button>
      </div>

      {enabled && (
        <>
          <div>
            <label className="text-xs text-[#8b949e] mb-1 block">실행 시간</label>
            <select value={hour} onChange={(e) => setHour(Number(e.target.value))}
              className="w-full bg-[#0d1117] border border-[#30363d] rounded-lg px-3 py-1.5 text-sm text-white">
              {HOURS.map((h) => (
                <option key={h} value={h}>{String(h).padStart(2, "0")}:00</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-[#8b949e] mb-1 block">분석 기간</label>
            <select value={period} onChange={(e) => setPeriod(e.target.value)}
              className="w-full bg-[#0d1117] border border-[#30363d] rounded-lg px-3 py-1.5 text-sm text-white">
              {Object.entries(PERIODS).map(([label, val]) => (
                <option key={val} value={val}>{label}</option>
              ))}
            </select>
          </div>
          {nextRun && (
            <p className="text-xs text-[#484f58]">다음 실행: {new Date(nextRun).toLocaleString("ko-KR")}</p>
          )}
        </>
      )}

      <button onClick={handleSave} disabled={saving}
        className="w-full bg-[#21262d] hover:bg-[#30363d] disabled:opacity-50 text-[#c9d1d9] text-xs font-semibold py-2 rounded-lg transition">
        {saving ? "저장 중..." : saved ? "✅ 저장됨" : "저장"}
      </button>
    </div>
  );
}
