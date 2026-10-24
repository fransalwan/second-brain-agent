<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  (e: 'navigate-tab', tab: 'overview' | 'health' | 'coursework' | 'research' | 'agentops'): void
  (e: 'open-rag', query?: string): void
  (e: 'open-tech-specs'): void
}>()

const isOpen = ref(false)
const currentStep = ref(1)
const totalSteps = 4

function openTour() {
  currentStep.value = 1
  isOpen.value = true
}

function closeTour() {
  isOpen.value = false
}

function nextStep() {
  if (currentStep.value < totalSteps) {
    currentStep.value++
  } else {
    closeTour()
  }
}

function prevStep() {
  if (currentStep.value > 1) {
    currentStep.value--
  }
}

function goToStep(step: number) {
  currentStep.value = step
}

defineExpose({
  openTour,
  closeTour,
})
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4">
    <!-- Backdrop -->
    <div class="fixed inset-0 bg-slate-950/70 backdrop-blur-md transition-opacity" @click="closeTour"></div>

    <!-- Tour Dialog Card -->
    <div class="relative w-full max-w-xl rounded-3xl border border-slate-200 bg-white p-6 sm:p-7 shadow-2xl space-y-5 animate-in fade-in zoom-in-95 duration-200">
      <!-- Top Step Indicator Strip -->
      <div class="flex items-center justify-between pb-3 border-b border-slate-100">
        <div class="flex items-center gap-2">
          <span class="flex h-7 w-7 items-center justify-center rounded-xl bg-indigo-600 text-white text-xs font-bold">
            🚀
          </span>
          <div>
            <h3 class="text-xs font-bold uppercase tracking-wider text-slate-800">
              Recruiter &amp; Tech Lead Tour (60 Detik)
            </h3>
            <span class="text-[11px] text-slate-500">Langkah {{ currentStep }} dari {{ totalSteps }}</span>
          </div>
        </div>

        <div class="flex items-center gap-1.5">
          <!-- Step Dots -->
          <div class="flex gap-1 mr-2">
            <button
              v-for="s in totalSteps"
              :key="s"
              type="button"
              @click="goToStep(s)"
              class="h-1.5 rounded-full transition-all cursor-pointer"
              :class="s === currentStep ? 'w-6 bg-indigo-600' : 'w-2 bg-slate-200 hover:bg-slate-300'"
            ></button>
          </div>

          <button
            type="button"
            @click="closeTour"
            class="text-slate-400 hover:text-slate-700 text-sm font-bold p-1 cursor-pointer"
          >
            ✕
          </button>
        </div>
      </div>

      <!-- STEP 1: Polyglot Distributed Architecture -->
      <div v-if="currentStep === 1" class="space-y-4">
        <div class="flex items-center gap-3">
          <div class="h-12 w-12 rounded-2xl bg-cyan-50 border border-cyan-200 text-cyan-800 flex items-center justify-center text-2xl font-bold shrink-0">
            ⚡
          </div>
          <div>
            <h4 class="text-base font-bold text-slate-900">1. Arsitektur Polyglot (Go + Python)</h4>
            <p class="text-xs text-slate-500">Menggabungkan konkurensi tinggi Golang dengan kepintaran AI Python.</p>
          </div>
        </div>

        <div class="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2 text-xs text-slate-700 leading-relaxed">
          <p>
            • <strong>Golang Worker Engine (:8085):</strong> Worker pool mandiri dengan Goroutines untuk mengevaluasi peringatan jam malam, deteksi sleep debt 7 hari, dan monitoring SLA bimbingan tesis (>14 hari) secara non-blocking.
          </p>
          <p>
            • <strong>FastAPI Backend (:8000):</strong> Mengelola orkestrasi model AI Google Gemini, webhook GitHub, dan perutean domain akademik.
          </p>
        </div>

        <div class="flex items-center justify-between pt-1">
          <button
            type="button"
            @click="emit('navigate-tab', 'agentops'); closeTour();"
            class="rounded-xl border border-cyan-300 bg-cyan-50 px-3.5 py-2 text-xs font-bold text-cyan-900 hover:bg-cyan-100 transition-colors cursor-pointer"
          >
            Buka Tab Agent Ops ↗
          </button>
          <button
            type="button"
            @click="nextStep"
            class="rounded-xl bg-slate-900 px-4 py-2 text-xs font-bold text-white hover:bg-black transition-colors cursor-pointer shadow-xs"
          >
            Lanjut: Hybrid RAG ➔
          </button>
        </div>
      </div>

      <!-- STEP 2: Hybrid Vector RAG (pgvector 768-D) -->
      <div v-else-if="currentStep === 2" class="space-y-4">
        <div class="flex items-center gap-3">
          <div class="h-12 w-12 rounded-2xl bg-purple-50 border border-purple-200 text-purple-800 flex items-center justify-center text-2xl font-bold shrink-0">
            🧠
          </div>
          <div>
            <h4 class="text-base font-bold text-slate-900">2. Hybrid Vector RAG (pgvector 768-D)</h4>
            <p class="text-xs text-slate-500">Pencarian semantik catatan riset bebas halusinasi berbasis bukti empiris.</p>
          </div>
        </div>

        <div class="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2 text-xs text-slate-700 leading-relaxed">
          <p>
            • <strong>PostgreSQL + pgvector:</strong> Indeks <em>Hierarchical Navigable Small World (HNSW)</em> dengan representasi vektor 768 dimensi untuk latensi pencarian kosinus &lt; 15ms.
          </p>
          <p>
            • <strong>Reciprocal Rank Fusion (RRF):</strong> Formula fusi pencarian eksak kata kunci dan kemiripan semantik untuk presisi sitasi tertinggi.
          </p>
        </div>

        <div class="flex items-center justify-between pt-1">
          <button
            type="button"
            @click="emit('open-rag', 'apa itu Reciprocal Rank Fusion'); closeTour();"
            class="rounded-xl border border-purple-300 bg-purple-50 px-3.5 py-2 text-xs font-bold text-purple-900 hover:bg-purple-100 transition-colors cursor-pointer"
          >
            Coba Tanya AI (RAG) ↗
          </button>
          <div class="flex gap-2">
            <button
              type="button"
              @click="prevStep"
              class="rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50 cursor-pointer"
            >
              Kembali
            </button>
            <button
              type="button"
              @click="nextStep"
              class="rounded-xl bg-slate-900 px-4 py-2 text-xs font-bold text-white hover:bg-black transition-colors cursor-pointer shadow-xs"
            >
              Lanjut: Git Pipeline ➔
            </button>
          </div>
        </div>
      </div>

      <!-- STEP 3: Academic Git Pipeline & LaTeX Engine -->
      <div v-else-if="currentStep === 3" class="space-y-4">
        <div class="flex items-center gap-3">
          <div class="h-12 w-12 rounded-2xl bg-indigo-50 border border-indigo-200 text-indigo-800 flex items-center justify-center text-2xl font-bold shrink-0">
            🔬
          </div>
          <div>
            <h4 class="text-base font-bold text-slate-900">3. Git Pipeline &amp; LaTeX Exporter</h4>
            <p class="text-xs text-slate-500">Integrasi dua arah dengan repositori skripsi dan tugas kuliah.</p>
          </div>
        </div>

        <div class="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2 text-xs text-slate-700 leading-relaxed">
          <p>
            • <strong>3 Repositori Terintegrasi:</strong> <code>materi-kuliah</code> (auto-done task), <code>thesis-manuscripts</code> (Bab 1–5 &amp; bimbingan), dan <code>thesis-experiments</code> (metrik model AI).
          </p>
          <p>
            • <strong>Generator Tabel LaTeX IEEE 1-Klik:</strong> Ekspor metrik akurasi, F1, dan loss langsung ke format tabel Overleaf untuk Bab 4 naskah skripsi.
          </p>
        </div>

        <div class="flex items-center justify-between pt-1">
          <button
            type="button"
            @click="emit('navigate-tab', 'research'); closeTour();"
            class="rounded-xl border border-indigo-300 bg-indigo-50 px-3.5 py-2 text-xs font-bold text-indigo-900 hover:bg-indigo-100 transition-colors cursor-pointer"
          >
            Buka Tab Riset ↗
          </button>
          <div class="flex gap-2">
            <button
              type="button"
              @click="prevStep"
              class="rounded-xl border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50 cursor-pointer"
            >
              Kembali
            </button>
            <button
              type="button"
              @click="nextStep"
              class="rounded-xl bg-slate-900 px-4 py-2 text-xs font-bold text-white hover:bg-black transition-colors cursor-pointer shadow-xs"
            >
              Lanjut: Kontak Frans ➔
            </button>
          </div>
        </div>
      </div>

      <!-- STEP 4: Frans Alwan Purba Profile & Contact -->
      <div v-else-if="currentStep === 4" class="space-y-4">
        <div class="flex items-center gap-3">
          <div class="h-12 w-12 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 flex items-center justify-center text-2xl font-bold shrink-0">
            👨‍💻
          </div>
          <div>
            <h4 class="text-base font-bold text-slate-900">Frans Alwan Purba</h4>
            <p class="text-xs text-slate-500">Software Engineer (Golang &amp; Vue.js) • Magister Ilmu Komputer UGM (AI)</p>
          </div>
        </div>

        <div class="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2 text-xs text-slate-700 leading-relaxed">
          <p>
            Memiliki pengalaman 1.5+ tahun dalam rekayasa backend performa tinggi (Golang, PostgreSQL, Docker) serta modern frontend (Vue 3, TypeScript, Pinia, Tailwind CSS).
          </p>
          <div class="pt-2 flex flex-wrap gap-1.5 font-medium">
            <span class="rounded bg-slate-200/80 px-2 py-0.5 text-[10px] text-slate-800">Golang</span>
            <span class="rounded bg-slate-200/80 px-2 py-0.5 text-[10px] text-slate-800">Python</span>
            <span class="rounded bg-slate-200/80 px-2 py-0.5 text-[10px] text-slate-800">Vue 3 / TypeScript</span>
            <span class="rounded bg-slate-200/80 px-2 py-0.5 text-[10px] text-slate-800">PostgreSQL / pgvector</span>
            <span class="rounded bg-slate-200/80 px-2 py-0.5 text-[10px] text-slate-800">Docker</span>
          </div>
        </div>

        <div class="flex items-center justify-between pt-1">
          <div class="flex gap-2">
            <a
              href="mailto:fransalwan55@gmail.com"
              class="inline-flex items-center gap-1 rounded-xl bg-slate-900 px-3 py-2 text-xs font-bold text-white hover:bg-black transition-colors shadow-2xs"
            >
              ✉️ Email
            </a>
            <a
              href="https://github.com/fransalwan/second-brain-agent"
              target="_blank"
              class="inline-flex items-center gap-1 rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-800 hover:bg-slate-50 transition-colors shadow-2xs"
            >
              📦 GitHub
            </a>
          </div>

          <button
            type="button"
            @click="closeTour"
            class="rounded-xl bg-emerald-600 px-4 py-2 text-xs font-bold text-white hover:bg-emerald-700 transition-colors cursor-pointer shadow-xs"
          >
            Selesai Tour ✨
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

