import { create } from 'zustand'
import type { Message, Session, User } from '../types'

export interface UserProfile {
  age?: number
  region?: string
  employment_status?: string
  annual_income?: number
}

interface ChatStore {
  messages: Message[]
  sessions: Session[]
  currentSessionId: string | null
  isStreaming: boolean
  user: User | null
  profile: UserProfile

  addMessage: (msg: Message) => void
  appendToLast: (chunk: string) => void
  setStreaming: (v: boolean) => void
  setUser: (u: User | null) => void
  setSessions: (s: Session[]) => void
  setCurrentSession: (id: string) => void
  clearMessages: () => void
  loadSession: (session: Session) => void
  setProfile: (p: UserProfile) => void
}

export const useChatStore = create<ChatStore>((set) => ({
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

  setStreaming:        (v) => set({ isStreaming: v }),
  setUser:            (u) => set({ user: u }),
  setSessions:        (s) => set({ sessions: s }),
  setCurrentSession:  (id) => set({ currentSessionId: id }),
  clearMessages:      () => set({ messages: [] }),
  setProfile:         (p) => set({ profile: p }),

  loadSession: (session) =>
    set({ messages: session.messages, currentSessionId: session.id }),
}))
