import { useState } from 'react'
import { useRouter } from 'next/router'
import Head from 'next/head'

const API = process.env.NEXT_PUBLIC_API_URL || ''

export default function LoginPage() {
  const router = useRouter()
  const [tab, setTab] = useState<'login' | 'signup'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const handleAuth = async () => {
    if (!email || !password) { setError('이메일과 비밀번호를 입력하세요.'); return }
    setLoading(true); setError(''); setSuccess('')
    try {
      const res = await fetch(`${API}/api/auth/${tab}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || '오류 발생')

      if (tab === 'signup') {
        setSuccess('✅ 가입 완료! 로그인 탭에서 로그인하세요.')
        setTab('login')
      } else {
        localStorage.setItem('token', data.token)
        localStorage.setItem('user', JSON.stringify(data.user))
        router.push('/chat')
      }
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <Head><title>취업 상담 AI</title></Head>
      <div style={s.page}>
        <div style={s.card}>
          <div style={s.title}>💼 취업 상담 AI</div>
          <div style={s.sub}>AI 기반 취업공고 분석 서비스</div>

          {/* 탭 */}
          <div style={s.tabs}>
            {(['login', 'signup'] as const).map(t => (
              <button key={t} onClick={() => { setTab(t); setError(''); setSuccess('') }}
                style={{ ...s.tab, ...(tab === t ? s.tabActive : {}) }}>
                {t === 'login' ? '로그인' : '회원가입'}
              </button>
            ))}
          </div>

          {/* 폼 */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <input
              type="email" placeholder="이메일" value={email}
              onChange={e => setEmail(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleAuth()}
            />
            <input
              type="password" placeholder={tab === 'signup' ? '비밀번호 (6자 이상)' : '비밀번호'}
              value={password} onChange={e => setPassword(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleAuth()}
            />
          </div>

          {error   && <div style={s.error}>{error}</div>}
          {success && <div style={s.successMsg}>{success}</div>}

          <button style={s.btn} onClick={handleAuth} disabled={loading}>
            {loading ? '처리 중...' : tab === 'login' ? '로그인' : '회원가입'}
          </button>
        </div>
      </div>
    </>
  )
}

const s: Record<string, React.CSSProperties> = {
  page: {
    minHeight: '100vh', display: 'flex',
    alignItems: 'center', justifyContent: 'center',
    background: '#171717',
  },
  card: {
    width: 380, background: '#1e1e1e',
    border: '1px solid #2a2a2a', borderRadius: 20,
    padding: '36px 32px', display: 'flex',
    flexDirection: 'column', gap: 16,
  },
  title: {
    fontSize: 28, fontWeight: 700, textAlign: 'center',
    background: 'linear-gradient(135deg, #ececec 40%, #10a37f)',
    WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
  },
  sub: { textAlign: 'center', color: '#8e8ea0', fontSize: 14 },
  tabs: { display: 'flex', gap: 8 },
  tab: {
    flex: 1, background: 'transparent',
    color: '#8e8ea0', border: '1px solid #2a2a2a',
    borderRadius: 10, padding: '8px 0', fontSize: 14,
  },
  tabActive: {
    background: 'rgba(16,163,127,0.15)',
    borderColor: '#10a37f', color: '#10a37f',
  },
  btn: {
    background: 'linear-gradient(135deg, #10a37f, #0d8c6d)',
    color: 'white', fontWeight: 600, padding: '12px 0',
    fontSize: 15, borderRadius: 12, marginTop: 4,
    opacity: 1,
  },
  error:      { color: '#ff6b6b', fontSize: 13, textAlign: 'center' },
  successMsg: { color: '#10a37f', fontSize: 13, textAlign: 'center' },
}
