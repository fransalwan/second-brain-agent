<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

const props = defineProps<{
  isOpen: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'navigate-tab', tab: string): void
  (e: 'open-dospem-modal'): void
  (e: 'open-tech-specs'): void
  (e: 'open-brain-rag'): void
  (e: 'open-quick-capture'): void
}>()

const searchQuery = ref('')
const selectedIndex = ref(0)
const inputRef = ref<HTMLInputElement | null>(null)

interface CommandItem {
  id: string
  title: string
  category: '⚡ Demo Cepat AI' | '🧭 Navigasi Modul' | '🔬 Tesis & Riset S2' | '🛠️ Alat & Ekosistem'
  shortcut?: string
  action: () => void
}

const allCommands: CommandItem[] = [
  {
    id: 'cmd-eval-ood',
    title: 'Uji Guardrail OOD (Martabak 0% Halusinasi - 1.2s)',
    category: '⚡ Demo Cepat AI',
    shortcut: 'Spot-Check',
    action: () => {
      emit('navigate-tab', 'evals')
      emit('close')
    },
  },
  {
    id: 'cmd-eval-catboost',
    title: 'Uji Riset CatBoost (IDCS RAG Triad Evaluasi)',
    category: '⚡ Demo Cepat AI',
    shortcut: 'Judge',
    action: () => {
      emit('navigate-tab', 'evals')
      emit('close')
    },
  },
  {
    id: 'cmd-mlradar-test',
    title: 'Jalankan Radar Sirkadian Isolation Forest (< 2ms)',
    category: '⚡ Demo Cepat AI',
    shortcut: '<2ms',
    action: () => {
      emit('navigate-tab', 'mlradar')
      emit('close')
    },
  },
  {
    id: 'cmd-vlm-curve',
    title: 'Analisis Kurva Loss Model VLM (Gemini 2.0 Flash)',
    category: '⚡ Demo Cepat AI',
    shortcut: 'VLM',
    action: () => {
      emit('navigate-tab', 'vlm')
      emit('close')
    },
  },
  {
    id: 'cmd-thesis-arch',
    title: 'Buka Arsitektur 3 Tahap Tesis S2 (FMIPA UGM)',
    category: '🔬 Tesis & Riset S2',
    shortcut: 'Tesis',
    action: () => {
      emit('navigate-tab', 'research')
      emit('close')
    },
  },
  {
    id: 'cmd-thesis-perm',
    title: 'Simulator Uji Permutasi Kausal Cepat (140ms Preview)',
    category: '🔬 Tesis & Riset S2',
    shortcut: 'B=50',
    action: () => {
      emit('navigate-tab', 'research')
      emit('close')
    },
  },
  {
    id: 'cmd-dospem-wa',
    title: 'Draft Pesan WhatsApp Pembimbing (Bu Afiahayati / Prof. Sri Hartati)',
    category: '🔬 Tesis & Riset S2',
    shortcut: 'WhatsApp',
    action: () => {
      emit('open-dospem-modal')
      emit('close')
    },
  },
  {
    id: 'cmd-tab-overview',
    title: 'Ringkasan Eksekutif (Bento Grid 2.0 & Status Microservice)',
    category: '🧭 Navigasi Modul',
    action: () => {
      emit('navigate-tab', 'overview')
      emit('close')
    },
  },
  {
    id: 'cmd-tab-rag',
    title: 'Next-Gen Corrective RAG (CRAG & RAPTOR Tree)',
    category: '🧭 Navigasi Modul',
    action: () => {
      emit('navigate-tab', 'rag')
      emit('close')
    },
  },
  {
    id: 'cmd-tab-mcp',
    title: 'MCP Server & Telemetri Polyglot (SSE :8000 & Go :8085)',
    category: '🧭 Navigasi Modul',
    action: () => {
      emit('navigate-tab', 'agentops')
      emit('close')
    },
  },
  {
    id: 'cmd-open-rag',
    title: 'Tanya AI & Pencarian Vektor Semantik (pgvector 768-D)',
    category: '🛠️ Alat & Ekosistem',
    shortcut: 'Semantic',
    action: () => {
      emit('open-brain-rag')
      emit('close')
    },
  },
  {
    id: 'cmd-quick-capture',
    title: 'Catat Tugas Cepat, Air Minum, atau Kebiasaan (Quick Capture)',
    category: '🛠️ Alat & Ekosistem',
    shortcut: 'Capture',
    action: () => {
      emit('open-quick-capture')
      emit('close')
    },
  },
  {
    id: 'cmd-tech-specs',
    title: 'Buka Spesifikasi Teknis & Diagram Arsitektur Polyglot',
    category: '🛠️ Alat & Ekosistem',
    shortcut: 'Specs',
    action: () => {
      emit('open-tech-specs')
      emit('close')
    },
  },
]

