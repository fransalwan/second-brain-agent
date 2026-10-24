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
  ],
})

let isInitialAuthResolved = false
const initialAuthPromise = supabase.auth.getSession().then(() => {
  isInitialAuthResolved = true
})

router.beforeEach(async (to) => {
  if (!isInitialAuthResolved) {
    await initialAuthPromise
  }

  const isDemo = localStorage.getItem('secondbrain_demo_mode') === 'true'

  const {
    data: { session },
  } = await supabase.auth.getSession()

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

