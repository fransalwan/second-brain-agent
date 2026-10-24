<script setup lang="ts">
import { onMounted, ref } from 'vue'

const props = defineProps<{
  userId: string
  userEmail?: string | null
}>()

interface TelemetryEvent {
  id: string
  timestamp: string
  source: 'github_webhook' | 'local_git_hook' | 'go_worker' | 'rag_engine'
  repo_or_service: string
  message: string
  status: 'success' | 'warning' | 'info'
  payload_summary?: string
}

const telemetryLogs = ref<TelemetryEvent[]>([
  {
    id: 'evt-1',
    timestamp: new Date(Date.now() - 2 * 60 * 1000).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    source: 'local_git_hook',
    repo_or_service: 'thesis-experiments',
    message: 'Commit auto-sync: eval XGBoost IDCS acc=94.5% f1=93.8% loss=0.12',
    status: 'success',
    payload_summary: 'Akurasi: 94.5%, F1: 93.8%, Epoch: 100, LR: 0.001',
  },
  {
    id: 'evt-2',
    timestamp: new Date(Date.now() - 15 * 60 * 1000).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    source: 'github_webhook',
    repo_or_service: 'thesis-manuscripts',
    message: 'Push event: feat(bab 3) metodologi penelitian diperbarui ke 80%',
    status: 'success',
    payload_summary: 'Bab 3 -> Progress 80% [Drafting]',
  },
  {
    id: 'evt-3',
    timestamp: new Date(Date.now() - 45 * 60 * 1000).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    source: 'go_worker',
    repo_or_service: 'telemetry-worker-go',
    message: 'Evaluated bedtime guardian & sleep debt: 0 critical alerts',
    status: 'info',
    payload_summary: 'Cutoff: 23:00, Goroutines: 8, P95: 1.2ms',
  },
  {
    id: 'evt-4',
    timestamp: new Date(Date.now() - 90 * 60 * 1000).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    source: 'local_git_hook',
    repo_or_service: 'materi-kuliah',
    message: 'Commit auto-sync: selesaikan tugas 2 kriptografi implementasi RSA',
    status: 'success',
    payload_summary: 'Tugas #2 Kriptografi marked completed',
  },
  {
    id: 'evt-5',
    timestamp: new Date(Date.now() - 120 * 60 * 1000).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    source: 'rag_engine',
    repo_or_service: 'pgvector-768d',
    message: 'Hybrid Search (BM25 + RRF) executed for thesis notes query',
    status: 'info',
    payload_summary: 'Top 5 hits retrieved in 14.8ms',
  },
])

const simulationToast = ref<string | null>(null)

function showSimulationNotice(msg: string) {
  simulationToast.value = msg
  setTimeout(() => {
    simulationToast.value = null
  }, 4000)
}

function simulateEvent(type: 'experiment' | 'manuscript' | 'coursework' | 'goworker') {
  const nowStr = new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  if (type === 'experiment') {
    telemetryLogs.value.unshift({
      id: 'evt-' + Date.now(),
      timestamp: nowStr,
      source: 'local_git_hook',
      repo_or_service: 'thesis-experiments',
      message: 'Commit: exp(CatBoost) acc=95.1% f1=94.4% auc=0.97 epoch=150',
      status: 'success',
      payload_summary: 'Recorded to experiment_metrics & LaTeX ready',
    })
    showSimulationNotice('🧪 Berhasil mensimulasikan commit evaluasi model AI ke thesis-experiments!')
  } else if (type === 'manuscript') {
    telemetryLogs.value.unshift({
      id: 'evt-' + Date.now(),
      timestamp: nowStr,
      source: 'github_webhook',
      repo_or_service: 'thesis-manuscripts',
      message: 'Push: revisi bab 4 hasil simulasi SRA sesuai feedback dospem',
      status: 'success',
      payload_summary: 'Bab 4 -> Status: Revisi (85%) & SupervisionLog saved',
    })
    showSimulationNotice('📝 Berhasil mensimulasikan commit naskah skripsi Bab 4!')
  } else if (type === 'coursework') {
    telemetryLogs.value.unshift({
      id: 'evt-' + Date.now(),
      timestamp: nowStr,
      source: 'local_git_hook',
      repo_or_service: 'materi-kuliah',
      message: 'Commit: selesai tugas praktikum machine learning k-means',
      status: 'success',
      payload_summary: 'Tugas Praktikum ML marked as done',
    })
    showSimulationNotice('🎓 Berhasil mensimulasikan penyelesaian tugas materi-kuliah!')
  } else if (type === 'goworker') {
    telemetryLogs.value.unshift({
      id: 'evt-' + Date.now(),
      timestamp: nowStr,
      source: 'go_worker',
      repo_or_service: 'telemetry-worker-go',
      message: 'Heartbeat ping: Goroutines active=8, mem=14.2MB, worker status: healthy',
      status: 'info',
      payload_summary: 'Worker queue empty, throughput: 120 eval/min',
    })
    showSimulationNotice('⚡ Go Telemetry Worker merespon dengan status HEALTHY!')
  }
}

