import React from 'react';

// 공통 타입
interface IconProps {
  color?: string;
  className?: string;
}

// 귀여운 팔다리 컴포넌트
const Limbs = ({ color = "#1e1e24", type = "stand", yOffset = 0 }: { color?: string, type?: "stand"|"run"|"jump"|"sit", yOffset?: number }) => {
  return (
    <g stroke={color} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" fill="none" transform={`translate(0, ${yOffset})`}>
      {type === "stand" && (
        <>
          <path d="M 35 75 L 35 88 M 65 75 L 65 88" />
          <path d="M 25 55 Q 15 65 20 75 M 75 55 Q 85 65 80 75" />
        </>
      )}
      {type === "run" && (
        <>
          <path d="M 35 75 Q 25 85 30 90 M 65 75 Q 75 80 70 95" />
          <path d="M 25 55 Q 10 45 15 35 M 75 55 Q 90 60 85 75" />
        </>
      )}
      {type === "jump" && (
        <>
          <path d="M 35 75 Q 25 85 30 85 M 65 75 Q 75 85 70 85" />
          <path d="M 25 50 Q 15 40 25 30 M 75 50 Q 85 40 75 30" />
        </>
      )}
    </g>
  );
};

// 귀여운 표정 (다양한 감정)
const Face = ({ x = 0, y = 0, type = "happy", color = "#1e1e24" }: { x?: number; y?: number; type?: string; color?: string }) => (
  <g transform={`translate(${x}, ${y})`}>
    {type === "happy" && (
      <>
        <circle cx="40" cy="50" r="3" fill={color} />
        <circle cx="60" cy="50" r="3" fill={color} />
        <path d="M 45 55 Q 50 62 55 55" stroke={color} strokeWidth="3" fill="none" strokeLinecap="round" />
        <ellipse cx="33" cy="54" rx="4" ry="2.5" fill="#FF8A8A" opacity="0.6"/>
        <ellipse cx="67" cy="54" rx="4" ry="2.5" fill="#FF8A8A" opacity="0.6"/>
      </>
    )}
    {type === "excited" && (
      <>
        <path d="M 37 50 Q 40 45 43 50 M 57 50 Q 60 45 63 50" stroke={color} strokeWidth="3" fill="none" strokeLinecap="round" />
        <path d="M 45 55 Q 50 65 55 55 Z" fill={color} />
        <ellipse cx="32" cy="55" rx="4" ry="2.5" fill="#FF8A8A" opacity="0.6"/>
        <ellipse cx="68" cy="55" rx="4" ry="2.5" fill="#FF8A8A" opacity="0.6"/>
      </>
    )}
    {type === "cool" && (
      <>
        <rect x="35" y="47" width="10" height="4" rx="1" fill={color} />
        <rect x="55" y="47" width="10" height="4" rx="1" fill={color} />
        <path d="M 45 47 L 55 47" stroke={color} strokeWidth="2" />
        <path d="M 48 57 Q 50 58 52 57" stroke={color} strokeWidth="2" fill="none" strokeLinecap="round" />
      </>
    )}
    {type === "tired" && (
      <>
        <path d="M 37 50 L 43 50 M 57 50 L 63 50" stroke={color} strokeWidth="3" fill="none" strokeLinecap="round" />
        <path d="M 37 53 Q 40 55 43 53 M 57 53 Q 60 55 63 53" stroke={color} strokeWidth="1.5" fill="none" strokeLinecap="round" opacity="0.5" />
        <path d="M 48 58 Q 50 60 52 58" stroke={color} strokeWidth="2" fill="none" strokeLinecap="round" />
      </>
    )}
    {type === "wink" && (
      <>
        <circle cx="40" cy="50" r="3" fill={color} />
        <path d="M 57 49 Q 60 46 63 49 M 57 51 Q 60 54 63 51" stroke={color} strokeWidth="2.5" fill="none" strokeLinecap="round" />
        <path d="M 46 55 Q 50 60 55 54" stroke={color} strokeWidth="3" fill="none" strokeLinecap="round" />
        <circle cx="53" cy="58" r="2" fill="#FF8A8A" opacity="0.8" />
      </>
    )}
    {type === "goggle" && (
      <>
        <circle cx="40" cy="50" r="6" fill="white" stroke={color} strokeWidth="3" />
        <circle cx="60" cy="50" r="6" fill="white" stroke={color} strokeWidth="3" />
        <circle cx="40" cy="50" r="2" fill={color} />
        <circle cx="60" cy="50" r="2" fill={color} />
        <path d="M 46 50 L 54 50" stroke={color} strokeWidth="3" />
        <path d="M 47 58 Q 50 62 53 58" stroke={color} strokeWidth="3" fill="none" strokeLinecap="round" />
      </>
    )}
  </g>
);

