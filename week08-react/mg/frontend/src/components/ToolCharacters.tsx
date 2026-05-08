"use client";

import React, { useEffect, useState } from "react";

interface Props {
  activeTools: string[];
}

interface Character {
  id: string;
  name: string;
  emoji: string;
  color: string;
  idle: string;
  dance: string;
  desc: string;
  example: string;
}

const CHARACTERS: Character[] = [
  { id: "delivery_tracking", name: "택배", emoji: "📦", color: "#F59E0B", idle: "bob", dance: "jump",
    desc: "CJ대한통운, 우체국택배 배송 추적", example: "내 택배 어디야? 운송장 6123456789" },
  { id: "fine_dust", name: "미세먼지", emoji: "😷", color: "#94A3B8", idle: "breathe", dance: "spin",
    desc: "PM10/PM2.5 실시간 대기질 조회", example: "안양 미세먼지 어때?" },
  { id: "han_river_water_level", name: "한강", emoji: "🌊", color: "#38BDF8", idle: "wave", dance: "splash",
    desc: "한강 관측소별 수위/유량 조회", example: "잠실 한강 수위 알려줘" },
  { id: "cheap_gas_nearby", name: "주유소", emoji: "⛽", color: "#EF4444", idle: "bob", dance: "pump",
    desc: "주변 최저가 주유소 검색 (휘발유/경유/LPG)", example: "강남역 근처 저렴한 주유소" },
  { id: "zipcode_search", name: "우편", emoji: "✉️", color: "#A78BFA", idle: "breathe", dance: "fly",
    desc: "주소로 우편번호 검색", example: "테헤란로 우편번호 알려줘" },
  { id: "real_estate_price", name: "부동산", emoji: "🏠", color: "#10B981", idle: "bob", dance: "grow",
    desc: "아파트/오피스텔 실거래가 조회", example: "강남구 아파트 실거래가" },
  { id: "seoul_subway_arrival", name: "지하철", emoji: "🚇", color: "#3B82F6", idle: "slide", dance: "rush",
    desc: "서울 지하철 실시간 도착 정보", example: "강남역 지하철 언제 와?" },

  { id: "daiso_search", name: "다이소", emoji: "🛒", color: "#EC4899", idle: "bob", dance: "cartwheel",
    desc: "다이소 매장/상품 검색", example: "다이소에 니들샷 있어?" },
  { id: "daiso_pickup_stock", name: "다이소재고", emoji: "📊", color: "#F472B6", idle: "breathe", dance: "jump",
    desc: "다이소 특정 매장 픽업 재고 확인", example: "독산점에 피크닉 매트 재고" },
  { id: "coupang_search", name: "쿠팡", emoji: "🚀", color: "#8B5CF6", idle: "hover", dance: "rocket",
    desc: "쿠팡 상품 검색 + 가격 비교", example: "쿠팡에서 에어팟 검색해줘" },
  { id: "oliveyoung_store_search", name: "올영매장", emoji: "💄", color: "#F43F5E", idle: "bob", dance: "sparkle",
    desc: "올리브영 매장 검색", example: "강남역 올리브영 매장" },
  { id: "oliveyoung_product_search", name: "올영상품", emoji: "🧴", color: "#FB7185", idle: "breathe", dance: "spin",
    desc: "올리브영 상품 검색", example: "올리브영 선크림 검색" },
  { id: "oliveyoung_inventory", name: "올영재고", emoji: "✅", color: "#4ADE80", idle: "bob", dance: "jump",
    desc: "올리브영 매장별 재고 확인", example: "명동 올리브영 선크림 재고" },
  { id: "used_car_price", name: "중고차", emoji: "🚗", color: "#6366F1", idle: "slide", dance: "drive",
    desc: "SK 타고BUY 중고차 시세 검색", example: "아반떼 중고차 가격" },

  { id: "blue_ribbon_nearby", name: "맛집", emoji: "🍽️", color: "#F97316", idle: "bob", dance: "feast",
    desc: "블루리본 맛집 검색", example: "홍대 맛집 추천해줘" },
  { id: "kakao_bar_nearby", name: "술집", emoji: "🍺", color: "#FBBF24", idle: "wobble", dance: "cheers",
    desc: "카카오맵 주변 바/술집 검색", example: "이태원 술집 추천" },

  { id: "kbo_results", name: "야구", emoji: "⚾", color: "#EF4444", idle: "bob", dance: "pitch",
    desc: "KBO 프로야구 경기 결과/일정", example: "어제 야구 결과 알려줘" },
  { id: "kleague_results", name: "축구", emoji: "⚽", color: "#22C55E", idle: "bob", dance: "kick",
    desc: "K리그 축구 결과/순위", example: "K리그 결과 알려줘" },
  { id: "lck_results", name: "롤", emoji: "🎮", color: "#8B5CF6", idle: "breathe", dance: "combo",
    desc: "LCK 롤 e스포츠 경기 결과", example: "오늘 LCK 경기 결과" },

  { id: "korean_law_search", name: "법률", emoji: "⚖️", color: "#64748B", idle: "breathe", dance: "gavel",
    desc: "법률/판례/조례 검색", example: "임대차보호법 검색해줘" },
  { id: "joseon_sillok_search", name: "실록", emoji: "📜", color: "#D97706", idle: "bob", dance: "unroll",
    desc: "조선왕조실록 역사 기록 검색", example: "훈민정음 실록에서 찾아줘" },

  { id: "korean_spell_check", name: "맞춤법", emoji: "✏️", color: "#14B8A6", idle: "bob", dance: "write",
    desc: "한국어 맞춤법/문법 검사", example: "맞춤법 검사해줘: 됬다" },
  { id: "hwp_convert", name: "한글", emoji: "📄", color: "#0EA5E9", idle: "breathe", dance: "flip",
    desc: "HWP 문서를 텍스트/마크다운으로 변환", example: "이 한글 파일 변환해줘" },

  { id: "lotto_results", name: "로또", emoji: "🎱", color: "#FACC15", idle: "spin-slow", dance: "jackpot",
    desc: "로또 당첨번호 조회/번호 확인", example: "이번 주 로또 당첨번호?" },
  { id: "get_current_time", name: "시간", emoji: "⏰", color: "#F472B6", idle: "tick", dance: "ring",
    desc: "현재 한국 날짜/시간 확인", example: "지금 몇시야?" },
  { id: "calculate", name: "계산기", emoji: "🧮", color: "#A3E635", idle: "bob", dance: "compute",
    desc: "수학 계산 (사칙연산, 퍼센트 등)", example: "150만원의 3.3% 계산해줘" },
];

