import { useEffect, useRef, useState, useCallback } from 'react'
import { flushSync } from 'react-dom'
import { useChatStore } from './store/chatStore'
import { dbSaveMessages, dbLoadMessages } from './utils/offlineDB'
import { registerServiceWorker, requestNotificationPermission } from './utils/pushNotify'
import CategoryGrid from './components/CategoryGrid'
import ChatBubble from './components/ChatBubble'
import ChatInput from './components/ChatInput'
import Sidebar from './components/Sidebar'
import AuthModal from './components/AuthModal'
import ProfileModal from './components/ProfileModal'
import type { Session } from './types'

export default function App() {
  const { messages, isStreaming, loadSession, clearMessages, setCurrentSession, setMessages } = useChatStore()
  const [showAuth,    setShowAuth]    = useState(false)
  const [showProfile, setShowProfile] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  // ── 스크롤 아래로 ──
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // ── Service Worker 등록 + 알림 권한 요청 ──
  useEffect(() => {
    registerServiceWorker()
    // 3초 후 알림 권한 요청 (사용자 경험을 위해 즉시 요청하지 않음)
    const timer = setTimeout(() => requestNotificationPermission(), 3000)
    return () => clearTimeout(timer)
  }, [])

  // ── IndexedDB: 앱 시작 시 저장된 메시지 복원 ──
  useEffect(() => {
    if (messages.length > 0) return  // 이미 메시지 있으면 복원 스킵
    dbLoadMessages().then((stored) => {
      if (stored.length > 0) {
        setMessages(stored.map((m) => ({ ...m, createdAt: new Date(m.createdAt) })))
      }
    })
  // eslint 규칙 때문에 의존성 배열 비움 (마운트 시 1회만 실행)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // ── IndexedDB: 메시지 변경 시 저장 ──
  useEffect(() => {
    if (messages.length === 0) return
    dbSaveMessages(
      messages.map((m) => ({ ...m, createdAt: m.createdAt.toISOString() }))
    )
  }, [messages])

  // ── History API + View Transitions: 세션 전환 ──
  const handleSessionLoad = useCallback((session: Session) => {
    const doLoad = () => {
      flushSync(() => loadSession(session))
      window.history.pushState({ sessionId: session.id }, '', `?s=${session.id}`)
    }
    if ('startViewTransition' in document) {
      document.startViewTransition(doLoad)
    } else {
      doLoad()
    }
  }, [loadSession])

  // ── History API + View Transitions: 새 대화 ──
  const handleNewChat = useCallback(() => {
    const doNew = () => {
      flushSync(() => {
        clearMessages()
        setCurrentSession('')
      })
      window.history.pushState({}, '', '/')
    }
    if ('startViewTransition' in document) {
      document.startViewTransition(doNew)
    } else {
      doNew()
    }
  }, [clearMessages, setCurrentSession])

  // ── History API: 뒤로가기/앞으로가기 지원 ──
  useEffect(() => {
    const onPop = (e: PopStateEvent) => {
      if (e.state?.sessionId) {
        // TODO: 세션 ID로 세션 로드 (세션 목록에서 찾아 복원)
      } else {
        clearMessages()
        setCurrentSession('')
      }
    }
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [clearMessages, setCurrentSession])

  const showWelcome = messages.length === 0

  return (
    <div className="flex h-screen w-screen overflow-hidden">
      <Sidebar
        onAuthClick={()  => setShowAuth(true)}
        onProfileClick={() => setShowProfile(true)}
        onSessionLoad={handleSessionLoad}
        onNewChat={handleNewChat}
      />

      <main className="flex-1 flex flex-col min-w-0">
        <div className="flex-1 overflow-y-auto">
          {showWelcome ? (
            <CategoryGrid />
          ) : (
            <div className="max-w-3xl mx-auto px-4 py-6">
              {messages.map((msg, i) => (
                <ChatBubble
                  key={msg.id}
                  message={msg}
                  isStreaming={isStreaming && i === messages.length - 1 && msg.role === 'bot'}
                />
              ))}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        <ChatInput />
      </main>

      {showAuth    && <AuthModal    onClose={() => setShowAuth(false)} />}
      {showProfile && <ProfileModal onClose={() => setShowProfile(false)} />}
    </div>
  )
}
