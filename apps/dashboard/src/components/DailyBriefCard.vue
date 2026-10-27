<script setup lang="ts">
const props = defineProps<{
  fullName?: string | null
  email?: string | null
  briefTime?: string | null
  nightCutoffTime?: string | null
  tasks?: any[]
  timeLogs?: any[]
  habits?: any[]
  habitLogs?: any[]
}>()

const emit = defineEmits<{
  (e: 'navigate-tab', tab: string): void
  (e: 'toggle-task', taskId: number): void
}>()
</script>

<template>
  <div class="h-full rounded-3xl border border-slate-200/90 bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 text-white p-5 sm:p-6 shadow-md shadow-indigo-950/20 relative overflow-hidden flex flex-col justify-between">
    <!-- Ambient subtle background glow -->
    <div class="absolute -top-12 -right-12 w-64 h-64 bg-purple-600/15 rounded-full blur-3xl pointer-events-none"></div>
    <div class="absolute -bottom-12 -left-12 w-64 h-64 bg-cyan-600/15 rounded-full blur-3xl pointer-events-none"></div>

    <div class="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
      <!-- Sisi Kiri: Executive AI System Overview & SLA Indicators -->
      <div class="space-y-4 max-w-xl">
        <div class="flex items-center gap-2 flex-wrap">
          <span class="inline-flex items-center gap-1.5 rounded-full bg-indigo-500/20 border border-indigo-500/30 px-2.5 py-0.5 text-[11px] font-bold text-indigo-300">
            <span class="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>Production AI Architecture</span>
          </span>
          <span class="rounded-full bg-purple-500/20 border border-purple-500/30 px-2.5 py-0.5 text-[11px] font-mono text-purple-300 font-bold">
            Google ADK + Anthropic MCP
          </span>
          <span class="text-xs text-slate-400 font-medium hidden sm:inline">
            · S2 Computer Science FMIPA UGM
          </span>
        </div>

        <div>
          <h2 class="text-lg sm:text-xl font-black tracking-tight text-white leading-snug">
            Autonomous AI Operations &amp; System SLA Cockpit
          </h2>
          <p class="text-xs text-slate-300 mt-1 leading-relaxed">
            Klaster multi-agent terdistribusi aktif: <strong>Corrective RAG (CRAG) + RAPTOR Tree</strong>, Computer Vision <strong>Gemini 2.0 Flash VLM</strong>, deteksi anomali <strong>Classical ML (&lt; 2ms)</strong>, serta vector store <strong>pgvector 768-D HNSW</strong>.
          </p>
        </div>

        <!-- 4 Live Operational SLA Indicators -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
          <!-- SLA 1 -->
          <div class="rounded-2xl border border-slate-800 bg-slate-900/80 p-2.5 backdrop-blur-xs">
            <div class="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">Faithfulness</div>
            <div class="mt-1 flex items-baseline gap-1">
              <span class="text-base sm:text-lg font-mono font-black text-emerald-400">85.0%</span>
              <span class="text-[10px] text-emerald-500 font-bold">PASSED</span>
            </div>
            <div class="text-[10px] text-slate-500 mt-0.5">Anti-Halusinasi</div>
          </div>

          <!-- SLA 2 -->
          <div class="rounded-2xl border border-slate-800 bg-slate-900/80 p-2.5 backdrop-blur-xs">
            <div class="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">OOD Refusal</div>
            <div class="mt-1 flex items-baseline gap-1">
              <span class="text-base sm:text-lg font-mono font-black text-cyan-300">100%</span>
              <span class="text-[10px] text-cyan-400 font-bold">PERFECT</span>
            </div>
            <div class="text-[10px] text-slate-500 mt-0.5">Guardrail Out-of-Dist</div>
          </div>

          <!-- SLA 3 -->
          <div class="rounded-2xl border border-slate-800 bg-slate-900/80 p-2.5 backdrop-blur-xs">
            <div class="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">p95 Latency</div>
            <div class="mt-1 flex items-baseline gap-1">
              <span class="text-base sm:text-lg font-mono font-black text-purple-300">36.0ms</span>
              <span class="text-[10px] text-purple-400 font-bold">Vector</span>
            </div>
            <div class="text-[10px] text-slate-500 mt-0.5">HNSW Re-ranking</div>
          </div>

          <!-- SLA 4 -->
          <div class="rounded-2xl border border-slate-800 bg-slate-900/80 p-2.5 backdrop-blur-xs">
            <div class="text-[10px] uppercase tracking-wider text-slate-400 font-semibold">Composite Score</div>
            <div class="mt-1 flex items-baseline gap-1">
              <span class="text-base sm:text-lg font-mono font-black text-amber-300">81.8</span>
              <span class="text-[10px] text-amber-400 font-bold">/100</span>
            </div>
            <div class="text-[10px] text-slate-500 mt-0.5">Golden Evals (20/20)</div>
          </div>
        </div>
      </div>

      <!-- Sisi Kanan: Agent Orchestrator & Live Guardrail Status -->
      <div class="w-full lg:w-72 rounded-2xl bg-slate-900/90 p-4 border border-slate-800 shadow-xl space-y-3 shrink-0">
        <div class="flex items-center justify-between pb-2 border-b border-slate-800">
          <span class="text-xs font-bold text-slate-200 flex items-center gap-1.5">
            <span class="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>Agent Guardrail Gate</span>
          </span>
          <span class="text-[10px] font-mono text-emerald-400 font-bold bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/30">
            SECURE
          </span>
        </div>

        <div class="space-y-1.5 text-[11px]">
          <div class="flex items-center justify-between p-1.5 rounded-xl bg-slate-950/80 border border-slate-800/80">
            <span class="text-slate-300 flex items-center gap-1.5">
              <span class="text-cyan-400">●</span>
              <span>Semantic Threshold</span>
            </span>
            <span class="font-mono text-cyan-300 text-[10px] font-bold">&gt; 0.65 Cosine</span>
          </div>

          <div class="flex items-center justify-between p-1.5 rounded-xl bg-slate-950/80 border border-slate-800/80">
            <span class="text-slate-300 flex items-center gap-1.5">
              <span class="text-purple-400">●</span>
              <span>HyDE Query Expander</span>
            </span>
            <span class="font-mono text-purple-300 text-[10px]">Aktif (Zero-Shot)</span>
          </div>

          <div class="flex items-center justify-between p-1.5 rounded-xl bg-slate-950/80 border border-slate-800/80">
            <span class="text-slate-300 flex items-center gap-1.5">
              <span class="text-emerald-400">●</span>
              <span>Role RBAC Engine</span>
            </span>
            <span class="font-mono text-emerald-300 text-[10px]">Recruiter / Owner</span>
          </div>
        </div>

        <!-- Fast Interactive Navigation Actions -->
        <div class="grid grid-cols-2 gap-1.5 pt-1 border-t border-slate-800 text-[11px]">
          <button
            type="button"
            @click="emit('navigate-tab', 'rag')"
            class="rounded-xl bg-purple-600/20 hover:bg-purple-600/30 border border-purple-500/30 py-1.5 font-bold text-purple-300 text-center transition-colors cursor-pointer"
          >
            🧠 Uji CRAG
          </button>
          <button
            type="button"
            @click="emit('navigate-tab', 'mlradar')"
            class="rounded-xl bg-cyan-600/20 hover:bg-cyan-600/30 border border-cyan-500/30 py-1.5 font-bold text-cyan-300 text-center transition-colors cursor-pointer"
          >
            📊 Radar &lt;2ms
          </button>
          <button
            type="button"
            @click="emit('navigate-tab', 'evals')"
            class="rounded-xl bg-amber-600/20 hover:bg-amber-600/30 border border-amber-500/30 py-1.5 font-bold text-amber-300 text-center transition-colors cursor-pointer"
          >
            🏆 Inspeksi Evals
          </button>
          <button
            type="button"
            @click="emit('navigate-tab', 'agentops')"
            class="rounded-xl bg-emerald-600/20 hover:bg-emerald-600/30 border border-emerald-500/30 py-1.5 font-bold text-emerald-300 text-center transition-colors cursor-pointer"
          >
            ⚡ Agent Ops
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
