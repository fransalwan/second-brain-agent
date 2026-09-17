<script setup lang="ts">
import { ref } from 'vue'
import { supabase } from '../lib/supabase'

const email = ref('')
const loading = ref(false)
const message = ref('')
const errorMessage = ref('')

async function handleLogin() {
  if (!email.value) return

  loading.value = true
  message.value = ''
  errorMessage.value = ''

  try {
    const { error } = await supabase.auth.signInWithOtp({
      email: email.value.trim(),
      options: {
        emailRedirectTo: window.location.origin,
      },
    })

    if (error) {
      errorMessage.value = error.message
    } else {
      message.value = 'Tautan masuk telah dikirim ke email kamu. Silakan periksa kotak masuk atau spam.'
    }
  } catch (err: any) {
    errorMessage.value = 'Terjadi kesalahan saat memproses permintaan. Silakan coba lagi.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12">
    <div class="w-full max-w-md space-y-6 rounded-xl border border-gray-200 bg-white p-8 shadow-sm">
      <div class="text-center">
        <h1 class="text-2xl font-bold tracking-tight text-gray-900">Second Brain</h1>
        <p class="mt-2 text-sm text-gray-600">
          Masuk ke dashboard menggunakan tautan email (Magic Link).
        </p>
      </div>

      <form @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <label for="email" class="block text-sm font-medium text-gray-700">Email</label>
          <input
            id="email"
            v-model="email"
            type="email"
            required
            autocomplete="email"
            placeholder="nama@email.com"
            class="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 placeholder-gray-400 focus:border-gray-900 focus:outline-none focus:ring-1 focus:ring-gray-900 sm:text-sm"
          />
        </div>

        <div v-if="message" class="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-750 border border-emerald-200 text-emerald-800">
          {{ message }}
        </div>

        <div v-if="errorMessage" class="rounded-lg bg-rose-50 p-3 text-sm border border-rose-200 text-rose-800">
          {{ errorMessage }}
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="flex w-full justify-center rounded-lg bg-gray-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {{ loading ? 'Mengirim tautan...' : 'Kirim Magic Link' }}
        </button>
      </form>
    </div>
  </div>
</template>

