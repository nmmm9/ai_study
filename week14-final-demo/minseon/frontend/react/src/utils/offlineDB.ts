// IndexedDB — 로그인 없이도 대화 기록 로컬 저장
const DB_NAME = 'youth-policy-chat'
const DB_VER  = 1
const STORE   = 'messages'

function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VER)
    req.onupgradeneeded = () => {
      if (!req.result.objectStoreNames.contains(STORE)) {
        req.result.createObjectStore(STORE, { keyPath: 'id' })
      }
    }
    req.onsuccess = () => resolve(req.result)
    req.onerror  = () => reject(req.error)
  })
}

export interface StoredMessage {
  id:        string
  role:      'user' | 'bot'
  content:   string
  tool?:     string
  createdAt: string   // ISO string (Date는 IDB에 직렬화 안전하게 저장)
}

export async function dbSaveMessages(messages: StoredMessage[]): Promise<void> {
  const db = await openDB()
  return new Promise((resolve, reject) => {
    const tx    = db.transaction(STORE, 'readwrite')
    const store = tx.objectStore(STORE)
    store.clear()
    messages.forEach((m) => store.put(m))
    tx.oncomplete = () => resolve()
    tx.onerror    = () => reject(tx.error)
  })
}

export async function dbLoadMessages(): Promise<StoredMessage[]> {
  const db = await openDB()
  return new Promise((resolve, reject) => {
    const tx  = db.transaction(STORE, 'readonly')
    const req = tx.objectStore(STORE).getAll()
    req.onsuccess = () => resolve(req.result as StoredMessage[])
    req.onerror   = () => reject(req.error)
  })
}

export async function dbClearMessages(): Promise<void> {
  const db = await openDB()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, 'readwrite')
    tx.objectStore(STORE).clear()
    tx.oncomplete = () => resolve()
    tx.onerror    = () => reject(tx.error)
  })
}
