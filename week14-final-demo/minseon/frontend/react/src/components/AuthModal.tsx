import { useState } from 'react'
import { login, signup } from '../api/client'
import { useChatStore } from '../store/chatStore'

interface Props {
  onClose: () => void
}

export default function AuthModal({ onClose }: Props) {
  const [mode, setMode] = useState<'login' | 'signup'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const setUser = useChatStore((s) => s.setUser)

  const handleSubmit = async () => {
    if (!email || !password) return
    setLoading(true)
    setError('')
    try {
      if (mode === 'login') {
        const res = await login(email, password)
        setUser({ email: res.email, access_token: res.access_token })
        onClose()
      } else {
        await signup(email, password)
        setError('회원가입 완료! 이메일 인증 후 로그인하세요.')
        setMode('login')
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '오류가 발생했습니다')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={onClose}>
      <div
        className="bg-[#1e1e1e] border border-[#333] rounded-2xl p-6 w-80"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-5">
          <h3 className="text-white font-semibold">
            {mode === 'login' ? '로그인' : '회원가입'}
          </h3>
          <button onClick={onClose} className="text-gray-500 hover:text-white">x</button>
        </div>

        <div className="flex gap-1 bg-[#2a2a2a] rounded-lg p-1 mb-4">
          {(['login', 'signup'] as const).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`flex-1 py-1.5 rounded-md text-sm transition-colors ${
                mode === m ? 'bg-[#444] text-white' : 'text-gray-500'
              }`}
            >
              {m === 'login' ? '로그인' : '회원가입'}
            </button>
          ))}
        </div>

        <div className="flex flex-col gap-3">
          <input
            type="email"
            placeholder="이메일"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="bg-[#2a2a2a] border border-[#3a3a3a] rounded-xl px-3 py-2.5 text-sm text-white placeholder-gray-500 outline-none focus:border-[#4a7cff]"
          />
          <input
            type="password"
            placeholder="비밀번호"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
            className="bg-[#2a2a2a] border border-[#3a3a3a] rounded-xl px-3 py-2.5 text-sm text-white placeholder-gray-500 outline-none focus:border-[#4a7cff]"
          />
          {error && <p className="text-sm text-red-400">{error}</p>}
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="bg-[#4a7cff] hover:bg-[#3a6cef] text-white py-2.5 rounded-xl text-sm font-medium disabled:opacity-50 transition-colors"
          >
            {loading ? '처리 중...' : mode === 'login' ? '로그인' : '회원가입'}
          </button>
        </div>
      </div>
    </div>
  )
}
