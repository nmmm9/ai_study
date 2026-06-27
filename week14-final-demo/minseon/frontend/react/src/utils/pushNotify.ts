// Push API + Notifications API 유틸리티

export async function registerServiceWorker(): Promise<ServiceWorkerRegistration | null> {
  if (!('serviceWorker' in navigator)) return null
  try {
    const reg = await navigator.serviceWorker.register('/sw.js', { scope: '/' })
    console.log('[SW] 등록 완료')
    return reg
  } catch (e) {
    console.error('[SW] 등록 실패:', e)
    return null
  }
}

export async function requestNotificationPermission(): Promise<boolean> {
  if (!('Notification' in window)) return false
  if (Notification.permission === 'granted') return true
  if (Notification.permission === 'denied') return false
  const perm = await Notification.requestPermission()
  return perm === 'granted'
}

export function showLocalNotification(title: string, body: string): void {
  if (!('Notification' in window)) return
  if (Notification.permission !== 'granted') return
  navigator.serviceWorker.ready.then((reg) => {
    reg.showNotification(title, {
      body,
      icon:  '/favicon.svg',
      badge: '/favicon.svg',
      tag:   'policy-notification',
    })
  })
}
