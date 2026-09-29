export interface AppNotification {
  id: string
  title: string
  message: string
  type: 'urgent' | 'brief' | 'exam' | 'health' | 'habit' | 'info'
  category: 'coursework' | 'health' | 'general'
  timestamp: string
  read: boolean
  actionTab?: 'overview' | 'health' | 'coursework' | 'research' | 'hobby' | 'guide'
  actionLabel?: string
  actionData?: Record<string, any>
}

const STORAGE_KEY_READ = 'sb_notifications_read'
const STORAGE_KEY_DISMISSED = 'sb_notifications_dismissed'

export function getReadNotificationIds(): Set<string> {
  try {
    const raw = localStorage.getItem(STORAGE_KEY_READ)
    return new Set(raw ? JSON.parse(raw) : [])
  } catch {
    return new Set()
  }
}

export function markNotificationAsRead(id: string) {
  try {
    const set = getReadNotificationIds()
    set.add(id)
    localStorage.setItem(STORAGE_KEY_READ, JSON.stringify(Array.from(set)))
  } catch {}
}

export function markAllNotificationsAsRead(ids: string[]) {
  try {
    const set = getReadNotificationIds()
    ids.forEach((id) => set.add(id))
    localStorage.setItem(STORAGE_KEY_READ, JSON.stringify(Array.from(set)))
  } catch {}
}

export function isNotificationDismissed(id: string): boolean {
  try {
    const raw = localStorage.getItem(STORAGE_KEY_DISMISSED)
    const set = new Set(raw ? JSON.parse(raw) : [])
    return set.has(id)
  } catch {
    return false
  }
}

export function dismissNotification(id: string) {
  try {
    const raw = localStorage.getItem(STORAGE_KEY_DISMISSED)
    const set = new Set(raw ? JSON.parse(raw) : [])
    set.add(id)
    localStorage.setItem(STORAGE_KEY_DISMISSED, JSON.stringify(Array.from(set)))
  } catch {}
}

/**
 * Web Audio API gentle sound chime (zero external assets needed)
 */
export function playNotificationSound(type: 'chime' | 'gentle' | 'alert' = 'chime') {
  try {
    const AudioCtx = window.AudioContext || (window as any).webkitAudioContext
    if (!AudioCtx) return
    const ctx = new AudioCtx()
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.connect(gain)
    gain.connect(ctx.destination)

    const now = ctx.currentTime
    if (type === 'chime') {
      osc.type = 'sine'
      osc.frequency.setValueAtTime(587.33, now) // D5
      osc.frequency.exponentialRampToValueAtTime(880, now + 0.15) // A5
      gain.gain.setValueAtTime(0.12, now)
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35)
      osc.start(now)
      osc.stop(now + 0.35)
    } else if (type === 'gentle') {
      osc.type = 'triangle'
      osc.frequency.setValueAtTime(440, now)
      osc.frequency.exponentialRampToValueAtTime(523.25, now + 0.2)
      gain.gain.setValueAtTime(0.08, now)
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.4)
      osc.start(now)
      osc.stop(now + 0.4)
    } else {
      osc.type = 'sine'
      osc.frequency.setValueAtTime(659.25, now)
      gain.gain.setValueAtTime(0.15, now)
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25)
      osc.start(now)
      osc.stop(now + 0.25)
    }
  } catch {
    // Audio context may be suspended before user gesture
  }
}

/**
 * Browser Web Push Notification
 */
export async function requestBrowserNotificationPermission(): Promise<NotificationPermission> {
  if (!('Notification' in window)) {
    return 'denied'
  }
  return await Notification.requestPermission()
}

export function sendBrowserPush(title: string, body: string) {
  if (!('Notification' in window)) return
  if (Notification.permission !== 'granted') return

  try {
    new Notification(title, {
      body,
      icon: '/favicon.ico',
      badge: '/favicon.ico',
    })
  } catch {
    // Ignore if not supported in background
  }
}
