"use client";

import ReactMarkdown from "react-markdown";
import type { ChatMessage as ChatMessageType } from "@/types/chat";

interface Props {
  message: ChatMessageType;
}

const TOOL_LABELS: Record<string, string> = {
  delivery_tracking: "택배 추적",
  lotto_results: "로또 조회",
  fine_dust: "미세먼지",
  han_river_water_level: "한강 수위",
  kbo_results: "KBO 야구",
  kleague_results: "K리그",
  korean_spell_check: "맞춤법 검사",
  korean_law_search: "법률 검색",
  joseon_sillok_search: "조선왕조실록",
  blue_ribbon_nearby: "블루리본 맛집",
  cheap_gas_nearby: "최저가 주유소",
  real_estate_price: "부동산 실거래가",
  zipcode_search: "우편번호",
  get_current_time: "현재 시간",
  calculate: "계산기",
  daiso_search: "다이소 검색",
  daiso_pickup_stock: "다이소 재고 확인",
  coupang_search: "쿠팡 검색",
  kakao_bar_nearby: "주변 바/술집",
  oliveyoung_store_search: "올리브영 매장",
  oliveyoung_product_search: "올리브영 상품",
  oliveyoung_inventory: "올리브영 재고",
  seoul_subway_arrival: "지하철 도착",
  used_car_price: "중고차 시세",
  lck_results: "LCK 결과",
  hwp_convert: "HWP 변환",
};

export default function ChatMessage({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`py-5 ${isUser ? "" : "bg-base-50/20"}`}>
      <div className="mx-auto max-w-3xl px-6">
        <div className="flex gap-5">
          <div
            className={`mt-0.5 flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${
              isUser ? "bg-pearl/8 text-pearl-dim" : "bg-gold/10 text-gold"
            }`}
          >
            {isUser ? "나" : "K"}
          </div>

          <div className="min-w-0 flex-1 pt-0.5">
            {isUser ? (
              <p className="text-[14px] leading-relaxed text-pearl">{message.content}</p>
            ) : (
              <>
                {/* Tool calls */}
                {message.toolCalls && message.toolCalls.length > 0 && (
                  <div className="mb-4 space-y-2">
                    {message.toolCalls.map((tc, i) => {
                      const hasResult = message.toolResults && message.toolResults[i];
                      const label = TOOL_LABELS[tc.name] || tc.name;
                      const argsStr = Object.entries(tc.arguments)
                        .map(([k, v]) => `${k}: ${JSON.stringify(v)}`)
                        .join(", ");
                      const resultPreview = hasResult ? message.toolResults![i].result : null;

                      return (
                        <div key={i} className="rounded-lg bg-base-100/40 px-3.5 py-2.5">
                          <div className="flex items-center gap-2 text-[12px]">
                            <span className={hasResult ? "text-good" : "text-gold animate-pulse"}>
                              {hasResult ? "✓" : "●"}
                            </span>
                            <span className="font-medium text-pearl-dim">{label}</span>
                            <code className="text-[10px] text-pearl-muted/50">{tc.name}()</code>
                          </div>
                          {argsStr && (
                            <p className="mt-1 text-[11px] font-mono text-pearl-muted/40 pl-5">
                              {argsStr}
                            </p>
                          )}
                          {resultPreview && (
                            <p className="mt-1 text-[11px] text-good/50 pl-5 line-clamp-1">
                              {resultPreview.length > 100 ? resultPreview.slice(0, 100) + "..." : resultPreview}
                            </p>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Content */}
                {message.content ? (
                  <div className="chat-markdown text-[14px] leading-[1.8] text-pearl-dim">
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                    {message.isStreaming && (
                      <span className="inline-block h-[18px] w-[2px] animate-blink bg-gold/60 ml-0.5 align-text-bottom" />
                    )}
                  </div>
                ) : message.isStreaming && (!message.toolCalls || message.toolCalls.length === 0) ? (
                  <div className="flex items-center gap-2 text-[13px] text-pearl-muted/60">
                    <span className="flex gap-1">
                      <span className="h-1.5 w-1.5 rounded-full bg-gold/40 animate-bounce" style={{ animationDelay: "0ms" }} />
                      <span className="h-1.5 w-1.5 rounded-full bg-gold/40 animate-bounce" style={{ animationDelay: "150ms" }} />
                      <span className="h-1.5 w-1.5 rounded-full bg-gold/40 animate-bounce" style={{ animationDelay: "300ms" }} />
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
