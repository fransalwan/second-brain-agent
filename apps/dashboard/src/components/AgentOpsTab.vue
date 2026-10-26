<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  userId: string
  userEmail?: string | null
}>()

interface TelemetryEvent {
  id: string
  timestamp: string
  source: 'mcp_server' | 'github_webhook' | 'local_git_hook' | 'go_worker' | 'rag_engine'
  repo_or_service: string
  message: string
  status: 'success' | 'warning' | 'info'
  payload_summary?: string
}

interface McpTool {
  name: string
  description: string
  parameters: string[]
  category: 'Knowledge' | 'Thesis' | 'Health' | 'ML/Vision'
}

const mcpTools = ref<McpTool[]>([
  {
    name: 'save_note',
    description: 'Menyimpan catatan atau ide baru ke Second Brain & mengindeks embedding vektor 768-D.',
    parameters: ['content: string', 'tags?: string[]'],
    category: 'Knowledge',
  },
  {
    name: 'search_notes',
    description: 'Pencarian semantik hybrid menggunakan pgvector (HNSW) + BM25 Reciprocal Rank Fusion.',
    parameters: ['query: string', 'limit?: number'],
    category: 'Knowledge',
  },
  {
    name: 'get_thesis_progress',
    description: 'Mengambil ringkasan progres Bab 1 s.d. 5 skripsi beserta catatan bimbingan terakhir.',
    parameters: [],
    category: 'Thesis',
  },
  {
    name: 'log_habit',
    description: 'Mencatat penyelesaian habit harian (misal: Bedtime Guardian atau Hidrasi).',
    parameters: ['habit_name: string'],
    category: 'Health',
  },
  {
    name: 'record_focus_session',
    description: 'Mencatat sesi deep work terverifikasi ke log produktivitas sirkadian.',
    parameters: ['project_name: string', 'duration_minutes: number'],
    category: 'Health',
  },
  {
    name: 'evaluate_burnout_radar',
    description: 'Menjalankan evaluasi Isolation Forest & intervensi LLM deterministik < 2ms.',
    parameters: ['email?: string'],
    category: 'Health',
  },
  {
    name: 'upload_visual_document',
    description: 'Menganalisis berkas visual (kurva loss CatBoost, catatan tangan) via Gemini 2.0 VLM.',
    parameters: ['filename: string', 'mime_type: string'],
    category: 'ML/Vision',
  },
  {
    name: 'run_rag_qa',
    description: 'Eksekusi pipeline Corrective RAG (CRAG) + RAPTOR hierarchical summary & reranker.',
    parameters: ['question: string'],
    category: 'Knowledge',
  },
])

const telemetryLogs = ref<TelemetryEvent[]>([
  {
    id: 'evt-mcp',
    timestamp: new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    source: 'mcp_server',
    repo_or_service: 'FastAPI MCP SSE',
    message: 'Claude Desktop client connected via SSE transport (/mcp/sse)',
    status: 'success',
    payload_summary: 'JSON-RPC 2.0: tools/list returned 8 active tools',
  },
  {
    id: 'evt-1',
    timestamp: new Date(Date.now() - 2 * 60 * 1000).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    source: 'local_git_hook',
    repo_or_service: 'thesis-experiments',
    message: 'Commit auto-sync: eval CatBoost epoch 350 acc=95.1% f1=94.4% loss=0.118',
    status: 'success',
    payload_summary: 'Akurasi: 95.1%, F1: 94.4%, Epoch: 350, LR: 0.03',
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
    id: 'evt-5',
    timestamp: new Date(Date.now() - 120 * 60 * 1000).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    source: 'rag_engine',
    repo_or_service: 'pgvector-768d',
    message: 'CRAG Hybrid Search (HNSW + RRF) executed for CatBoost loss curve',
    status: 'info',
    payload_summary: 'Top 5 hits retrieved in 14.8ms',
  },
])

const simulationToast = ref<string | null>(null)
const jsonRpcOutput = ref<string | null>(null)

function showSimulationNotice(msg: string) {
  simulationToast.value = msg
  setTimeout(() => {
    simulationToast.value = null
  }, 4000)
}

