import { useState, useRef, useCallback, type KeyboardEvent } from 'react'
import { useChat } from '../hooks/useChat'
import { useChatStore } from '../store/chatStore'

// Web Speech API — SpeechRecognition/webkitSpeechRecognition (Chrome)
// TypeScript DOM lib에 SpeechRecognition 생성자가 없으므로 Window 확장
declare global {
  interface Window {
    SpeechRecognition?:       new () => SpeechRecognitionPolyfill
    webkitSpeechRecognition?: new () => SpeechRecognitionPolyfill
  }
}
interface SpeechRecognitionPolyfill {
  lang:           string
  continuous:     boolean
  interimResults: boolean
  onresult:       ((e: SpeechRecognitionPolyfillEvent) => void) | null
  onend:          (() => void) | null
  onerror:        (() => void) | null
  start():        void
  stop():         void
}
interface SpeechRecognitionPolyfillEvent {
  results: {
    readonly length: number
    [i: number]: { [j: number]: { readonly transcript: string } }
  }
}

export default function ChatInput() {
  const [text,        setText]        = useState('')
  const [isListening, setIsListening] = useState(false)
  const { sendMessage } = useChat()
  const isStreaming     = useChatStore((s) => s.isStreaming)
  const textareaRef     = useRef<HTMLTextAreaElement>(null)
  const recognitionRef  = useRef<SpeechRecognitionPolyfill | null>(null)

  const handleSend = useCallback(() => {
    if (!text.trim() || isStreaming) return
    sendMessage(text)
    setText('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }, [text, isStreaming, sendMessage])

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

  // ── Web Speech API (STT): 음성 입력 ──
  const handleVoice = useCallback(() => {
    const SR = window.SpeechRecognition ?? window.webkitSpeechRecognition
    if (!SR) {
      alert('이 브라우저는 음성 인식을 지원하지 않습니다. (Chrome 권장)')
      return
    }

    if (isListening) {
      recognitionRef.current?.stop()
      setIsListening(false)
      return
    }

    const rec = new SR()
    rec.lang           = 'ko-KR'
    rec.continuous     = false
    rec.interimResults = true

    rec.onresult = (e: SpeechRecognitionPolyfillEvent) => {
      let transcript = ''
      for (let i = 0; i < e.results.length; i++) {
        transcript += e.results[i][0].transcript
      }
      setText(transcript)
    }
    rec.onend   = () => setIsListening(false)
    rec.onerror = () => setIsListening(false)

    recognitionRef.current = rec
    rec.start()
    setIsListening(true)
  }, [isListening])

  return (
    <div className="border-t border-[#333] bg-[#1a1a1a] p-4">
      <div className="flex items-end gap-2 bg-[#2a2a2a] border border-[#3a3a3a] rounded-2xl px-4 py-2">

        {/* 음성 입력 버튼 (Web Speech API STT) */}
        <button
          onClick={handleVoice}
          title={isListening ? '녹음 중지' : '음성으로 입력'}
          className={`
            w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mb-0.5 transition-all
            ${isListening
              ? 'bg-red-500 text-white animate-pulse shadow-lg shadow-red-500/40'
              : 'text-gray-500 hover:text-white hover:bg-[#3a3a3a]'
            }
          `}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm-1-9c0-.55.45-1 1-1s1 .45 1 1v6c0 .55-.45 1-1 1s-1-.45-1-1V5zm6 6c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
          </svg>
        </button>

        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder={isListening ? '🎤 듣고 있습니다...' : '청년정책에 대해 무엇이든 물어보세요...'}
          rows={1}
          disabled={isStreaming}
          className="
            flex-1 bg-transparent text-sm text-white placeholder-gray-500
            resize-none outline-none py-1.5 max-h-40
          "
        />

        {/* 전송 버튼 */}
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
        Enter 전송 · Shift+Enter 줄바꿈 · 🎤 음성 입력 가능
      </p>
    </div>
  )
}
