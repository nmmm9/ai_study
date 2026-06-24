import { useState } from 'react'
import { useChatStore } from '../store/chatStore'

interface Props {
  onClose: () => void
}

const REGIONS = [
  '서울', '경기', '인천', '부산', '대구', '광주', '대전', '울산', '세종',
  '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주',
]

const EMPLOYMENT_OPTIONS = [
  { value: '', label: '선택 안 함' },
  { value: '대학생', label: '대학생' },
  { value: '구직중', label: '구직중 (취업 준비)' },
  { value: '재직', label: '재직 중' },
  { value: '프리랜서', label: '프리랜서 / 자영업' },
  { value: '창업', label: '창업 준비 중' },
]

export default function ProfileModal({ onClose }: Props) {
  const { profile, setProfile } = useChatStore()
  const [age, setAge]                       = useState(profile?.age?.toString() ?? '')
  const [region, setRegion]                 = useState(profile?.region ?? '')
  const [employment, setEmployment]         = useState(profile?.employment_status ?? '')
  const [income, setIncome]                 = useState(profile?.annual_income?.toString() ?? '')

  const handleSave = () => {
    setProfile({
      age:               age ? Number(age) : undefined,
      region:            region || undefined,
      employment_status: employment || undefined,
      annual_income:     income ? Number(income) : undefined,
    })
    onClose()
  }

  const handleClear = () => {
    setAge(''); setRegion(''); setEmployment(''); setIncome('')
    setProfile({})
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={onClose}>
      <div
        className="bg-[#1e1e1e] border border-[#333] rounded-2xl p-6 w-[340px]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-5">
          <h3 className="text-white font-semibold">내 정보</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-white text-lg leading-none">×</button>
        </div>

        <p className="text-gray-500 text-xs mb-4">
          입력하면 맞춤 정책 추천에 자동 활용됩니다.
        </p>

        <div className="flex flex-col gap-3">
          {/* 나이 */}
          <div>
            <label className="text-gray-400 text-xs mb-1 block">만 나이</label>
            <input
              type="number"
              min={19} max={39}
              placeholder="예: 25"
              value={age}
              onChange={(e) => setAge(e.target.value)}
              className="w-full bg-[#2a2a2a] border border-[#3a3a3a] rounded-xl px-3 py-2.5 text-sm text-white placeholder-gray-500 outline-none focus:border-[#4a7cff]"
            />
          </div>

          {/* 거주 지역 */}
          <div>
            <label className="text-gray-400 text-xs mb-1 block">거주 지역</label>
            <select
              value={region}
              onChange={(e) => setRegion(e.target.value)}
              className="w-full bg-[#2a2a2a] border border-[#3a3a3a] rounded-xl px-3 py-2.5 text-sm text-white outline-none focus:border-[#4a7cff]"
            >
              <option value="">선택 안 함</option>
              {REGIONS.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </div>

          {/* 취업 상태 */}
          <div>
            <label className="text-gray-400 text-xs mb-1 block">취업 상태</label>
            <select
              value={employment}
              onChange={(e) => setEmployment(e.target.value)}
              className="w-full bg-[#2a2a2a] border border-[#3a3a3a] rounded-xl px-3 py-2.5 text-sm text-white outline-none focus:border-[#4a7cff]"
            >
              {EMPLOYMENT_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>

          {/* 연 소득 */}
          <div>
            <label className="text-gray-400 text-xs mb-1 block">연 소득 (만 원, 선택)</label>
            <input
              type="number"
              min={0}
              placeholder="예: 2400"
              value={income}
              onChange={(e) => setIncome(e.target.value)}
              className="w-full bg-[#2a2a2a] border border-[#3a3a3a] rounded-xl px-3 py-2.5 text-sm text-white placeholder-gray-500 outline-none focus:border-[#4a7cff]"
            />
          </div>
        </div>

        {/* 저장된 정보 미리보기 */}
        {(age || region || employment) && (
          <div className="mt-4 p-3 bg-[#2a2a2a] rounded-xl text-xs text-gray-400">
            {age && <span className="mr-2">만 {age}세</span>}
            {region && <span className="mr-2">{region}</span>}
            {employment && <span>{employment}</span>}
          </div>
        )}

        <div className="flex gap-2 mt-5">
          <button
            onClick={handleClear}
            className="flex-1 py-2.5 rounded-xl text-sm text-gray-400 border border-[#333] hover:bg-[#222] transition-colors"
          >
            초기화
          </button>
          <button
            onClick={handleSave}
            className="flex-1 py-2.5 rounded-xl text-sm text-white bg-[#4a7cff] hover:bg-[#3a6cef] transition-colors"
          >
            저장
          </button>
        </div>
      </div>
    </div>
  )
}
