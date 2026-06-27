import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import type { Message, Session, User } from '../types'

export interface UserProfile {
  age?:               number
  region?:            string
  employment_status?: string
  annual_income?:     number
}

interface ChatStore {
  messages:         Message[]
  sessions:         Session[]
  currentSessionId: string | null
  isStreaming:      boolean
  user:             User | null
  profile:          UserProfile

  addMessage:       (msg: Message) => void
  appendToLast:     (chunk: string) => void
  setStreaming:     (v: boolean) => void
  setUser:          (u: User | null) => void
  setSessions:      (s: Session[]) => void
  setCurrentSession:(id: string) => void
  clearMessages:    () => void
  loadSession:      (session: Session) => void
  setProfile:       (p: UserProfile) => void
  setMessages:      (msgs: Message[]) => void
}

export const useChatStore = create<ChatStore>()(
  persist(
    (set) => ({
      messages:         [],
      sessions:         [],
      currentSessionId: null,
      isStreaming:      false,
      user:             null,
      profile:          {},

      addMessage: (msg) =>
        set((s) => ({ messages: [...s.messages, msg] })),

      appendToLast: (chunk) =>
        set((s) => {
          const msgs = [...s.messages]
          if (msgs.length === 0) return s
          msgs[msgs.length - 1] = {
            ...msgs[msgs.length - 1],
            content: msgs[msgs.length - 1].content + chunk,
          }
          return { messages: msgs }
        }),

      setStreaming:        (v)  => set({ isStreaming: v }),
      setUser:             (u)  => set({ user: u }),
      setSessions:         (s)  => set({ sessions: s }),
      setCurrentSession:   (id) => set({ currentSessionId: id }),
      clearMessages:       ()   => set({ messages: [] }),
      setMessages:         (msgs) => set({ messages: msgs }),
      setProfile:          (p)  => set({ profile: p }),

      loadSession: (session) =>
        set({ messages: session.messages, currentSessionId: session.id }),
    }),
    {
      name:    'youth-policy-store',
      storage: createJSONStorage(() => localStorage),
      // user, profile, sessions만 localStorage에 유지
      // messages는 IndexedDB로 별도 관리 (대용량 방지)
      partialize: (state) => ({
        user:     state.user,
        profile:  state.profile,
        sessions: state.sessions,
      }),
    }
  )
)
