export type UserRole = 'owner' | 'recruiter'

export const ROLE_STORAGE_KEY = 'secondbrain_user_role'
export const DEMO_STORAGE_KEY = 'secondbrain_demo_mode'

// Master Passkey untuk Frans Alwan Purba (Pemilik)
export const OWNER_PASSKEY = import.meta.env.VITE_OWNER_PASSKEY || 'frans-ugm-2026'
export const OWNER_EMAIL = 'fransalwanpurba@mail.ugm.ac.id'

export function getUserRole(): UserRole {
  try {
    const stored = localStorage.getItem(ROLE_STORAGE_KEY)
    if (stored === 'owner') return 'owner'
    if (stored === 'recruiter') return 'recruiter'
    const isDemo = localStorage.getItem(DEMO_STORAGE_KEY) === 'true'
    return isDemo ? 'recruiter' : 'recruiter'
  } catch {
    return 'recruiter'
  }
}

export function setRoleRecruiter(): void {
  try {
    localStorage.setItem(ROLE_STORAGE_KEY, 'recruiter')
    localStorage.setItem(DEMO_STORAGE_KEY, 'true')
  } catch (err) {
    console.error('Gagal menyimpan role recruiter di localStorage', err)
  }
}

export function setRoleOwner(): void {
  try {
    localStorage.setItem(ROLE_STORAGE_KEY, 'owner')
    localStorage.setItem(DEMO_STORAGE_KEY, 'false')
  } catch (err) {
    console.error('Gagal menyimpan role owner di localStorage', err)
  }
}

export function clearAuthRole(): void {
  try {
    localStorage.removeItem(ROLE_STORAGE_KEY)
    localStorage.removeItem(DEMO_STORAGE_KEY)
  } catch (err) {
    console.error('Gagal membersihkan role dari localStorage', err)
  }
}
