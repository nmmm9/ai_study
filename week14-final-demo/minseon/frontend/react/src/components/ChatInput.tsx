import { useState, useRef, type KeyboardEvent } from 'react'
import { useChat } from '../hooks/useChat'
import { useChatStore } from '../store/chatStore'

export default function ChatInput() {
  const [text, setText] = useState('')
  const { sendMessage } = useChat()
  const isStreaming = useChatStore((s) => s.isStreaming)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSend = () => {
    if (!text.trim() || isStreaming) return
    sendMessage(text)
    setText('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleInput = () => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`
  }

  return (
    <div className="border-t border-[#333] bg-[#1a1a1a] p-4">
      <div className="flex items-end gap-2 bg-[#2a2a2a] border border-[#3a3a3a] rounded-2xl px-4 py-2">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder="청년정책에 대해 무엇이든 물어보세요..."
          rows={1}
          disabled={isStreaming}
          className="
            flex-1 bg-transparent text-sm text-white placeholder-gray-500
            resize-none outline-none py-1.5 max-h-40
          "
        />
        <button
          onClick={handleSend}
          disabled={!text.trim() || isStreaming}
          className="
            w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mb-0.5
            bg-[#4a7cff] text-white disabled:bg-[#444] disabled:text-gray-600
            hover:bg-[#3a6cef] transition-colors
          "
        >
          {isStreaming ? (
            <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
            </svg>
          )}
        </button>
      </div>
      <p className="text-center text-gray-600 text-xs mt-2">
        Enter로 전송 · Shift+Enter 줄바꿈
      </p>
    </div>
  )
}
