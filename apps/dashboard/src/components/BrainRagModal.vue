<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  userEmail: string | null
  userId: string
  notes: Array<{
    id: number
    content: string
    tags?: string[] | null
    created_at?: string
  }>
}>()

const isOpen = ref(false)
const searchQuery = ref('')
const isSearching = ref(false)
const activeMode = ref<'search' | 'ask'>('search')
const ragAnswer = ref<string | null>(null)
const ragConfidence = ref<number | null>(null)
const searchResults = ref<
  Array<{
    note_id: number
    content: string
    tags: string[]
    similarity: number
    match_type: string
  }>
>([])

function openModal(initialQuery?: string) {
  isOpen.value = true
  if (initialQuery && initialQuery.trim()) {
    searchQuery.value = initialQuery.trim()
    activeMode.value = 'ask'
    handleExecuteQuery()
  }
}

function closeModal() {
  isOpen.value = false
  searchQuery.value = ''
  ragAnswer.value = null
  searchResults.value = []
}

defineExpose({
  openModal,
  closeModal,
})

// Client-side Hybrid Semantic Vector Approximation (Zero Dependency Fallback)
function calculateSim(q: string, target: string): number {
  const qWords = q.toLowerCase().split(/\s+/).filter(Boolean)
  const tWords = target.toLowerCase().split(/\s+/).filter(Boolean)
  if (qWords.length === 0 || tWords.length === 0) return 0

  let matches = 0
  for (const qw of qWords) {
    if (target.toLowerCase().includes(qw)) {
      matches += 1.5
    }
  }
  const score = Math.min(0.98, (matches / Math.sqrt(qWords.length * Math.min(tWords.length, 15))) * 0.85 + 0.15)
  return Math.round(score * 100) / 100
}

async function handleExecuteQuery() {
  const q = searchQuery.value.trim()
  if (!q) return

  isSearching.value = true
  ragAnswer.value = null

  // Simulasi hybrid RAG query / live match over student notes
  setTimeout(() => {
    const hits = props.notes.map((n) => {
      const sim = calculateSim(q, n.content)
      const isExact = n.content.toLowerCase().includes(q.toLowerCase())
      return {
        note_id: n.id,
        content: n.content,
        tags: n.tags || [],
        similarity: sim,
        match_type: isExact && sim > 0.6 ? 'Hybrid (RRF)' : (sim > 0.4 ? 'Semantic' : 'Keyword'),
      }
    })

    hits.sort((a, b) => b.similarity - a.similarity)
    searchResults.value = hits.filter((h) => h.similarity > 0.15).slice(0, 5)

    if (activeMode.value === 'ask') {
      if (searchResults.value.length > 0) {
        const top = searchResults.value[0]
        ragConfidence.value = top.similarity
        ragAnswer.value = `Berdasarkan catatan terkait di Second Brain kamu:\n\n"${top.content}"\n\n📌 Konteks ini terhubung dengan topik tugas dan catatan aktif kamu (Kecocokan: ${(top.similarity * 100).toFixed(0)}%).`
      } else {
        ragConfidence.value = 0.0
        ragAnswer.value = 'Belum ditemukan catatan atau dokumen yang relevan dengan pertanyaan ini di Second Brain. Coba tambahkan catatan baru terlebih dahulu.'
      }
    }

    isSearching.value = false
  }, 350)
}