function simulateMcpRpc(action: 'list' | 'search_notes' | 'radar') {
  const nowStr = new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  if (action === 'list') {
    jsonRpcOutput.value = JSON.stringify(
      {
        jsonrpc: '2.0',
        id: 'req-' + Date.now(),
        result: {
          tools: mcpTools.value.map((t) => ({
            name: t.name,
            description: t.description,
            inputSchema: { type: 'object', properties: t.parameters },
          })),
        },
      },
      null,
      2
    )
    showSimulationNotice('🔌 JSON-RPC "tools/list" berhasil dieksekusi via protokol MCP!')
  } else if (action === 'search_notes') {
    jsonRpcOutput.value = JSON.stringify(
      {
        jsonrpc: '2.0',
        id: 'req-' + Date.now(),
        result: {
          content: [
            {
              type: 'text',
              text: 'Found 2 matching notes: [1] Metodologi Bab 3 HNSW Indexing (score: 0.945), [2] CatBoost Hyperparameter Tuning (score: 0.892).',
            },
          ],
        },
      },
      null,
      2
    )
    showSimulationNotice('🔍 JSON-RPC "tools/call: search_notes" sukses!')
  } else {
    jsonRpcOutput.value = JSON.stringify(
      {
        jsonrpc: '2.0',
        id: 'req-' + Date.now(),
        result: {
          anomaly_score: 0.354,
          status: 'HEALTHY_OPTIMAL',
          latency_ms: 1.2,
          intervention_triggered: false,
        },
      },
      null,
      2
    )
    showSimulationNotice('📊 JSON-RPC "tools/call: evaluate_burnout_radar" sukses (< 2ms)!')
  }

  telemetryLogs.value.unshift({
    id: 'mcp-' + Date.now(),
    timestamp: nowStr,
    source: 'mcp_server',
    repo_or_service: 'mcp-server-sse',
    message: `JSON-RPC dispatch: ${action}() responded with 200 OK`,
    status: 'success',
    payload_summary: 'Transport: SSE, Latency: 4.8ms',
  })
}

