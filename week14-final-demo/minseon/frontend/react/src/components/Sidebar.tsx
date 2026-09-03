import { useChatStore } from '../store/chatStore'
import { deleteSession, logout } from '../api/client'
import type { Session } from '../types'

interface Props {
  onAuthClick:    () => void
  onProfileClick: () => void
  onSessionLoad:  (session: Session) => void   // History API + View Transitions
  onNewChat:      () => void                   // History API + View Transitions
}

export default function Sidebar({ onAuthClick, onProfileClick, onSessionLoad, onNewChat }: Props) {
  const { sessions, user, currentSessionId, setSessions, clearMessages, setUser } = useChatStore()

  const handleLogout = async () => {
    await logout()
    setUser(null)
    setSessions([])
    clearMessages()
  }

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    if (!user?.access_token) return
    await deleteSession(user.access_token, id)
    setSessions(sessions.filter((s) => s.id !== id))
    if (currentSessionId === id) clearMessages()
  }

  return (
    <aside className="w-60 flex flex-col bg-[#111] border-r border-[#2a2a2a] h-full">
      <div className="p-4 border-b border-[#2a2a2a]">
        <h2 className="text-white font-bold text-lg">청년정책 AI</h2>
      </div>

      <div className="p-3">
        <button
          onClick={onNewChat}
          className="w-full py-2 rounded-xl text-sm text-gray-300 border border-[#333] hover:bg-[#222] transition-colors"
        >
          + 새 대화
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-2">
        {sessions.length === 0 && (
          <p className="text-gray-600 text-xs text-center mt-4">저장된 대화 없음</p>
        )}
        {sessions.map((s: Session) => (
          <div
            key={s.id}
            onClick={() => onSessionLoad(s)}
            className={`
              group flex items-center justify-between px-3 py-2 rounded-lg mb-1 cursor-pointer text-sm
              ${currentSessionId === s.id ? 'bg-[#2a2a2a] text-white' : 'text-gray-400 hover:bg-[#1e1e1e]'}
            `}
          >
            <span className="truncate flex-1">{s.name}</span>
            <button
              onClick={(e) => handleDelete(e, s.id)}
              className="hidden group-hover:block text-gray-600 hover:text-red-400 ml-1 text-xs"
            >
              x
            </button>
          </div>
        ))}
      </div>

      <div className="p-3 border-t border-[#2a2a2a] flex flex-col gap-2">
        {user ? (
          <>
            <div className="text-xs text-gray-500 truncate px-1">{user.email}</div>
            <button
              onClick={onProfileClick}
              className="w-full py-2 rounded-xl text-sm text-gray-300 border border-[#333] hover:bg-[#222] transition-colors"
            >
              내 정보 설정
            </button>
            <button
              onClick={handleLogout}
              className="w-full py-2 rounded-xl text-sm text-red-400 border border-[#333] hover:bg-[#1a1a1a] transition-colors"
            >
              로그아웃
            </button>
          </>
        ) : (
          <button
            onClick={onAuthClick}
            className="w-full py-2 rounded-xl text-sm text-gray-300 border border-[#333] hover:bg-[#222] transition-colors"
          >
            로그인 / 회원가입
          </button>
        )}
      </div>
    </aside>
  )
}
