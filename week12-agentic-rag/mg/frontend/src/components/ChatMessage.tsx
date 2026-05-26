"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import type {
  ChatMessage as ChatMessageType, AgentTrace, CriticReport,
  PlanStep, ReplanRecord, RetrievalRound,
} from "@/types/chat";

const DOMAIN_LABELS: Record<string, string> = {
  shopping: "쇼핑", lifestyle: "생활", sports: "스포츠", news: "뉴스",
  finance: "금융", government: "공공", education: "교육", info: "정보",
  documents: "문서",
};

function RetrievalPanel({ rounds }: { rounds: RetrievalRound[] }) {
  const [open, setOpen] = useState(false);
  if (!rounds || rounds.length === 0) return null;
  const lastScore = rounds[rounds.length - 1]?.score ?? 0;
  const totalChunks = rounds.reduce((acc, r) => acc + (r.chunks?.length || 0), 0);

  return (
    <div className="mb-3 rounded-lg border border-cyan-500/20 bg-cyan-500/5 px-3.5 py-2.5">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between"
      >
        <span className="text-[11px] font-semibold uppercase tracking-wider text-cyan-300">
          Agentic Retrieval · {rounds.length} round{rounds.length > 1 ? "s" : ""}
        </span>
        <span className="flex gap-1.5 items-center">
          <span className="rounded-md bg-cyan-500/15 border border-cyan-500/30 px-2 py-0.5 text-[10px] text-cyan-300">
            {totalChunks} chunks
          </span>
          <span
            className={`rounded-md border px-2 py-0.5 text-[10px] font-bold ${
              lastScore >= 3
                ? "bg-emerald-500/15 border-emerald-500/30 text-emerald-400"
                : "bg-red-500/15 border-red-500/30 text-red-400"
            }`}
          >
            {lastScore}/5
          </span>
          <span className="text-[10px] text-pearl-muted/50 ml-1">
            {open ? "▾" : "▸"}
          </span>
        </span>
      </button>
      {open && (
        <div className="mt-2 space-y-2.5">
          {rounds.map((r, i) => (
            <div key={i} className="rounded-md bg-base-50/30 px-2.5 py-2">
              <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                <span className="text-[10px] text-pearl-muted/70">Round {r.round}</span>
                <code className="text-[10px] bg-base/40 px-1.5 py-0.5 rounded">
                  {r.query}
                </code>
                <span
                  className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                    r.score >= 3 ? "text-emerald-400" : "text-red-400"
                  }`}
                >
                  {r.score}/5
                </span>
              </div>
              {r.reasoning && (
                <p className="text-[10px] text-pearl-muted/70 italic mb-1.5">
                  {r.reasoning}
                </p>
              )}
              {r.chunks && r.chunks.length > 0 && (
                <ul className="space-y-1">
                  {r.chunks.slice(0, 3).map((c, j) => (
                    <li key={j} className="text-[10px] text-pearl-dim/80">
                      <span className="text-cyan-400/80">
                        [{j + 1}] {c.doc_name}
                        {c.page !== null && `, p.${c.page}`}
                      </span>
                      <span className="text-pearl-muted/50"> · {c.score.toFixed(3)}</span>
                      <p className="ml-3 text-pearl-muted/60 line-clamp-2">
                        {c.text_snippet || c.text}
                      </p>
                    </li>
                  ))}
                  {r.chunks.length > 3 && (
                    <li className="text-[10px] text-pearl-muted/40 ml-3">
                      + {r.chunks.length - 3} more...
                    </li>
                  )}
                </ul>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function PlanPanel({ plan, planReasoning, replans }: {
  plan: PlanStep[]; planReasoning?: string; replans?: ReplanRecord[];
}) {
  if (!plan || plan.length === 0) return null;
  const doneCount = plan.filter((s) => s.status === "done").length;
  const skippedCount = plan.filter((s) => s.status === "skipped").length;
  const totalActive = plan.filter((s) => s.status !== "skipped").length;

  return (
    <div className="mb-3 rounded-lg border border-purple-500/20 bg-purple-500/5 px-3.5 py-2.5">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-purple-300">
          Plan
        </span>
        <span className="rounded-md bg-purple-500/15 border border-purple-500/30 px-2 py-0.5 text-[10px] text-purple-300">
          {doneCount}/{totalActive} {skippedCount > 0 && `(skip ${skippedCount})`}
        </span>
      </div>
      {planReasoning && (
        <p className="text-[11px] text-pearl-muted/70 italic mb-2">{planReasoning}</p>
      )}
      <ol className="space-y-1.5">
        {plan.map((s, idx) => {
          const isActive = s.status === "active";
          const isDone = s.status === "done";
          const isSkipped = s.status === "skipped";
          return (
            <li key={`step-${idx}-${s.id}`} className="flex items-start gap-2.5">
              <span
                className={`inline-flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${
                  isDone
                    ? "bg-emerald-500/20 text-emerald-400"
                    : isActive
                    ? "bg-amber-500/30 text-amber-300 animate-pulse"
                    : isSkipped
                    ? "bg-stroke/30 text-pearl-muted/50"
                    : "bg-stroke/30 text-pearl-muted"
                }`}
              >
                {isDone ? "✓" : isSkipped ? "−" : s.id}
              </span>
              <div className="flex-1 min-w-0">
                <div className="flex items-baseline gap-2">
                  {s.domain && (
                    <span className="rounded bg-blue-500/15 border border-blue-500/30 px-1.5 py-0 text-[9px] font-medium text-blue-400">
                      {DOMAIN_LABELS[s.domain] || s.domain}
                    </span>
                  )}
                  <span
                    className={`text-[12px] ${
                      isSkipped ? "text-pearl-muted/50 line-through" : "text-pearl-dim"
                    }`}
                  >
                    {s.task}
                  </span>
                </div>
                {isDone && s.tool_count !== undefined && (
                  <span className="text-[10px] text-emerald-400/60">
                    → {s.tool_count}개 도구 호출
                  </span>
                )}
              </div>
            </li>
          );
        })}
      </ol>
      {replans && replans.length > 0 && (
        <div className="mt-2 pt-2 border-t border-purple-500/15 space-y-1">
          {replans.map((r, i) => (
            <div key={i} className="flex items-baseline gap-2 text-[10px]">
              <span
                className={`rounded px-1.5 py-0 font-medium ${
                  r.action === "finish"
                    ? "bg-emerald-500/15 text-emerald-400"
                    : r.action === "revise"
                    ? "bg-amber-500/15 text-amber-400"
                    : "bg-stroke/30 text-pearl-muted"
                }`}
              >
                replan: {r.action}
              </span>
              <span className="text-pearl-muted/70 italic">{r.reasoning}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

interface Props {
  message: ChatMessageType;
}

const TOOL_LABELS: Record<string, string> = {
  delivery_tracking: "택배 추적", lotto_results: "로또 조회", fine_dust: "미세먼지",
  korea_weather: "날씨", han_river_water_level: "한강 수위",
  kbo_results: "KBO 야구", kleague_results: "K리그", lck_results: "LCK 결과",
  kbl_results: "KBL 농구",
  korean_spell_check: "맞춤법", korean_character_count: "글자수",
  korean_law_search: "법률 검색", joseon_sillok_search: "조선왕조실록",
  blue_ribbon_nearby: "블루리본 맛집", cheap_gas_nearby: "최저가 주유소",
  real_estate_price: "부동산 실거래가", zipcode_search: "우편번호",
  get_current_time: "현재 시간", calculate: "계산기",
  daiso_search: "다이소 검색", daiso_pickup_stock: "다이소 재고",
  coupang_search: "쿠팡 검색", naver_shopping_search: "네이버 쇼핑",
  kakao_bar_nearby: "주변 바/술집",
  oliveyoung_store_search: "올리브영 매장", oliveyoung_product_search: "올리브영 상품",
  oliveyoung_inventory: "올리브영 재고", seoul_subway_arrival: "지하철 도착",
  used_car_price: "중고차 시세", hwp_convert: "HWP 변환",
  naver_news_search: "네이버 뉴스", geeknews_search: "긱뉴스",
  korean_stock_search: "한국 주식",
  parking_lot_nearby: "주차장 검색", household_waste_info: "생활폐기물",
  mfds_drug_safety: "의약품 안전", mfds_food_safety: "식품 안전",
  lh_notice_search: "LH 청약 공고",
  library_book_search: "도서 검색", school_meal: "학교 급식",
};

const NODE_META: Record<string, { label: string; color: string; bg: string }> = {
  supervisor: { label: "Supervisor", color: "text-purple-400", bg: "bg-purple-500/15 border-purple-500/30" },
  shopping:   { label: "Shopping",   color: "text-blue-400",   bg: "bg-blue-500/15 border-blue-500/30" },
  lifestyle:  { label: "Lifestyle",  color: "text-blue-400",   bg: "bg-blue-500/15 border-blue-500/30" },
  sports:     { label: "Sports",     color: "text-blue-400",   bg: "bg-blue-500/15 border-blue-500/30" },
  news:       { label: "News",       color: "text-blue-400",   bg: "bg-blue-500/15 border-blue-500/30" },
  finance:    { label: "Finance",    color: "text-blue-400",   bg: "bg-blue-500/15 border-blue-500/30" },
  government: { label: "Government", color: "text-blue-400",   bg: "bg-blue-500/15 border-blue-500/30" },
  education:  { label: "Education",  color: "text-blue-400",   bg: "bg-blue-500/15 border-blue-500/30" },
  info:       { label: "Info",       color: "text-blue-400",   bg: "bg-blue-500/15 border-blue-500/30" },
  writer:     { label: "Writer",     color: "text-amber-400",  bg: "bg-amber-500/15 border-amber-500/30" },
  critic:     { label: "Critic",     color: "text-red-400",    bg: "bg-red-500/15 border-red-500/30" },
};

function CriticPanel({ critiques, finalScore, iterations }: { critiques: CriticReport[]; finalScore?: number; iterations?: number }) {
  if (!critiques || critiques.length === 0) return null;

  return (
    <div className="mb-3 rounded-lg border border-red-500/20 bg-red-500/5 px-3.5 py-2.5">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-red-400/80">
          Self-Correction
        </span>
        <div className="flex gap-1.5">
          {iterations !== undefined && iterations > 0 && (
            <span className="rounded-md bg-amber-500/15 border border-amber-500/30 px-2 py-0.5 text-[10px] text-amber-400">
              Iter {iterations}
            </span>
          )}
          {finalScore !== undefined && (
            <span
              className={`rounded-md border px-2 py-0.5 text-[10px] font-bold ${
                finalScore >= 7
                  ? "bg-emerald-500/15 border-emerald-500/30 text-emerald-400"
                  : "bg-red-500/15 border-red-500/30 text-red-400"
              }`}
            >
              최종 {finalScore}/10
            </span>
          )}
        </div>
      </div>
      <div className="space-y-2">
        {critiques.map((c, i) => (
          <div key={i} className="rounded-md bg-base-50/30 px-2.5 py-1.5">
            <div className="mb-1 flex items-center gap-2">
              <span className="text-[10px] text-pearl-muted/70">Iter {c.iteration}</span>
              <span
                className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${
                  c.passed ? "text-emerald-400" : "text-red-400"
                }`}
              >
                {c.score}/10 {c.passed ? "통과" : "재작성"}
              </span>
            </div>
            {c.issues && c.issues.length > 0 && (
              <ul className="ml-3 list-disc space-y-0.5 text-[11px] text-pearl-muted/80">
                {c.issues.map((x, j) => (
                  <li key={j}>{x}</li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function NodeBadge({ node, status }: { node: string; status: AgentTrace["status"] }) {
  const m = NODE_META[node] || { label: node, color: "text-pearl-muted", bg: "bg-stroke/30 border-stroke/50" };
  return (
    <span className={`inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${m.bg} ${m.color}`}>
      {status === "active" && (
        <span className="h-1.5 w-1.5 rounded-full bg-current animate-pulse" />
      )}
      {status === "done" && (
        <svg viewBox="0 0 12 12" className="h-2.5 w-2.5 fill-current">
          <path d="M2 6.5l3 3 5-7" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      )}
      {m.label}
    </span>
  );
}

function AgentTraces({ traces, planDomains, reasoning, isStreaming }: {
  traces: AgentTrace[];
  planDomains: string[];
  reasoning: string;
  isStreaming: boolean;
}) {
  const plan = planDomains;
  const [collapsed, setCollapsed] = useState(false);

  if (!traces || traces.length === 0) return null;

  return (
    <div className="mb-4">
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="mb-2 text-[11px] text-[#7D7972] hover:text-[#B5B0A6] transition-colors"
      >
        {collapsed ? `에이전트 트레이스 펼치기 (${traces.length}개)` : "에이전트 트레이스 접기"}
      </button>

      {!collapsed && (
        <div className="space-y-3 border-l-2 border-[#383840] pl-4">
          {/* Supervisor reasoning */}
          {reasoning && (
            <div className="animate-fade-in">
              <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                <NodeBadge node="supervisor" status="done" />
                {plan.length > 0 && (
                  <span className="text-[10px] text-pearl-muted/50">
                    → {plan.join(", ")}
                  </span>
                )}
              </div>
              <p className="text-[12px] text-pearl-dim/80 italic leading-relaxed">
                {reasoning}
              </p>
            </div>
          )}

          {/* Each domain agent trace */}
          {traces
            .filter((t) => t.node !== "supervisor")
            .map((t, i) => (
              <div key={i} className="animate-fade-in">
                <div className="flex items-center gap-2 mb-1.5">
                  <NodeBadge node={t.node} status={t.status} />
                  {t.summary && (
                    <span className="text-[10px] text-pearl-muted/50">
                      {t.summary}
                    </span>
                  )}
                </div>

                {/* Tool calls inside this agent */}
                {t.tools.length > 0 && (
                  <div className="space-y-1.5 ml-1">
                    {t.tools.map((tool, j) => (
                      <div key={j} className="rounded-lg bg-[#212127] px-3 py-2">
                        <p className="text-[12px] font-mono">
                          <span className="text-blue-400">
                            {TOOL_LABELS[tool.tool] || tool.tool}
                          </span>
                          <span className="text-[#7D7972]">(</span>
                          <span className="text-[#D4B07A]">
                            {Object.entries(tool.args || {}).map(([k, v]) => `${k}: ${JSON.stringify(v)}`).join(", ")}
                          </span>
                          <span className="text-[#7D7972]">)</span>
                        </p>
                        {tool.result && (
                          <p className="mt-1 text-[11px] text-emerald-400/60 line-clamp-2 font-mono">
                            → {tool.result}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}

          {/* Writer status */}
          {traces.find((t) => t.node === "writer") && (
            <div className="animate-fade-in">
              <NodeBadge
                node="writer"
                status={traces.find((t) => t.node === "writer")?.status || "idle"}
              />
            </div>
          )}

          {isStreaming && (
            <div className="text-[10px] text-pearl-muted/40 animate-pulse">실행 중...</div>
          )}
        </div>
      )}
    </div>
  );
}

export default function ChatMessage({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`py-5 ${isUser ? "" : "bg-[#212127]/20"}`}>
      <div className="mx-auto max-w-3xl px-6">
        <div className="flex gap-5">
          <div
            className={`mt-0.5 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${
              isUser ? "bg-[#F2EFE9]/8 text-[#B5B0A6]" : "bg-[#D4B07A]/10 text-[#D4B07A]"
            }`}
          >
            {isUser ? "나" : "K"}
          </div>

          <div className="min-w-0 flex-1 pt-0.5">
            {isUser ? (
              <p className="text-[14px] leading-relaxed text-[#F2EFE9]">{message.content}</p>
            ) : (
              <>
                <PlanPanel
                  plan={message.plan || []}
                  planReasoning={message.planReasoning}
                  replans={message.replans}
                />

                <RetrievalPanel rounds={message.retrievalRounds || []} />

                <AgentTraces
                  traces={message.traces || []}
                  planDomains={(message.plan || []).map((s) => s.domain || "?")}
                  reasoning={message.reasoning || ""}
                  isStreaming={message.isStreaming || false}
                />

                <CriticPanel
                  critiques={message.critiques || []}
                  finalScore={message.finalScore}
                  iterations={message.iterations}
                />

                {message.content ? (
                  <div className="chat-markdown text-[14px] leading-[1.8] text-[#B5B0A6]">
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                    {message.isStreaming && (
                      <span className="inline-block h-[18px] w-[2px] animate-blink bg-[#D4B07A]/60 ml-0.5 align-text-bottom" />
                    )}
                  </div>
                ) : message.isStreaming && (!message.traces || message.traces.length === 0) ? (
                  <div className="flex items-center gap-2 text-[13px] text-[#7D7972]">
                    <span className="flex gap-1">
                      <span className="h-1.5 w-1.5 rounded-full bg-[#D4B07A]/40 animate-bounce" style={{ animationDelay: "0ms" }} />
                      <span className="h-1.5 w-1.5 rounded-full bg-[#D4B07A]/40 animate-bounce" style={{ animationDelay: "150ms" }} />
                      <span className="h-1.5 w-1.5 rounded-full bg-[#D4B07A]/40 animate-bounce" style={{ animationDelay: "300ms" }} />
                    </span>
                  </div>
                ) : null}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
