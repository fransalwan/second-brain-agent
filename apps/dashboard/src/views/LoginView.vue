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

    // 1. Coba langsung pakai session dari signUp jika tersedia
    if (data.session?.user) {
      try {
        await supabase.from('profiles').upsert({
          id: data.session.user.id,
          full_name: trimmedName,
        })
      } catch {
        // Abaikan error upsert profil jika sudah ada trigger DB
      }
      router.push({ name: 'home' })
      return
    }

    // 2. Auto-login langsung dengan password (zero friction untuk mahasiswa)
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
        // Abaikan error upsert
      }
      router.push({ name: 'home' })
      return
    }

    // 3. Fallback jika belum otomatis login
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
    <!-- SISI KIRI: Showcase, Value Proposition & Kredibilitas Mahasiswa -->
    <div class="flex-1 p-6 sm:p-10 lg:p-16 flex flex-col justify-between bg-gradient-to-br from-slate-900 via-indigo-950/80 to-slate-950 border-b lg:border-b-0 lg:border-r border-slate-800/80 relative overflow-hidden">
      <!-- Glow ambient background effect -->
      <div class="absolute -top-32 -left-32 w-96 h-96 bg-purple-600/15 rounded-full blur-3xl pointer-events-none"></div>
      <div class="absolute -bottom-32 -right-32 w-96 h-96 bg-indigo-600/15 rounded-full blur-3xl pointer-events-none"></div>

      <!-- Top Brand -->
      <div class="relative z-10">
        <div class="flex items-center gap-3">
          <div class="h-11 w-11 rounded-2xl bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-white text-2xl font-bold shadow-lg shadow-indigo-500/25">
            🧠
          </div>
          <div>
            <div class="flex items-center gap-2">
              <span class="text-xl font-black tracking-tight text-white">Second Brain</span>
              <span class="rounded-full bg-indigo-500/20 px-2.5 py-0.5 text-[11px] font-bold text-indigo-300 border border-indigo-500/30">
                Student Edition 🎓
              </span>
            </div>
            <p class="text-xs text-slate-400">Autonomous AI Copilot &amp; Life Balance Hub</p>
          </div>
        </div>

        <!-- Main Headline -->
        <div class="mt-8 lg:mt-12 space-y-3">
          <h1 class="text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight text-white leading-tight">
            Lulus Skripsi &amp; Kuliah Sukses, Tetap Sehat, dan <span class="bg-gradient-to-r from-amber-300 via-orange-300 to-amber-200 bg-clip-text text-transparent">Me-Time Tanpa Rasa Bersalah.</span>
          </h1>
          <p class="text-xs sm:text-sm text-slate-300 leading-relaxed max-w-2xl">
            Satu asisten pribadi yang menyatukan kecerdasan Telegram ambient dengan Dashboard interaktif untuk 4 prioritas nyata mahasiswa:
          </p>
        </div>

        <!-- 4 Pillars Interactive Showcase Grid -->
        <div class="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-3.5 max-w-2xl">
          <!-- Pilar 1: Kesehatan -->
          <div class="rounded-2xl border border-emerald-500/20 bg-emerald-950/20 p-4 backdrop-blur-xs transition-all hover:border-emerald-500/40">
            <div class="flex items-center gap-2.5">
              <span class="text-xl p-1.5 rounded-xl bg-emerald-500/20">🩺</span>
              <div>
                <h2 class="text-xs font-bold text-emerald-300">Priority #1: Kesehatan</h2>
                <p class="text-[11px] text-slate-400">Hidrasi 8 gelas, kalkulator Sleep Debt, &amp; radar risiko burnout.</p>
              </div>
            </div>
          </div>

          <!-- Pilar 2: Kuliah -->
          <div class="rounded-2xl border border-blue-500/20 bg-blue-950/20 p-4 backdrop-blur-xs transition-all hover:border-blue-500/40">
            <div class="flex items-center gap-2.5">
              <span class="text-xl p-1.5 rounded-xl bg-blue-500/20">🎓</span>
              <div>
                <h2 class="text-xs font-bold text-blue-300">Priority #2: Kuliah</h2>
                <p class="text-[11px] text-slate-400">Filter bobot tugas, milestone Tubes, &amp; Exam Mastery Radar.</p>
              </div>
            </div>
          </div>

          <!-- Pilar 3: Riset -->
          <div class="rounded-2xl border border-purple-500/20 bg-purple-950/20 p-4 backdrop-blur-xs transition-all hover:border-purple-500/40">
            <div class="flex items-center gap-2.5">
              <span class="text-xl p-1.5 rounded-xl bg-purple-500/20">🔬</span>
              <div>
                <h2 class="text-xs font-bold text-purple-300">Priority #3: Riset &amp; Skripsi</h2>
                <p class="text-[11px] text-slate-400">Progress 5 Bab, Anti-Ghosting dospem, &amp; 1-klik export tabel LaTeX.</p>
              </div>
            </div>
          </div>

          <!-- Pilar 4: Hobby -->
          <div class="rounded-2xl border border-amber-500/20 bg-amber-950/20 p-4 backdrop-blur-xs transition-all hover:border-amber-500/40">
            <div class="flex items-center gap-2.5">
              <span class="text-xl p-1.5 rounded-xl bg-amber-500/20">🎨</span>
              <div>
                <h2 class="text-xs font-bold text-amber-300">Priority #4: Hobby &amp; Rest</h2>
                <p class="text-[11px] text-slate-400">Guilt-free me-time 90m/hari, backlog game/buku, &amp; dopamine return.</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Academic Trust Badges -->
        <div class="mt-8 pt-6 border-t border-slate-800/80 space-y-2.5">
          <p class="text-[11px] font-bold uppercase tracking-wider text-slate-400">Keunggulan Kredibilitas Akademik:</p>
          <div class="flex flex-wrap gap-2 text-xs">
            <span class="inline-flex items-center gap-1.5 rounded-lg bg-slate-800/80 px-3 py-1.5 text-slate-300 border border-slate-700/60">
              <span>📄</span>
              <span>IEEE / Overleaf LaTeX Table Ready</span>
            </span>
            <span class="inline-flex items-center gap-1.5 rounded-lg bg-slate-800/80 px-3 py-1.5 text-slate-300 border border-slate-700/60">
              <span>🛡️</span>
              <span>Anti-Ghosting Dosen Radar (&gt;14 Hari)</span>
            </span>
            <span class="inline-flex items-center gap-1.5 rounded-lg bg-slate-800/80 px-3 py-1.5 text-slate-300 border border-slate-700/60">
              <span>🤖</span>
              <span>Google Gemini 2.5 Flash + Telegram</span>
            </span>
            <span class="inline-flex items-center gap-1.5 rounded-lg bg-slate-800/80 px-3 py-1.5 text-slate-300 border border-slate-700/60">
              <span>⚡</span>
              <span>Git Hook Commit Telemetry</span>
            </span>
          </div>
        </div>
      </div>

      <!-- Bottom Student Quote -->
      <div class="mt-8 relative z-10 pt-4 text-xs text-slate-400 italic">
        "Gak ada lagi overthinking waktu main game atau ngerasa bersalah pas istirahat. Skripsi dan tugas tetap selesai tepat waktu."
      </div>
    </div>

    <!-- SISI KANAN: Modern Auth Card (Sign In & Sign Up) -->
    <div class="w-full lg:w-[460px] xl:w-[500px] flex items-center justify-center p-6 sm:p-10 bg-slate-900/60 backdrop-blur-md">
      <div class="w-full max-w-md space-y-6 rounded-3xl border border-slate-800 bg-slate-900 p-6 sm:p-8 shadow-2xl shadow-indigo-950/40">
        <!-- Auth Header Title -->
        <div class="text-left space-y-1">
          <h2 class="text-xl font-bold text-white tracking-tight">
            {{ authMode === 'login' ? 'Masuk ke Akun Kamu' : 'Mulai Second Brain Kamu' }}
          </h2>
          <p class="text-xs text-slate-400">
            {{ authMode === 'login' ? 'Lanjutkan progres skripsi, kuliah, dan kesehatanmu.' : 'Daftar gratis dan rasakan keseimbangan hidup mahasiswa.' }}
          </p>
        </div>

        <!-- Mode Switcher: Masuk vs Daftar Baru -->
        <div class="flex items-center rounded-xl bg-slate-950 p-1 text-xs font-semibold border border-slate-800">
          <button
            type="button"
            @click="switchMode('login')"
            class="flex-1 py-2 rounded-lg transition-all cursor-pointer"
            :class="authMode === 'login' ? 'bg-indigo-600 text-white shadow-xs' : 'text-slate-400 hover:text-white'"
          >
            Masuk (Sign In)
          </button>
          <button
            type="button"
            @click="switchMode('register')"
            class="flex-1 py-2 rounded-lg transition-all cursor-pointer"
            :class="authMode === 'register' ? 'bg-indigo-600 text-white shadow-xs' : 'text-slate-400 hover:text-white'"
          >
            Daftar Baru (Sign Up)
          </button>
        </div>

        <!-- Alerts -->
        <div
          v-if="message"
          class="rounded-xl bg-emerald-950/50 p-3.5 text-xs text-emerald-300 border border-emerald-500/30 flex items-start gap-2"
        >
          <span>✅</span>
          <p class="leading-relaxed">{{ message }}</p>
        </div>

        <div
          v-if="errorMessage"
          class="rounded-xl bg-rose-950/50 p-3.5 text-xs text-rose-300 border border-rose-500/30 flex items-start gap-2"
        >
          <span>⚠️</span>
          <p class="leading-relaxed">{{ errorMessage }}</p>
        </div>

        <!-- FORM: MASUK (SIGN IN) -->
        <div v-if="authMode === 'login'" class="space-y-4">
          <!-- Toggle Password vs Magic Link -->
          <div class="flex items-center justify-between text-[11px] text-slate-400 pb-1">
            <span>Metode Autentikasi:</span>
            <div class="flex items-center gap-1.5">
              <button
                type="button"
                @click="switchLoginMethod('password')"
                class="px-2.5 py-1 rounded-lg transition-colors cursor-pointer"
                :class="loginMethod === 'password' ? 'bg-slate-800 text-indigo-400 font-bold border border-slate-700' : 'text-slate-500 hover:text-slate-300'"
              >
                Password
              </button>
              <button
                type="button"
                @click="switchLoginMethod('magic_link')"
                class="px-2.5 py-1 rounded-lg transition-colors cursor-pointer"
                :class="loginMethod === 'magic_link' ? 'bg-slate-800 text-indigo-400 font-bold border border-slate-700' : 'text-slate-500 hover:text-slate-300'"
              >
                Magic Link
              </button>
            </div>
          </div>

          <form @submit.prevent="handleLogin" class="space-y-3.5">
            <div>
              <label class="block text-xs font-semibold text-slate-300 mb-1">Email Mahasiswa / Akun</label>
              <input
                v-model="email"
                type="email"
                required
                placeholder="nama@kampus.ac.id atau email pribadi"
                class="w-full rounded-xl border border-slate-800 bg-slate-950 px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none transition-colors"
              />
            </div>

            <div v-if="loginMethod === 'password'">
              <div class="flex items-center justify-between mb-1">
                <label class="block text-xs font-semibold text-slate-300">Password</label>
                <button
                  type="button"
                  @click="showPassword = !showPassword"
                  class="text-[11px] text-indigo-400 hover:underline cursor-pointer"
                >
                  {{ showPassword ? 'Sembunyikan' : 'Lihat' }}
                </button>
              </div>
              <input
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                required
                placeholder="••••••••"
                class="w-full rounded-xl border border-slate-800 bg-slate-950 px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none transition-colors"
              />
            </div>

            <button
              type="submit"
              :disabled="loading"
              class="w-full mt-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-xs font-bold text-white shadow-md shadow-indigo-600/30 hover:bg-indigo-500 transition-all disabled:opacity-50 cursor-pointer"
            >
              {{ loading ? 'Memproses...' : (loginMethod === 'password' ? 'Masuk ke Dashboard' : 'Kirim Tautan Magic Link') }}
            </button>
          </form>
        </div>

        <!-- FORM: DAFTAR BARU (SIGN UP) -->
        <div v-else class="space-y-3.5">
          <form @submit.prevent="handleRegister" class="space-y-3.5">
            <div>
              <label class="block text-xs font-semibold text-slate-300 mb-1">Nama Lengkap</label>
              <input
                v-model="fullName"
                type="text"
                required
                placeholder="Contoh: Frans Alwan Purba"
                class="w-full rounded-xl border border-slate-800 bg-slate-950 px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none transition-colors"
              />
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-300 mb-1">Email</label>
              <input
                v-model="email"
                type="email"
                required
                placeholder="nama@kampus.ac.id atau email pribadi"
                class="w-full rounded-xl border border-slate-800 bg-slate-950 px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none transition-colors"
              />
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-300 mb-1">Password (Minimal 6 Karakter)</label>
              <input
                v-model="password"
                type="password"
                required
                placeholder="••••••••"
                class="w-full rounded-xl border border-slate-800 bg-slate-950 px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none transition-colors"
              />
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-300 mb-1">Konfirmasi Password</label>
              <input
                v-model="confirmPassword"
                type="password"
                required
                placeholder="••••••••"
                class="w-full rounded-xl border border-slate-800 bg-slate-950 px-3.5 py-2.5 text-xs text-white placeholder-slate-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 focus:outline-none transition-colors"
              />
            </div>

            <button
              type="submit"
              :disabled="loading"
              class="w-full mt-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-xs font-bold text-white shadow-md shadow-indigo-600/30 hover:bg-indigo-500 transition-all disabled:opacity-50 cursor-pointer"
            >
              {{ loading ? 'Mendaftarkan...' : 'Buat Akun Mahasiswa Baru' }}
            </button>
          </form>
        </div>

        <!-- Footer Help Link -->
        <div class="pt-2 text-center text-[11px] text-slate-500">
          <span>Tersinkronisasi otomatis dengan bot Telegram Second Brain via </span>
          <code class="text-indigo-400 font-mono">/connect [email]</code>
        </div>
      </div>
    </div>
  </div>
</template>
