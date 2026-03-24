import { useState, useEffect, useRef, useCallback } from 'react'
import { useRouter } from 'next/router'
import Head from 'next/head'
import ReactMarkdown from 'react-markdown'

const API = process.env.NEXT_PUBLIC_API_URL || ''

// ── 타입 ────────────────────────────────────────────────────
interface Message {
  role: 'user' | 'assistant'
  content: string
  citations?: string[]
  queries?: string[]
  company_filter?: string
  blocked?: boolean
  feedback?: 'like' | 'dislike' | null
  bookmarkId?: string
}
interface Conversation { id: string; title: string; messages: Message[]; updated_at?: string }
interface JobCard      { company: string; section: string; snippet: string }
interface Bookmark     { id: string; question: string; answer: string; citations: string[]; saved_at: string }

// ── API 헬퍼 ────────────────────────────────────────────────
const api = (token: string, onUnauth?: () => void) => {
  const handle = async (res: Response) => {
    if (res.status === 401) { onUnauth?.(); throw new Error('401') }
    return res
  }
  return {
    get:    (url: string)              => fetch(`${API}${url}`, { headers: { Authorization: `Bearer ${token}` } }).then(handle),
    post:   (url: string, body: unknown) => fetch(`${API}${url}`, { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }, body: JSON.stringify(body) }).then(handle),
    delete: (url: string)              => fetch(`${API}${url}`, { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } }).then(handle),
  }
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 서브 컴포넌트
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

function JobCardList({ cards }: { cards: JobCard[] }) {
  if (!cards.length) return null
  return (
    <div style={{ marginTop: 12 }}>
      <div style={{ fontSize: 12, color: '#8e8ea0', marginBottom: 6 }}>🏢 관련 채용공고 Top {cards.length}</div>
      {cards.map((c, i) => (
        <div key={i} style={s.jobCard}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
            <span style={s.jobRank}>#{i + 1}</span>
            <span style={{ fontWeight: 700, fontSize: 13 }}>{c.company}</span>
            <span style={s.jobSection}>{c.section}</span>
          </div>
          <div style={s.jobSnippet}>{c.snippet}{c.snippet.length >= 150 ? '...' : ''}</div>
        </div>
      ))}
    </div>
  )
}

function SourceList({ citations }: { citations: string[] }) {
  if (!citations.length) return null
  return (
    <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 4 }}>
      {citations.map((c, i) => (
        <div key={i} style={s.sourceCard}>
          <span style={s.sourceNum}>{i + 1}</span>
          <span style={{ fontSize: 12 }}>{c}</span>
        </div>
      ))}
    </div>
  )
}

