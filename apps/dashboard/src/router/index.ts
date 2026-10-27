import { createRouter, createWebHistory } from 'vue-router'
import { supabase } from '../lib/supabase'
import HomeView from '../views/HomeView.vue'
import LoginView from '../views/LoginView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: { requiresAuth: true },
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

// Safe session resolver with a strict 800ms timeout to prevent blank screen hangs on slow/offline networks
async function getSafeSession(): Promise<any> {
  try {
    const sessionPromise = supabase.auth.getSession().then((res) => res?.data?.session || null)
    const timeoutPromise = new Promise<null>((resolve) => setTimeout(() => resolve(null), 800))
    return await Promise.race([sessionPromise, timeoutPromise])
  } catch (err) {
    console.warn('Supabase getSession error (proceeding in fallback mode):', err)
    return null
  }
}

let isInitialAuthResolved = false
let initialSession: any = null

const initialAuthPromise = (async () => {
  initialSession = await getSafeSession()
  isInitialAuthResolved = true
})()

router.beforeEach(async (to) => {
  if (!isInitialAuthResolved) {
    await initialAuthPromise
  }

  let isDemo = false
  let userRole: string | null = null
  try {
    isDemo = localStorage.getItem('secondbrain_demo_mode') === 'true'
    userRole = localStorage.getItem('secondbrain_user_role')
  } catch {
    isDemo = false
    userRole = null
  }

  let session = initialSession
  if (isInitialAuthResolved && session === null && !isDemo && userRole !== 'owner') {
    session = await getSafeSession()
  }

  const isAuthenticated = !!session || isDemo || userRole === 'owner' || userRole === 'recruiter'

  // Akses rute yang membutuhkan auth: izinkan jika authenticated (session, demo recruiter, atau owner)
  if (to.meta.requiresAuth && !isAuthenticated) {
    return { name: 'login' }
  }

  // Jika sudah terautentikasi dan mencoba buka /login, arahkan ke dashboard
  if (to.name === 'login' && isAuthenticated) {
    return { name: 'home' }
  }
})

export default router