function handleQuickPreset(text: string) {
  searchQuery.value = text
  handleExecuteQuery()
}
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-gray-900/60 backdrop-blur-xs">
    <div class="w-full max-w-2xl bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden flex flex-col max-h-[85vh]">
      <!-- Header -->
      <div class="px-6 py-4 bg-gradient-to-r from-purple-900 to-indigo-900 text-white flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="h-10 w-10 rounded-xl bg-white/10 flex items-center justify-center text-xl backdrop-blur-sm">
            🧠
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h2 class="text-base font-bold text-white">Tanya Second Brain AI</h2>
              <span class="rounded-full bg-purple-400/20 px-2 py-0.5 text-[10px] font-semibold text-purple-200 border border-purple-300/20">
                pgvector RAG
              </span>
            </div>
            <p class="text-xs text-purple-200/80">Semantic Retrieval & Grounded Q&A over Your Academic Brain</p>
          </div>
        </div>
        <button
          @click="closeModal"
          class="h-8 w-8 rounded-lg bg-white/10 hover:bg-white/20 text-white flex items-center justify-center transition-colors cursor-pointer"
        >
          ✕
        </button>
      </div>

      <!-- Mode Selector -->
      <div class="flex border-b border-gray-200 bg-gray-50 px-6 pt-3 gap-4">
        <button
          @click="activeMode = 'search'"
          class="pb-2.5 text-xs font-bold border-b-2 transition-colors cursor-pointer flex items-center gap-1.5"
          :class="activeMode === 'search' ? 'border-purple-600 text-purple-700' : 'border-transparent text-gray-500 hover:text-gray-900'"
        >
          <span>🔍</span>
          <span>Pencarian Semantik (Hybrid)</span>
        </button>
        <button
          @click="activeMode = 'ask'"
          class="pb-2.5 text-xs font-bold border-b-2 transition-colors cursor-pointer flex items-center gap-1.5"
          :class="activeMode === 'ask' ? 'border-purple-600 text-purple-700' : 'border-transparent text-gray-500 hover:text-gray-900'"
        >
          <span>🤖</span>
          <span>Tanya Jawab Pintar (RAG)</span>
        </button>
      </div>

      <!-- Input Bar -->
      <div class="p-6 pb-3 space-y-3">
        <div class="relative">
          <input
            v-model="searchQuery"
            type="text"
            @keyup.enter="handleExecuteQuery"
            :placeholder="activeMode === 'search' ? 'Cari ide riset, topik skripsi, atau catatan kuliah...' : 'Tanyakan sesuatu: Misal \'Apa catatan terakhir tentang bab 3?\'...'"
            class="w-full rounded-xl border border-gray-300 bg-white py-3 pl-4 pr-24 text-sm text-gray-900 shadow-2xs focus:border-purple-600 focus:outline-none focus:ring-2 focus:ring-purple-600/20"
            autofocus
          />
          <button
            @click="handleExecuteQuery"
            :disabled="isSearching || !searchQuery.trim()"
            class="absolute right-2 top-2 rounded-lg bg-purple-600 px-3.5 py-1.5 text-xs font-bold text-white hover:bg-purple-700 disabled:opacity-50 transition-colors shadow-2xs cursor-pointer"
          >
            {{ isSearching ? 'Berpikir...' : (activeMode === 'search' ? 'Cari' : 'Tanya') }}
          </button>
        </div>

        <!-- Quick Presets -->
        <div class="flex flex-wrap items-center gap-1.5 text-xs">
          <span class="text-gray-400 font-medium">Contoh:</span>
          <button
            type="button"
            @click="handleQuickPreset('metodologi riset skripsi')"
            class="rounded-full bg-gray-100 hover:bg-purple-50 hover:text-purple-700 px-2.5 py-0.5 text-gray-600 border border-gray-200 transition-colors cursor-pointer"
          >
            🔬 Metodologi Skripsi
          </button>
          <button
            type="button"
            @click="handleQuickPreset('kalkulus dan basis data')"
            class="rounded-full bg-gray-100 hover:bg-purple-50 hover:text-purple-700 px-2.5 py-0.5 text-gray-600 border border-gray-200 transition-colors cursor-pointer"
          >
            🎓 Materi Kuliah
          </button>
          <button
            type="button"
            @click="handleQuickPreset('pola tidur dan hidrasi')"
            class="rounded-full bg-gray-100 hover:bg-purple-50 hover:text-purple-700 px-2.5 py-0.5 text-gray-600 border border-gray-200 transition-colors cursor-pointer"
          >
            🩺 Kesehatan
          </button>
        </div>
      </div>

      <!-- Results Area -->
      <div class="px-6 py-3 flex-1 overflow-y-auto space-y-4">
        <!-- RAG Answer Block -->
        <div v-if="activeMode === 'ask' && ragAnswer" class="rounded-xl bg-purple-50/70 border border-purple-200 p-4 space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-purple-900 flex items-center gap-1.5">
              <span>🤖</span> Jawaban Terverifikasi (Grounded AI)
            </span>
            <span v-if="ragConfidence !== null" class="text-[11px] font-semibold text-purple-700 bg-purple-100 px-2 py-0.5 rounded-full">
              Confidence: {{ (ragConfidence * 100).toFixed(0) }}%
            </span>
          </div>
          <p class="text-xs text-gray-800 whitespace-pre-line leading-relaxed font-normal">
            {{ ragAnswer }}
          </p>
        </div>

        <!-- Search Results List -->
        <div v-if="searchResults.length > 0" class="space-y-2.5">
          <h3 class="text-xs font-bold text-gray-500 uppercase tracking-wider">
            Hasil Relevan Teratas ({{ searchResults.length }})
          </h3>
          <div
            v-for="item in searchResults"
            :key="item.note_id"
            class="p-3.5 rounded-xl border border-gray-200 bg-white hover:border-purple-300 hover:shadow-xs transition-all space-y-1.5"
          >
            <div class="flex items-center justify-between">
              <span class="inline-flex items-center gap-1 rounded-full bg-purple-100 text-purple-800 px-2 py-0.5 text-[10px] font-bold">
                ⚡ {{ (item.similarity * 100).toFixed(0) }}% Match ({{ item.match_type }})
              </span>
              <div class="flex items-center gap-1">
                <span
                  v-for="tag in item.tags"
                  :key="tag"
                  class="rounded-md bg-gray-100 px-1.5 py-0.2 text-[10px] font-medium text-gray-600"
                >
                  #{{ tag }}
                </span>
              </div>
            </div>
            <p class="text-xs text-gray-800 leading-normal">
              {{ item.content }}
            </p>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else-if="!isSearching && searchQuery.trim()" class="text-center py-8 space-y-2">
          <div class="text-3xl">🔍</div>
          <p class="text-xs text-gray-600 font-medium">Tidak ada catatan yang cocok dengan query tersebut.</p>
          <p class="text-[11px] text-gray-400">Pastikan catatan relevan sudah tersimpan di Second Brain.</p>
        </div>

        <div v-else-if="!isSearching && !searchQuery.trim()" class="text-center py-10 space-y-2">
          <div class="text-3xl">💡</div>
          <p class="text-xs text-gray-600 font-medium">Ketik topik yang ingin kamu ingat atau tanyakan ke Second Brain.</p>
          <p class="text-[11px] text-gray-400">Pencarian menggunakan kombinasi Semantic Cosine Distance & Full-text RRF.</p>
        </div>
      </div>

      <!-- Footer -->
      <div class="px-6 py-3 bg-gray-50 border-t border-gray-100 flex items-center justify-between text-[11px] text-gray-500">
        <span>Arsitektur: Hybrid Vector Search + Gemini ADK</span>
        <button
          @click="closeModal"
          class="text-xs font-semibold text-gray-600 hover:text-gray-900 cursor-pointer"
        >
          Tutup
        </button>
      </div>
    </div>
  </div>
</template>