onMounted(() => {
  // Check live endpoints if reachable
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header Banner -->
    <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs sm:p-6">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div class="flex items-center gap-2">
            <span class="text-2xl">⚡</span>
            <h2 class="text-lg font-bold text-slate-900 sm:text-xl">Agent Ops &amp; System Telemetry</h2>
            <span class="rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-800">
              Polyglot Concurrency
            </span>
          </div>
          <p class="mt-1 text-xs text-slate-500 sm:text-sm">
            Pemantauan arsitektur terdistribusi: Background Worker (Golang), AI Engine (FastAPI + pgvector), dan pipeline Git Webhook akademik.
          </p>
        </div>

        <div class="flex items-center gap-2">
          <span class="inline-flex items-center gap-1.5 rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-bold text-emerald-800">
            <span class="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>Cluster Healthy</span>
          </span>
        </div>
      </div>
    </div>

    <!-- Cluster Nodes Status Grid -->
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
      <!-- Node 1: Go Telemetry Worker -->
      <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-2xs">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold uppercase tracking-wider text-slate-400">Worker Engine</span>
          <span class="rounded-md bg-cyan-50 border border-cyan-200 px-1.5 py-0.5 text-[10px] font-bold text-cyan-800">
            Golang 1.22
          </span>
        </div>
        <div class="mt-2 flex items-baseline gap-2">
          <h3 class="text-base font-bold text-slate-900">Telemetry Daemon</h3>
          <span class="text-[11px] text-emerald-600 font-semibold flex items-center gap-1">
            <span class="h-1.5 w-1.5 rounded-full bg-emerald-500"></span> Online (:8085)
          </span>
        </div>
        <p class="mt-1 text-[11px] text-slate-500">
          Goroutines pool untuk evaluasi sleep debt 7 hari, bedtime guardian cutoff, &amp; monitoring SLA bimbingan (>14 hari).
        </p>
        <div class="mt-3 flex items-center justify-between text-[11px] border-t border-slate-100 pt-2 text-slate-600">
          <span>Concurrency: <strong>Worker Pool</strong></span>
          <span>P95: <strong>&lt; 2.5ms</strong></span>
        </div>
      </div>

      <!-- Node 2: FastAPI AI Agent -->
      <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-2xs">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold uppercase tracking-wider text-slate-400">AI Core &amp; Webhooks</span>
          <span class="rounded-md bg-purple-50 border border-purple-200 px-1.5 py-0.5 text-[10px] font-bold text-purple-800">
            Python / FastAPI
          </span>
        </div>
        <div class="mt-2 flex items-baseline gap-2">
          <h3 class="text-base font-bold text-slate-900">Gemini &amp; Git Dispatcher</h3>
          <span class="text-[11px] text-emerald-600 font-semibold flex items-center gap-1">
            <span class="h-1.5 w-1.5 rounded-full bg-emerald-500"></span> Online (:8000)
          </span>
        </div>
        <p class="mt-1 text-[11px] text-slate-500">
          Menerima push webhook GitHub, parsing regex akademis, dan orkestrasi Telegram bot.
        </p>
        <div class="mt-3 flex items-center justify-between text-[11px] border-t border-slate-100 pt-2 text-slate-600">
          <span>Intent Acc: <strong>94.2%</strong></span>
          <span>Security: <strong>HMAC Secret</strong></span>
        </div>
      </div>

      <!-- Node 3: PostgreSQL Vector Store -->
      <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-2xs">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold uppercase tracking-wider text-slate-400">Database &amp; RAG</span>
          <span class="rounded-md bg-indigo-50 border border-indigo-200 px-1.5 py-0.5 text-[10px] font-bold text-indigo-800">
            PostgreSQL + pgvector
          </span>
        </div>
        <div class="mt-2 flex items-baseline gap-2">
          <h3 class="text-base font-bold text-slate-900">Knowledge Store</h3>
          <span class="text-[11px] text-emerald-600 font-semibold flex items-center gap-1">
            <span class="h-1.5 w-1.5 rounded-full bg-emerald-500"></span> RLS Protected
          </span>
        </div>
        <p class="mt-1 text-[11px] text-slate-500">
          Indeks 768-D HNSW embeddings dengan algoritma Reciprocal Rank Fusion (RRF) untuk pencarian catatan.
        </p>
        <div class="mt-3 flex items-center justify-between text-[11px] border-t border-slate-100 pt-2 text-slate-600">
          <span>Search Latency: <strong>~14ms</strong></span>
          <span>Isolation: <strong>Per-User RLS</strong></span>
        </div>
      </div>
    </div>

    <!-- Academic Repositories Pipeline Status -->
    <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h3 class="text-sm font-bold text-slate-900 sm:text-base flex items-center gap-2">
            <span>🐙</span>
            <span>Academic Repositories Git Pipeline</span>
          </h3>
          <p class="text-xs text-slate-500 mt-0.5">
            Integrasi aktif dua arah via Local Git Hook (<code>post-commit</code>) dan GitHub Webhook (<code>/api/v1/github/webhook</code>).
          </p>
        </div>
      </div>

      <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <!-- Pipeline 1: materi-kuliah -->
        <div class="rounded-xl border border-blue-100 bg-blue-50/50 p-3.5">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-blue-900 truncate">fransalwan/materi-kuliah</span>
            <span class="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
          </div>
          <p class="text-[11px] text-slate-600 mt-1">
            Mendeteksi nama matkul &amp; assignment, auto-complete status tugas kuliah.
          </p>
          <div class="mt-2.5 pt-2 border-t border-blue-200/60 flex items-center justify-between text-[10px] text-slate-500 font-medium">
            <span>Hook: <strong>post-commit</strong></span>
            <span class="text-blue-700">Auto Task Done</span>
          </div>
        </div>

        <!-- Pipeline 2: thesis-manuscripts -->
        <div class="rounded-xl border border-purple-100 bg-purple-50/50 p-3.5">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-purple-900 truncate">thesis-manuscripts</span>
            <span class="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
          </div>
          <p class="text-[11px] text-slate-600 mt-1">
            Tracking Bab 1 - 5 skripsi &amp; pencatatan otomatis arahan bimbingan dospem.
          </p>
          <div class="mt-2.5 pt-2 border-t border-purple-200/60 flex items-center justify-between text-[10px] text-slate-500 font-medium">
            <span>Hook: <strong>post-commit</strong></span>
            <span class="text-purple-700">Bab 1-5 Sync</span>
          </div>
        </div>

        <!-- Pipeline 3: thesis-experiments -->
        <div class="rounded-xl border border-indigo-100 bg-indigo-50/50 p-3.5">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-indigo-900 truncate">thesis-experiments</span>
            <span class="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
          </div>
          <p class="text-[11px] text-slate-600 mt-1">
            Ekstraksi metrik model AI (Akurasi, F1, Loss, Epoch) ke tabel LaTeX Bab 4.
          </p>
          <div class="mt-2.5 pt-2 border-t border-indigo-200/60 flex items-center justify-between text-[10px] text-slate-500 font-medium">
            <span>Hook: <strong>post-commit</strong></span>
            <span class="text-indigo-700">LaTeX Ready</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Live Interactive Test Trigger Console (for Recruiters & Testing) -->
    <div class="rounded-2xl border border-slate-200 bg-slate-900 text-white p-5 shadow-xs">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
        <div>
          <h3 class="text-sm font-bold sm:text-base flex items-center gap-2">
            <span>💻</span>
            <span>Live Interactive Event Simulator</span>
            <span class="rounded bg-indigo-500/30 border border-indigo-400/30 text-indigo-300 text-[10px] px-1.5 py-0.2 uppercase font-mono">Recruiter Sandbox</span>
          </h3>
          <p class="text-xs text-slate-400 mt-0.5">
            Uji coba langsung bagaimana sistem menerima dan memproses event Git &amp; worker telemetri secara realtime.
          </p>
        </div>
      </div>

      <div class="flex flex-wrap gap-2 mb-4">
        <button
          type="button"
          @click="simulateEvent('experiment')"
          class="rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-500 transition-colors cursor-pointer flex items-center gap-1.5 shadow-2xs"
        >
          <span>🧪</span>
          <span>Simulasi Commit Riset (CatBoost)</span>
        </button>
        <button
          type="button"
          @click="simulateEvent('manuscript')"
          class="rounded-lg bg-purple-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-purple-500 transition-colors cursor-pointer flex items-center gap-1.5 shadow-2xs"
        >
          <span>📝</span>
          <span>Simulasi Commit Naskah (Bab 4)</span>
        </button>
        <button
          type="button"
          @click="simulateEvent('coursework')"
          class="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-blue-500 transition-colors cursor-pointer flex items-center gap-1.5 shadow-2xs"
        >
          <span>🎓</span>
          <span>Simulasi Tugas Kuliah Selesai</span>
        </button>
        <button
          type="button"
          @click="simulateEvent('goworker')"
          class="rounded-lg bg-slate-800 border border-slate-700 px-3 py-1.5 text-xs font-semibold text-cyan-400 hover:bg-slate-700 transition-colors cursor-pointer flex items-center gap-1.5 shadow-2xs"
        >
          <span>⚡</span>
          <span>Ping Go Worker (:8085)</span>
        </button>
      </div>

      <!-- Realtime Event Terminal Log -->
      <div class="rounded-xl bg-slate-950 border border-slate-800 p-3.5 font-mono text-xs overflow-x-auto">
        <div class="flex items-center justify-between pb-2 mb-2 border-b border-slate-800 text-[11px] text-slate-500">
          <span>STREAMED AGENT AUDIT LOGS</span>
          <span class="flex items-center gap-1">
            <span class="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-ping"></span>
            <span class="text-emerald-400">LIVE</span>
          </span>
        </div>
        <div class="space-y-2 max-h-60 overflow-y-auto no-scrollbar">
          <div
            v-for="log in telemetryLogs"
            :key="log.id"
            class="flex items-start gap-2 leading-relaxed hover:bg-slate-900/60 p-1 rounded transition-colors"
          >
            <span class="text-slate-500 shrink-0">[{{ log.timestamp }}]</span>
            <span
              class="px-1.5 py-0.2 rounded text-[10px] font-bold uppercase shrink-0"
              :class="{
                'bg-emerald-950 text-emerald-400 border border-emerald-800': log.status === 'success',
                'bg-blue-950 text-blue-400 border border-blue-800': log.status === 'info',
                'bg-amber-950 text-amber-400 border border-amber-800': log.status === 'warning',
              }"
            >
              {{ log.source }}
            </span>
            <span class="text-slate-300 font-semibold shrink-0">{{ log.repo_or_service }}:</span>
            <span class="text-slate-200">{{ log.message }}</span>
            <span v-if="log.payload_summary" class="text-indigo-400 ml-auto hidden md:inline shrink-0">
              ({{ log.payload_summary }})
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Toast Notification -->
    <div
      v-if="simulationToast"
      class="fixed bottom-5 right-5 z-50 rounded-xl bg-slate-900 text-white px-4 py-2.5 text-xs shadow-xl flex items-center gap-2 border border-slate-700 animate-bounce"
    >
      <span>✨</span>
      <span>{{ simulationToast }}</span>
    </div>
  </div>
</template>
