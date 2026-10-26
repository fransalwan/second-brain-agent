<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  (e: 'navigate-tab', tab: string): void
  (e: 'open-rag', query?: string): void
  (e: 'open-tech-specs'): void
}>()

const isOpen = ref(false)
const currentStep = ref(1)
const totalSteps = 5

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
              AI Engineer Portfolio Tour (60 Detik)
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

      <!-- STEP 1: Anthropic MCP Standard & Polyglot Go Engine -->
      <div v-if="currentStep === 1" class="space-y-4">
        <div class="flex items-center gap-3">
          <div class="h-12 w-12 rounded-2xl bg-indigo-50 border border-indigo-200 text-indigo-800 flex items-center justify-center text-2xl font-bold shrink-0">
            🔌
          </div>
          <div>
            <h4 class="text-base font-bold text-slate-900">1. Anthropic Model Context Protocol (MCP)</h4>
            <p class="text-xs text-slate-500">Standar industri ekosistem tool AI terbuka &amp; konkurensi Golang.</p>
          </div>
        </div>

        <div class="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2 text-xs text-slate-700 leading-relaxed">
          <p>
            • <strong>MCP Server SSE Endpoint (<code>/mcp/sse</code>):</strong> Mengekspos 8 tool schemas berstandar industri sehingga Claude Desktop dan IDE Cursor dapat langsung memanggil kapabilitas Second Brain kita via JSON-RPC 2.0.
          </p>
          <p>
            • <strong>Go Concurrency Telemetry (:8085):</strong> Worker pool mandiri dengan Goroutines untuk komputasi sirkadian deterministik &lt; 2ms tanpa membebani Python runner.
          </p>
        </div>

        <div class="flex items-center justify-between pt-1">
          <button
            type="button"
            @click="emit('navigate-tab', 'agentops'); closeTour();"
            class="rounded-xl border border-indigo-300 bg-indigo-50 px-3.5 py-2 text-xs font-bold text-indigo-900 hover:bg-indigo-100 transition-colors cursor-pointer"
          >
            Buka Tab MCP &amp; Telemetry ↗
          </button>
          <button
            type="button"
            @click="nextStep"
            class="rounded-xl bg-slate-900 px-4 py-2 text-xs font-bold text-white hover:bg-black transition-colors cursor-pointer shadow-xs"
          >
            Lanjut: Next-Gen RAG ➔
          </button>
        </div>
      </div>

      <!-- STEP 2: Next-Gen RAG (CRAG + RAPTOR Tree) -->
      <div v-else-if="currentStep === 2" class="space-y-4">
        <div class="flex items-center gap-3">
          <div class="h-12 w-12 rounded-2xl bg-purple-50 border border-purple-200 text-purple-800 flex items-center justify-center text-2xl font-bold shrink-0">
            🧠
          </div>
          <div>
            <h4 class="text-base font-bold text-slate-900">2. Next-Gen RAG &amp; RAPTOR Tree</h4>
            <p class="text-xs text-slate-500">Corrective RAG, GMM Hierarchical Clustering, &amp; Cross-Encoder.</p>
          </div>
        </div>

        <div class="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2 text-xs text-slate-700 leading-relaxed">
          <p>
            • <strong>RAPTOR Hierarchical Summaries:</strong> Dokumen dikelompokkan dengan Gaussian Mixture Models (GMM) dan dirangkum secara rekursif menjadi pohon pengetahuan tingkat tinggi.
          </p>
          <p>
            • <strong>Self-Correction (CRAG) &amp; HyDE:</strong> Jika confidence tinggi (>0.75) langsung diteruskan; jika ambigu (0.4-0.75) memicu ekspansi kueri hipotesis (HyDE); jika &lt;0.4 menolak halusinasi (OOD Refusal 100%).
          </p>
        </div>

        <div class="flex items-center justify-between pt-1">
          <button
            type="button"
            @click="emit('navigate-tab', 'rag'); closeTour();"
            class="rounded-xl border border-purple-300 bg-purple-50 px-3.5 py-2 text-xs font-bold text-purple-900 hover:bg-purple-100 transition-colors cursor-pointer"
          >
            Uji Coba Tab Next-Gen RAG ↗
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
              Lanjut: VLM &amp; ML Radar ➔
            </button>
          </div>
        </div>
      </div>

      <!-- STEP 3: Multimodal VLM & Classical ML Radar -->
      <div v-else-if="currentStep === 3" class="space-y-4">
        <div class="flex items-center gap-3">
          <div class="h-12 w-12 rounded-2xl bg-blue-50 border border-blue-200 text-blue-800 flex items-center justify-center text-2xl font-bold shrink-0">
            📸
          </div>
          <div>
            <h4 class="text-base font-bold text-slate-900">3. Multimodal VLM &amp; Classical ML Hybrid</h4>
            <p class="text-xs text-slate-500">Gemini 2.0 Flash VLM dipadukan dengan Isolation Forest &lt; 2ms.</p>
          </div>
        </div>

        <div class="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2 text-xs text-slate-700 leading-relaxed">
          <p>
            • <strong>Multimodal Document AI:</strong> Mengekstrak kurva loss CatBoost, catatan kuliah tulisan tangan, dan diagram arsitektur menjadi JSON terstruktur dan otomatis diindeks ke pgvector 768-D.
          </p>
          <p>
            • <strong>Classical ML Anomaly Radar:</strong> Menghitung anomali burnout secara instan (&lt; 2ms, zero token cost) dan hanya memicu intervensi empatik otonom LLM ketika skor &lt; -0.15.
          </p>
        </div>

        <div class="flex items-center justify-between pt-1">
          <button
            type="button"
            @click="emit('navigate-tab', 'mlradar'); closeTour();"
            class="rounded-xl border border-blue-300 bg-blue-50 px-3.5 py-2 text-xs font-bold text-blue-900 hover:bg-blue-100 transition-colors cursor-pointer"
          >
            Buka Tab ML Radar ↗
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
              Lanjut: Evals &amp; CI/CD ➔
            </button>
          </div>
        </div>
      </div>

      <!-- STEP 4: AI Quality Flywheel & Production Evals -->
      <div v-else-if="currentStep === 4" class="space-y-4">
        <div class="flex items-center gap-3">
          <div class="h-12 w-12 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-800 flex items-center justify-center text-2xl font-bold shrink-0">
            🏆
          </div>
          <div>
            <h4 class="text-base font-bold text-slate-900">4. AI Quality Flywheel &amp; LLM Judge</h4>
            <p class="text-xs text-slate-500">Skor Kualitas Komposit 81.8/100 &amp; Golden Dataset CI/CD Gate.</p>
          </div>
        </div>

        <div class="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2 text-xs text-slate-700 leading-relaxed">
          <p>
            • <strong>Metrik RAG Triad Terukur:</strong> Context Recall 86.0%, Faithfulness (Groundedness) 85.0%, Answer Relevancy 78.5%, dan OOD Refusal 100%.
          </p>
          <p>
            • <strong>Automated GitHub Actions:</strong> Setiap commit ke repository diuji secara ketat via <code>.github/workflows/ai_eval.yml</code> untuk mencegah regresi akurasi sebelum deployment.
          </p>
        </div>

        <div class="flex items-center justify-between pt-1">
          <button
            type="button"
            @click="emit('navigate-tab', 'evals'); closeTour();"
            class="rounded-xl border border-emerald-300 bg-emerald-50 px-3.5 py-2 text-xs font-bold text-emerald-900 hover:bg-emerald-100 transition-colors cursor-pointer"
          >
            Inspeksi Golden Dataset ↗
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

      <!-- STEP 5: Frans Alwan Purba Profile & Contact -->
      <div v-else-if="currentStep === 5" class="space-y-4">
        <div class="flex items-center gap-3">
          <div class="h-12 w-12 rounded-2xl bg-slate-900 text-white flex items-center justify-center text-2xl font-bold shrink-0 shadow-xs">
            👨‍💻
          </div>
          <div>
            <h4 class="text-base font-bold text-slate-900">Frans Alwan Purba</h4>
            <p class="text-xs text-slate-500">AI Engineer &amp; Distributed Systems • Magister Ilmu Komputer UGM</p>
          </div>
        </div>

        <div class="p-4 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-2 text-xs text-slate-700 leading-relaxed">
          <p>
            Berfokus pada arsitektur agen AI produksi (Google ADK, Anthropic MCP, Advanced RAG/CRAG, VLM), hybrid Machine Learning (Isolation Forest, CatBoost), serta backend berkecepatan tinggi (Golang, FastAPI, PostgreSQL pgvector).
          </p>
          <div class="pt-2 flex flex-wrap gap-1.5 font-medium">
            <span class="rounded bg-slate-200/80 px-2 py-0.5 text-[10px] text-slate-800">AI Engineering</span>
            <span class="rounded bg-slate-200/80 px-2 py-0.5 text-[10px] text-slate-800">Anthropic MCP</span>
            <span class="rounded bg-slate-200/80 px-2 py-0.5 text-[10px] text-slate-800">Google ADK</span>
            <span class="rounded bg-slate-200/80 px-2 py-0.5 text-[10px] text-slate-800">Golang 1.22</span>
            <span class="rounded bg-slate-200/80 px-2 py-0.5 text-[10px] text-slate-800">Python / FastAPI</span>
            <span class="rounded bg-slate-200/80 px-2 py-0.5 text-[10px] text-slate-800">pgvector HNSW</span>
            <span class="rounded bg-slate-200/80 px-2 py-0.5 text-[10px] text-slate-800">Vue 3 / Vite</span>
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
