<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../lib/supabase'
import PrivacyModal from '../components/PrivacyModal.vue'

const router = useRouter()
const privacyModalRef = ref<InstanceType<typeof PrivacyModal> | null>(null)

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
const loadingDemo = ref(false)
const message = ref('')
const errorMessage = ref('')

function resetAlerts() {
  message.value = ''
  errorMessage.value = ''
}

async function handleGuestDemo() {
  resetAlerts()
  loadingDemo.value = true
  try {
    localStorage.setItem('secondbrain_demo_mode', 'true')
    await router.push({ name: 'home' })
  } catch (err) {
    // Fallback hard navigation jika router transition terhambat
    window.location.href = '/'
  } finally {
    loadingDemo.value = false
  }
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
    return 'Email atau password salah. Silakan periksa kembali atau gunakan Mode Demo Instan.'
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
        localStorage.removeItem('secondbrain_demo_mode')
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

    if (data.session?.user) {
      try {
        await supabase.from('profiles').upsert({
          id: data.session.user.id,
          full_name: trimmedName,
        })
      } catch {
        // Ignored
      }
      localStorage.removeItem('secondbrain_demo_mode')
      router.push({ name: 'home' })
      return
    }

    const { data: loginData } = await supabase.auth.signInWithPassword({
      email: trimmedEmail,
      password: password.value,
    })

    if (loginData?.session?.user) {
      try {
        await supabase.from('profiles').upsert({
          id: loginData.session.user.id,
          full_name: trimmedName,
        })
      } catch {
        // Ignored
      }
      localStorage.removeItem('secondbrain_demo_mode')
      router.push({ name: 'home' })
      return
    }

    message.value = 'Akun berhasil dibuat! Silakan langsung masuk dengan email dan password kamu.'
    authMode.value = 'login'
    loginMethod.value = 'password'
  } catch (err: any) {
    errorMessage.value = 'Gagal melakukan pendaftaran akun. Silakan coba lagi.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-slate-950 text-slate-100 flex flex-col lg:flex-row">
    <!-- SISI KIRI: Architectural Showcase & Recruiter Authority -->
    <div class="order-2 lg:order-1 flex-1 p-6 sm:p-10 lg:p-14 flex flex-col justify-between bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950/80 border-t lg:border-t-0 lg:border-r border-slate-800/80 relative overflow-hidden">
      <!-- Glow ambient background effect -->
      <div class="absolute -top-32 -left-32 w-96 h-96 bg-purple-600/15 rounded-full blur-3xl pointer-events-none"></div>
      <div class="absolute -bottom-32 -right-32 w-96 h-96 bg-indigo-600/15 rounded-full blur-3xl pointer-events-none"></div>

      <!-- Top Brand -->
      <div class="relative z-10">
        <div class="flex items-center gap-3">
          <div class="h-11 w-11 rounded-2xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center text-white text-2xl font-bold shadow-lg shadow-indigo-500/25 shrink-0">
            🧠
          </div>
          <div>
            <div class="flex items-center gap-2">
              <span class="text-xl font-black tracking-tight text-white">Second Brain</span>
              <span class="rounded-full bg-purple-500/20 px-2.5 py-0.5 text-[11px] font-bold text-purple-300 border border-purple-500/30">
                Autonomous AI Agent
              </span>
            </div>
            <p class="text-xs text-slate-400 font-medium">
              Engineered by Frans Alwan Purba · Master's in CS (AI), Universitas Gadjah Mada
            </p>
          </div>
        </div>

        <!-- Main Headline -->
        <div class="mt-8 lg:mt-12 space-y-3">
          <h1 class="text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight text-white leading-tight">
            Autonomous AI Productivity Agent &amp; <span class="bg-gradient-to-r from-indigo-400 via-purple-300 to-cyan-300 bg-clip-text text-transparent">Polyglot Telemetry Engine.</span>
          </h1>
          <p class="text-xs sm:text-sm text-slate-300 leading-relaxed max-w-2xl">
            Sistem operasi personal terdistribusi untuk mahasiswa magister dan software engineer. Mengintegrasikan background worker Go, inferensi FastAPI, hybrid semantic RAG pgvector (768-D), serta pipeline webhook otomatis dari 3 repositori akademik.
          </p>
        </div>

        <!-- 4 Pillars Engineering Showcase Grid -->
        <div class="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-3.5 max-w-2xl">
          <!-- Pilar 1: Kesehatan -->
          <div class="rounded-2xl border border-emerald-500/20 bg-emerald-950/25 p-4 backdrop-blur-xs transition-all hover:border-emerald-500/40 hover:bg-emerald-950/40">
            <div class="flex items-center gap-2.5">
              <span class="text-xl p-2 rounded-xl bg-emerald-500/20 shrink-0">🩺</span>
              <div>
                <h2 class="text-xs font-bold text-emerald-300">Priority #1: Vitalitas &amp; Kesehatan</h2>
                <p class="text-[11px] text-slate-400 mt-0.5">Analisis Sleep Debt sirkadian, target hidrasi 8 gelas, dan radar pencegahan burnout.</p>
              </div>
            </div>
          </div>

          <!-- Pilar 2: Kuliah -->
          <div class="rounded-2xl border border-blue-500/20 bg-blue-950/25 p-4 backdrop-blur-xs transition-all hover:border-blue-500/40 hover:bg-blue-950/40">
            <div class="flex items-center gap-2.5">
              <span class="text-xl p-2 rounded-xl bg-blue-500/20 shrink-0">🎓</span>
              <div>
                <h2 class="text-xs font-bold text-blue-300">Priority #2: Kuliah &amp; Akademik</h2>
                <p class="text-[11px] text-slate-400 mt-0.5">Prioritas bobot tugas, milestone Tubes Machine Learning, dan Exam Mastery Radar.</p>
              </div>
            </div>
          </div>

          <!-- Pilar 3: Riset -->
          <div class="rounded-2xl border border-purple-500/20 bg-purple-950/25 p-4 backdrop-blur-xs transition-all hover:border-purple-500/40 hover:bg-purple-950/40">
            <div class="flex items-center gap-2.5">
              <span class="text-xl p-2 rounded-xl bg-purple-500/20 shrink-0">🔬</span>
              <div>
                <h2 class="text-xs font-bold text-purple-300">Priority #3: Riset &amp; Skripsi</h2>
                <p class="text-[11px] text-slate-400 mt-0.5">Pelacak eksperimen CatBoost, milestone 5 Bab, radar anti-ghosting dospem, &amp; ekspor LaTeX.</p>
              </div>
            </div>
          </div>

          <!-- Pilar 4: Agent Ops -->
          <div class="rounded-2xl border border-cyan-500/20 bg-cyan-950/25 p-4 backdrop-blur-xs transition-all hover:border-cyan-500/40 hover:bg-cyan-950/40">
            <div class="flex items-center gap-2.5">
              <span class="text-xl p-2 rounded-xl bg-cyan-500/20 shrink-0">⚡</span>
              <div>
                <h2 class="text-xs font-bold text-cyan-300">Priority #4: Agent Ops &amp; Telemetry</h2>
                <p class="text-[11px] text-slate-400 mt-0.5">Worker Golang (:8085), pgvector 768-D RRF search, and auto-sync Git commit hook.</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Academic & Architecture Badges -->
        <div class="mt-8 pt-6 border-t border-slate-800/80 space-y-2.5">
          <p class="text-[11px] font-bold uppercase tracking-wider text-slate-400">Arsitektur &amp; Standar Rekayasa:</p>
          <div class="flex flex-wrap gap-2 text-xs">
            <span class="inline-flex items-center gap-1.5 rounded-lg bg-slate-900/90 px-3 py-1.5 text-slate-300 border border-slate-800 shadow-2xs">
              <span class="text-cyan-400 font-mono font-bold">Go</span>
              <span>Worker Concurrency (:8085)</span>
            </span>
            <span class="inline-flex items-center gap-1.5 rounded-lg bg-slate-900/90 px-3 py-1.5 text-slate-300 border border-slate-800 shadow-2xs">
              <span class="text-emerald-400 font-mono font-bold">FastAPI</span>
              <span>Vector AI Inference</span>
            </span>
            <span class="inline-flex items-center gap-1.5 rounded-lg bg-slate-900/90 px-3 py-1.5 text-slate-300 border border-slate-800 shadow-2xs">
              <span class="text-purple-400 font-mono font-bold">pgvector</span>
              <span>768-D Hybrid RAG</span>
            </span>
            <span class="inline-flex items-center gap-1.5 rounded-lg bg-slate-900/90 px-3 py-1.5 text-slate-300 border border-slate-800 shadow-2xs">
              <span class="text-indigo-400 font-bold">Git</span>
              <span>Webhook Telemetry Sync</span>
            </span>
            <span class="inline-flex items-center gap-1.5 rounded-lg bg-slate-900/90 px-3 py-1.5 text-slate-300 border border-slate-800 shadow-2xs">
              <span class="text-emerald-400 font-bold">RLS</span>
              <span>PostgreSQL Privacy Guard</span>
            </span>
          </div>
        </div>
      </div>

      <!-- Author Note -->
      <div class="mt-8 relative z-10 pt-4 flex items-center justify-between text-xs text-slate-500 border-t border-slate-900">
        <span class="font-mono text-[11px]">System Status: Production v2.4 (All Systems Nominal)</span>
        <span class="text-slate-400">Yogyakarta, Indonesia</span>
      </div>
    </div>

    <!-- SISI KANAN: Auth Card & Recruiter Instant Access -->
    <div class="order-1 lg:order-2 w-full lg:w-[480px] xl:w-[520px] flex items-center justify-center p-4 sm:p-8 lg:p-10 bg-slate-950/80 backdrop-blur-xl border-b lg:border-b-0 lg:border-l border-slate-800/80">
      <div class="w-full max-w-md space-y-5 rounded-3xl border border-slate-800/90 bg-slate-900/95 p-6 sm:p-8 shadow-2xl shadow-indigo-950/50">
        
        <!-- Mobile Mini-Brand Header -->
        <div class="flex items-center gap-3 pb-1 lg:hidden">
          <div class="h-10 w-10 rounded-2xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center text-white text-xl font-bold shadow-md shadow-indigo-500/25 shrink-0">
            🧠
          </div>
          <div>
            <div class="flex items-center gap-1.5">
              <span class="text-base font-black tracking-tight text-white">Second Brain</span>
              <span class="rounded-full bg-purple-500/20 px-2 py-0.2 text-[10px] font-bold text-purple-300 border border-purple-500/30">
                AI Agent
              </span>
            </div>
            <p class="text-[11px] text-slate-400">Autonomous Productivity Agent · Frans Alwan Purba</p>
          </div>
        </div>

        <!-- 1-Click Recruiter Demo Button (PROMINENT & HIGHEST VALUE) -->
        <div class="p-4 rounded-2xl bg-gradient-to-br from-indigo-950/80 via-purple-950/60 to-slate-900 border border-indigo-500/40 shadow-lg shadow-indigo-950/50 space-y-2.5">
          <div class="flex items-center justify-between">
            <span class="inline-flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-amber-300">
              <span class="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
              Akses Cepat Recruiter &amp; Reviewer
            </span>
            <span class="rounded bg-indigo-500/20 px-1.5 py-0.5 text-[10px] font-mono text-indigo-300 border border-indigo-500/30">Zero Setup</span>
          </div>

          <button
            type="button"
            @click="handleGuestDemo"
            :disabled="loadingDemo"
            class="w-full min-h-[46px] flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 via-purple-600 to-pink-600 px-4 py-2.5 text-xs font-extrabold text-white shadow-md shadow-indigo-600/30 hover:from-indigo-400 hover:to-pink-500 hover:shadow-indigo-600/50 transition-all cursor-pointer disabled:opacity-60"
          >
            <span v-if="!loadingDemo" class="text-sm">⚡</span>
            <span v-else class="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin"></span>
            <span>{{ loadingDemo ? 'Mempersiapkan Lingkungan Demo...' : 'Masuk Mode Demo Instan (1-Click)' }}</span>
          </button>
          
          <p class="text-[11px] text-center text-slate-300 leading-snug">
            Langsung eksplorasi Bento Grid, pgvector RAG, cluster telemetry, dan tour 60 detik tanpa perlu login.
          </p>
        </div>

        <!-- Divider -->
        <div class="relative flex items-center justify-center">
          <div class="border-t border-slate-800 w-full"></div>
          <span class="bg-slate-900 px-3 text-[11px] font-medium text-slate-500 uppercase tracking-wider shrink-0">
            atau masuk dengan akun
          </span>
        </div>

        <!-- Mode Switcher: Masuk vs Daftar Baru -->
        <div class="flex items-center rounded-xl bg-slate-950 p-1 text-xs font-semibold border border-slate-800">
          <button
            type="button"
            @click="switchMode('login')"
            class="flex-1 min-h-[40px] flex items-center justify-center py-2 rounded-lg transition-all cursor-pointer"
            :class="authMode === 'login' ? 'bg-indigo-600 text-white shadow-xs font-bold' : 'text-slate-400 hover:text-white'"
          >
            Masuk (Sign In)
          </button>
          <button
            type="button"
            @click="switchMode('register')"
            class="flex-1 min-h-[40px] flex items-center justify-center py-2 rounded-lg transition-all cursor-pointer"
            :class="authMode === 'register' ? 'bg-indigo-600 text-white shadow-xs font-bold' : 'text-slate-400 hover:text-white'"
          >
            Daftar Baru (Sign Up)
          </button>
        </div>

        <!-- Alerts -->
        <div
          v-if="message"
          class="rounded-xl bg-emerald-950/60 p-3.5 text-xs text-emerald-300 border border-emerald-500/30 flex items-start gap-2"
        >
          <span>✅</span>
          <p class="leading-relaxed">{{ message }}</p>
        </div>

        <div
          v-if="errorMessage"
          class="rounded-xl bg-rose-950/60 p-3.5 text-xs text-rose-300 border border-rose-500/30 flex items-start gap-2"
        >
          <span>⚠️</span>
          <p class="leading-relaxed">{{ errorMessage }}</p>
        </div>

        <!-- FORM: MASUK (SIGN IN) -->
        <div v-if="authMode === 'login'" class="space-y-4">
          <!-- Toggle Password vs Magic Link -->
          <div class="flex items-center justify-between text-[11px] text-slate-400">
            <span>Metode Autentikasi:</span>
            <div class="flex items-center gap-1.5">
              <button
                type="button"
                @click="switchLoginMethod('password')"
                class="px-2.5 py-1 rounded-lg transition-colors cursor-pointer text-xs"
                :class="loginMethod === 'password' ? 'bg-slate-800 text-indigo-300 font-bold border border-slate-700' : 'text-slate-500 hover:text-slate-300'"
              >
                Password
              </button>
              <button
                type="button"
                @click="switchLoginMethod('magic_link')"
                class="px-2.5 py-1 rounded-lg transition-colors cursor-pointer text-xs"
                :class="loginMethod === 'magic_link' ? 'bg-slate-800 text-indigo-300 font-bold border border-slate-700' : 'text-slate-500 hover:text-slate-300'"
              >
                Magic Link
              </button>
            </div>
          </div>

          <form @submit.prevent="handleLogin" class="space-y-3.5">
            <div>
              <label class="block text-xs font-semibold text-slate-300 mb-1">Email</label>
              <input
                v-model="email"
                type="email"
                required
                autocomplete="email"
                placeholder="nama@email.com atau email kampus"
                class="w-full min-h-[44px] rounded-xl border border-slate-800 bg-slate-950 px-3.5 py-2 text-sm sm:text-xs text-white placeholder-slate-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none transition-colors"
              />
            </div>

            <div v-if="loginMethod === 'password'">
              <div class="flex items-center justify-between mb-1">
                <label class="block text-xs font-semibold text-slate-300">Password</label>
                <button
                  type="button"
                  @click="showPassword = !showPassword"
                  class="text-xs text-indigo-400 hover:underline cursor-pointer"
                >
                  {{ showPassword ? 'Sembunyikan' : 'Lihat' }}
                </button>
              </div>
              <input
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                required
                autocomplete="current-password"
                placeholder="••••••••"
                class="w-full min-h-[44px] rounded-xl border border-slate-800 bg-slate-950 px-3.5 py-2 text-sm sm:text-xs text-white placeholder-slate-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none transition-colors"
              />
            </div>

            <button
              type="submit"
              :disabled="loading"
              class="w-full min-h-[46px] mt-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-xs sm:text-sm font-bold text-white shadow-md shadow-indigo-600/30 hover:bg-indigo-500 transition-all disabled:opacity-50 cursor-pointer flex items-center justify-center gap-2"
            >
              <span v-if="loading" class="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin"></span>
              <span>{{ loading ? 'Memverifikasi...' : (loginMethod === 'password' ? 'Masuk ke Dashboard' : 'Kirim Tautan Magic Link') }}</span>
            </button>
          </form>
        </div>

        <!-- FORM: DAFTAR BARU (SIGN UP) -->
        <div v-else class="space-y-3.5">
          <form @submit.prevent="handleRegister" class="space-y-3">
            <div>
              <label class="block text-xs font-semibold text-slate-300 mb-1">Nama Lengkap</label>
              <input
                v-model="fullName"
                type="text"
                required
                placeholder="Contoh: Frans Alwan Purba"
                class="w-full min-h-[44px] rounded-xl border border-slate-800 bg-slate-950 px-3.5 py-2 text-sm sm:text-xs text-white placeholder-slate-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none transition-colors"
              />
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-300 mb-1">Email</label>
              <input
                v-model="email"
                type="email"
                required
                autocomplete="email"
                placeholder="nama@email.com"
                class="w-full min-h-[44px] rounded-xl border border-slate-800 bg-slate-950 px-3.5 py-2 text-sm sm:text-xs text-white placeholder-slate-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none transition-colors"
              />
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-300 mb-1">Password (Minimal 6 Karakter)</label>
              <input
                v-model="password"
                type="password"
                required
                autocomplete="new-password"
                placeholder="••••••••"
                class="w-full min-h-[44px] rounded-xl border border-slate-800 bg-slate-950 px-3.5 py-2 text-sm sm:text-xs text-white placeholder-slate-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none transition-colors"
              />
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-300 mb-1">Konfirmasi Password</label>
              <input
                v-model="confirmPassword"
                type="password"
                required
                autocomplete="new-password"
                placeholder="••••••••"
                class="w-full min-h-[44px] rounded-xl border border-slate-800 bg-slate-950 px-3.5 py-2 text-sm sm:text-xs text-white placeholder-slate-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none transition-colors"
              />
            </div>

            <button
              type="submit"
              :disabled="loading"
              class="w-full min-h-[46px] mt-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-xs sm:text-sm font-bold text-white shadow-md shadow-indigo-600/30 hover:bg-indigo-500 transition-all disabled:opacity-50 cursor-pointer flex items-center justify-center gap-2"
            >
              <span v-if="loading" class="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin"></span>
              <span>{{ loading ? 'Mendaftarkan Akun...' : 'Buat Akun Baru' }}</span>
            </button>
          </form>
        </div>

        <!-- Footer Trust & Privacy Link -->
        <div class="pt-2 text-center text-[11px] text-slate-400 space-y-1">
          <p>
            <span>Data dilindungi secara terisolasi via </span>
            <span class="text-indigo-400 font-semibold">PostgreSQL Row-Level Security</span>
          </p>
          <button
            type="button"
            @click="privacyModalRef?.openModal('policy')"
            class="text-indigo-300 hover:text-indigo-200 underline font-medium cursor-pointer"
          >
            🛡️ Kedaulatan Data &amp; Privasi (Zero Trackers / Zero Ads) ↗
          </button>
        </div>
      </div>
    </div>

    <!-- Privacy & Data Sovereignty Center Modal -->
    <PrivacyModal ref="privacyModalRef" />
  </div>
</template>
