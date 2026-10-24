<script setup lang="ts">
import { ref } from 'vue'

const isOpen = ref(false)

function openModal() {
  isOpen.value = true
}

function closeModal() {
  isOpen.value = false
}

defineExpose({
  openModal,
  closeModal,
})
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-950/70 backdrop-blur-xs">
    <div class="w-full max-w-3xl bg-slate-900 rounded-3xl shadow-2xl border border-slate-800 text-slate-100 overflow-hidden flex flex-col max-h-[90vh]">
      <!-- Header -->
      <div class="px-6 py-4 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="h-10 w-10 rounded-xl bg-purple-600/20 border border-purple-500/30 flex items-center justify-center text-xl">
            🛠️
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h2 class="text-sm sm:text-base font-bold text-white">Engineering Architecture &amp; Tech Specs</h2>
              <span class="rounded-full bg-indigo-500/20 px-2 py-0.5 text-[10px] font-bold text-indigo-300 border border-indigo-500/30">
                Production-Ready
              </span>
            </div>
            <p class="text-xs text-slate-400">Arsitektur Polyglot Berkinerja Tinggi: AI Agent + Concurrency Worker</p>
          </div>
        </div>
        <button
          @click="closeModal"
          class="h-8 w-8 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center justify-center transition-colors cursor-pointer"
        >
          ✕
        </button>
      </div>

      <!-- Content Body -->
      <div class="p-6 space-y-6 overflow-y-auto">
        <!-- 4 Core Pillars Grid -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
          <!-- 1. AI & RAG -->
          <div class="p-4 rounded-2xl bg-purple-950/30 border border-purple-500/30 space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-purple-300 flex items-center gap-1.5">
                <span>🧠</span> AI &amp; Agentic RAG
              </span>
              <span class="text-[10px] bg-purple-500/20 text-purple-200 px-2 py-0.5 rounded-full font-mono">Python 3.11</span>
            </div>
            <p class="text-xs text-slate-300 leading-relaxed">
              Google ADK + Gemini 1.5 dengan multi-step tool-calling. Dilengkapi <strong class="text-white">Hybrid Semantic Search (pgvector)</strong> menggunakan formula <strong class="text-purple-300">Reciprocal Rank Fusion (RRF)</strong> untuk menggabungkan BM25 dan Cosine Distance.
            </p>
          </div>

          <!-- 2. Go Telemetry -->
          <div class="p-4 rounded-2xl bg-sky-950/30 border border-sky-500/30 space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-sky-300 flex items-center gap-1.5">
                <span>🐹</span> High-Concurrency Telemetry
              </span>
              <span class="text-[10px] bg-sky-500/20 text-sky-200 px-2 py-0.5 rounded-full font-mono">Golang 1.22+</span>
            </div>
            <p class="text-xs text-slate-300 leading-relaxed">
              Daemon mandiri berbasis <strong class="text-white">Goroutines &amp; Channel Worker Pool</strong> dengan <strong class="text-sky-300">Exponential Backoff Retry</strong> untuk mengevaluasi jam malam, radar risiko burnout, dan bimbingan dospem secara non-blocking.
            </p>
          </div>

          <!-- 3. Database & Security -->
          <div class="p-4 rounded-2xl bg-emerald-950/30 border border-emerald-500/30 space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-emerald-300 flex items-center gap-1.5">
                <span>🔒</span> Database &amp; Multi-Tenancy
              </span>
              <span class="text-[10px] bg-emerald-500/20 text-emerald-200 px-2 py-0.5 rounded-full font-mono">PostgreSQL + RLS</span>
            </div>
            <p class="text-xs text-slate-300 leading-relaxed">
              Supabase PostgreSQL dengan <strong class="text-white">Row-Level Security (RLS)</strong> ketat per-user. Indeks <strong class="text-emerald-300">HNSW (Hierarchical Navigable Small World)</strong> pada vektor 768 dimensi untuk query sub-milidetik.
            </p>
          </div>

          <!-- 4. Quality Flywheel -->
          <div class="p-4 rounded-2xl bg-amber-950/30 border border-amber-500/30 space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-amber-300 flex items-center gap-1.5">
                <span>🧪</span> Quality Flywheel (Eval Suite)
              </span>
              <span class="text-[10px] bg-amber-500/20 text-amber-200 px-2 py-0.5 rounded-full font-mono">Automated CI</span>
            </div>
            <p class="text-xs text-slate-300 leading-relaxed">
              Test suite otomatis menguji <strong class="text-white">Akurasi Intent Classification &ge; 90%</strong> pada 12 skenario, ketepatan parsing waktu/deadline, dan latensi inferensi <strong class="text-amber-300">P95 &lt; 50ms</strong>.
            </p>
          </div>
        </div>

        <!-- Architecture Flow Diagram (ASCII / Box Model) -->
        <div class="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-3 font-mono text-[11px]">
          <span class="text-slate-400 font-bold uppercase tracking-wider block">Flow Arsitektur Sistem:</span>
          <div class="bg-slate-900/90 p-3 rounded-xl text-slate-300 leading-relaxed overflow-x-auto no-scrollbar">
[Client: Vue 3 PWA] ──► [Ctrl+K Quick Capture / Tanya AI RAG]
        │                     │
        ▼                     ▼
[Golang Telemetry Worker]  [Python FastAPI + Google ADK]
(Goroutine Worker Pool)    (Hybrid Search: BM25 + Vector)
        │                     │
        ▼                     ▼
  [Web Push / Alert]       [Supabase PostgreSQL + pgvector + RLS]
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="px-6 py-3.5 bg-slate-950/80 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
        <span>Kandidat: Frans Alwan Purba (M.Cs in AI Student, UGM)</span>
        <button
          @click="closeModal"
          class="rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white px-3.5 py-1.5 font-bold transition-colors cursor-pointer"
        >
          Mengerti
        </button>
      </div>
    </div>
  </div>
</template>

