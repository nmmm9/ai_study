import { useCallback } from 'react'
import { streamChat, createSession, saveSession } from '../api/client'
import { useChatStore } from '../store/chatStore'
import type { Message } from '../types'

function uid() {
  return Math.random().toString(36).slice(2)
}

export function useChat() {
  const {
    addMessage, appendToLast, setStreaming, isStreaming,
    profile, user, messages, currentSessionId, setCurrentSession, setSessions, sessions,
  } = useChatStore()

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || isStreaming) return

    // 이번 턴의 메시지를 추가하기 전, 이전 대화 이력을 스냅샷으로 확보
    const history = messages
      .filter((m) => m.content.trim())
      .map((m) => ({ role: m.role, content: m.content }))

    const userMsg: Message = {
      id:        uid(),
      role:      'user',
      content:   text.trim(),
      createdAt: new Date(),
    }
    addMessage(userMsg)

    const botMsg: Message = {
      id:        uid(),
      role:      'bot',
      content:   '',
      createdAt: new Date(),
    }
    addMessage(botMsg)
    setStreaming(true)

    // 첫 메시지일 때 새 세션 생성 — 로그인한 사용자만 Supabase에 동기화
    let sessionId = currentSessionId
    if (!sessionId && user?.access_token) {
      try {
        const res = await createSession(user.access_token)
        sessionId = res.session_id
        setCurrentSession(sessionId)
        const newSession = {
          id:         sessionId,
          name:       text.trim().slice(0, 30),
          messages:   [],
          created_at: new Date().toISOString(),
        }
        setSessions([newSession, ...sessions])
      } catch { /* 세션 생성 실패해도 채팅은 계속 */ }
    }

    try {
      await streamChat(
        text.trim(),
        (chunk) => appendToLast(chunk),
        (_tool) => {},
        async () => {
          setStreaming(false)
          // 대화 완료 후 세션에 메시지 저장
          if (sessionId && user?.access_token) {
            const allMsgs = useChatStore.getState().messages
            try {
              await saveSession(user.access_token, sessionId, allMsgs)
              // 사이드바 세션 이름을 첫 질문으로 업데이트
              setSessions(
                useChatStore.getState().sessions.map((s) =>
                  s.id === sessionId ? { ...s, messages: allMsgs } : s
                )
              )
            } catch { /* 저장 실패 무시 */ }
          }
        },
        { email: user?.email, ...profile },
        history,
      )
    } catch {
      appendToLast('오류가 발생했습니다. 잠시 후 다시 시도해주세요.')
      setStreaming(false)
    }
  }, [
    isStreaming, addMessage, appendToLast, setStreaming,
    profile, user, messages, currentSessionId, setCurrentSession, setSessions, sessions,
  ])

  return { sendMessage }
}
