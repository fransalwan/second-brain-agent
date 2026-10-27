<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../lib/supabase'
import { setRoleRecruiter, setRoleOwner, OWNER_PASSKEY, OWNER_EMAIL } from '../lib/authRole'
import PrivacyModal from '../components/PrivacyModal.vue'
import TechSpecsModal from '../components/TechSpecsModal.vue'

const router = useRouter()
const privacyModalRef = ref<InstanceType<typeof PrivacyModal> | null>(null)
const techSpecsModalRef = ref<InstanceType<typeof TechSpecsModal> | null>(null)

// Mode Akses: 'recruiter' (Akses Cepat Demo) vs 'owner' (Akses Pemilik Frans)
const portalMode = ref<'recruiter' | 'owner'>('recruiter')

// Form Pemilik
const ownerEmail = ref(OWNER_EMAIL)
const ownerKey = ref('')
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

function handleOpenPrivacy(tab: 'governance' | 'pii_redactor' | 'adrs' | 'export' = 'governance') {
  privacyModalRef.value?.openModal(tab)
}

// 1-Click Recruiter Instant Access
async function handleGuestDemo() {
  resetAlerts()
  loadingDemo.value = true
  try {
    setRoleRecruiter()
    await router.push({ name: 'home' })
  } catch {
    window.location.href = '/'
  } finally {
    loadingDemo.value = false
  }
}

function switchPortal(mode: 'recruiter' | 'owner') {
  portalMode.value = mode
  resetAlerts()
}

