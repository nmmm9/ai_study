import { useCallback } from 'react'
import { streamChat } from '../api/client'
import { useChatStore } from '../store/chatStore'
import type { Message } from '../types'

function uid() {
  return Math.random().toString(36).slice(2)
}

export function useChat() {
  const { addMessage, appendToLast, setStreaming, isStreaming } = useChatStore()

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || isStreaming) return

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

    try {
      await streamChat(
        text.trim(),
        (chunk) => appendToLast(chunk),
        (_tool) => {},
        () => setStreaming(false),
      )
    } catch {
      appendToLast('오류가 발생했습니다. 잠시 후 다시 시도해주세요.')
      setStreaming(false)
    }
  }, [isStreaming, addMessage, appendToLast, setStreaming])

  return { sendMessage }
}