export const Icons: Record<string, React.FC<IconProps>> = {
  // 1. 택배: 박스 요정 (손에 클립보드)
  delivery_tracking: ({ color = "#F59E0B", className }) => (
    <svg viewBox="0 0 100 100" className={className} width="1em" height="1em">
      <Limbs type="run" yOffset={-5} />
      <path d="M 20 30 L 50 15 L 80 30 L 80 70 L 50 85 L 20 70 Z" fill={color} stroke="#1e1e24" strokeWidth="3" strokeLinejoin="round" />
      <path d="M 20 30 L 50 45 L 80 30 M 50 45 L 50 85" stroke="#1e1e24" strokeWidth="3" strokeLinejoin="round" />
      <path d="M 50 15 L 35 25 M 50 15 L 65 25" stroke="#1e1e24" strokeWidth="3" opacity="0.4" />
      {/* 펄럭이는 박스 뚜껑 */}
      <path d="M 20 30 L 10 20 M 80 30 L 90 20" stroke="#1e1e24" strokeWidth="3" fill="none" strokeLinecap="round" />
      <Face x={0} y={15} type="excited" />
      {/* 운송장 스티커 */}
      <polygon points="55,50 72,42 72,55 55,62" fill="#fff" stroke="#1e1e24" strokeWidth="2" strokeLinejoin="round" />
      <line x1="60" y1="46" x2="68" y2="42" stroke="#1e1e24" strokeWidth="1.5" />
      <line x1="60" y1="52" x2="68" y2="48" stroke="#1e1e24" strokeWidth="1.5" />
    </svg>
  ),

  // 2. 미세먼지: 콜록거리는 마스크 낀 먼지구름
  fine_dust: ({ color = "#94A3B8", className }) => (
    <svg viewBox="0 0 100 100" className={className} width="1em" height="1em">
      <Limbs type="sit" yOffset={-10} />
      {/* 먼지 구름 몸통 */}
      <path d="M 30 70 C 10 70 10 40 30 40 C 35 20 65 20 70 40 C 90 40 90 70 70 70 Z" fill={color} stroke="#1e1e24" strokeWidth="3" strokeLinejoin="round" />
      <Face x={0} y={-5} type="tired" />
      {/* 주름진 KF94 마스크 */}
      <path d="M 35 55 Q 50 50 65 55 L 70 65 C 60 70 40 70 30 65 Z" fill="white" stroke="#1e1e24" strokeWidth="2" strokeLinejoin="round" />
      <path d="M 35 60 Q 50 55 65 60" stroke="#1e1e24" strokeWidth="1" fill="none" />
      {/* 귀걸이 끈 */}
      <path d="M 30 60 Q 20 60 25 50" stroke="white" strokeWidth="2" fill="none" strokeLinecap="round" />
      <path d="M 70 60 Q 80 60 75 50" stroke="white" strokeWidth="2" fill="none" strokeLinecap="round" />
    </svg>
  ),

  // 3. 한강수위: 수영 튜브를 낀 물방울
  han_river_water_level: ({ color = "#38BDF8", className }) => (
    <svg viewBox="0 0 100 100" className={className} width="1em" height="1em">
      <path d="M 25 60 Q 20 70 15 65 M 75 60 Q 80 50 85 45" stroke="#1e1e24" strokeWidth="3" strokeLinecap="round" fill="none" />
      <path d="M 40 85 V 95 M 60 85 V 95" stroke="#1e1e24" strokeWidth="3" strokeLinecap="round" fill="none" />
      <path d="M 50 15 C 50 15 20 50 20 75 C 20 91.568 33.431 105 50 105 C 66.568 105 80 91.568 80 75 C 80 50 50 15 50 15 Z" fill={color} stroke="#1e1e24" strokeWidth="3" strokeLinejoin="round" transform="translate(0, -10)" />
      {/* 고글 */}
      <Face x={0} y={15} type="goggle" />
      {/* 수영 튜브 */}
      <ellipse cx="50" cy="70" rx="35" ry="12" fill="#F43F5E" stroke="#1e1e24" strokeWidth="3" />
      <ellipse cx="50" cy="70" rx="25" ry="8" fill="none" stroke="#1e1e24" strokeWidth="3" />
    </svg>
  ),

  // 4. 주유소: 주유기 로봇
  cheap_gas_nearby: ({ color = "#EF4444", className }) => (
    <svg viewBox="0 0 100 100" className={className} width="1em" height="1em">
      {/* 궤도바퀴 */}
      <rect x="25" y="80" width="20" height="10" rx="5" fill="#475569" stroke="#1e1e24" strokeWidth="2" />
      <rect x="55" y="80" width="20" height="10" rx="5" fill="#475569" stroke="#1e1e24" strokeWidth="2" />
      {/* 팔 */}
      <path d="M 20 55 Q 10 65 15 75 M 80 55 Q 95 45 95 65 L 85 65" stroke="#1e1e24" strokeWidth="3" fill="none" strokeLinecap="round" />
      {/* 몸통 */}
      <rect x="25" y="20" width="50" height="65" rx="8" fill={color} stroke="#1e1e24" strokeWidth="3" />
      {/* 화면 (얼굴) */}
      <rect x="35" y="30" width="30" height="25" rx="4" fill="#0F172A" stroke="#1e1e24" strokeWidth="2" />
      <Face x={0} y={-5} type="happy" color="#4ADE80" />
      {/* 주유 호스와 건 */}
      <path d="M 75 35 Q 95 35 95 50 Q 95 70 85 65" stroke="#333" strokeWidth="4" fill="none" strokeLinecap="round" />
      <path d="M 85 65 L 80 60 V 68 Z" fill="#FACC15" stroke="#1e1e24" strokeWidth="2" />
    </svg>
  ),

  // 5. 우편번호: 파닥거리는 우편새
  zipcode_search: ({ color = "#A78BFA", className }) => (
    <svg viewBox="0 0 100 100" className={className} width="1em" height="1em">
      <Limbs type="jump" yOffset={-15} />
      {/* 날개 */}
      <path d="M 20 40 Q 5 30 10 15 Q 15 25 20 25 M 80 40 Q 95 30 90 15 Q 85 25 80 25" fill="#fff" stroke="#1e1e24" strokeWidth="3" strokeLinejoin="round" />
      {/* 편지봉투 몸통 */}
      <rect x="15" y="35" width="70" height="45" rx="5" fill={color} stroke="#1e1e24" strokeWidth="3" />
      <path d="M 15 40 L 50 65 L 85 40" fill="none" stroke="#1e1e24" strokeWidth="3" strokeLinejoin="round" />
      {/* 왁스 씰 & 얼굴 */}
      <circle cx="50" cy="65" r="8" fill="#EF4444" stroke="#1e1e24" strokeWidth="2" />
      <circle cx="50" cy="65" r="4" fill="#B91C1C" opacity="0.5" />
      <Face x={0} y={-5} type="excited" />
      {/* 우체부 모자 */}
      <path d="M 40 35 L 60 35 L 65 25 L 35 25 Z" fill="#3B82F6" stroke="#1e1e24" strokeWidth="2" strokeLinejoin="round" />
      <path d="M 30 35 L 70 35 Q 75 35 75 40 H 25 Q 25 35 30 35 Z" fill="#1e1e24" />
    </svg>
  ),

  // 6. 부동산: 눈/코/입이 달린 살아있는 집
  real_estate_price: ({ color = "#10B981", className }) => (
    <svg viewBox="0 0 100 100" className={className} width="1em" height="1em">
      {/* 굴뚝 연기 */}
      <circle cx="75" cy="25" r="5" fill="#94A3B8" opacity="0.6" />
      <circle cx="82" cy="15" r="7" fill="#94A3B8" opacity="0.6" />
      <circle cx="92" cy="8" r="9" fill="#94A3B8" opacity="0.6" />
      <Limbs type="stand" />
      {/* 집 본체 */}
      <path d="M 10 45 L 50 15 L 90 45" fill="none" stroke="#1e1e24" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
      <polygon points="10,45 50,15 90,45 90,80 10,80" fill={color} stroke="#1e1e24" strokeWidth="3" strokeLinejoin="round" />
      {/* 굴뚝 */}
      <rect x="70" y="20" width="10" height="15" fill="#EF4444" stroke="#1e1e24" strokeWidth="2" />
      <polygon points="10,45 50,15 90,45" fill="#FCD34D" stroke="#1e1e24" strokeWidth="3" strokeLinejoin="round" />
      {/* 눈 (창문) */}
      <rect x="25" y="50" width="15" height="15" rx="2" fill="white" stroke="#1e1e24" strokeWidth="2" />
      <rect x="60" y="50" width="15" height="15" rx="2" fill="white" stroke="#1e1e24" strokeWidth="2" />
      <circle cx="32" cy="57" r="3" fill="#1e1e24" />
      <circle cx="67" cy="57" r="3" fill="#1e1e24" />
      <path d="M 25 57 H 40 M 32 50 V 65 M 60 57 H 75 M 67 50 V 65" stroke="#1e1e24" strokeWidth="1" />
      {/* 입 (문) */}
      <path d="M 43 80 V 68 C 43 65 57 65 57 68 V 80" fill="#B45309" stroke="#1e1e24" strokeWidth="2" />
      <circle cx="46" cy="74" r="1.5" fill="#1e1e24" />
    </svg>
  ),

  // 7. 지하철: 전동차 얼굴 캐릭터
  seoul_subway_arrival: ({ color = "#3B82F6", className }) => (
    <svg viewBox="0 0 100 100" className={className} width="1em" height="1em">
      <path d="M 25 60 L 15 55 M 75 60 L 85 55" stroke="#1e1e24" strokeWidth="4" strokeLinecap="round" />
      {/* 선로 위 바퀴 */}
      <circle cx="35" cy="85" r="6" fill="#475569" stroke="#1e1e24" strokeWidth="2" />
      <circle cx="65" cy="85" r="6" fill="#475569" stroke="#1e1e24" strokeWidth="2" />
      <path d="M 15 91 L 85 91 M 15 95 L 85 95" stroke="#1e1e24" strokeWidth="2" fill="none" opacity="0.5" />
      {/* 열차 몸통 */}
      <rect x="20" y="25" width="60" height="60" rx="10" fill={color} stroke="#1e1e24" strokeWidth="3" />
      <rect x="25" y="32" width="50" height="25" rx="5" fill="#0F172A" stroke="#1e1e24" strokeWidth="2" />
      <path d="M 50 32 V 57" stroke="#1e1e24" strokeWidth="2" />
      {/* 헤드라이트 (눈) / 사실 표정으로 대체 */}
      <Face x={0} y={-5} type="cool" color="#4ADE80" />
      {/* 기관사 모자 */}
      <path d="M 30 25 V 15 C 30 10 70 10 70 15 V 25" fill="#1e293b" stroke="#1e1e24" strokeWidth="2" strokeLinejoin="round" />
      <path d="M 25 25 H 75" stroke="#FACC15" strokeWidth="3" strokeLinecap="round" />
      <circle cx="50" cy="18" r="3" fill="#FACC15" />
    </svg>
  ),

  // 8. 다이소 검색: 카트 몬스터
  daiso_search: ({ color = "#EC4899", className }) => (
    <svg viewBox="0 0 100 100" className={className} width="1em" height="1em">
      {/* 앞 발(손)과 뒷 발(바퀴) */}
      <circle cx="70" cy="85" r="6" fill="#475569" stroke="#1e1e24" strokeWidth="2" />
      <circle cx="35" cy="85" r="6" fill="#475569" stroke="#1e1e24" strokeWidth="2" />
      <path d="M 25 45 Q 10 50 15 65" stroke="#1e1e24" strokeWidth="4" strokeLinecap="round" fill="none" />
      {/* 카트 몸통 */}
      <path d="M 20 30 H 80 L 75 75 H 30 Z" fill={color} stroke="#1e1e24" strokeWidth="3" strokeLinejoin="round" />
      {/* 그물망 패턴 */}
      <path d="M 30 45 H 78 M 32 60 H 76 M 45 30 L 40 75 M 65 30 L 60 75" stroke="#1e1e24" strokeWidth="2" opacity="0.3" />
      {/* 카트 손잡이 */}
      <path d="M 80 30 L 90 20 L 95 25" stroke="#475569" strokeWidth="4" fill="none" strokeLinecap="round" strokeLinejoin="round" />
      {/* 장바구니 바구니 (손에 든 것) */}
      <rect x="5" y="60" width="15" height="10" fill="#EF4444" stroke="#1e1e24" strokeWidth="1.5" />
      <path d="M 8 60 C 8 55 17 55 17 60" fill="none" stroke="#1e1e24" strokeWidth="1.5" />
      <Face x={2} y={5} type="wink" color="#fff" />
    </svg>
  ),

  // 9. 다이소 재고: 체크하는 클립보드 박사
  daiso_pickup_stock: ({ color = "#F472B6", className }) => (
    <svg viewBox="0 0 100 100" className={className} width="1em" height="1em">
      <Limbs type="stand" yOffset={-5} />
      <path d="M 20 40 L 10 45" stroke="#1e1e24" strokeWidth="4" fill="none" strokeLinecap="round" />
      <path d="M 80 40 L 95 50" stroke="#1e1e24" strokeWidth="4" fill="none" strokeLinecap="round" />
      {/* 몸통 (클립보드 판) */}
      <rect x="20" y="25" width="60" height="60" rx="4" fill={color} stroke="#1e1e24" strokeWidth="3" />
      {/* 종이 */}
      <rect x="25" y="30" width="50" height="50" rx="2" fill="white" stroke="#1e1e24" strokeWidth="2" />
      {/* 은색 클립 (모자 느낌) */}
      <path d="M 35 25 V 15 H 65 V 25 Z" fill="#CBD5E1" stroke="#1e1e24" strokeWidth="2" strokeLinejoin="round" />
      <circle cx="50" cy="20" r="2" fill="#1e1e24" />
      <Face x={0} y={10} type="happy" />
      {/* 돋보기 (손에 든) */}
      <line x1="90" y1="50" x2="80" y2="60" stroke="#B45309" strokeWidth="4" strokeLinecap="round" />
      <circle cx="75" cy="65" r="10" fill="#E0F2FE" stroke="#1e1e24" strokeWidth="2" opacity="0.9" />
      <path d="M 70 60 Q 75 62 78 58" stroke="white" strokeWidth="2" fill="none" strokeLinecap="round" />
    </svg>
  ),

  // 10. 쿠팡 로켓: 고글 쓴 로켓돌이
  coupang_search: ({ color = "#8B5CF6", className }) => (
    <svg viewBox="0 0 100 100" className={className} width="1em" height="1em">
      {/* 불꽃 */}
      <path d="M 40 80 Q 50 100 60 80 Q 50 90 40 80 Z" fill="#FACC15" stroke="#EF4444" strokeWidth="2" />
      <path d="M 45 80 Q 50 90 55 80 Z" fill="#EF4444" />
      <path d="M 30 65 L 15 50 L 30 50 Z" fill="#F43F5E" stroke="#1e1e24" strokeWidth="2" strokeLinejoin="round" />
      <path d="M 70 65 L 85 50 L 70 50 Z" fill="#F43F5E" stroke="#1e1e24" strokeWidth="2" strokeLinejoin="round" />
      {/* 파닥거리는 팔 */}
      <path d="M 30 45 Q 15 50 20 60 M 70 45 Q 85 50 80 60" stroke="#1e1e24" strokeWidth="3" fill="none" strokeLinecap="round" />
      {/* 로켓 바디 */}
      <path d="M 50 10 C 20 30 30 80 30 80 H 70 C 70 80 80 30 50 10 Z" fill={color} stroke="#1e1e24" strokeWidth="3" strokeLinejoin="round" />
      {/* 줄무늬 포인트 */}
      <path d="M 31 70 H 69 M 35 75 H 65" stroke="white" strokeWidth="2" opacity="0.5" />
      <Face x={0} y={15} type="goggle" />
    </svg>
  ),

  // 11. 올리브영 매장: 립스틱 아가씨
  oliveyoung_store_search: ({ color = "#F43F5E", className }) => (
    <svg viewBox="0 0 100 100" className={className} width="1em" height="1em">
      <Limbs type="stand" yOffset={0} />
      {/* 베이스 골드 튜브 */}
      <rect x="35" y="55" width="30" height="30" rx="3" fill="#FBBF24" stroke="#1e1e24" strokeWidth="3" />
      {/* 립스틱 내용물 (모자) */}
      <path d="M 40 55 V 35 L 55 25 L 60 30 V 55 Z" fill={color} stroke="#1e1e24" strokeWidth="3" strokeLinejoin="round" />
      {/* 다이아몬드 윤기 */}
      <path d="M 45 38 V 50" stroke="white" strokeWidth="3" fill="none" opacity="0.6" strokeLinecap="round" />
      <Face x={0} y={15} type="wink" />
      {/* 긴 속눈썹 추가 패치 */}
      <path d="M 35 63 Q 32 60 30 63 M 65 63 Q 68 60 70 63" stroke="#1e1e24" strokeWidth="1.5" fill="none" strokeLinecap="round" />
    </svg>
  ),

  // 12. 올리브영 상품: 디스펜서 로션
  oliveyoung_product_search: ({ color = "#FB7185", className }) => (
    <svg viewBox="0 0 100 100" className={className} width="1em" height="1em">
      <Limbs type="stand" yOffset={-10} />
      {/* 비눗방울 */}
      <circle cx="85" cy="30" r="6" fill="#E0F2FE" stroke="#1e1e24" strokeWidth="1.5" opacity="0.8" />
      <circle cx="75" cy="20" r="4" fill="#E0F2FE" stroke="#1e1e24" strokeWidth="1.5" opacity="0.8" />
      {/* 팔 (한 손은 펌프를 누름) */}
      <path d="M 25 55 Q 15 45 40 25 M 75 55 Q 85 45 80 35" stroke="#1e1e24" strokeWidth="3" fill="none" strokeLinecap="round" />
      {/* 로션 바디 */}
      <rect x="25" y="45" width="50" height="40" rx="10" fill={color} stroke="#1e1e24" strokeWidth="3" />
      {/* 펌프헤드 & 목 */}
      <rect x="40" y="35" width="20" height="10" fill="#E2E8F0" stroke="#1e1e24" strokeWidth="2" />
      <path d="M 45 35 V 25 M 45 25 H 35 M 45 25 H 65" stroke="#1e1e24" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
      <Face x={0} y={12} type="happy" color="white" />
    </svg>
  ),

  // 13. 올영재고: 체크마크 지팡이를 든 초록 상자
  oliveyoung_inventory: ({ color = "#4ADE80", className }) => (
    <svg viewBox="0 0 100 100" className={className} width="1em" height="1em">
      <Limbs type="stand" yOffset={-5} />
      {/* 팔 (지팡이 잡음) */}
      <path d="M 20 45 Q 10 50 15 65 M 80 45 Q 90 50 85 55" stroke="#1e1e24" strokeWidth="4" fill="none" strokeLinecap="round" />
      {/* OY 헤어밴드 */}
      <path d="M 25 35 C 25 15 75 15 75 35" fill="none" stroke="#F43F5E" strokeWidth="6" strokeLinecap="round" />
      {/* 박스 몬스터 */}
      <rect x="20" y="30" width="60" height="50" rx="8" fill={color} stroke="#1e1e24" strokeWidth="3" />
      <Face x={0} y={10} type="excited" color="white" />
      {/* 큰 체크표 등딱지/무기 */}
      <path d="M 75 65 L 85 85 L 105 45" stroke="#F43F5E" strokeWidth="6" strokeLinecap="round" strokeLinejoin="round" fill="none" />
    </svg>
  ),

  // 14. 중고차: 딜러 넥타이 멘 자동차 캐릭터
  used_car_price: ({ color = "#6366F1", className }) => (
    <svg viewBox="0 0 100 100" className={className} width="1em" height="1em">
      {/* 바퀴 */}
      <circle cx="25" cy="80" r="10" fill="#1e293b" stroke="#1e1e24" strokeWidth="3" />
      <circle cx="75" cy="80" r="10" fill="#1e293b" stroke="#1e1e24" strokeWidth="3" />
      <circle cx="25" cy="80" r="4" fill="#cbd5e1" />
      <circle cx="75" cy="80" r="4" fill="#cbd5e1" />
      <path d="M 10 65 Q -5 65 0 85 M 90 65 Q 105 65 100 85" stroke="#1e1e24" strokeWidth="3" fill="none" strokeLinecap="round" /> // 팔
      {/* 윗부분 창문 */}
      <path d="M 20 45 L 30 25 H 70 L 80 45 Z" fill="#E2E8F0" stroke="#1e1e24" strokeWidth="3" strokeLinejoin="round" />
      {/* 몸통 */}
      <rect x="10" y="45" width="80" height="30" rx="8" fill={color} stroke="#1e1e24" strokeWidth="3" />
      {/* 그릴 (입)과 헤드라이트 (눈) */}
      <circle cx="20" cy="55" r="5" fill="#FACC15" stroke="#1e1e24" strokeWidth="2" />
      <circle cx="80" cy="55" r="5" fill="#FACC15" stroke="#1e1e24" strokeWidth="2" />
      <path d="M 35 65 Q 50 75 65 65" stroke="#1e1e24" strokeWidth="3" fill="none" strokeLinecap="round" />
      {/* 딜러 넥타이 */}
      <polygon points="48,50 52,50 55,60 50,65 45,60" fill="#EF4444" stroke="#1e1e24" strokeWidth="1" />
    </svg>
  ),

  // 15. 맛집 블루리본: 클로쉬(음식 덮개)에서 빼꼼
  blue_ribbon_nearby: ({ color = "#F97316", className }) => (
    <svg viewBox="0 0 100 100" className={className} width="1em" height="1em">
      <Limbs type="sit" yOffset={-10} />
      {/* 속에 있는 얼굴 (음식) */}
      <circle cx="50" cy="65" r="20" fill={color} />
      <Face x={0} y={15} type="happy" color="white" />
      {/* 덮개 열린 각도 */}
      <path d="M 10 70 A 40 40 0 0 1 90 70 A 40 10 0 0 1 10 70 Z" fill="none" stroke="#1e1e24" strokeWidth="4" strokeLinejoin="round" transform="translate(0,-15) rotate(-15 50 50)" />
      {/* 리본 */}
      <path d="M 40 50 L 30 65 L 45 60 Z M 60 50 L 70 65 L 55 60 Z" fill="#3B82F6" stroke="#1e1e24" strokeWidth="2" strokeLinejoin="round" />
      <circle cx="50" cy="55" r="5" fill="#3B82F6" stroke="#1e1e24" strokeWidth="2" />
      <circle cx="50" cy="55" r="2" fill="white" />
      <path d="M 15 50 Q 5 60 5 70" stroke="#1e1e24" strokeWidth="3" fill="none" strokeLinecap="round" />
    </svg>
  ),

  // 16. 술집: 거품 머리 맥주잔 병정
  kakao_bar_nearby: ({ color = "#FBBF24", className }) => (
    <svg viewBox="0 0 100 100" className={className} width="1em" height="1em">
      <Limbs type="stand" />
      <path d="M 25 55 Q 10 55 15 45 M 75 55 Q 90 55 85 45" stroke="#1e1e24" strokeWidth="4" fill="none" strokeLinecap="round" />
      {/* 손잡이 */}
      <path d="M 75 35 Q 95 35 95 50 Q 95 65 75 65" stroke="#1e1e24" strokeWidth="4" fill="none" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M 75 42 Q 85 42 85 50 Q 85 58 75 58" fill="none" />
      {/* 몸통 (맥주) */}
      <rect x="25" y="30" width="50" height="50" rx="3" fill={color} stroke="#1e1e24" strokeWidth="3" />
      {/* 거품 머리 (구름 모양) */}
      <path d="M 20 30 Q 15 20 25 10 Q 40 -5 50 10 Q 60 -5 75 10 Q 85 20 80 30 Z" fill="#FFF" stroke="#1e1e24" strokeWidth="3" strokeLinejoin="round" />
      <Face x={0} y={15} type="excited" />
      {/* 양 볼 빨간 홍조 강하게 */}
      <ellipse cx="33" cy="65" rx="6" ry="4" fill="#EF4444" opacity="0.7"/>
      <ellipse cx="67" cy="65" rx="6" ry="4" fill="#EF4444" opacity="0.7"/>
      {/* 땅콩 (한 손에) */}
      <ellipse cx="85" cy="40" rx="4" ry="6" fill="#D97706" stroke="#1e1e24" strokeLinecap="round" />
      <ellipse cx="85" cy="48" rx="4" ry="6" fill="#D97706" stroke="#1e1e24" strokeLinecap="round" />
    </svg>
  ),

  // 17. 야구: 모자 쓰고 배트 든 야구공
  kbo_results: ({ color = "#EF4444", className }) => (
    <svg viewBox="0 0 100 100" className={className} width="1em" height="1em">
      <Limbs type="run" yOffset={-5} />
      {/* 배트 */}
      <path d="M 75 65 L 100 20 L 95 15 L 70 60 Z" fill="#D97706" stroke="#1e1e24" strokeWidth="2" strokeLinejoin="round" />
      <path d="M 74 62 L 70 66" stroke="#1e1e24" strokeWidth="3" />
      <circle cx="50" cy="50" r="30" fill="white" stroke="#1e1e24" strokeWidth="3" />
      <path d="M 30 29 A 25 25 0 0 0 30 71 M 70 29 A 25 25 0 0 1 70 71" stroke={color} strokeWidth="3" strokeLinecap="round" fill="none" strokeDasharray="5,5" />
      <Face x={0} y={0} type="cool" />
      {/* 거꾸로 쓴 야구모자 */}
      <path d="M 30 25 Q 50 5 70 25 Z M 70 25 Q 85 25 85 15" fill="#2563EB" stroke="#1e1e24" strokeWidth="2" strokeLinejoin="round" />
    </svg>
  ),

  // 18. 축구: 축구화 신고 공차는 축구공
  kleague_results: ({ color = "#22C55E", className }) => (
    <svg viewBox="0 0 100 100" className={className} width="1em" height="1em">
      {/* 팔 */}
      <path d="M 20 40 Q 10 45 15 55 M 80 40 Q 90 45 85 55" stroke="#1e1e24" strokeWidth="3" strokeLinecap="round" fill="none" />
      {/* 점핑 다리들 + 축구화 */}
      <path d="M 40 75 Q 30 90 20 85 M 60 75 Q 65 90 85 85" stroke="#1e1e24" strokeWidth="3" strokeLinecap="round" fill="none" />
      <rect x="10" y="80" width="15" height="10" rx="3" fill="#EF4444" stroke="#1e1e24" strokeWidth="2" transform="rotate(-15 15 85)" />
      <rect x="75" y="80" width="15" height="10" rx="3" fill="#EF4444" stroke="#1e1e24" strokeWidth="2" transform="rotate(15 85 85)" />
      {/* 별 (차는 공) */}
      <polygon points="85,65 90,75 100,75 92,82 95,92 85,86 75,92 78,82 70,75 80,75" fill="#FACC15" stroke="#1e1e24" strokeWidth="1" transform="scale(0.5) translate(100, 100)" />
      {/* 축구공 몸 */}
      <circle cx="50" cy="45" r="30" fill="white" stroke="#1e1e24" strokeWidth="3" />
      {/* 오각형 무늬 */}
      <polygon points="50,25 65,35 60,50 40,50 35,35" fill="#1e1e24" />
      <polygon points="30,60 20,50 30,35" fill="#1e1e24" opacity="0.2"/>
      <polygon points="70,60 80,50 70,35" fill="#1e1e24" opacity="0.2"/>
      <polygon points="40,75 50,65 60,75" fill="#1e1e24" opacity="0.2" />
      <Face x={0} y={-5} type="happy" color="white" />
    </svg>
  ),

  // 19. 롤결과: 게이머 헤드셋 쓴 패드
  lck_results: ({ color = "#8B5CF6", className }) => (
    <svg viewBox="0 0 100 100" className={className} width="1em" height="1em">
      <Limbs type="sit" yOffset={-10} />
      {/* 헤드셋 마이크 */}
      <path d="M 20 40 Q 15 65 30 70" stroke="#1e1e24" strokeWidth="3" fill="none" strokeLinecap="round" />
      <circle cx="30" cy="70" r="3" fill="#EF4444" />
      {/* 패드 몸통 */}
      <path d="M 20 40 C 10 40 5 60 10 70 C 20 90 30 80 40 70 L 60 70 C 70 80 80 90 90 70 C 95 60 90 40 80 40 Z" fill={color} stroke="#1e1e24" strokeWidth="3" strokeLinejoin="round" />
      {/* 헤드셋 밴드 & 귀걸개 */}
      <path d="M 15 45 C 15 15 85 15 85 45" fill="none" stroke="#1e1e24" strokeWidth="5" />
      <rect x="5" y="35" width="15" height="20" rx="5" fill="#333" stroke="#1e1e24" strokeWidth="2" />
      <rect x="80" y="35" width="15" height="20" rx="5" fill="#333" stroke="#1e1e24" strokeWidth="2" />
      {/* 얼굴 및 패드 버튼들 */}
      <Face x={0} y={15} type="excited" color="white" />
      {/* 십자키 */}
      <path d="M 25 55 h 4 v 4 h 4 v 4 h -4 v 4 h -4 v -4 h -4 v -4 h 4 z" fill="white" stroke="#1e1e24" strokeWidth="1" />
      {/* 액션 버튼 */}
      <circle cx="75" cy="55" r="3" fill="#EF4444" />
      <circle cx="82" cy="62" r="3" fill="#3B82F6" />
      <circle cx="68" cy="62" r="3" fill="#FACC15" />
    </svg>
  ),

  // 20. 법률: 판사가발을 쓴 망치
  korean_law_search: ({ color = "#64748B", className }) => (
    <svg viewBox="0 0 100 100" className={className} width="1em" height="1em">
      <Limbs type="stand" />
      <path d="M 20 45 Q 10 50 25 70 M 80 45 Q 90 50 75 70" stroke="#1e1e24" strokeWidth="4" fill="none" strokeLinecap="round" />
      {/* 법전 든 손 */}
      <rect x="15" y="65" width="15" height="20" rx="2" fill="#8B4513" stroke="#1e1e24" strokeWidth="2" />
      <path d="M 20 65 V 85" stroke="#FACC15" strokeWidth="2" />
      {/* 망치 손잡이 */}
      <rect x="42" y="55" width="16" height="35" rx="3" fill="#D97706" stroke="#1e1e24" strokeWidth="3" />
      {/* 망치 머리 */}
      <path d="M 25 25 H 75 V 55 H 25 Z" fill={color} stroke="#1e1e24" strokeWidth="3" strokeLinejoin="round" />
      <path d="M 20 30 H 25 V 50 H 20 Z M 75 30 H 80 V 50 H 75 Z" fill="white" stroke="#1e1e24" strokeWidth="3" strokeLinejoin="round" />
      {/* 판사가발 (하얀 돌돌 말린 머리) */}
      <path d="M 20 30 C 10 20 20 10 30 15 C 40 0 60 0 70 15 C 80 10 90 20 80 30" fill="white" stroke="#1e1e24" strokeWidth="3" strokeLinejoin="round" />
      <Face x={0} y={-5} type="cool" color="white" />
    </svg>
  ),

  // 21. 실록: 갓을 쓴 조선 두루마리
  joseon_sillok_search: ({ color = "#D97706", className }) => (
    <svg viewBox="0 0 100 100" className={className} width="1em" height="1em">
      <Limbs type="stand" yOffset={5} />
      {/* 팔 (뒷짐진 선비 느낌) */}
      <path d="M 30 55 Q 10 60 20 75 M 70 55 Q 90 60 80 75" stroke="#1e1e24" strokeWidth="3" fill="none" strokeLinecap="round" />
      {/* 두루마리 종이 */}
      <path d="M 30 25 H 70 V 75 H 30 Z" fill="#FEF3C7" stroke="#1e1e24" strokeWidth="3" strokeLinejoin="round" />
      {/* 양 끝단 (말린 부분) */}
      <ellipse cx="30" cy="25" rx="10" ry="4" fill={color} stroke="#1e1e24" strokeWidth="2" />
      <ellipse cx="70" cy="25" rx="10" ry="4" fill={color} stroke="#1e1e24" strokeWidth="2" />
      <ellipse cx="30" cy="75" rx="10" ry="4" fill={color} stroke="#1e1e24" strokeWidth="2" />
      <ellipse cx="70" cy="75" rx="10" ry="4" fill={color} stroke="#1e1e24" strokeWidth="2" />
      {/* 갓 (조선시대 모자) */}
      <path d="M 10 25 H 90 M 35 25 V 5 H 65 V 25" fill="#1e1e24" stroke="#1e1e24" strokeWidth="3" strokeLinejoin="round" />
      <Face x={0} y={10} type="happy" />
      {/* 글씨 흉내 */}
      <path d="M 60 30 v 30 M 50 30 v 25 M 40 30 v 30" stroke="#1e1e24" strokeWidth="2" strokeDasharray="4,4" fill="none" />
    </svg>
  ),

  // 22. 맞춤법: 안경 쓴 학구파 연필
  korean_spell_check: ({ color = "#14B8A6", className }) => (
    <svg viewBox="0 0 100 100" className={className} width="1em" height="1em">
      <Limbs type="stand" />
      <path d="M 30 45 Q 15 50 25 70" stroke="#1e1e24" strokeWidth="3" fill="none" strokeLinecap="round" /> // 한 팔
      {/* 지우개 든 팔 */}
      <path d="M 70 45 Q 90 40 85 30" stroke="#1e1e24" strokeWidth="3" fill="none" strokeLinecap="round" />
      <rect x="75" y="20" width="15" height="15" rx="2" fill="#F472B6" stroke="#1e1e24" strokeWidth="2" /> // 지우개
      {/* 연필 바디 */}
      <polygon points="30,15 70,15 70,60 50,85 30,60" fill={color} stroke="#1e1e24" strokeWidth="3" strokeLinejoin="round" />
      <polygon points="30,60 70,60 50,85" fill="#FDE047" stroke="#1e1e24" strokeWidth="2" />
      <polygon points="45,78 55,78 50,85" fill="#1e1e24" /> // 심
      {/* 연필 머리 지우개 부분 */}
      <rect x="30" y="5" width="40" height="10" rx="2" fill="#F472B6" stroke="#1e1e24" strokeWidth="3" />
      <rect x="30" y="15" width="40" height="5" fill="#94A3B8" stroke="#1e1e24" strokeWidth="3" />
      {/* 둥근 안경 */}
      <circle cx="42" cy="35" r="7" fill="white" stroke="#1e1e24" strokeWidth="2" />
      <circle cx="58" cy="35" r="7" fill="white" stroke="#1e1e24" strokeWidth="2" />
      <path d="M 49 35 H 51" stroke="#1e1e24" strokeWidth="2" />
      <circle cx="42" cy="35" r="2" fill="#1e1e24" />
      <circle cx="58" cy="35" r="2" fill="#1e1e24" />
      <path d="M 47 45 Q 50 48 53 45" stroke="#1e1e24" strokeWidth="2" fill="none" strokeLinecap="round" /> // 입
    </svg>
  ),

  // 23. 한글 변환: 유생 모자를 쓴 두툼한 문서
  hwp_convert: ({ color = "#0EA5E9", className }) => (
    <svg viewBox="0 0 100 100" className={className} width="1em" height="1em">
      <Limbs type="sit" yOffset={0} />
      <path d="M 25 55 Q 10 50 15 65 M 75 55 Q 90 50 85 75 L 90 85" stroke="#1e1e24" strokeWidth="3" fill="none" strokeLinecap="round" />
      {/* 붓 (오른손) */}
      <path d="M 90 85 L 85 70 L 95 65 Z" fill="#1e1e24" stroke="#1e1e24" strokeWidth="1" strokeLinejoin="round" />
      <path d="M 90 67 L 100 40" stroke="#8B4513" strokeWidth="3" strokeLinecap="round" />
      {/* 두툼한 문서 바디 */}
      <path d="M 20 20 H 60 L 80 40 V 80 H 20 Z" fill="white" stroke="#1e1e24" strokeWidth="3" strokeLinejoin="round" />
      <path d="M 60 20 V 40 H 80" fill="none" stroke="#1e1e24" strokeWidth="3" strokeLinejoin="round" />
      {/* 한글 로고 컬러 (배 부위) */}
      <rect x="35" y="60" width="30" height="10" rx="3" fill={color} stroke="#1e1e24" strokeWidth="2" />
      {/* 복건 (유생 모자) */}
      <path d="M 30 20 C 30 5 70 5 70 20 L 60 20 L 50 10 L 40 20 Z" fill="#1e1e24" stroke="#1e1e24" strokeWidth="2" strokeLinejoin="round" />
      <path d="M 25 20 Q 20 40 10 45 M 75 20 Q 80 40 90 45" stroke="#1e1e24" strokeWidth="4" fill="none" strokeLinecap="round" /> // 모자 끈
      <Face x={0} y={15} type="wink" />
    </svg>
  ),

  // 24. 로또: 공을 품고 도는 가챠 머신
  lotto_results: ({ color = "#FACC15", className }) => (
    <svg viewBox="0 0 100 100" className={className} width="1em" height="1em">
      <Limbs type="stand" yOffset={5} />
      <path d="M 20 60 Q -5 40 5 30 M 80 60 Q 105 40 95 30" stroke="#1e1e24" strokeWidth="3" fill="none" strokeLinecap="round" /> // 신나는 팔
      {/* 기계 본체 */}
      <path d="M 25 55 H 75 V 85 L 65 95 H 35 L 25 85 Z" fill={color} stroke="#1e1e24" strokeWidth="3" strokeLinejoin="round" />
      {/* 유리 돔 */}
      <circle cx="50" cy="40" r="30" fill="#E0F2FE" stroke="#1e1e24" strokeWidth="3" opacity="0.9" />
      {/* 로또 공들 */}
      <circle cx="40" cy="55" r="8" fill="#EF4444" stroke="#1e1e24" strokeWidth="1.5" />
      <circle cx="60" cy="55" r="8" fill="#3B82F6" stroke="#1e1e24" strokeWidth="1.5" />
      <circle cx="50" cy="40" r="8" fill="#FACC15" stroke="#1e1e24" strokeWidth="1.5" />
      <circle cx="35" cy="40" r="8" fill="#10B981" stroke="#1e1e24" strokeWidth="1.5" />
      <circle cx="65" cy="42" r="8" fill={color} stroke="#1e1e24" strokeWidth="1.5" />
      {/* 얼굴은 돔 기계 아래 하단 쪽에 */}
      <Face x={0} y={30} type="excited" color="white" />
      {/* 레버 */}
      <path d="M 75 70 L 90 60" stroke="#1e1e24" strokeWidth="3" strokeLinecap="round" />
      <circle cx="90" cy="60" r="5" fill="#EF4444" stroke="#1e1e24" strokeWidth="2" />
    </svg>
  ),

  // 25. 시간: 수염(바늘) 난 알람시계
  get_current_time: ({ color = "#F472B6", className }) => (
    <svg viewBox="0 0 100 100" className={className} width="1em" height="1em">
      <Limbs type="run" yOffset={0} />
      <path d="M 15 50 Q 5 40 10 30 M 85 50 Q 95 40 90 30" stroke="#1e1e24" strokeWidth="4" fill="none" strokeLinecap="round" /> // 시계 치는 손
      {/* 귀(종) */}
      <circle cx="25" cy="25" r="12" fill={color} stroke="#1e1e24" strokeWidth="3" />
      <circle cx="75" cy="25" r="12" fill={color} stroke="#1e1e24" strokeWidth="3" />
      <path d="M 40 15 Q 50 5 60 15" stroke="#1e1e24" strokeWidth="3" fill="none" strokeLinecap="round" /> // 손잡이
      {/* 시계 얼굴 */}
      <circle cx="50" cy="55" r="35" fill="white" stroke="#1e1e24" strokeWidth="3" />
      {/* 얼굴 - 수염 대신 멋진 콧수염처럼 시계바늘을 표현할까 하다가 그냥 귀여운 얼굴 위에 바늘 */}
      <Face x={0} y={15} type="cool" />
      {/* 시계 바늘 (콧수염 같은 위치) */}
      <path d="M 50 63 L 35 55 M 50 63 L 65 60" stroke="#EF4444" strokeWidth="3" strokeLinecap="round" />
      <circle cx="50" cy="63" r="3" fill="#1e1e24" />
      <circle cx="35" cy="55" r="2" fill="#EF4444" />
      <circle cx="65" cy="60" r="2" fill="#EF4444" />
    </svg>
  ),

  // 26. 계산기: 자기 버튼을 누르는 레트로 계산기
  calculate: ({ color = "#A3E635", className }) => (
    <svg viewBox="0 0 100 100" className={className} width="1em" height="1em">
      <Limbs type="stand" yOffset={-10} />
      {/* 버튼을 누르는 자기 팔 */}
      <path d="M 20 60 Q 0 50 15 30 Q 30 10 40 50" stroke="#1e1e24" strokeWidth="4" fill="none" strokeLinecap="round" /> 
      <path d="M 80 60 Q 100 60 90 80" stroke="#1e1e24" strokeWidth="4" fill="none" strokeLinecap="round" /> 
      {/* 계산기 본체 */}
      <rect x="25" y="15" width="50" height="70" rx="8" fill={color} stroke="#1e1e24" strokeWidth="4" />
      {/* 화면 (이곳이 눈동자가 됨) */}
      <rect x="32" y="25" width="36" height="15" rx="3" fill="#0F172A" stroke="#1e1e24" strokeWidth="2" />
      <text x="36" y="37" fill="#4ADE80" fontFamily="monospace" fontSize="12" fontWeight="bold">0.123</text>
      {/* 볼터치, 입은 본체 껍질에 방긋하게 */}
      <path d="M 45 45 Q 50 50 55 45" stroke="#1e1e24" strokeWidth="3" fill="none" strokeLinecap="round" />
      <ellipse cx="37" cy="45" rx="3" ry="1.5" fill="#FF8A8A" opacity="0.6"/>
      <ellipse cx="63" cy="45" rx="3" ry="1.5" fill="#FF8A8A" opacity="0.6"/>
      {/* 둥근 버튼들 */}
      <circle cx="35" cy="60" r="4" fill="white" stroke="#1e1e24" strokeWidth="2" />
      <circle cx="50" cy="60" r="4" fill="white" stroke="#1e1e24" strokeWidth="2" />
      <circle cx="65" cy="60" r="4" fill="white" stroke="#1e1e24" strokeWidth="2" />
      <circle cx="35" cy="72" r="4" fill="white" stroke="#1e1e24" strokeWidth="2" />
      <circle cx="50" cy="72" r="4" fill="white" stroke="#1e1e24" strokeWidth="2" />
      <circle cx="65" cy="72" r="4" fill="#EF4444" stroke="#1e1e24" strokeWidth="2" />
      <circle cx="40" cy="50" r="3" fill="white" opacity="0.7" /> // 누르는 손 끝
    </svg>
  ),
};

export default Icons;
