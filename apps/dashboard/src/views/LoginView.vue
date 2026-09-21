<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../lib/supabase'

const router = useRouter()

const authMode = ref<'login' | 'register'>('login')
const loginMethod = ref<'password' | 'magic_link'>('password')

// Form Fields
const fullName = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)

// UI State
const loading = ref(false)
const message = ref('')
const errorMessage = ref('')

function resetAlerts() {
  message.value = ''
  errorMessage.value = ''
}

function switchMode(mode: 'login' | 'register') {
  authMode.value = mode
  resetAlerts()
}

function switchLoginMethod(method: 'password' | 'magic_link') {
  loginMethod.value = method
  resetAlerts()
}

function translateError(errText: string): string {
  const lower = errText.toLowerCase()
  if (lower.includes('invalid login credentials') || lower.includes('invalid grant')) {
    return 'Email atau password salah. Silakan periksa kembali.'
  }
  if (lower.includes('user already registered') || lower.includes('already exists')) {
    return 'Email ini sudah terdaftar. Silakan langsung masuk.'
  }
  if (lower.includes('password should be at least 6 characters')) {
    return 'Password harus memiliki panjang minimal 6 karakter.'
  }
  if (lower.includes('rate limit')) {
    return 'Terlalu banyak percobaan. Harap tunggu beberapa saat lalu coba lagi.'
  }
  if (lower.includes('email not confirmed')) {
    return 'Email kamu belum dikonfirmasi. Periksa kotak masuk atau spam untuk tautan verifikasi.'
  }
  return errText || 'Terjadi kendala saat memproses autentikasi.'
}