function MessageBubble({ msg, idx, token, onFeedback, onCopy, onBookmark, isBookmarked, top3 }: {
  msg: Message; idx: number; token: string
  onFeedback: (f: 'like' | 'dislike') => void
  onCopy: () => void
  onBookmark: () => void
  isBookmarked: boolean
  top3: JobCard[]
}) {
  const isUser = msg.role === 'user'
  return (
    <div style={{ ...s.msgWrap, justifyContent: isUser ? 'flex-end' : 'flex-start' }}>
      {!isUser && <span style={s.avatar}>🤖</span>}
      <div style={{ maxWidth: '74%' }}>
        <div style={{ ...s.bubble, ...(isUser ? s.bubbleUser : s.bubbleAI) }}>
          {msg.blocked
            ? <span style={{ color: '#ff9800' }}>⚠️ {msg.content}</span>
            : isUser
              ? <span style={{ whiteSpace: 'pre-wrap', lineHeight: 1.65 }}>{msg.content}</span>
              : <div className="md-body"><ReactMarkdown>{msg.content}</ReactMarkdown></div>
          }
        </div>

        {!isUser && !msg.blocked && <>
          <SourceList citations={msg.citations || []} />
          <JobCardList cards={top3} />

          {/* 검색 상세 */}
          {msg.queries && msg.queries.length > 0 && (
            <details style={{ marginTop: 6 }}>
              <summary style={{ fontSize: 12, color: '#8e8ea0', cursor: 'pointer' }}>🔍 검색 상세</summary>
              <div style={{ padding: '4px 0', display: 'flex', flexDirection: 'column', gap: 2 }}>
                {msg.company_filter && <span style={{ fontSize: 11, color: '#10a37f' }}>🏢 {msg.company_filter}</span>}
                {msg.queries.map((q, i) => (
                  <span key={i} style={{ fontSize: 11, color: '#8e8ea0' }}>{i === 0 ? '원본' : `확장 ${i}`}: {q}</span>
                ))}
              </div>
            </details>
          )}

          {/* 액션 바 */}
          <div style={s.actionBar}>
            <button style={s.actionBtn} onClick={onCopy}>📋 복사</button>
            <button style={{ ...s.actionBtn, ...(msg.feedback === 'like'    ? s.actionActive : {}) }} onClick={() => onFeedback('like')}>👍</button>
            <button style={{ ...s.actionBtn, ...(msg.feedback === 'dislike' ? s.actionActive : {}) }} onClick={() => onFeedback('dislike')}>👎</button>
            <button style={{ ...s.actionBtn, ...(isBookmarked ? s.bookmarkActive : {}) }} onClick={onBookmark}>
              {isBookmarked ? '⭐ 저장됨' : '☆ 북마크'}
            </button>
          </div>
        </>}
      </div>
      {isUser && <span style={s.avatar}>🧑</span>}
    </div>
  )
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 메인 페이지
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
export default function ChatPage() {
  const router = useRouter()
  const bottomRef   = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [user, setUser]             = useState<{ id: string; email: string } | null>(null)
  const [token, setToken]           = useState('')
  const [conversations, setConvs]   = useState<Conversation[]>([])
  const [currentId, setCurrentId]   = useState('')
  const [input, setInput]           = useState('')
  const [streaming, setStreaming]   = useState(false)
  const [streamText, setStreamText] = useState('')
  const [streamStatus, setStatus]   = useState('')
  const [filterStack, setStack]     = useState('')
  const [filterCareer, setCareer]   = useState('전체')
  const [companies, setCompanies]   = useState<string[]>([])
  const [showCompanies, setShowCo]  = useState(false)
  const [tokenUsage, setTokenUsage] = useState({ input: 0, output: 0 })
  const [bookmarks, setBookmarks]   = useState<Bookmark[]>([])
  const [showBookmarks, setShowBm]  = useState(false)
  const [uploads, setUploads]       = useState<string[]>([])
  const [editingId, setEditingId]   = useState<string | null>(null)
  const [editTitle, setEditTitle]   = useState('')
  const [msgTop3, setMsgTop3]       = useState<Record<number, JobCard[]>>({})

  // ── 초기화 ────────────────────────────────────────────────
  useEffect(() => {
    const t = localStorage.getItem('token')
    const u = localStorage.getItem('user')
    if (!t || !u) { router.push('/'); return }
    setToken(t); setUser(JSON.parse(u))
  }, [router])

  useEffect(() => {
    if (!token) return
    loadConversations()
    loadSidebarData()
  }, [token])

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [conversations, streamText])

  const autoLogout = useCallback(() => {
    localStorage.clear(); router.push('/')
  }, [router])

  // ── 사이드바 데이터 ───────────────────────────────────────
  const loadSidebarData = async () => {
    const a = api(token, autoLogout)
    const [coRes, bmRes, upRes, tkRes] = await Promise.allSettled([
      a.get('/api/companies').then(r => r.json()),
      a.get('/api/bookmarks').then(r => r.json()),
      a.get('/api/uploads').then(r => r.json()),
      a.get('/api/token-usage').then(r => r.json()),
    ])
    if (coRes.status === 'fulfilled') setCompanies(coRes.value)
    if (bmRes.status === 'fulfilled') setBookmarks(bmRes.value)
    if (upRes.status === 'fulfilled') setUploads(upRes.value)
    if (tkRes.status === 'fulfilled') setTokenUsage(tkRes.value)
  }

  // ── 대화 목록 ─────────────────────────────────────────────
  const loadConversations = async () => {
    const res  = await api(token, autoLogout).get('/api/conversations')
    const data: Conversation[] = await res.json()
    if (!data.length) { newChat(); return }
    setConvs(data); setCurrentId(data[0].id)
  }

  const currentConv = conversations.find(c => c.id === currentId)
  const messages    = currentConv?.messages || []

  const newChat = useCallback(() => {
    const id   = crypto.randomUUID()
    const conv: Conversation = { id, title: '새 대화', messages: [] }
    setConvs(prev => [conv, ...prev]); setCurrentId(id)
  }, [])

  const saveConv = async (conv: Conversation) => {
    await api(token, autoLogout).post('/api/conversations', { id: conv.id, title: conv.title, messages: conv.messages })
  }

  const deleteConv = async (id: string) => {
    await api(token, autoLogout).delete(`/api/conversations/${id}`)
    setConvs(prev => {
      const next = prev.filter(c => c.id !== id)
      if (!next.length) { newChat(); return next }
      if (currentId === id) setCurrentId(next[0].id)
      return next
    })
  }

  const saveTitle = async (id: string) => {
    setConvs(prev => prev.map(c => {
      if (c.id !== id) return c
      const updated = { ...c, title: editTitle }
      saveConv(updated)
      return updated
    }))
    setEditingId(null)
  }

  // ── 메시지 전송 ───────────────────────────────────────────
  const sendMessage = async (text: string) => {
    if (!text.trim() || streaming) return
    setInput(''); setStreaming(true); setStreamText(''); setStatus('검색 중...')

    const userMsg: Message = { role: 'user', content: text }
    setConvs(prev => prev.map(c => {
      if (c.id !== currentId) return c
      return { ...c, title: c.messages.length === 0 ? text.slice(0, 28) : c.title, messages: [...c.messages, userMsg] }
    }))

    let fullText = '', citations: string[] = [], queries: string[] = [], company_filter = '', blocked = false

    try {
      const res = await fetch(`${API}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ message: text, filter_stack: filterStack, filter_career: filterCareer }),
      })
      if (!res.ok) throw new Error((await res.json()).detail)
      const reader = res.body!.getReader(); const decoder = new TextDecoder()
      while (true) {
        const { done, value } = await reader.read(); if (done) break
        for (const line of decoder.decode(value).split('\n')) {
          if (!line.startsWith('data: ')) continue
          const raw = line.slice(6); if (raw === '[DONE]') break
          try {
            const ev = JSON.parse(raw)
            if (ev.type === 'status')    setStatus(ev.text)
            if (ev.type === 'queries')   { queries = ev.queries; company_filter = ev.company_filter || '' }
            if (ev.type === 'citations') citations = ev.citations
            if (ev.type === 'text')      { fullText += ev.text; setStreamText(fullText) }
            if (ev.type === 'blocked')   { blocked = true; fullText = ev.text }
            if (ev.type === 'done')      setStatus('')
          } catch {}
        }
      }
    } catch (e: any) { fullText = `오류: ${e.message}`; blocked = true }

    const aiMsg: Message = { role: 'assistant', content: fullText, citations, queries, company_filter, blocked, feedback: null }
    const newMsgIdx = messages.length + 1  // user + ai

    setConvs(prev => prev.map(c => {
      if (c.id !== currentId) return c
      const updated = { ...c, messages: [...c.messages, aiMsg] }
      saveConv(updated)
      return updated
    }))

    // Top-3 카드 조회
    if (!blocked) {
      api(token).get(`/api/top3?query=${encodeURIComponent(text)}`).then(r => r.json()).then((cards: JobCard[]) => {
        setMsgTop3(prev => ({ ...prev, [newMsgIdx]: cards }))
      }).catch(() => {})
      // 토큰 사용량 갱신
      api(token).get('/api/token-usage').then(r => r.json()).then(setTokenUsage).catch(() => {})
    }

    setStreaming(false); setStreamText(''); setStatus('')
  }

  // ── 피드백 ────────────────────────────────────────────────
  const handleFeedback = (msgIdx: number, f: 'like' | 'dislike') => {
    setConvs(prev => prev.map(c => {
      if (c.id !== currentId) return c
      const msgs = c.messages.map((m, i) => i !== msgIdx ? m : { ...m, feedback: m.feedback === f ? null : f })
      const updated = { ...c, messages: msgs }; saveConv(updated); return updated
    }))
  }

  // ── 북마크 ────────────────────────────────────────────────
  const handleBookmark = async (msgIdx: number) => {
    const msg = messages[msgIdx]
    const userQ = messages.slice(0, msgIdx).reverse().find(m => m.role === 'user')?.content || ''
    const bid = `msg_${currentId}_${msgIdx}`
    const already = bookmarks.some(b => b.id === bid)
    if (already) {
      await api(token).delete(`/api/bookmarks/${bid}`)
      setBookmarks(prev => prev.filter(b => b.id !== bid))
    } else {
      await api(token).post('/api/bookmarks', { id: bid, question: userQ, answer: msg.content, citations: msg.citations || [] })
      setBookmarks(prev => [...prev, { id: bid, question: userQ, answer: msg.content, citations: msg.citations || [], saved_at: '' }])
    }
  }

  // ── 파일 업로드 ───────────────────────────────────────────
  const handleUpload = async (file: File) => {
    const form = new FormData(); form.append('file', file)
    const res = await fetch(`${API}/api/upload`, { method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: form })
    if (res.ok) { setUploads(prev => [...prev, file.name]); await loadSidebarData() }
  }

  const handleDeleteUpload = async (fname: string) => {
    await api(token).delete(`/api/uploads/${fname}`)
    setUploads(prev => prev.filter(f => f !== fname))
  }

  // ── 복사 ──────────────────────────────────────────────────
  const handleCopy = (text: string) => navigator.clipboard.writeText(text).catch(() => {})

  // ── 로그아웃 ──────────────────────────────────────────────
  const logout = () => { localStorage.clear(); router.push('/') }

  const SUGGESTIONS = [
    '백엔드 개발자 채용 공고 있는 회사 알려줘',
    '데이터 엔지니어 또는 AI 엔지니어 채용 공고 알려줘',
    '카카오 백엔드 개발자가 되려면 무엇이 필요한가요?',
    'Java Spring 경험으로 지원할 수 있는 회사는?',
  ]

  const totalTokens = tokenUsage.input + tokenUsage.output

  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  return (
    <>
      <Head><title>💼 취업 상담 AI</title></Head>
      <div style={s.layout}>

        {/* ━━ 사이드바 ━━ */}
        <aside style={s.sidebar}>
          <div style={s.sideTitle}>💼 취업 상담 AI</div>
          <div style={s.sideEmail}>{user?.email}</div>

          <button style={s.newChatBtn} onClick={newChat}>✏️ 새 채팅</button>

          {/* 대화 목록 */}
          <div style={s.sideLabel}>대화 목록</div>
          <div style={{ flex: 1, overflowY: 'auto', minHeight: 0 }}>
            {conversations.map(c => (
              <div key={c.id} style={{ position: 'relative' }}>
                {editingId === c.id ? (
                  <div style={{ display: 'flex', gap: 4, padding: '4px 0' }}>
                    <input value={editTitle} onChange={e => setEditTitle(e.target.value)}
                      style={{ ...s.inlineInput }} onKeyDown={e => e.key === 'Enter' && saveTitle(c.id)} />
                    <button style={s.smallBtn} onClick={() => saveTitle(c.id)}>✓</button>
                    <button style={s.smallBtn} onClick={() => setEditingId(null)}>✕</button>
                  </div>
                ) : (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <button style={{ ...s.convBtn, ...(c.id === currentId ? s.convBtnActive : {}), flex: 1 }}
                      onClick={() => setCurrentId(c.id)}>
                      💬 {c.title.slice(0, 18)}{c.title.length > 18 ? '...' : ''}
                    </button>
                    <button style={s.iconBtn} onClick={() => { setEditingId(c.id); setEditTitle(c.title) }}>✎</button>
                    <button style={s.iconBtn} onClick={() => deleteConv(c.id)}>✕</button>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* 검색 필터 */}
          <div style={s.sideLabel}>🔍 검색 필터</div>
          <input style={{ ...s.filterInput, marginBottom: 6 }} placeholder="기술스택 (Python, React...)"
            value={filterStack} onChange={e => setStack(e.target.value)} />
          <select style={s.filterInput} value={filterCareer} onChange={e => setCareer(e.target.value)}>
            <option>전체</option><option>신입</option><option>경력</option>
          </select>

          {/* 파일 업로드 */}
          <div style={s.sideLabel}>📁 공고 파일 추가</div>
          <button style={s.uploadBtn} onClick={() => fileInputRef.current?.click()}>+ MD 파일 업로드</button>
          <input ref={fileInputRef} type="file" accept=".md" style={{ display: 'none' }}
            onChange={e => e.target.files?.[0] && handleUpload(e.target.files[0])} />
          {uploads.map(f => (
            <div key={f} style={s.uploadItem}>
              <span style={{ fontSize: 12, color: '#8e8ea0', flex: 1 }}>📄 {f}</span>
              <button style={s.iconBtn} onClick={() => handleDeleteUpload(f)}>✕</button>
            </div>
          ))}

          {/* 북마크 */}
          {bookmarks.length > 0 && (
            <>
              <button style={s.collapseBtn} onClick={() => setShowBm(v => !v)}>
                ⭐ 북마크 ({bookmarks.length}개) {showBookmarks ? '▲' : '▼'}
              </button>
              {showBookmarks && bookmarks.map(bm => (
                <div key={bm.id} style={s.bmItem}>
                  <button style={{ ...s.convBtn, flex: 1, fontSize: 11 }}
                    onClick={() => sendMessage(bm.question)}>
                    {bm.question.slice(0, 28)}{bm.question.length > 28 ? '...' : ''}
                  </button>
                  <button style={s.iconBtn} onClick={async () => {
                    await api(token).delete(`/api/bookmarks/${bm.id}`)
                    setBookmarks(prev => prev.filter(b => b.id !== bm.id))
                  }}>✕</button>
                </div>
              ))}
            </>
          )}

          {/* 등록 회사 */}
          {companies.length > 0 && (
            <>
              <button style={s.collapseBtn} onClick={() => setShowCo(v => !v)}>
                🏢 등록 회사 ({companies.length}개) {showCompanies ? '▲' : '▼'}
              </button>
              {showCompanies && (
                <div style={{ maxHeight: 140, overflowY: 'auto' }}>
                  {companies.map(c => <div key={c} style={{ fontSize: 11, color: '#8e8ea0', padding: '2px 4px' }}>• {c}</div>)}
                </div>
              )}
            </>
          )}

          {/* 토큰 사용량 + 로그아웃 */}
          <div style={{ marginTop: 'auto', paddingTop: 8, borderTop: '1px solid #2a2a2a' }}>
            <div style={s.tokenBadge}>🔢 토큰 {totalTokens.toLocaleString()}</div>
            <button style={s.logoutBtn} onClick={logout}>🚪 로그아웃</button>
          </div>
        </aside>

        {/* ━━ 메인 ━━ */}
        <main style={s.main}>
          {/* 환영 화면 */}
          {messages.length === 0 && !streaming && (
            <div style={s.welcome}>
              <div style={s.welcomeTitle}>무엇을 도와드릴까요?</div>
              <div style={s.welcomeSub}>취업공고 기반 AI 상담 서비스</div>
              <div style={s.suggGrid}>
                {SUGGESTIONS.map((q, i) => (
                  <button key={i} style={s.suggBtn} onClick={() => sendMessage(q)}>{q}</button>
                ))}
              </div>
            </div>
          )}

          {/* 메시지 */}
          <div style={s.msgList}>
            {messages.map((msg, i) => (
              <MessageBubble key={i} msg={msg} idx={i} token={token}
                onFeedback={f => handleFeedback(i, f)}
                onCopy={() => handleCopy(msg.content)}
                onBookmark={() => handleBookmark(i)}
                isBookmarked={bookmarks.some(b => b.id === `msg_${currentId}_${i}`)}
                top3={msgTop3[i] || []}
              />
            ))}

            {/* 스트리밍 */}
            {streaming && (
              <div style={{ ...s.msgWrap, justifyContent: 'flex-start' }}>
                <span style={s.avatar}>🤖</span>
                <div style={{ maxWidth: '74%' }}>
                  {streamStatus && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                      <span style={s.statusDot} /><span style={{ fontSize: 12, color: '#8e8ea0' }}>{streamStatus}</span>
                    </div>
                  )}
                  {streamText && (
                    <div style={{ ...s.bubble, ...s.bubbleAI }}>
                      <div className="md-body"><ReactMarkdown>{streamText + '▌'}</ReactMarkdown></div>
                    </div>
                  )}
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* 입력창 */}
          <div style={s.inputWrap}>
            <textarea style={s.inputBox} rows={1} placeholder="취업 관련 질문을 입력하세요..."
              value={input} onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(input) } }} />
            <button style={{ ...s.sendBtn, opacity: streaming ? 0.5 : 1 }}
              onClick={() => sendMessage(input)} disabled={streaming}>▶</button>
          </div>
        </main>
      </div>
    </>
  )
}

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 스타일
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
const s: Record<string, React.CSSProperties> = {
  layout:  { display: 'flex', height: '100vh', overflow: 'hidden' },

  sidebar: {
    width: 268, background: '#111', borderRight: '1px solid #2a2a2a',
    display: 'flex', flexDirection: 'column', padding: '16px 12px', gap: 6, overflowY: 'auto',
  },
  sideTitle:  { fontSize: 16, fontWeight: 700 },
  sideEmail:  { fontSize: 11, color: '#8e8ea0', marginBottom: 2 },
  sideLabel:  { fontSize: 11, color: '#8e8ea0', fontWeight: 600, marginTop: 8 },
  newChatBtn: { background: 'linear-gradient(135deg,#10a37f,#0d8c6d)', color: 'white', fontWeight: 600, padding: '9px 0', borderRadius: 10 },
  convBtn:    { textAlign: 'left', background: 'transparent', color: '#ececec', border: '1px solid transparent', borderRadius: 8, padding: '7px 8px', fontSize: 12, cursor: 'pointer' },
  convBtnActive: { background: '#1e1e1e', borderColor: '#10a37f' },
  iconBtn:    { background: 'transparent', color: '#555', border: 'none', padding: '4px 5px', fontSize: 12, borderRadius: 6, cursor: 'pointer', flexShrink: 0 },
  smallBtn:   { background: '#2a2a2a', color: '#ececec', border: 'none', padding: '4px 8px', fontSize: 11, borderRadius: 6, cursor: 'pointer' },
  inlineInput: { flex: 1, fontSize: 12, padding: '4px 8px', borderRadius: 6, background: '#2a2a2a', color: '#ececec', border: '1px solid #3a3a3a' },
  filterInput: { fontSize: 12, padding: '7px 10px', borderRadius: 8 },
  uploadBtn:  { background: '#1e1e1e', color: '#8e8ea0', border: '1px dashed #3a3a3a', borderRadius: 8, padding: '7px 0', fontSize: 12 },
  uploadItem: { display: 'flex', alignItems: 'center', gap: 4, padding: '2px 0' },
  collapseBtn: { background: 'transparent', color: '#8e8ea0', border: 'none', textAlign: 'left', padding: '6px 2px', fontSize: 12, cursor: 'pointer', fontWeight: 600 },
  bmItem:     { display: 'flex', alignItems: 'center', gap: 2 },
  tokenBadge: { fontSize: 11, color: '#555', background: '#1a1a1a', borderRadius: 20, padding: '3px 10px', display: 'inline-block', marginBottom: 6 },
  logoutBtn:  { width: '100%', background: 'transparent', color: '#8e8ea0', border: '1px solid #2a2a2a', borderRadius: 8, padding: '8px 0', fontSize: 12 },

  main:    { flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' },
  msgList: { flex: 1, overflowY: 'auto', padding: '24px 8%', display: 'flex', flexDirection: 'column', gap: 18 },

  msgWrap:    { display: 'flex', alignItems: 'flex-start', gap: 10 },
  avatar:     { fontSize: 20, flexShrink: 0, marginTop: 2 },
  bubble:     { borderRadius: 16, padding: '12px 16px', fontSize: 14 },
  bubbleUser: { background: '#1e1e1e', border: '1px solid #2a2a2a' },
  bubbleAI:   { background: 'transparent', padding: '0' },

  sourceCard: { display: 'flex', alignItems: 'center', gap: 8, background: '#1e1e1e', border: '1px solid #2a2a2a', borderRadius: 10, padding: '6px 10px' },
  sourceNum:  { background: '#10a37f', color: 'white', borderRadius: '50%', width: 18, height: 18, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, fontWeight: 700, flexShrink: 0 },

  jobCard:    { background: '#1a1a1a', border: '1px solid #2a2a2a', borderRadius: 12, padding: '10px 12px', marginBottom: 6 },
  jobRank:    { background: 'linear-gradient(135deg,#10a37f,#0d8c6d)', color: 'white', borderRadius: 6, padding: '1px 7px', fontSize: 11, fontWeight: 700 },
  jobSection: { marginLeft: 'auto', fontSize: 11, color: '#10a37f', background: 'rgba(16,163,127,0.1)', borderRadius: 6, padding: '1px 7px' },
  jobSnippet: { fontSize: 12, color: '#8e8ea0', lineHeight: 1.5 },

  actionBar:     { display: 'flex', gap: 4, marginTop: 8, flexWrap: 'wrap' },
  actionBtn:     { background: 'transparent', color: '#8e8ea0', border: '1px solid #2a2a2a', borderRadius: 6, padding: '3px 10px', fontSize: 12 },
  actionActive:  { background: 'rgba(16,163,127,0.15)', borderColor: '#10a37f', color: '#10a37f' },
  bookmarkActive:{ background: 'rgba(255,193,7,0.15)', borderColor: '#ffc107', color: '#ffc107' },

  statusDot: { width: 8, height: 8, background: '#10a37f', borderRadius: '50%', flexShrink: 0 },

  welcome:      { flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: 40 },
  welcomeTitle: { fontSize: 30, fontWeight: 700, background: 'linear-gradient(135deg,#ececec,#10a37f)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', marginBottom: 8 },
  welcomeSub:   { color: '#8e8ea0', marginBottom: 24 },
  suggGrid:     { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, width: '100%', maxWidth: 580 },
  suggBtn:      { background: '#1e1e1e', color: '#ececec', border: '1px solid #2a2a2a', borderRadius: 14, padding: '14px 16px', fontSize: 13, textAlign: 'left', cursor: 'pointer', lineHeight: 1.5 },

  inputWrap: { padding: '14px 8%', borderTop: '1px solid #2a2a2a', display: 'flex', gap: 10, alignItems: 'flex-end' },
  inputBox:  { flex: 1, background: '#2a2a2a', color: '#ececec', border: '1px solid #3a3a3a', borderRadius: 16, padding: '13px 18px', fontSize: 15, resize: 'none', maxHeight: 200, overflowY: 'auto' },
  sendBtn:   { background: '#10a37f', color: 'white', borderRadius: 12, padding: '12px 16px', fontSize: 16, flexShrink: 0 },
}
