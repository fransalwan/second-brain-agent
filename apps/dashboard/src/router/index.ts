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
  try {
    isDemo = localStorage.getItem('secondbrain_demo_mode') === 'true'
  } catch {
    isDemo = false
  }

  let session = initialSession
  if (isInitialAuthResolved && session === null && !isDemo) {
    session = await getSafeSession()
  }

  // Akses rute yang membutuhkan auth: izinkan jika ada session aktif ATAU sedang dalam mode demo
  if (to.meta.requiresAuth && !session && !isDemo) {
    return { name: 'login' }
  }

  // Jika sudah login atau mode demo aktif dan mencoba buka /login, arahkan ke dashboard
  if (to.name === 'login' && (session || isDemo)) {
    return { name: 'home' }
  }
})

export default router
