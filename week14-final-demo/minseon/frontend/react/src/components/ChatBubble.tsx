import { useState, useEffect, useRef, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { Message } from '../types'

interface Props {
  message:     Message
  isStreaming?: boolean
}

export default function ChatBubble({ message, isStreaming }: Props) {
  const isUser = message.role === 'user'
  const [copied,   setCopied]   = useState(false)
  const [speaking, setSpeaking] = useState(false)
  const [visible,  setVisible]  = useState(false)  // Intersection Observer
  const bubbleRef = useRef<HTMLDivElement>(null)

  // ── Intersection Observer: 메시지가 뷰포트에 들어오면 페이드인 ──
  useEffect(() => {
    const el = bubbleRef.current
    if (!el) return
    const obs = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true)
          obs.unobserve(el)
        }
      },
      { threshold: 0.05 }
    )
    obs.observe(el)
    return () => obs.disconnect()
  }, [])

  // ── Clipboard API: 답변 복사 ──
  const handleCopy = useCallback(async () => {
    await navigator.clipboard.writeText(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }, [message.content])

  // ── Web Share API: 정책 공유 ──
  const handleShare = useCallback(async () => {
    if (navigator.share) {
      await navigator.share({
        title: '청년정책 AI 답변',
        text:  message.content.slice(0, 300),
        url:   window.location.href,
      })
    } else {
      // 공유 API 미지원 브라우저 → 클립보드 복사로 대체
      await navigator.clipboard.writeText(message.content)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }, [message.content])

  // ── Web Speech API (TTS): 답변 읽어주기 ──
  const handleSpeak = useCallback(() => {
    if (speaking) {
      window.speechSynthesis.cancel()
      setSpeaking(false)
      return
    }
    const plain = message.content.replace(/[#*`>|_~]/g, '').trim()
    const utter = new SpeechSynthesisUtterance(plain)
    utter.lang  = 'ko-KR'
    utter.rate  = 1.0
    utter.pitch = 1.0
    utter.onend = () => setSpeaking(false)
    window.speechSynthesis.speak(utter)
    setSpeaking(true)
  }, [message.content, speaking])

  return (
    <div
      ref={bubbleRef}
      className={`
        flex mb-4 group
        transition-all duration-300 ease-out
        ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-3'}
        ${isUser ? 'justify-end' : 'justify-start'}
      `}
    >
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-[#3a3a3a] flex items-center justify-center text-sm mr-2 mt-1 flex-shrink-0">
          AI
        </div>
      )}

      <div className="max-w-[80%] flex flex-col gap-1">
        {/* 말풍선 */}
        <div
          className={`
            px-4 py-3 rounded-2xl text-sm leading-relaxed
            ${isUser
              ? 'bg-[#4a7cff] text-white rounded-br-sm'
              : 'bg-[#2a2a2a] text-gray-100 rounded-bl-sm border border-[#3a3a3a]'
            }
          `}
        >
          {isUser ? (
            message.content
          ) : (
            <div className="markdown">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content || (isStreaming ? '▍' : '')}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* 액션 버튼 (AI 메시지, 스트리밍 끝난 후) */}
        {!isUser && !isStreaming && message.content && (
          <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-150 ml-1">
            {/* 복사 */}
            <button
              onClick={handleCopy}
              title="복사"
              className="px-2 py-1 rounded-lg text-xs text-gray-500 hover:text-white hover:bg-[#2a2a2a] transition-colors"
            >
              {copied ? '✓ 복사됨' : '복사'}
            </button>

            {/* 공유 */}
            <button
              onClick={handleShare}
              title="공유"
              className="px-2 py-1 rounded-lg text-xs text-gray-500 hover:text-white hover:bg-[#2a2a2a] transition-colors"
            >
              공유
            </button>

            {/* 읽어주기 (TTS) */}
            <button
              onClick={handleSpeak}
              title={speaking ? '읽기 중지' : '읽어주기'}
              className={`px-2 py-1 rounded-lg text-xs transition-colors ${
                speaking
                  ? 'text-[#4a7cff] bg-[#2a2a2a]'
                  : 'text-gray-500 hover:text-white hover:bg-[#2a2a2a]'
              }`}
            >
              {speaking ? '■ 중지' : '▶ 읽기'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
