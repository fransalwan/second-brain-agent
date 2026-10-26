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
    <div class="w-full max-w-4xl bg-slate-900 rounded-3xl shadow-2xl border border-slate-800 text-slate-100 overflow-hidden flex flex-col max-h-[90vh]">
      <!-- Header -->
      <div class="px-6 py-4 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="h-10 w-10 rounded-xl bg-purple-600/20 border border-purple-500/30 flex items-center justify-center text-xl">
            🛠️
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h2 class="text-sm sm:text-base font-bold text-white">Engineering Architecture &amp; AI Tech Specs</h2>
              <span class="rounded-full bg-indigo-500/20 px-2 py-0.5 text-[10px] font-bold text-indigo-300 border border-indigo-500/30">
                Production-Ready AI Agent
              </span>
            </div>
            <p class="text-xs text-slate-400">Arsitektur Polyglot Berkinerja Tinggi: AI Engine + Classical ML + MCP Standard + Concurrency Worker</p>
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
        <!-- 6 Core Pillars Grid (Fase 1 - 5) -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
          <!-- 1. MCP Standard -->
          <div class="p-4 rounded-2xl bg-indigo-950/30 border border-indigo-500/30 space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-indigo-300 flex items-center gap-1.5">
                <span>🔌</span> Model Context Protocol (MCP)
              </span>
              <span class="text-[10px] bg-indigo-500/20 text-indigo-200 px-2 py-0.5 rounded-full font-mono">Anthropic Std</span>
            </div>
            <p class="text-xs text-slate-300 leading-relaxed">
              FastAPI SSE transport (<code class="text-indigo-300">/mcp/sse</code>) mengekspos 8 tool schemas berstandar industri sehingga Claude Desktop dan IDE Cursor dapat memanggil Second Brain via JSON-RPC 2.0.
            </p>
          </div>

          <!-- 2. Next-Gen RAG & RAPTOR -->
          <div class="p-4 rounded-2xl bg-purple-950/30 border border-purple-500/30 space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-purple-300 flex items-center gap-1.5">
                <span>🧠</span> Next-Gen RAG &amp; RAPTOR
              </span>
              <span class="text-[10px] bg-purple-500/20 text-purple-200 px-2 py-0.5 rounded-full font-mono">CRAG + GMM</span>
            </div>
            <p class="text-xs text-slate-300 leading-relaxed">
              Gaussian Mixture Models (GMM) untuk hierarchical clustering dokumen. Dilengkapi Corrective RAG (CRAG), ekspansi kueri hipotesis (HyDE), dan Cross-Encoder reranking untuk presisi pengambilan tertinggi.
            </p>
          </div>

          <!-- 3. Multimodal Document VLM -->
          <div class="p-4 rounded-2xl bg-blue-950/30 border border-blue-500/30 space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-blue-300 flex items-center gap-1.5">
                <span>📸</span> Multimodal Document AI
              </span>
              <span class="text-[10px] bg-blue-500/20 text-blue-200 px-2 py-0.5 rounded-full font-mono">Gemini 2.0 VLM</span>
            </div>
            <p class="text-xs text-slate-300 leading-relaxed">
              Mengekstrak kurva loss CatBoost, catatan kuliah tulisan tangan, dan diagram arsitektur menjadi structured JSON dan otomatis mengindeksnya ke vektor pgvector 768-D.
            </p>
          </div>

          <!-- 4. Classical ML Hybrid -->
          <div class="p-4 rounded-2xl bg-cyan-950/30 border border-cyan-500/30 space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-cyan-300 flex items-center gap-1.5">
                <span>📊</span> Classical ML Hybrid Radar
              </span>
              <span class="text-[10px] bg-cyan-500/20 text-cyan-200 px-2 py-0.5 rounded-full font-mono">&lt; 2ms Deterministic</span>
            </div>
            <p class="text-xs text-slate-300 leading-relaxed">
              Isolation Forest (scikit-learn) mendeteksi anomali sirkadian secara deterministik dalam &lt; 2ms tanpa membakar token LLM, hanya memanggil agen intervensi empatik saat skor &lt; -0.15.
            </p>
          </div>

          <!-- 5. AI Quality Flywheel -->
          <div class="p-4 rounded-2xl bg-emerald-950/30 border border-emerald-500/30 space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-emerald-300 flex items-center gap-1.5">
                <span>🏆</span> AI Quality Flywheel (Evals)
              </span>
              <span class="text-[10px] bg-emerald-500/20 text-emerald-200 px-2 py-0.5 rounded-full font-mono">81.8 / 100</span>
            </div>
            <p class="text-xs text-slate-300 leading-relaxed">
              Evaluasi LLM-as-a-Judge otomatis terhadap 20 Golden Dataset uji akademik pada metrik RAG Triad: Context Recall (86.0%), Faithfulness (85.0%), dan OOD Refusal (100%) via GitHub Actions CI/CD.
            </p>
          </div>

          <!-- 6. Go Telemetry Engine -->
          <div class="p-4 rounded-2xl bg-sky-950/30 border border-sky-500/30 space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-sky-300 flex items-center gap-1.5">
                <span>🐹</span> Go Concurrency Telemetry
              </span>
              <span class="text-[10px] bg-sky-500/20 text-sky-200 px-2 py-0.5 rounded-full font-mono">Golang 1.22+</span>
            </div>
            <p class="text-xs text-slate-300 leading-relaxed">
              Daemon mandiri berbasis Goroutines &amp; Channel Worker Pool pada port :8085 dengan exponential backoff retry untuk evaluasi non-blocking terhadap batas waktu tidur dan SLA bimbingan.
            </p>
          </div>
        </div>

        <!-- Architecture Flow Diagram -->
        <div class="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-3 font-mono text-[11px]">
          <span class="text-slate-400 font-bold uppercase tracking-wider block">Target System Architecture:</span>
          <div class="bg-slate-900/90 p-3 rounded-xl text-slate-300 leading-relaxed overflow-x-auto no-scrollbar">
[Client: Vue 3 / External Claude Desktop] ──► [Anthropic MCP Server SSE :8000/mcp/sse]
                    │                                             │
                    ▼                                             ▼
       [Go Telemetry Worker :8085]                 [Google ADK Agent Orchestrator]
       (Goroutines Pool &lt; 2.5ms)                    (CRAG + HyDE Query Expansion)
                    │                                             │
                    ▼                                             ▼
        [Isolation Forest ML Radar]                [RAPTOR GMM Cluster Tree + Reranker]
                    │                                             │
                    ▼                                             ▼
        [Circadian Alert / Webhook]               [PostgreSQL + pgvector HNSW 768-D]
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="px-6 py-3.5 bg-slate-950/80 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
        <span>Kandidat: Frans Alwan Purba (M.Cs in AI Student, Universitas Gadjah Mada)</span>
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
