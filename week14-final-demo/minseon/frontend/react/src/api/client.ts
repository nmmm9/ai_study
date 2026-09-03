const BASE = (import.meta.env.VITE_API_URL ?? '') + '/api'

export interface UserProfile {
  email?:             string
  age?:               number
  region?:            string
  employment_status?: string
  annual_income?:     number
}

export interface HistoryTurn {
  role:    'user' | 'bot'
  content: string
}

export async function streamChat(
  message: string,
  onChunk: (chunk: string) => void,
  onMeta: (tool: string) => void,
  onDone: () => void,
  profile?: UserProfile,
  history?: HistoryTurn[],
) {
  const res = await fetch(`${BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history: history ?? [], ...profile }),
  })
  if (!res.ok) throw new Error('서버 오류')

  const reader = res.body!.getReader()
  const decoder = new TextDecoder()

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const lines = decoder.decode(value).split('\n')
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      try {
        const data = JSON.parse(line.slice(6))
        if (data.type === 'meta')  onMeta(data.tool)
        if (data.type === 'chunk') onChunk(data.content)
        if (data.type === 'done')  onDone()
      } catch {}
    }
  }
}

async function _parseError(res: Response, fallback: string): Promise<string> {
  try {
    const data = await res.json()
    return data.detail || fallback
  } catch {
    return fallback
  }
}

export async function login(email: string, password: string) {
  const res = await fetch(`${BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) throw new Error(await _parseError(res, '로그인 실패'))
  return res.json()
}

export async function signup(email: string, password: string) {
  const res = await fetch(`${BASE}/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) throw new Error(await _parseError(res, '회원가입 실패'))
  return res.json()
}

export async function logout() {
  await fetch(`${BASE}/auth/logout`, { method: 'POST' })
}

function _authHeaders(token: string): Record<string, string> {
  return { Authorization: `Bearer ${token}` }
}

// 세션 API는 전부 로그인 필요 — access_token을 넘겨줘야 합니다.

export async function getSessions(token: string) {
  const res = await fetch(`${BASE}/sessions`, { headers: _authHeaders(token) })
  if (!res.ok) throw new Error('세션 목록을 가져오지 못했습니다')
  return res.json()
}

export async function createSession(token: string) {
  const res = await fetch(`${BASE}/sessions`, { method: 'POST', headers: _authHeaders(token) })
  if (!res.ok) throw new Error('세션 생성 실패')
  return res.json()
}

export async function saveSession(token: string, id: string, messages: unknown[]) {
  await fetch(`${BASE}/sessions/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ..._authHeaders(token) },
    body: JSON.stringify({ messages }),
  })
}

export async function deleteSession(token: string, id: string) {
  await fetch(`${BASE}/sessions/${id}`, { method: 'DELETE', headers: _authHeaders(token) })
}