async function handleLogin() {
  if (!email.value) return
  resetAlerts()
  loading.value = true

  try {
    if (loginMethod.value === 'password') {
      if (!password.value) {
        errorMessage.value = 'Password wajib diisi.'
        loading.value = false
        return
      }

      const { data, error } = await supabase.auth.signInWithPassword({
        email: email.value.trim(),
        password: password.value,
      })

      if (error) {
        errorMessage.value = translateError(error.message)
      } else if (data.session) {
        router.push({ name: 'home' })
      }
    } else {
      // Magic Link
      const { error } = await supabase.auth.signInWithOtp({
        email: email.value.trim(),
        options: {
          emailRedirectTo: window.location.origin,
        },
      })

      if (error) {
        errorMessage.value = translateError(error.message)
      } else {
        message.value =
          'Tautan masuk ajaib (Magic Link) telah dikirim ke email kamu! Silakan buka email dan klik tautan untuk masuk.'
      }
    }
  } catch (err: any) {
    errorMessage.value = 'Terjadi kesalahan tidak terduga. Silakan coba lagi.'
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  resetAlerts()

  if (!fullName.value.trim()) {
    errorMessage.value = 'Nama lengkap wajib diisi.'
    return
  }
  if (!email.value.trim()) {
    errorMessage.value = 'Email wajib diisi.'
    return
  }
  if (password.value.length < 6) {
    errorMessage.value = 'Password minimal 6 karakter.'
    return
  }
  if (password.value !== confirmPassword.value) {
    errorMessage.value = 'Konfirmasi password tidak cocok.'
    return
  }

  loading.value = true

  try {
    const trimmedEmail = email.value.trim()
    const trimmedName = fullName.value.trim()

    const { data, error } = await supabase.auth.signUp({
      email: trimmedEmail,
      password: password.value,
      options: {
        data: {
          full_name: trimmedName,
        },
      },
    })

    if (error) {
      errorMessage.value = translateError(error.message)
      return
    }

    // Jika Supabase auto-confirm session
    if (data.session?.user) {
      // Inisialisasi profil dasar di tabel profiles
      try {
        await supabase.from('profiles').upsert({
          id: data.session.user.id,
          full_name: trimmedName,
        })
      } catch {
        // Abaikan error upsert profil jika sudah ada trigger DB
      }
      router.push({ name: 'home' })
    } else {
      message.value =
        'Akun berhasil dibuat! Silakan periksa email untuk konfirmasi aktivasi, atau langsung masuk dengan password kamu.'
      authMode.value = 'login'
      loginMethod.value = 'password'
    }
  } catch (err: any) {
    errorMessage.value = 'Gagal melakukan pendaftaran akun. Silakan coba lagi.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12">
    <div class="w-full max-w-md space-y-6 rounded-2xl border border-gray-200 bg-white p-6 sm:p-8 shadow-sm">
      <!-- Header Branding -->
      <div class="text-center">
        <div class="mx-auto h-12 w-12 rounded-2xl bg-gray-900 flex items-center justify-center text-white text-2xl font-bold shadow-xs">
          🧠
        </div>
        <h1 class="mt-3 text-2xl font-bold tracking-tight text-gray-900">Second Brain</h1>
        <p class="mt-1 text-xs sm:text-sm text-gray-500">
          Dashboard Asisten Produktivitas & Manajemen Ide
        </p>
      </div>

      <!-- Tab Switcher: Masuk vs Daftar Baru -->
      <div class="flex items-center rounded-xl bg-gray-100 p-1 text-xs font-semibold">
        <button
          type="button"
          @click="switchMode('login')"
          :class="[
            'flex-1 py-2 rounded-lg transition-all',
            authMode === 'login' ? 'bg-white text-gray-900 shadow-xs' : 'text-gray-500 hover:text-gray-700'
          ]"
        >
          Masuk (Sign In)
        </button>
        <button
          type="button"
          @click="switchMode('register')"
          :class="[
            'flex-1 py-2 rounded-lg transition-all',
            authMode === 'register' ? 'bg-white text-gray-900 shadow-xs' : 'text-gray-500 hover:text-gray-700'
          ]"
        >
          Daftar Baru (Sign Up)
        </button>
      </div>

      <!-- Alert Messages -->
      <div
        v-if="message"
        class="rounded-xl bg-emerald-50 p-3.5 text-xs sm:text-sm text-emerald-800 border border-emerald-200"
      >
        <div class="flex items-start gap-2">
          <span>✅</span>
          <p class="leading-relaxed">{{ message }}</p>
        </div>
      </div>

      <div
        v-if="errorMessage"
        class="rounded-xl bg-rose-50 p-3.5 text-xs sm:text-sm border border-rose-200 text-rose-800"
      >
        <div class="flex items-start gap-2">
          <span>⚠️</span>
          <p class="leading-relaxed">{{ errorMessage }}</p>
        </div>
      </div>

      <!-- FORM 1: MASUK (SIGN IN) -->
      <div v-if="authMode === 'login'" class="space-y-4">
        <!-- Sub-pills: Password vs Magic Link -->
        <div class="flex items-center justify-center gap-2 text-[11px] font-medium text-gray-500 pb-1">
          <span>Metode:</span>
          <button
            type="button"
            @click="switchLoginMethod('password')"
            :class="[
              'px-2.5 py-1 rounded-full transition-colors',
              loginMethod === 'password'
                ? 'bg-gray-900 text-white font-semibold'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            ]"
          >
            Password Langsung
          </button>
          <button
            type="button"
            @click="switchLoginMethod('magic_link')"
            :class="[
              'px-2.5 py-1 rounded-full transition-colors',
              loginMethod === 'magic_link'
                ? 'bg-gray-900 text-white font-semibold'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            ]"
          >
            Magic Link Email
          </button>
        </div>

        <form @submit.prevent="handleLogin" class="space-y-3.5">
          <div>
            <label for="login-email" class="block text-xs font-semibold text-gray-700">Alamat Email</label>
            <input
              id="login-email"
              v-model="email"
              type="email"
              required
              autocomplete="email"
              placeholder="nama@email.com"
              class="mt-1 block w-full rounded-xl border border-gray-300 px-3.5 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-gray-900 focus:outline-none focus:ring-1 focus:ring-gray-900"
            />
          </div>

          <div v-if="loginMethod === 'password'">
            <div class="flex items-center justify-between">
              <label for="login-password" class="block text-xs font-semibold text-gray-700">Password</label>
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="text-[11px] text-gray-500 hover:text-gray-800"
              >
                {{ showPassword ? 'Sembunyikan' : 'Lihat' }}
              </button>
            </div>
            <div class="relative mt-1">
              <input
                id="login-password"
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                required
                autocomplete="current-password"
                placeholder="••••••••"
                class="block w-full rounded-xl border border-gray-300 px-3.5 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-gray-900 focus:outline-none focus:ring-1 focus:ring-gray-900"
              />
            </div>
          </div>

          <button
            type="submit"
            :disabled="loading"
            class="mt-2 flex w-full justify-center rounded-xl bg-gray-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60 transition-colors shadow-xs"
          >
            {{ loading ? 'Memproses...' : loginMethod === 'password' ? 'Masuk ke Dashboard' : 'Kirim Tautan Masuk' }}
          </button>
        </form>
      </div>

      <!-- FORM 2: DAFTAR BARU (SIGN UP) -->
      <div v-else class="space-y-4">
        <form @submit.prevent="handleRegister" class="space-y-3.5">
          <div>
            <label for="reg-name" class="block text-xs font-semibold text-gray-700">Nama Lengkap</label>
            <input
              id="reg-name"
              v-model="fullName"
              type="text"
              required
              autocomplete="name"
              placeholder="Contoh: Budi Santoso"
              class="mt-1 block w-full rounded-xl border border-gray-300 px-3.5 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-gray-900 focus:outline-none focus:ring-1 focus:ring-gray-900"
            />
          </div>

          <div>
            <label for="reg-email" class="block text-xs font-semibold text-gray-700">Alamat Email</label>
            <input
              id="reg-email"
              v-model="email"
              type="email"
              required
              autocomplete="email"
              placeholder="nama@email.com"
              class="mt-1 block w-full rounded-xl border border-gray-300 px-3.5 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-gray-900 focus:outline-none focus:ring-1 focus:ring-gray-900"
            />
          </div>

          <div>
            <div class="flex items-center justify-between">
              <label for="reg-password" class="block text-xs font-semibold text-gray-700">Password Baru</label>
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="text-[11px] text-gray-500 hover:text-gray-800"
              >
                {{ showPassword ? 'Sembunyikan' : 'Lihat' }}
              </button>
            </div>
            <input
              id="reg-password"
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              required
              minlength="6"
              autocomplete="new-password"
              placeholder="Minimal 6 karakter"
              class="mt-1 block w-full rounded-xl border border-gray-300 px-3.5 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-gray-900 focus:outline-none focus:ring-1 focus:ring-gray-900"
            />
          </div>

          <div>
            <label for="reg-confirm-password" class="block text-xs font-semibold text-gray-700">Ulangi Password</label>
            <input
              id="reg-confirm-password"
              v-model="confirmPassword"
              :type="showPassword ? 'text' : 'password'"
              required
              minlength="6"
              autocomplete="new-password"
              placeholder="Ketik ulang password"
              class="mt-1 block w-full rounded-xl border border-gray-300 px-3.5 py-2.5 text-sm text-gray-900 placeholder-gray-400 focus:border-gray-900 focus:outline-none focus:ring-1 focus:ring-gray-900"
            />
          </div>

          <button
            type="submit"
            :disabled="loading"
            class="mt-2 flex w-full justify-center rounded-xl bg-gray-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60 transition-colors shadow-xs"
          >
            {{ loading ? 'Mendaftarkan akun...' : 'Buat Akun Sekarang' }}
          </button>
        </form>
      </div>

      <!-- Footer Help -->
      <div class="text-center pt-2 border-t border-gray-100">
        <p class="text-[11px] text-gray-500 leading-relaxed">
          Setelah masuk, tautkan akun Telegrammu dengan mengirimkan
          <code class="rounded bg-gray-100 px-1 py-0.5 font-mono text-gray-800">/connect email@kamu</code>
          di bot Telegram.
        </p>
      </div>
    </div>
  </div>
</template>
