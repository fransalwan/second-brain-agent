<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from './lib/supabase'

const router = useRouter()

let authSubscription: { unsubscribe: () => void } | null = null

onMounted(() => {
  const {
    data: { subscription },
  } = supabase.auth.onAuthStateChange((event, session) => {
    if (event === 'SIGNED_IN' && session) {
      // Bersihkan hash token dari address bar setelah sesi Supabase aktif
      if (window.location.hash && window.location.hash.includes('access_token')) {
        window.history.replaceState(null, '', window.location.pathname)
      }
      router.push({ name: 'home' })
    } else if (event === 'SIGNED_OUT') {
      router.push({ name: 'login' })
    }
  })

  authSubscription = subscription
})

onUnmounted(() => {
  if (authSubscription) {
    authSubscription.unsubscribe()
  }
})
</script>

<template>
  <router-view />
</template>
