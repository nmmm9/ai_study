import { useChat } from '../hooks/useChat'

const CATEGORIES = [
  { label: '일자리', query: '청년 일자리 취업 지원 정책' },
  { label: '진로',   query: '청년 진로 자격증 직업훈련' },
  { label: '창업',   query: '청년 창업 스타트업 지원' },
  { label: '주거',   query: '청년 주거 월세 전세 지원' },
  { label: '금융',   query: '청년 금융 적금 도약계좌' },
  { label: '교육',   query: '청년 장학금 학자금 지원' },
  { label: '마음건강', query: '청년 심리 상담 마음건강' },
  { label: '신체건강', query: '청년 건강검진 의료비 지원' },
  { label: '문화/예술', query: '청년 문화 예술 여가 지원' },
  { label: '생활지원', query: '청년 생활 복지 지원' },
]

export default function CategoryGrid() {
  const { sendMessage } = useChat()

  return (
    <div className="flex flex-col items-center gap-8 py-12">
      <div>
        <h1 className="text-2xl font-bold text-center text-white">청년정책 AI</h1>
        <p className="text-gray-400 text-center mt-2">궁금한 청년정책을 물어보세요</p>
      </div>

      <div className="flex flex-wrap justify-center gap-3 max-w-2xl">
        {CATEGORIES.map((cat) => (
          <button
            key={cat.label}
            onClick={() => sendMessage(cat.query)}
            className="
              px-5 py-2.5 rounded-full text-sm font-medium
              bg-[#2a2a2a] text-white border border-[#444]
              hover:bg-[#f0ede7] hover:text-[#3a3228] hover:border-[#8b7355]
              transition-all duration-200
            "
          >
            {cat.label}
          </button>
        ))}
      </div>

      <div className="flex flex-col gap-2 w-full max-w-xl">
        {[
          '청년도약계좌 가입 조건 알려줘',
          '나에게 맞는 주거 지원 정책 추천해줘',
          '곧 마감되는 청년 정책 알려줘',
        ].map((q) => (
          <button
            key={q}
            onClick={() => sendMessage(q)}
            className="
              text-left px-4 py-3 rounded-xl
              bg-[#2a2a2a] border border-[#3a3a3a]
              text-gray-300 text-sm
              hover:bg-[#333] hover:border-[#555]
              transition-all duration-150
            "
          >
            {q}
          </button>
        ))}
      </div>
    </div>
  )
}
