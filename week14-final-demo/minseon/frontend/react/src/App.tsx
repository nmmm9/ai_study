import { useEffect, useRef, useState } from 'react'
import { useChatStore } from './store/chatStore'
import CategoryGrid from './components/CategoryGrid'
import ChatBubble from './components/ChatBubble'
import ChatInput from './components/ChatInput'
import Sidebar from './components/Sidebar'
import AuthModal from './components/AuthModal'
import ProfileModal from './components/ProfileModal'

export default function App() {
  const { messages, isStreaming } = useChatStore()
  const [showAuth, setShowAuth] = useState(false)
  const [showProfile, setShowProfile] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const showWelcome = messages.length === 0

  return (
    <div className="flex h-screen w-screen overflow-hidden">
      <Sidebar onAuthClick={() => setShowAuth(true)} onProfileClick={() => setShowProfile(true)} />

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