const filteredCommands = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return allCommands
  return allCommands.filter(
    (cmd) =>
      cmd.title.toLowerCase().includes(q) ||
      cmd.category.toLowerCase().includes(q) ||
      cmd.shortcut?.toLowerCase().includes(q)
  )
})

watch(
  () => props.isOpen,
  (open) => {
    if (open) {
      searchQuery.value = ''
      selectedIndex.value = 0
      nextTick(() => {
        inputRef.value?.focus()
      })
    }
  }
)

function handleKeyDown(e: KeyboardEvent) {
  if (!props.isOpen) return

  if (e.key === 'ArrowDown') {
    e.preventDefault()
    selectedIndex.value = (selectedIndex.value + 1) % Math.max(1, filteredCommands.value.length)
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    selectedIndex.value =
      (selectedIndex.value - 1 + filteredCommands.value.length) % Math.max(1, filteredCommands.value.length)
  } else if (e.key === 'Enter') {
    e.preventDefault()
    const target = filteredCommands.value[selectedIndex.value]
    if (target) {
      target.action()
    }
  } else if (e.key === 'Escape') {
    emit('close')
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})
</script>

<template>
  <div
    v-if="isOpen"
    class="fixed inset-0 z-50 flex items-start justify-center pt-16 sm:pt-24 px-4 bg-slate-950/60 backdrop-blur-sm transition-all"
    @click.self="emit('close')"
  >
    <div
      class="w-full max-w-xl rounded-2xl bg-white shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150"
    >
      <!-- Search Input Bar -->
      <div class="flex items-center gap-3 px-4 py-3 border-b border-slate-100 bg-slate-50/50">
        <span class="text-slate-400 text-lg">🔍</span>
        <input
          ref="inputRef"
          v-model="searchQuery"
          type="text"
          placeholder="Ketik perintah atau navigasi (misal: 'martabak', 'tesis', 'radar', 'vlm')..."
          class="flex-1 bg-transparent text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none"
        />
        <kbd class="hidden sm:inline-block rounded bg-white px-2 py-0.5 text-[10px] font-mono font-semibold text-slate-400 border border-slate-200 shadow-2xs">ESC to close</kbd>
      </div>

      <!-- Commands Results List -->
      <div class="max-h-96 overflow-y-auto p-2 space-y-1">
        <div v-if="filteredCommands.length === 0" class="py-8 text-center text-xs text-slate-400">
          Tidak ada perintah yang cocok dengan "{{ searchQuery }}".
        </div>

        <button
          v-for="(cmd, idx) in filteredCommands"
          :key="cmd.id"
          type="button"
          @click="cmd.action()"
          @mouseenter="selectedIndex = idx"
          class="w-full flex items-center justify-between gap-3 px-3.5 py-2.5 rounded-xl text-left text-xs transition-colors cursor-pointer"
          :class="selectedIndex === idx ? 'bg-purple-50 text-purple-950 border border-purple-200/80 font-semibold' : 'text-slate-700 hover:bg-slate-50 border border-transparent'"
        >
          <div class="flex items-center gap-2.5 min-w-0">
            <span class="text-slate-400 text-[11px] shrink-0 font-medium font-mono">
              {{ cmd.category.split(' ')[0] }}
            </span>
            <span class="truncate">{{ cmd.title }}</span>
          </div>

          <div class="flex items-center gap-2 shrink-0">
            <span
              v-if="cmd.shortcut"
              class="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-mono font-bold text-slate-600 border border-slate-200"
            >
              {{ cmd.shortcut }}
            </span>
            <span v-if="selectedIndex === idx" class="text-purple-600 text-[10px] font-bold">↵ Enter</span>
          </div>
        </button>
      </div>

      <!-- Footer Quick Tips -->
      <div class="flex items-center justify-between px-4 py-2 border-t border-slate-100 bg-slate-50 text-[11px] text-slate-500">
        <div class="flex items-center gap-3">
          <span>↑↓ Navigasi</span>
          <span>↵ Pilih</span>
          <span>ESC Tutup</span>
        </div>
        <span class="font-bold text-purple-700">Second Brain Command Cockpit</span>
      </div>
    </div>
  </div>
</template>
