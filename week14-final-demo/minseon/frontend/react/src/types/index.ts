export interface Message {
  id: string
  role: 'user' | 'bot'
  content: string
  tool?: string
  createdAt: Date
}

export interface Session {
  id: string
  name: string
  messages: Message[]
  created_at: string
}

export interface User {
  email: string
  access_token: string
}
