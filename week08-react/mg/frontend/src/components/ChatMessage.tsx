"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import type { ChatMessage as ChatMessageType, ReActStep } from "@/types/chat";

interface Props {
  message: ChatMessageType;
}

const TOOL_LABELS: Record<string, string> = {
  delivery_tracking: "택배 추적", lotto_results: "로또 조회", fine_dust: "미세먼지",
  han_river_water_level: "한강 수위", kbo_results: "KBO 야구", kleague_results: "K리그",
  korean_spell_check: "맞춤법", korean_law_search: "법률 검색",
  joseon_sillok_search: "조선왕조실록", blue_ribbon_nearby: "블루리본 맛집",
  cheap_gas_nearby: "최저가 주유소", real_estate_price: "부동산 실거래가",
  zipcode_search: "우편번호", get_current_time: "현재 시간", calculate: "계산기",
  daiso_search: "다이소 검색", daiso_pickup_stock: "다이소 재고",
  coupang_search: "쿠팡 검색", kakao_bar_nearby: "주변 바/술집",
  oliveyoung_store_search: "올리브영 매장", oliveyoung_product_search: "올리브영 상품",
  oliveyoung_inventory: "올리브영 재고", seoul_subway_arrival: "지하철 도착",
  used_car_price: "중고차 시세", lck_results: "LCK 결과", hwp_convert: "HWP 변환",
};

function StepBadge({ type }: { type: ReActStep["type"] }) {
  const styles = {
    thought: "bg-purple-500/15 text-purple-400 border-purple-500/30",
    action: "bg-blue-500/15 text-blue-400 border-blue-500/30",
    observation: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  };
  const labels = { thought: "Thought", action: "Action", observation: "Observation" };
  return (
    <span className={`inline-block rounded-md border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${styles[type]}`}>
      {labels[type]}
    </span>
  );
}

function ReActSteps({ steps, isStreaming }: { steps: ReActStep[]; isStreaming: boolean }) {
  const [collapsed, setCollapsed] = useState(false);

  if (!steps || steps.length === 0) return null;

  return (
    <div className="mb-4">
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="mb-2 text-[11px] text-[#7D7972] hover:text-[#B5B0A6] transition-colors"
      >
        {collapsed ? `추론 과정 펼치기 (${steps.length}단계)` : "추론 과정 접기"}
      </button>

      {!collapsed && (
        <div className="space-y-2 border-l-2 border-[#383840] pl-4">
          {steps.map((step, i) => {
            const isLast = i === steps.length - 1 && isStreaming;
            return (
              <div key={i} className={`animate-fade-in ${isLast ? "opacity-80" : ""}`}>
                <div className="flex items-center gap-2 mb-1">
                  <StepBadge type={step.type} />
                  <span className="text-[11px] text-[#7D7972]">Round {step.round}</span>
                </div>

                {step.type === "thought" && (
                  <p className="text-[13px] text-[#B5B0A6] leading-relaxed italic">
                    {step.text}
                  </p>
                )}

                {step.type === "action" && (
                  <div className="rounded-lg bg-[#212127] px-3 py-2">
                    <p className="text-[12px] font-mono">
                      <span className="text-blue-400">{TOOL_LABELS[step.tool || ""] || step.tool}</span>
                      <span className="text-[#7D7972]">(</span>
                      <span className="text-[#D4B07A]">
                        {Object.entries(step.arguments || {}).map(([k, v]) => `${k}: ${JSON.stringify(v)}`).join(", ")}
                      </span>
                      <span className="text-[#7D7972]">)</span>
                    </p>
                  </div>
                )}

                {step.type === "observation" && (
                  <div className="rounded-lg bg-[#212127] px-3 py-2">
                    <p className="text-[11px] text-emerald-400/70 line-clamp-3 font-mono">
                      {step.result}
                    </p>
                  </div>
                )}
              </div>
            );
          })}
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
                {/* ReAct Steps */}
                <ReActSteps steps={message.steps || []} isStreaming={message.isStreaming || false} />

                {/* Answer */}
                {message.content ? (
                  <div className="chat-markdown text-[14px] leading-[1.8] text-[#B5B0A6]">
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                    {message.isStreaming && (
                      <span className="inline-block h-[18px] w-[2px] animate-blink bg-[#D4B07A]/60 ml-0.5 align-text-bottom" />
                    )}
                  </div>
                ) : message.isStreaming && (!message.steps || message.steps.length === 0) ? (
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