export default function ToolCharacters({ activeTools }: Props) {
  const [spotlight, setSpotlight] = useState<Set<string>>(new Set());
  const [exiting, setExiting] = useState<Set<string>>(new Set());
  const [selected, setSelected] = useState<Character | null>(null);

  useEffect(() => {
    const newActive = new Set(activeTools);
    setSpotlight(newActive);

    const timer = setTimeout(() => {
      setExiting(newActive);
      setTimeout(() => {
        setExiting(new Set());
        setSpotlight(new Set());
      }, 600);
    }, 4000);

    return () => clearTimeout(timer);
  }, [activeTools.join(",")]);

  return (
    <div className="flex flex-col h-full">
      {/* Stage */}
      <div className="relative flex items-center justify-center min-h-[120px] border-b border-[#383840]/30 bg-gradient-to-b from-[#2A2A31] to-[#1A1A1F] overflow-hidden">
        {spotlight.size > 0 ? (
          <div className="flex items-end gap-4 py-4">
            {CHARACTERS.filter(c => spotlight.has(c.id)).map((char) => (
              <div
                key={char.id}
                className={`flex flex-col items-center ${exiting.has(char.id) ? "animate-exit" : "animate-enter"}`}
              >
                <div
                  className="text-4xl animate-dance"
                  style={{ filter: `drop-shadow(0 0 12px ${char.color}80)` }}
                >
                  {char.emoji}
                </div>
                <span className="mt-1 text-[10px] font-bold" style={{ color: char.color }}>
                  {char.name}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-[11px] text-[#7D7972]/40 tracking-widest">STAGE</p>
        )}

        {spotlight.size > 0 && (
          <div className="absolute inset-0 pointer-events-none">
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-40 h-40 rounded-full bg-white/[0.03] blur-3xl" />
          </div>
        )}
      </div>

      {/* Tool detail popup */}
      {selected && (
        <div className="border-b border-[#383840]/30 bg-[#212127] px-3 py-3 animate-fade-in">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="text-xl">{selected.emoji}</span>
              <span className="text-[13px] font-bold" style={{ color: selected.color }}>{selected.name}</span>
            </div>
            <button
              onClick={() => setSelected(null)}
              className="text-[10px] text-[#7D7972] hover:text-[#B5B0A6]"
            >
              닫기
            </button>
          </div>
          <p className="text-[12px] text-[#B5B0A6] mb-2">{selected.desc}</p>
          <div className="rounded-lg bg-[#1A1A1F] px-3 py-2">
            <p className="text-[10px] text-[#7D7972] mb-1">예시 질문:</p>
            <p className="text-[11px] text-[#D4B07A] italic">&ldquo;{selected.example}&rdquo;</p>
          </div>
          <p className="mt-2 text-[9px] font-mono text-[#7D7972]/50">{selected.id}()</p>
        </div>
      )}

      {/* Rooms */}
      <div className="flex-1 overflow-y-auto p-3">
        <p className="text-[9px] text-[#7D7972]/40 uppercase tracking-wider mb-2 px-1">대기실 ({CHARACTERS.length})</p>
        <div className="grid grid-cols-4 gap-1.5">
          {CHARACTERS.map((char) => {
            const isActive = spotlight.has(char.id);
            const isSelected = selected?.id === char.id;
            return (
              <button
                key={char.id}
                onClick={() => setSelected(isSelected ? null : char)}
                className={`flex flex-col items-center rounded-lg py-2 px-1 transition-all duration-300 ${
                  isActive
                    ? "opacity-20 scale-90"
                    : isSelected
                      ? "bg-[#2A2A31]"
                      : "opacity-100 hover:bg-[#2A2A31]/50"
                }`}
                style={isSelected ? { outline: `1px solid ${char.color}40` } : undefined}
                title={char.desc}
              >
                <span className={`text-lg ${isActive ? "" : "animate-idle-" + char.idle}`}>
                  {char.emoji}
                </span>
                <span className="text-[8px] text-[#7D7972] mt-0.5 truncate w-full text-center">
                  {char.name}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      <style jsx>{`
        @keyframes enter {
          0% { opacity: 0; transform: translateY(40px) scale(0.5); }
          50% { transform: translateY(-10px) scale(1.1); }
          100% { opacity: 1; transform: translateY(0) scale(1); }
        }
        @keyframes exit {
          0% { opacity: 1; transform: translateY(0) scale(1); }
          100% { opacity: 0; transform: translateY(40px) scale(0.5); }
        }
        @keyframes dance {
          0%, 100% { transform: translateY(0) rotate(0deg); }
          15% { transform: translateY(-12px) rotate(-8deg); }
          30% { transform: translateY(0) rotate(8deg); }
          45% { transform: translateY(-8px) rotate(-5deg); }
          60% { transform: translateY(0) rotate(5deg); }
          75% { transform: translateY(-5px) rotate(-3deg); }
        }
        @keyframes idle-bob {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-2px); }
        }
        @keyframes idle-breathe {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.05); }
        }
        @keyframes idle-wave {
          0%, 100% { transform: rotate(0deg); }
          25% { transform: rotate(3deg); }
          75% { transform: rotate(-3deg); }
        }
        @keyframes idle-wobble {
          0%, 100% { transform: rotate(0deg); }
          33% { transform: rotate(5deg); }
          66% { transform: rotate(-5deg); }
        }
        @keyframes idle-slide {
          0%, 100% { transform: translateX(0); }
          50% { transform: translateX(2px); }
        }
        @keyframes idle-hover {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-3px); }
        }
        @keyframes idle-spin-slow {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        @keyframes idle-tick {
          0%, 90%, 100% { transform: rotate(0deg); }
          95% { transform: rotate(6deg); }
        }
        @keyframes fade-in {
          from { opacity: 0; transform: translateY(-4px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .animate-enter { animation: enter 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) both; }
        .animate-exit { animation: exit 0.5s ease-in both; }
        .animate-dance { animation: dance 0.8s ease-in-out infinite; }
        .animate-fade-in { animation: fade-in 0.2s ease-out both; }
        .animate-idle-bob { animation: idle-bob 3s ease-in-out infinite; }
        .animate-idle-breathe { animation: idle-breathe 4s ease-in-out infinite; }
        .animate-idle-wave { animation: idle-wave 3s ease-in-out infinite; }
        .animate-idle-wobble { animation: idle-wobble 2s ease-in-out infinite; }
        .animate-idle-slide { animation: idle-slide 3s ease-in-out infinite; }
        .animate-idle-hover { animation: idle-hover 2s ease-in-out infinite; }
        .animate-idle-spin-slow { animation: idle-spin-slow 8s linear infinite; }
        .animate-idle-tick { animation: idle-tick 2s ease-in-out infinite; }
      `}</style>
    </div>
  );
}
