const BASE = '/api'

export async function streamChat(
  message: string,
  onChunk: (chunk: string) => void,
  onMeta: (tool: string) => void,
  onDone: () => void,
) {
  const res = await fetch(`${BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
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

export async function login(email: string, password: string) {
  const res = await fetch(`${BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) throw new Error((await res.json()).detail || '로그인 실패')
  return res.json()
}

export async function signup(email: string, password: string) {
  const res = await fetch(`${BASE}/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) throw new Error((await res.json()).detail || '회원가입 실패')
  return res.json()
}

export async function logout() {
  await fetch(`${BASE}/auth/logout`, { method: 'POST' })
}

export async function getSessions() {
  const res = await fetch(`${BASE}/sessions`)
  return res.json()
}

export async function createSession() {
  const res = await fetch(`${BASE}/sessions`, { method: 'POST' })
  return res.json()
}

export async function saveSession(id: string, messages: unknown[]) {
  await fetch(`${BASE}/sessions/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ messages }),
  })
}

export async function deleteSession(id: string) {
  await fetch(`${BASE}/sessions/${id}`, { method: 'DELETE' })
}