// Owner Login (Frans Alwan Purba)
async function handleOwnerLogin() {
  resetAlerts()
  if (!ownerKey.value) {
    errorMessage.value = 'Password atau Master Passkey Pemilik wajib diisi.'
    return
  }

  loading.value = true

  try {
    const inputKey = ownerKey.value.trim()
    const inputEmail = ownerEmail.value.trim().toLowerCase()

    // 1. Validasi via Master Passkey Riset (Zero-latency offline fallback)
    if (inputKey === OWNER_PASSKEY) {
      setRoleOwner()
      await router.push({ name: 'home' })
      return
    }

    // 2. Validasi via Supabase Auth jika ada kredensial terdaftar
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email: inputEmail,
        password: inputKey,
      })

      if (!error && data?.session) {
        setRoleOwner()
        await router.push({ name: 'home' })
        return
      }
    } catch {
      // Abaikan Supabase error, lanjutkan ke pengecekan passkey
    }

    errorMessage.value = 'Password atau Master Passkey Pemilik salah. Akses ditolak.'
  } catch {
    errorMessage.value = 'Terjadi kendala saat autentikasi. Silakan periksa kredensial Anda.'
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

        <!-- Scope & Audience Badge -->
        <div class="mt-7 p-3 rounded-2xl bg-amber-950/30 border border-amber-500/30 flex items-start gap-2.5 text-xs text-amber-200">
          <span class="text-base shrink-0">🛡️</span>
          <div>
            <strong class="font-bold text-amber-100">Closed Portfolio &amp; Private Research Environment:</strong>
            <p class="text-[11px] text-amber-200/90 mt-0.5 leading-relaxed">
              Platform ini dikhususkan secara eksklusif untuk <strong>Evaluasi Rekruter Teknis (Mode Demo)</strong> dan <strong>Riset Tesis Pemilik (Frans Alwan Purba)</strong>. Registrasi akun publik ditutup.
            </p>
          </div>
        </div>

        <!-- Hero Headline -->
        <div class="mt-7 space-y-3">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="inline-flex items-center gap-1.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 px-2.5 py-1 text-xs font-semibold text-indigo-300">
              <span>🚀 Production AI Architecture</span>
              <span class="text-indigo-400/50">|</span>
              <span class="text-purple-300 font-mono">Fase 1 s.d. 5 + UI/UX 3.0</span>
            </span>
            <span class="inline-flex items-center gap-1.5 rounded-lg bg-purple-500/10 border border-purple-500/20 px-2.5 py-1 text-xs font-semibold text-purple-300">
              <span>🏛️</span>
              <span>FMIPA UGM</span>
            </span>
          </div>

          <h1 class="text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight text-white leading-tight">
            Autonomous AI Engineering Platform &amp; <br class="hidden sm:inline" />
            <span class="bg-gradient-to-r from-indigo-400 via-purple-300 to-cyan-300 bg-clip-text text-transparent">
              Distributed Multi-Agent Architecture.
            </span>
          </h1>

          <p class="text-xs sm:text-sm text-slate-300 leading-relaxed max-w-2xl">
            Menghubungkan ekosistem tool terbuka (Anthropic Model Context Protocol SSE), Corrective RAG (CRAG) dengan pengelompokan hirarkis RAPTOR (GMM), Multimodal Document AI (Gemini 2.0 Flash VLM), Classical ML Anomaly Radar (<span class="text-cyan-300 font-mono font-semibold">&lt; 2ms</span>), evaluasi RAG Triad otomatis (81.8/100), serta riset tesis S2 Explainable AI terverifikasi.
          </p>
        </div>

        <!-- 5 Core AI Engineering Systems Grid -->
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

          <!-- Fase 5: AI Quality Flywheel -->
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
                  Evaluasi LLM-as-a-Judge otomatis terhadap 20 Golden Dataset uji akademik pada metrik RAG Triad: Context Recall 86.0%, Faithfulness 85.0%, dan OOD Refusal 100% via CI/CD gate.
                </p>
              </div>
            </div>
          </div>

          <!-- Tesis S2 & Explainable AI Research Engine (FMIPA UGM) -->
          <div class="sm:col-span-2 rounded-2xl border border-purple-500/30 bg-gradient-to-r from-purple-950/30 to-indigo-950/20 p-3.5 backdrop-blur-xs hover:border-purple-500/50 transition-all">
            <div class="flex items-start gap-3">
              <span class="text-lg p-2 rounded-xl bg-purple-500/20 text-purple-300 shrink-0">🔬</span>
              <div class="flex-1">
                <div class="flex items-center justify-between flex-wrap gap-2">
                  <div class="flex items-center gap-1.5">
                    <h2 class="text-xs font-bold text-purple-300">Riset Tesis S2: IDCS Explainable AI &amp; Uji Kausalitas</h2>
                    <span class="rounded bg-rose-500/30 text-rose-200 text-[9px] font-bold px-1.5 py-0.2 border border-rose-500/40">🔒 Area Privat Pemilik</span>
                  </div>
                  <span class="text-[10px] text-slate-400 font-medium">
                    Dospem: Afiahayati, Ph.D &amp; Prof. Sri Hartati
                  </span>
                </div>
                <p class="text-[11px] text-slate-300 mt-1 leading-relaxed">
                  Naskah riset aktif, log bimbingan dospem, dan token repositori privat dilindungi kontrol akses berbasis peran (RBAC). Hanya dapat diakses oleh pemilik.
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
        <span class="font-mono text-[11px]">System Status: Production v2.5 (Pure Portfolio · Zero Public Signup)</span>
        <span class="text-slate-400">Yogyakarta, Indonesia · Master of AI Candidate UGM</span>
      </div>
    </div>

    <!-- SISI KANAN: Dedicated Dual-Portal (Recruiter Demo vs Private Owner) -->
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

        <!-- Portal Role Selector Tabs -->
        <div class="space-y-1.5">
          <div class="flex items-center justify-between text-xs text-slate-400 mb-1">
            <span class="font-semibold text-slate-300 uppercase tracking-wider text-[11px]">Pilih Jalur Akses Masuk:</span>
          </div>

          <div class="flex items-center rounded-2xl bg-slate-950 p-1.5 text-xs font-semibold border border-slate-800 gap-1.5">
            <button
              type="button"
              @click="switchPortal('recruiter')"
              class="flex-1 min-h-[44px] flex items-center justify-center gap-1.5 py-2 px-3 rounded-xl transition-all cursor-pointer text-xs"
              :class="portalMode === 'recruiter' ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-md shadow-indigo-600/30 font-bold' : 'text-slate-400 hover:text-white hover:bg-slate-900'"
            >
              <span>👔</span>
              <span>Demo Rekruter</span>
            </button>
            <button
              type="button"
              @click="switchPortal('owner')"
              class="flex-1 min-h-[44px] flex items-center justify-center gap-1.5 py-2 px-3 rounded-xl transition-all cursor-pointer text-xs"
              :class="portalMode === 'owner' ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-md shadow-purple-600/30 font-bold' : 'text-slate-400 hover:text-white hover:bg-slate-900'"
            >
              <span>👑</span>
              <span>Pemilik (Frans)</span>
            </button>
          </div>
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

        <!-- ============================================== -->
        <!-- PORTAL 1: REKRUTER & TECH LEAD INSTANT ACCESS  -->
        <!-- ============================================== -->
        <div v-if="portalMode === 'recruiter'" class="space-y-4">
          <div class="p-4 sm:p-5 rounded-2xl bg-gradient-to-br from-indigo-950/90 via-purple-950/70 to-slate-900 border border-indigo-500/40 shadow-xl shadow-indigo-950/60 space-y-3">
            <div class="flex items-center justify-between">
              <span class="inline-flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-amber-300">
                <span class="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
                Akses Evaluasi Cepat
              </span>
              <span class="rounded bg-indigo-500/20 px-2 py-0.5 text-[10px] font-mono text-indigo-300 border border-indigo-500/30 font-bold">
                Zero Setup
              </span>
            </div>

            <p class="text-xs text-slate-300 leading-relaxed">
              Didesain khusus untuk <strong>Tech Lead, Engineering Manager, dan Recruiter</strong>. Masuk ke dashboard interaktif secara instan tanpa perlu registrasi atau kredensial.
            </p>

            <button
              type="button"
              @click="handleGuestDemo"
              :disabled="loadingDemo"
              class="w-full min-h-[50px] flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 via-purple-600 to-pink-600 px-4 py-3 text-xs sm:text-sm font-extrabold text-white shadow-lg shadow-purple-600/30 hover:from-indigo-400 hover:to-pink-500 hover:shadow-purple-600/50 transition-all cursor-pointer disabled:opacity-60"
            >
              <span v-if="!loadingDemo" class="text-base">🚀</span>
              <span v-else class="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin"></span>
              <span>{{ loadingDemo ? 'Mempersiapkan Lingkungan Demo...' : 'Masuk sebagai Rekruter (Instant Access) ➔' }}</span>
            </button>
            
            <!-- Recruiter Access Matrix -->
            <div class="space-y-2 pt-2 border-t border-slate-800/80 text-[11px]">
              <div class="flex items-start gap-1.5 text-emerald-300">
                <span class="font-bold">✓</span>
                <span><strong>Akses Penuh:</strong> Next-Gen CRAG, Gemini 2.0 VLM, Classical ML Radar (&lt;2ms), Quality Flywheel 81.8, dan Anthropic MCP SSE.</span>
              </div>
              <div class="flex items-start gap-1.5 text-amber-300">
                <span class="font-bold">🔒</span>
                <span><strong>Akses Terproteksi:</strong> Naskah Tesis S2 UGM, Notulensi Dosen Pembimbing, dan Catatan Riset Privat Pemilik dikunci demi privasi akademik.</span>
              </div>
            </div>
          </div>

          <div class="rounded-xl bg-slate-950 p-3 border border-slate-800/90 text-[11px] text-slate-400 space-y-1">
            <p class="font-semibold text-slate-300 flex items-center gap-1.5">
              <span>💡</span>
              <span>Tips untuk Evaluator:</span>
            </p>
            <p class="leading-relaxed">
              Setelah masuk, tekan <kbd class="rounded bg-slate-800 px-1 py-0.5 font-mono text-slate-300 border border-slate-700">Ctrl + K</kbd> untuk membuka Command Palette, atau klik pill <strong>✨ Demo (Tour 60s)</strong> di navbar atas untuk walkthrough terpandu.
            </p>
          </div>
        </div>

        <!-- ============================================== -->
        <!-- PORTAL 2: PEMILIK & PENELITI S2 (FRANS ALWAN) -->
        <!-- ============================================== -->
        <div v-else class="space-y-4">
          <div class="p-4 sm:p-5 rounded-2xl bg-gradient-to-br from-purple-950/90 via-slate-900 to-slate-950 border border-purple-500/40 shadow-xl shadow-purple-950/60 space-y-3">
            <div class="flex items-center justify-between">
              <span class="inline-flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-purple-300">
                <span>👑</span>
                Portal Privat Pemilik
              </span>
              <span class="rounded bg-purple-500/20 px-2 py-0.5 text-[10px] font-mono text-purple-300 border border-purple-500/30 font-bold">
                Full Clearance
              </span>
            </div>

            <p class="text-xs text-slate-300 leading-relaxed">
              Akses administratif penuh untuk <strong>Frans Alwan Purba</strong>: Mengelola naskah Tesis S2 FMIPA UGM (Bab 1–5), log bimbingan dospem, simulator permutasi kausal, serta ekspor LaTeX.
            </p>

            <form @submit.prevent="handleOwnerLogin" class="space-y-3 pt-1">
              <div>
                <label class="block text-xs font-semibold text-slate-300 mb-1">Email Pemilik</label>
                <input
                  v-model="ownerEmail"
                  type="email"
                  required
                  autocomplete="username"
                  class="w-full min-h-[44px] rounded-xl border border-slate-800 bg-slate-950 px-3.5 py-2 text-sm sm:text-xs text-white placeholder-slate-500 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 focus:outline-none transition-colors font-mono"
                />
              </div>

              <div>
                <div class="flex items-center justify-between mb-1">
                  <label class="block text-xs font-semibold text-slate-300">Password / Master Passkey</label>
                  <button
                    type="button"
                    @click="showPassword = !showPassword"
                    class="text-xs text-purple-400 hover:underline cursor-pointer"
                  >
                    {{ showPassword ? 'Sembunyikan' : 'Lihat' }}
                  </button>
                </div>
                <input
                  v-model="ownerKey"
                  :type="showPassword ? 'text' : 'password'"
                  required
                  autocomplete="current-password"
                  placeholder="Masukkan password atau passkey riset..."
                  class="w-full min-h-[44px] rounded-xl border border-slate-800 bg-slate-950 px-3.5 py-2 text-sm sm:text-xs text-white placeholder-slate-500 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 focus:outline-none transition-colors"
                />
              </div>

              <button
                type="submit"
                :disabled="loading"
                class="w-full min-h-[48px] mt-2 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 px-4 py-3 text-xs sm:text-sm font-extrabold text-white shadow-lg shadow-purple-600/30 hover:from-purple-500 hover:to-pink-500 transition-all disabled:opacity-50 cursor-pointer flex items-center justify-center gap-2"
              >
                <span v-if="loading" class="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin"></span>
                <span v-else>🔐</span>
                <span>{{ loading ? 'Memverifikasi Otoritas...' : 'Masuk sebagai Pemilik (Akses Penuh) ➔' }}</span>
              </button>
            </form>
          </div>

          <div class="rounded-xl bg-slate-950 p-3 border border-slate-800 text-[11px] text-slate-400 space-y-1">
            <p class="font-semibold text-purple-300 flex items-center gap-1.5">
              <span>🛡️</span>
              <span>Hak Akses Terbuka untuk Pemilik:</span>
            </p>
            <p class="leading-relaxed">
              Membuka modul <strong>Riset &amp; Tesis (IDCS XAI)</strong>, log konsultasi Bu Afiahayati Ph.D &amp; Prof. Sri Hartati, WhatsApp auto-drafting, serta fitur quick capture catatan &amp; habits pribadi.
            </p>
          </div>
        </div>

        <!-- Closed Portfolio Security Notice -->
        <div class="rounded-xl bg-slate-950/60 p-3 border border-slate-800/80 text-[11px] text-slate-400 text-center">
          <span>⚠️ Registrasi umum dinonaktifkan. Seluruh data dilindungi </span>
          <span class="text-indigo-400 font-semibold">PostgreSQL RLS &amp; OWASP Top 10 for LLMs</span>.
        </div>

        <!-- Footer AI Governance & Model Cards Modal Trigger -->
        <div class="pt-2 text-center text-[11px] text-slate-400 border-t border-slate-800/80">
          <button
            type="button"
            @click="handleOpenPrivacy('governance')"
            class="text-indigo-300 hover:text-indigo-200 underline font-medium cursor-pointer"
          >
            🛡️ Pusat Tata Kelola AI, Keamanan &amp; Model Cards (OWASP LLM Defense) ↗
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
