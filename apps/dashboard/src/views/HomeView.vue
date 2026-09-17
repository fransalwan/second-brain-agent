<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { supabase } from '../lib/supabase'

const userEmail = ref<string | null>(null)
const loading = ref(false)

onMounted(async () => {
  const { data: { session } } = await supabase.auth.getSession()
  userEmail.value = session?.user?.email ?? null
})

async function handleLogout() {
  loading.value = true
  try {
    await supabase.auth.signOut()
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <header class="border-b border-gray-200 bg-white">
      <div class="mx-auto flex max-w-5xl items-center justify-between px-4 py-4 sm:px-6">
        <div>
          <h1 class="text-xl font-bold text-gray-900">Second Brain Dashboard</h1>
          <p class="text-xs text-gray-500">
            Masuk sebagai: <span class="font-medium text-gray-700">{{ userEmail || '...' }}</span>
          </p>
        </div>
        <button
          @click="handleLogout"
          :disabled="loading"
          class="rounded-lg border border-gray-300 bg-white px-3.5 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:ring-offset-2 disabled:opacity-60"
        >
          {{ loading ? 'Keluar...' : 'Logout' }}
        </button>
      </div>
    </header>

    <main class="mx-auto max-w-5xl px-4 py-8 sm:px-6">
      <div class="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <h2 class="text-base font-semibold text-gray-900">Selamat Datang</h2>
        <p class="mt-1 text-sm text-gray-600">
          Sesi aktif terverifikasi. Data catatan dan pelacakan waktu akan ditampilkan di sini pada tahap berikutnya.
        </p>
      </div>
    </main>
  </div>
</template>

