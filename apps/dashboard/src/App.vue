<script setup lang="ts">
import { onErrorCaptured, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from './lib/supabase'

const router = useRouter()
const renderError = ref<string | null>(null)

let authSubscription: { unsubscribe: () => void } | null = null

onErrorCaptured((err) => {
  console.error('Unhandled Vue Error in Component Tree:', err)
  renderError.value = String(err instanceof Error ? err.message : err)
  return false
})

onMounted(() => {
  try {
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, session) => {
      const isDemo = localStorage.getItem('secondbrain_demo_mode') === 'true'
      if (event === 'SIGNED_IN' && session) {
        if (window.location.hash && window.location.hash.includes('access_token')) {
          window.history.replaceState(null, '', window.location.pathname)
        }
        router.push({ name: 'home' }).catch(() => {})
      } else if (event === 'SIGNED_OUT' && !isDemo) {
        router.push({ name: 'login' }).catch(() => {})
      }
    })
    authSubscription = subscription
  } catch (err) {
    console.warn('onAuthStateChange warning:', err)
  }
})

onUnmounted(() => {
  if (authSubscription) {
    authSubscription.unsubscribe()
  }
})
</script>

<template>
  <div v-if="renderError" class="p-6 max-w-lg mx-auto my-12 bg-rose-50 border border-rose-200 rounded-2xl text-rose-900 shadow-lg">
    <h2 class="text-base font-bold flex items-center gap-2 text-rose-800">
      ⚠️ Terjadi Kendala Render Komponen
    </h2>
    <p class="text-xs text-rose-700 mt-2 font-mono bg-white p-3 rounded-lg border border-rose-200/80 break-words">
      {{ renderError }}
    </p>
    <button
      type="button"
      @click="renderError = null; router.push({ name: 'home' })"
      class="mt-4 px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold rounded-lg transition-colors cursor-pointer"
    >
      Muat Ulang Halaman
    </button>
  </div>
  <router-view v-else />
</template>
