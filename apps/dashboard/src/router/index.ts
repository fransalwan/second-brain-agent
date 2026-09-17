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

  const {
    data: { session },
  } = await supabase.auth.getSession()

  if (to.meta.requiresAuth && !session) {
    return { name: 'login' }
  }

  if (to.name === 'login' && session) {
    return { name: 'home' }
  }
})

export default router

