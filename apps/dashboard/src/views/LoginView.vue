<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../lib/supabase'
import PrivacyModal from '../components/PrivacyModal.vue'
import TechSpecsModal from '../components/TechSpecsModal.vue'

const router = useRouter()
const privacyModalRef = ref<InstanceType<typeof PrivacyModal> | null>(null)
const techSpecsModalRef = ref<InstanceType<typeof TechSpecsModal> | null>(null)

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

function handleOpenTechSpecs() {
  techSpecsModalRef.value?.openModal()
}

function handleOpenPrivacy(tab: 'policy' | 'export' | 'delete' = 'policy') {
  privacyModalRef.value?.openModal(tab)
}

async function handleGuestDemo() {
  resetAlerts()
  loadingDemo.value = true
  try {
    localStorage.setItem('secondbrain_demo_mode', 'true')
    await router.push({ name: 'home' })
  } catch {
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
  } catch {
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
  } catch {
    errorMessage.value = 'Gagal melakukan pendaftaran akun. Silakan coba lagi.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-slate-950 text-slate-100 flex flex-col lg:flex-row relative selection:bg-purple-500 selection:text-white">
    <!-- Ambient Radial Glows -->
    <div class="fixed top-0 left-1/4 w-[500px] h-[500px] bg-purple-600/10 rounded-full blur-[140px] pointer-events-none"></div>
    <div class="fixed bottom-0 right-1/4 w-[500px] h-[500px] bg-indigo-600/10 rounded-full blur-[140px] pointer-events-none"></div>

    <!-- SISI KIRI: Architectural Authority & AI Engineering Showcase -->
    <div class="order-2 lg:order-1 flex-1 p-6 sm:p-10 lg:p-12 xl:p-14 flex flex-col justify-between bg-gradient-to-br from-slate-950 via-slate-900/90 to-indigo-950/70 border-t lg:border-t-0 lg:border-r border-slate-800/80 relative z-10">
      
      <!-- Top Brand Header -->
      <div>
        <div class="flex items-center justify-between flex-wrap gap-3">
          <div class="flex items-center gap-3">
            <div class="h-11 w-11 rounded-2xl bg-gradient-to-tr from-indigo-500 via-purple-600 to-pink-500 flex items-center justify-center text-white text-2xl font-bold shadow-lg shadow-purple-500/25 shrink-0">
              🧠
            </div>
            <div>
              <div class="flex items-center gap-2">
                <span class="text-xl font-black tracking-tight text-white">Second Brain</span>
                <span class="rounded-full bg-purple-500/20 px-2.5 py-0.5 text-[11px] font-bold text-purple-300 border border-purple-500/30">
                  AI Agent Platform
                </span>
              </div>
              <p class="text-xs text-slate-400 font-medium">
                Engineered by <strong class="text-slate-200">Frans Alwan Purba</strong> · M.Cs. in AI Candidate, Universitas Gadjah Mada
              </p>
            </div>
          </div>

          <!-- Stack Live Status Pill -->
          <div class="inline-flex items-center gap-2 rounded-full bg-slate-900/90 border border-slate-800 px-3 py-1 text-[11px] text-slate-300 shadow-2xs">
            <span class="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>Polyglot Stack Online</span>
            <span class="text-slate-500">•</span>
            <span class="font-mono text-purple-300 font-bold">FastAPI + Go</span>
          </div>
        </div>

        <!-- Hero Headline -->
        <div class="mt-8 lg:mt-10 space-y-3">
          <div class="inline-flex items-center gap-1.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 px-2.5 py-1 text-xs font-semibold text-indigo-300">
            <span>🚀 Production AI Architecture</span>
            <span class="text-indigo-400/50">|</span>
            <span class="text-purple-300 font-mono">Fase 1 s.d. 5 Completed</span>
          </div>

          <h1 class="text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight text-white leading-tight">
            Autonomous AI Engineering Platform &amp; <br class="hidden sm:inline" />
            <span class="bg-gradient-to-r from-indigo-400 via-purple-300 to-cyan-300 bg-clip-text text-transparent">
              Distributed Multi-Agent Architecture.
            </span>
          </h1>

          <p class="text-xs sm:text-sm text-slate-300 leading-relaxed max-w-2xl">
            Sistem orkestrasi agen AI produksi berkinerja tinggi: Menghubungkan ekosistem tool terbuka (Anthropic Model Context Protocol SSE), Corrective RAG (CRAG) dengan pengelompokan hirarkis RAPTOR (GMM), Multimodal Document AI (Gemini 2.0 Flash VLM), Classical ML Anomaly Radar (<span class="text-cyan-300 font-mono font-semibold">&lt; 2ms</span>), dan automated evaluation flywheel.
          </p>
        </div>

        <!-- 5 Core AI Engineering Systems (Fase 1 - 5) Grid -->
        <div class="mt-7 grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-3xl">
          <!-- Fase 1: Anthropic MCP -->
          <div class="rounded-2xl border border-indigo-500/20 bg-indigo-950/20 p-3.5 backdrop-blur-xs hover:border-indigo-500/40 hover:bg-indigo-950/30 transition-all">
            <div class="flex items-start gap-3">
              <span class="text-lg p-2 rounded-xl bg-indigo-500/20 text-indigo-300 shrink-0">🔌</span>
              <div>
                <div class="flex items-center gap-1.5">
                  <h2 class="text-xs font-bold text-indigo-300">Anthropic Model Context Protocol (MCP)</h2>
                  <span class="rounded bg-indigo-500/30 text-indigo-200 text-[9px] font-bold px-1 py-0.2">FASE 1</span>
                </div>
                <p class="text-[11px] text-slate-400 mt-1 leading-relaxed">
                  Endpoint SSE <code class="text-indigo-300 font-mono">/mcp/sse</code> &amp; 8 skema tool standar JSON-RPC 2.0 untuk Claude Desktop dan Cursor IDE.
                </p>
              </div>
            </div>
          </div>

          <!-- Fase 2: Next-Gen RAG & RAPTOR -->
          <div class="rounded-2xl border border-purple-500/20 bg-purple-950/20 p-3.5 backdrop-blur-xs hover:border-purple-500/40 hover:bg-purple-950/30 transition-all">
            <div class="flex items-start gap-3">
              <span class="text-lg p-2 rounded-xl bg-purple-500/20 text-purple-300 shrink-0">🧠</span>
              <div>
                <div class="flex items-center gap-1.5">
                  <h2 class="text-xs font-bold text-purple-300">Next-Gen CRAG &amp; RAPTOR Tree</h2>
                  <span class="rounded bg-purple-500/30 text-purple-200 text-[9px] font-bold px-1 py-0.2">FASE 2</span>
                </div>
                <p class="text-[11px] text-slate-400 mt-1 leading-relaxed">
                  GMM Hierarchical Clustering, evaluasi mandiri (CRAG), ekspansi kueri hipotesis (HyDE), dan Cross-Encoder reranking di pgvector 768-D.
                </p>
              </div>
            </div>
          </div>

          <!-- Fase 3: Multimodal Document VLM -->
          <div class="rounded-2xl border border-blue-500/20 bg-blue-950/20 p-3.5 backdrop-blur-xs hover:border-blue-500/40 hover:bg-blue-950/30 transition-all">
            <div class="flex items-start gap-3">
              <span class="text-lg p-2 rounded-xl bg-blue-500/20 text-blue-300 shrink-0">📸</span>
              <div>
                <div class="flex items-center gap-1.5">
                  <h2 class="text-xs font-bold text-blue-300">Multimodal Document AI (VLM)</h2>
                  <span class="rounded bg-blue-500/30 text-blue-200 text-[9px] font-bold px-1 py-0.2">FASE 3</span>
                </div>
                <p class="text-[11px] text-slate-400 mt-1 leading-relaxed">
                  Gemini 2.0 Flash VLM: Ekstraksi kurva konvergensi loss CatBoost (Epoch 350), OCR catatan tulisan tangan, dan auto-vectorization.
                </p>
              </div>
            </div>
          </div>

          <!-- Fase 4: Classical ML Hybrid Radar -->
          <div class="rounded-2xl border border-cyan-500/20 bg-cyan-950/20 p-3.5 backdrop-blur-xs hover:border-cyan-500/40 hover:bg-cyan-950/30 transition-all">
            <div class="flex items-start gap-3">
              <span class="text-lg p-2 rounded-xl bg-cyan-500/20 text-cyan-300 shrink-0">📊</span>
              <div>
                <div class="flex items-center gap-1.5">
                  <h2 class="text-xs font-bold text-cyan-300">Classical ML Radar (&lt; 2ms)</h2>
                  <span class="rounded bg-cyan-500/30 text-cyan-200 text-[9px] font-bold px-1 py-0.2">FASE 4</span>
                </div>
                <p class="text-[11px] text-slate-400 mt-1 leading-relaxed">
                  Isolation Forest deterministik 0 token cost pada 5-D sirkadian + pemicu intervensi empatik otonom LLM bersyarat jika skor &lt; -0.15.
                </p>
              </div>
            </div>
          </div>

          <!-- Fase 5: AI Quality Flywheel (Span 2 cols on tablet+) -->
          <div class="sm:col-span-2 rounded-2xl border border-emerald-500/20 bg-emerald-950/20 p-3.5 backdrop-blur-xs hover:border-emerald-500/40 hover:bg-emerald-950/30 transition-all">
            <div class="flex items-start gap-3">
              <span class="text-lg p-2 rounded-xl bg-emerald-500/20 text-emerald-300 shrink-0">🏆</span>
              <div class="flex-1">
                <div class="flex items-center justify-between flex-wrap gap-2">
                  <div class="flex items-center gap-1.5">
                    <h2 class="text-xs font-bold text-emerald-300">AI Quality Flywheel &amp; Production Evals</h2>
                    <span class="rounded bg-emerald-500/30 text-emerald-200 text-[9px] font-bold px-1 py-0.2">FASE 5</span>
                  </div>
                  <span class="rounded-full bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 text-[10px] font-mono font-bold px-2 py-0.2">
                    Composite Score: 81.8 / 100
                  </span>
                </div>
                <p class="text-[11px] text-slate-400 mt-1 leading-relaxed">
                  Evaluasi LLM-as-a-Judge otomatis terhadap 20 Golden Dataset uji akademik pada metrik RAG Triad: Context Recall 86.0%, Faithfulness 85.0%, dan OOD Refusal 100% via GitHub Actions CI/CD gate.
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Quick Architecture & Tech Specs Button -->
        <div class="mt-6 flex flex-wrap items-center gap-3">
          <button
            type="button"
            @click="handleOpenTechSpecs"
            class="inline-flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-900/90 px-3.5 py-2 text-xs font-bold text-slate-200 hover:bg-slate-800 hover:text-white hover:border-slate-600 transition-all cursor-pointer shadow-xs"
          >
            <span>🛠️</span>
            <span>Lihat Diagram Arsitektur &amp; Tech Specs</span>
          </button>

          <a
            href="https://github.com/fransalwan/second-brain-agent"
            target="_blank"
            class="inline-flex items-center gap-1.5 rounded-xl border border-slate-800 bg-slate-950 px-3.5 py-2 text-xs font-semibold text-slate-400 hover:text-slate-200 hover:bg-slate-900 transition-all shadow-xs"
          >
            <span>📦</span>
            <span>GitHub Repository</span>
          </a>
        </div>
      </div>

      <!-- Footer Metadata -->
      <div class="mt-8 pt-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 text-xs text-slate-500 border-t border-slate-800/80">
        <span class="font-mono text-[11px]">System Status: Production v2.5 (117/117 Tests Passed)</span>
        <span class="text-slate-400">Yogyakarta, Indonesia · Ready for Technical Interview</span>
      </div>
    </div>

    <!-- SISI KANAN: Auth Card & Recruiter Instant Access -->
    <div class="order-1 lg:order-2 w-full lg:w-[480px] xl:w-[520px] flex items-center justify-center p-4 sm:p-8 lg:p-10 bg-slate-950/90 backdrop-blur-xl border-b lg:border-b-0 lg:border-l border-slate-800/80 relative z-20">
      <div class="w-full max-w-md space-y-5 rounded-3xl border border-slate-800/90 bg-slate-900/95 p-6 sm:p-8 shadow-2xl shadow-indigo-950/60">
        
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
            <p class="text-[11px] text-slate-400">Autonomous AI Engineering Platform · Frans Alwan Purba</p>
          </div>
        </div>

        <!-- 1-Click Recruiter Demo Button (PROMINENT & HIGHEST VALUE) -->
        <div class="p-4 sm:p-5 rounded-2xl bg-gradient-to-br from-indigo-950/90 via-purple-950/70 to-slate-900 border border-indigo-500/40 shadow-xl shadow-indigo-950/60 space-y-3">
          <div class="flex items-center justify-between">
            <span class="inline-flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-amber-300">
              <span class="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
              Akses Cepat Recruiter &amp; Reviewer
            </span>
            <span class="rounded bg-indigo-500/20 px-2 py-0.5 text-[10px] font-mono text-indigo-300 border border-indigo-500/30 font-bold">
              Instant Access
            </span>
          </div>

          <button
            type="button"
            @click="handleGuestDemo"
            :disabled="loadingDemo"
            class="w-full min-h-[48px] flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 via-purple-600 to-pink-600 px-4 py-3 text-xs sm:text-sm font-extrabold text-white shadow-lg shadow-purple-600/30 hover:from-indigo-400 hover:to-pink-500 hover:shadow-purple-600/50 transition-all cursor-pointer disabled:opacity-60"
          >
            <span v-if="!loadingDemo" class="text-sm">⚡</span>
            <span v-else class="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin"></span>
            <span>{{ loadingDemo ? 'Mempersiapkan Lingkungan Demo...' : 'Masuk Mode Demo Instan (1-Click) ➔' }}</span>
          </button>
          
          <!-- Key Demo Features Chips -->
          <div class="grid grid-cols-2 gap-1.5 pt-1 text-[10px] text-slate-300">
            <div class="flex items-center gap-1 rounded-lg bg-slate-900/80 px-2 py-1 border border-slate-800">
              <span class="text-emerald-400 font-bold">✓</span>
              <span>Tanpa login / signup</span>
            </div>
            <div class="flex items-center gap-1 rounded-lg bg-slate-900/80 px-2 py-1 border border-slate-800">
              <span class="text-emerald-400 font-bold">✓</span>
              <span>20 Golden Dataset</span>
            </div>
            <div class="flex items-center gap-1 rounded-lg bg-slate-900/80 px-2 py-1 border border-slate-800">
              <span class="text-emerald-400 font-bold">✓</span>
              <span>Next-Gen CRAG Reranker</span>
            </div>
            <div class="flex items-center gap-1 rounded-lg bg-slate-900/80 px-2 py-1 border border-slate-800">
              <span class="text-emerald-400 font-bold">✓</span>
              <span>Tour Interaktif 60s</span>
            </div>
          </div>
        </div>

        <!-- Divider -->
        <div class="relative flex items-center justify-center">
          <div class="border-t border-slate-800 w-full"></div>
          <span class="bg-slate-900 px-3 text-[11px] font-medium text-slate-500 uppercase tracking-wider shrink-0">
            atau masuk dengan akun pengembang
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
                placeholder="nama@email.com atau email institusi"
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
              <span>{{ loading ? 'Memverifikasi...' : (loginMethod === 'password' ? 'Masuk ke Dashboard ➔' : 'Kirim Tautan Magic Link ➔') }}</span>
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
              <span>{{ loading ? 'Mendaftarkan Akun...' : 'Buat Akun Baru ➔' }}</span>
            </button>
          </form>
        </div>

        <!-- Footer Trust & Privacy Link -->
        <div class="pt-2 text-center text-[11px] text-slate-400 space-y-1 border-t border-slate-800/80">
          <p>
            <span>Data dilindungi secara terisolasi via </span>
            <span class="text-indigo-400 font-semibold">PostgreSQL Row-Level Security</span>
          </p>
          <button
            type="button"
            @click="handleOpenPrivacy('policy')"
            class="text-indigo-300 hover:text-indigo-200 underline font-medium cursor-pointer"
          >
            🛡️ Kedaulatan Data &amp; Privasi (Zero Trackers / Zero Ads) ↗
          </button>
        </div>
      </div>
    </div>

    <!-- Privacy & Data Sovereignty Center Modal -->
    <PrivacyModal ref="privacyModalRef" />

    <!-- Tech Specs & Architecture Inspector Modal -->
    <TechSpecsModal ref="techSpecsModalRef" />
  </div>
</template>