function simulateEvent(type: 'experiment' | 'manuscript' | 'coursework' | 'goworker') {
  const nowStr = new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  if (type === 'experiment') {
    telemetryLogs.value.unshift({
      id: 'evt-' + Date.now(),
      timestamp: nowStr,
      source: 'local_git_hook',
      repo_or_service: 'thesis-experiments',
      message: 'Commit: exp(CatBoost) acc=95.1% f1=94.4% auc=0.97 epoch=350',
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
</script>

<template>
  <div class="space-y-6">
    <!-- Header Banner -->
    <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs sm:p-6">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-2xl">🔌</span>
            <h2 class="text-lg font-bold text-slate-900 sm:text-xl">Model Context Protocol (MCP) &amp; Telemetry Ops</h2>
            <span class="rounded-full bg-indigo-100 border border-indigo-200 px-2.5 py-0.5 text-xs font-bold text-indigo-800">
              Anthropic MCP SSE Standard
            </span>
            <span class="rounded-full bg-cyan-100 border border-cyan-200 px-2.5 py-0.5 text-xs font-bold text-cyan-800">
              Go Concurrency (:8085)
            </span>
          </div>
          <p class="mt-1 text-xs text-slate-500 sm:text-sm">
            Arsitektur keterbukaan ekosistem agen: Menghubungkan Second Brain ke klien desktop (Claude Desktop, Cursor IDE) melalui protokol MCP SSE standar, dipadukan dengan daemon telemetri konkurensi Golang berkecepatan tinggi.
          </p>
        </div>

        <div class="flex items-center gap-2">
          <span class="inline-flex items-center gap-1.5 rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-bold text-emerald-800">
            <span class="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>MCP SSE: /mcp/sse</span>
          </span>
        </div>
      </div>
    </div>

    <!-- Cluster Nodes Status Grid -->
    <div class="grid grid-cols-1 gap-4 sm:grid-cols-3">
      <!-- Node 1: MCP Server SSE -->
      <div class="rounded-2xl border border-indigo-200 bg-gradient-to-br from-indigo-50/50 to-white p-4 shadow-2xs">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold uppercase tracking-wider text-indigo-900">Standard MCP Server</span>
          <span class="rounded-md bg-indigo-100 border border-indigo-200 px-1.5 py-0.5 text-[10px] font-bold text-indigo-800">
            Anthropic Standard
          </span>
        </div>
        <div class="mt-2 flex items-baseline gap-2">
          <h3 class="text-base font-bold text-slate-900">SSE Transport Endpoint</h3>
          <span class="text-[11px] text-emerald-600 font-semibold flex items-center gap-1">
            <span class="h-1.5 w-1.5 rounded-full bg-emerald-500"></span> /mcp/sse
          </span>
        </div>
        <p class="mt-1 text-[11px] text-slate-500">
          Mengekspos 8 tools berstandar JSON-RPC 2.0 untuk konsumsi langsung oleh Claude Desktop dan IDE Cursor.
        </p>
        <div class="mt-3 flex items-center justify-between text-[11px] border-t border-indigo-100 pt-2 text-slate-600">
          <span>Active Tools: <strong>8 Schemas</strong></span>
          <span>Transport: <strong>SSE + POST</strong></span>
        </div>
      </div>

      <!-- Node 2: Go Telemetry Worker -->
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
          Goroutines pool untuk evaluasi sirkadian 7 hari, bedtime guardian cutoff, &amp; monitoring SLA bimbingan (>14 hari).
        </p>
        <div class="mt-3 flex items-center justify-between text-[11px] border-t border-slate-100 pt-2 text-slate-600">
          <span>Concurrency: <strong>Worker Pool</strong></span>
          <span>P95: <strong>&lt; 2.5ms</strong></span>
        </div>
      </div>

      <!-- Node 3: PostgreSQL Vector Store -->
      <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-2xs">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold uppercase tracking-wider text-slate-400">Database &amp; RAG</span>
          <span class="rounded-md bg-purple-50 border border-purple-200 px-1.5 py-0.5 text-[10px] font-bold text-purple-800">
            PostgreSQL + pgvector
          </span>
        </div>
        <div class="mt-2 flex items-baseline gap-2">
          <h3 class="text-base font-bold text-slate-900">Knowledge Store</h3>
          <span class="text-[11px] text-emerald-600 font-semibold flex items-center gap-1">
            <span class="h-1.5 w-1.5 rounded-full bg-emerald-500"></span> 768-D HNSW
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

    <!-- MCP Tools Registry & JSON-RPC Simulator -->
    <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <div>
          <h3 class="text-sm font-bold text-slate-900">Registered Model Context Protocol (MCP) Tools</h3>
          <p class="text-xs text-slate-500">Kumpulan skema tool yang siap dikonsumsi oleh agen eksternal melalui antarmuka standar:</p>
        </div>

        <!-- Simulator actions -->
        <div class="flex flex-wrap gap-1.5">
          <button
            type="button"
            @click="simulateMcpRpc('list')"
            class="rounded-lg bg-indigo-50 border border-indigo-200 text-indigo-800 hover:bg-indigo-100 px-2.5 py-1 text-xs font-bold transition-colors cursor-pointer"
          >
            📋 Test tools/list
          </button>
          <button
            type="button"
            @click="simulateMcpRpc('search_notes')"
            class="rounded-lg bg-purple-50 border border-purple-200 text-purple-800 hover:bg-purple-100 px-2.5 py-1 text-xs font-bold transition-colors cursor-pointer"
          >
            🔍 Test search_notes()
          </button>
          <button
            type="button"
            @click="simulateMcpRpc('radar')"
            class="rounded-lg bg-cyan-50 border border-cyan-200 text-cyan-800 hover:bg-cyan-100 px-2.5 py-1 text-xs font-bold transition-colors cursor-pointer"
          >
            📊 Test evaluate_burnout()
          </button>
        </div>
      </div>

      <!-- JSON-RPC Live Inspector if clicked -->
      <div v-if="jsonRpcOutput" class="rounded-xl bg-slate-900 p-3.5 text-xs font-mono text-emerald-400 space-y-1.5 shadow-2xs">
        <div class="flex items-center justify-between text-[10px] text-slate-400 border-b border-slate-800 pb-1">
          <span>LIVE MCP JSON-RPC 2.0 RESPONSE PAYLOAD</span>
          <button type="button" @click="jsonRpcOutput = null" class="text-slate-400 hover:text-white cursor-pointer">✕ Tutup</button>
        </div>
        <pre class="overflow-x-auto whitespace-pre leading-relaxed">{{ jsonRpcOutput }}</pre>
      </div>

      <!-- Tools Grid -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <div
          v-for="tool in mcpTools"
          :key="tool.name"
          class="rounded-xl border border-slate-200 bg-slate-50/50 p-3 hover:bg-white hover:border-slate-300 transition-all space-y-1.5"
        >
          <div class="flex items-center justify-between">
            <span class="font-mono text-xs font-bold text-indigo-950">{{ tool.name }}()</span>
            <span
              class="rounded px-1.5 py-0.2 text-[9px] font-bold uppercase"
              :class="{
                'bg-purple-100 text-purple-800': tool.category === 'Knowledge',
                'bg-blue-100 text-blue-800': tool.category === 'Thesis',
                'bg-emerald-100 text-emerald-800': tool.category === 'Health',
                'bg-amber-100 text-amber-800': tool.category === 'ML/Vision',
              }"
            >
              {{ tool.category }}
            </span>
          </div>
          <p class="text-[11px] text-slate-600 line-clamp-2">
            {{ tool.description }}
          </p>
          <div class="pt-1.5 border-t border-slate-200/60 text-[10px] font-mono text-slate-500">
            <span>Params: {{ tool.parameters.length > 0 ? tool.parameters.join(', ') : 'none' }}</span>
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
            <span>Live System Event Simulator &amp; Audit Logs</span>
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
