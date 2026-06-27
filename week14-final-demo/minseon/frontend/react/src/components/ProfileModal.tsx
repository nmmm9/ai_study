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
  { value: '',      label: '선택 안 함' },
  { value: '대학생',  label: '대학생' },
  { value: '구직중',  label: '구직중 (취업 준비)' },
  { value: '재직',    label: '재직 중' },
  { value: '프리랜서', label: '프리랜서 / 자영업' },
  { value: '창업',    label: '창업 준비 중' },
]

// 좌표 → 한국 시도명 매핑 (Nominatim 응답 기반)
const REGION_MAP: Record<string, string> = {
  '서울': '서울', 'Seoul': '서울',
  '경기': '경기', 'Gyeonggi': '경기',
  '인천': '인천', 'Incheon': '인천',
  '부산': '부산', 'Busan': '부산',
  '대구': '대구', 'Daegu': '대구',
  '광주': '광주', 'Gwangju': '광주',
  '대전': '대전', 'Daejeon': '대전',
  '울산': '울산', 'Ulsan': '울산',
  '세종': '세종', 'Sejong': '세종',
  '강원': '강원', 'Gangwon': '강원',
  '충청북': '충북', '충북': '충북', 'North Chungcheong': '충북',
  '충청남': '충남', '충남': '충남', 'South Chungcheong': '충남',
  '전라북': '전북', '전북': '전북', 'North Jeolla': '전북',
  '전라남': '전남', '전남': '전남', 'South Jeolla': '전남',
  '경상북': '경북', '경북': '경북', 'North Gyeongsang': '경북',
  '경상남': '경남', '경남': '경남', 'South Gyeongsang': '경남',
  '제주': '제주', 'Jeju': '제주',
}

export default function ProfileModal({ onClose }: Props) {
  const { profile, setProfile } = useChatStore()
  const [age,        setAge]        = useState(profile?.age?.toString() ?? '')
  const [region,     setRegion]     = useState(profile?.region ?? '')
  const [employment, setEmployment] = useState(profile?.employment_status ?? '')
  const [income,     setIncome]     = useState(profile?.annual_income?.toString() ?? '')
  const [geoLoading, setGeoLoading] = useState(false)
  const [geoError,   setGeoError]   = useState('')

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

  // ── Geolocation API: 현재 위치로 지역 자동 입력 ──
  const handleGeolocate = () => {
    if (!navigator.geolocation) {
      setGeoError('이 브라우저는 위치 정보를 지원하지 않습니다.')
      return
    }
    setGeoLoading(true)
    setGeoError('')
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          const { latitude, longitude } = pos.coords
          // Nominatim (OpenStreetMap) 역지오코딩 — 무료, API 키 불필요
          const res  = await fetch(
            `https://nominatim.openstreetmap.org/reverse?lat=${latitude}&lon=${longitude}&format=json&accept-language=ko`,
            { headers: { 'User-Agent': 'youth-policy-chatbot/1.0' } }
          )
          const data = await res.json()
          const addr = data.address ?? {}
          // 시/도 우선 → state → city_district 순으로 탐색
          const raw  = addr.state ?? addr.city ?? addr.province ?? ''
          const matched = Object.keys(REGION_MAP).find((k) => raw.includes(k))
          if (matched) {
            setRegion(REGION_MAP[matched])
          } else {
            setGeoError('지역을 자동으로 감지하지 못했습니다. 직접 선택해주세요.')
          }
        } catch {
          setGeoError('위치 정보를 가져오는 중 오류가 발생했습니다.')
        }
        setGeoLoading(false)
      },
      (err) => {
        setGeoError(
          err.code === 1
            ? '위치 권한이 거부되었습니다. 브라우저 설정에서 허용해주세요.'
            : '위치를 가져오는 데 실패했습니다.'
        )
        setGeoLoading(false)
      },
      { timeout: 8000 }
    )
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

          {/* 거주 지역 + 자동 감지 버튼 */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-gray-400 text-xs">거주 지역</label>
              {/* Geolocation API 버튼 */}
              <button
                onClick={handleGeolocate}
                disabled={geoLoading}
                title="현재 위치로 자동 입력"
                className="flex items-center gap-1 text-xs text-[#4a7cff] hover:text-[#82b4ff] disabled:text-gray-600 transition-colors"
              >
                {geoLoading ? (
                  <span className="w-3 h-3 border-2 border-[#4a7cff] border-t-transparent rounded-full animate-spin inline-block" />
                ) : (
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 8c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4zm8.94 3c-.46-4.17-3.77-7.48-7.94-7.94V1h-2v2.06C6.83 3.52 3.52 6.83 3.06 11H1v2h2.06c.46 4.17 3.77 7.48 7.94 7.94V23h2v-2.06c4.17-.46 7.48-3.77 7.94-7.94H23v-2h-2.06zM12 19c-3.87 0-7-3.13-7-7s3.13-7 7-7 7 3.13 7 7-3.13 7-7 7z"/>
                  </svg>
                )}
                현재 위치
              </button>
            </div>
            {geoError && <p className="text-red-400 text-xs mb-1">{geoError}</p>}
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

        {(age || region || employment) && (
          <div className="mt-4 p-3 bg-[#2a2a2a] rounded-xl text-xs text-gray-400">
            {age        && <span className="mr-2">만 {age}세</span>}
            {region     && <span className="mr-2">{region}</span>}
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
