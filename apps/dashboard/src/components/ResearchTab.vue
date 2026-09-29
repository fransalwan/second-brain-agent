<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { supabase } from '../lib/supabase'
import DospemFollowupModal from './DospemFollowupModal.vue'

const props = defineProps<{
  userId: string
}>()

interface ThesisChapter {
  id: number
  chapter_num: number
  title: string
  status: string
  progress: number
  updated_at: string
}

interface SupervisionLog {
  id: number
  notes: string
  action_items: string | null
  created_at: string
}

interface ExperimentMetric {
  id: number
  model_name: string
  metrics_summary: string
  parameters: string | null
  created_at: string
}

const loading = ref(true)
const saving = ref(false)
const copyNotification = ref<string | null>(null)

const chapters = ref<ThesisChapter[]>([])
const supervisionLogs = ref<SupervisionLog[]>([])
const metrics = ref<ExperimentMetric[]>([])

const showSupervisionModal = ref(false)
const showMetricModal = ref(false)
const dospemModalRef = ref<InstanceType<typeof DospemFollowupModal> | null>(null)

function openDospemModal(template?: 'request_schedule' | 'submit_draft' | 'gentle_followup' | 'exam_approval') {
  dospemModalRef.value?.openModal(template)
}

// Forms
const supervisionForm = ref({
  notes: '',
  action_items: '',
})

const metricForm = ref({
  model_name: '',
  metrics_summary: '',
  parameters: '',
})

// Action items interactive state per supervision log
const parsedActionItems = ref<Record<number, Array<{ text: string, done: boolean }>>>({})

function parseActionItems(log: SupervisionLog) {
  if (!log.action_items) return []
  return log.action_items.split('\n').filter(line => line.trim().length > 0).map(line => {
    const isDone = line.trim().startsWith('[x]') || line.trim().startsWith('[X]')
    const text = line.replace(/^\[[ xX]\]\s*/, '').trim()
    return { text, done: isDone }
  })
}

async function fetchResearchData() {
  loading.value = true
  try {
    // 1. Thesis chapters
    const { data: chapData } = await supabase
      .from('thesis_chapters')
      .select('*')
      .eq('user_id', props.userId)
      .order('chapter_num', { ascending: true })

    chapters.value = chapData || []

    // 2. Supervision logs
    const { data: supData } = await supabase
      .from('supervision_logs')
      .select('*')
      .eq('user_id', props.userId)
      .order('created_at', { ascending: false })

    supervisionLogs.value = supData || []
    supervisionLogs.value.forEach(log => {
      parsedActionItems.value[log.id] = parseActionItems(log)
    })

    // 3. Experiment metrics
    const { data: metData } = await supabase
      .from('experiment_metrics')
      .select('*')
      .eq('user_id', props.userId)
      .order('created_at', { ascending: false })

    metrics.value = metData || []
  } catch (err) {
    console.error('Gagal mengambil data riset:', err)
  } finally {
    loading.value = false
  }
}

// Chapter update
async function updateChapter(chapter: ThesisChapter, newProgress?: number) {
  if (newProgress !== undefined) {
    chapter.progress = Math.max(0, Math.min(100, newProgress))
    if (chapter.progress === 100) {
      chapter.status = 'ACC / Selesai'
    } else if (chapter.progress > 0 && chapter.status === 'Belum Mulai') {
      chapter.status = 'Drafting'
    }
  }

  try {
    await supabase
      .from('thesis_chapters')
      .update({
        status: chapter.status,
        progress: chapter.progress,
        updated_at: new Date().toISOString(),
      })
      .eq('id', chapter.id)
  } catch (err) {
    console.error('Gagal update bab skripsi:', err)
  }
}

// Toggle action item
async function toggleActionItem(logId: number, itemIndex: number) {
  const items = parsedActionItems.value[logId]
  if (!items || !items[itemIndex]) return

  items[itemIndex].done = !items[itemIndex].done

  // Re-encode back to string
  const rawText = items.map(it => `[${it.done ? 'x' : ' '}] ${it.text}`).join('\n')

  try {
    await supabase
      .from('supervision_logs')
      .update({ action_items: rawText })
      .eq('id', logId)

    const targetLog = supervisionLogs.value.find(l => l.id === logId)
    if (targetLog) targetLog.action_items = rawText
  } catch (err) {
    console.error('Gagal update action item:', err)
  }
}

// Submit Supervision Log
async function submitSupervision() {
  if (saving.value) return
  saving.value = true
  try {
    // Format action items
    const rawAction = supervisionForm.value.action_items.trim()
    const formattedAction = rawAction ? rawAction.split('\n').map(l => {
      if (l.trim().startsWith('[')) return l.trim()
      return `[ ] ${l.trim()}`
    }).join('\n') : null

    const { error } = await supabase
      .from('supervision_logs')
      .insert({
        user_id: props.userId,
        notes: supervisionForm.value.notes.trim(),
        action_items: formattedAction,
      })

    if (!error) {
      showSupervisionModal.value = false
      supervisionForm.value = { notes: '', action_items: '' }
      await fetchResearchData()
    }
  } catch (err) {
    console.error('Gagal mencatat bimbingan:', err)
  } finally {
    saving.value = false
  }
}

async function deleteSupervision(id: number) {
  if (!confirm('Hapus catatan bimbingan ini?')) return
  try {
    await supabase.from('supervision_logs').delete().eq('id', id)
    supervisionLogs.value = supervisionLogs.value.filter(s => s.id !== id)
  } catch (err) {
    console.error('Gagal menghapus log bimbingan:', err)
  }
}

// Submit Metric
async function submitMetric() {
  if (saving.value) return
  saving.value = true
  try {
    const { error } = await supabase
      .from('experiment_metrics')
      .insert({
        user_id: props.userId,
        model_name: metricForm.value.model_name.trim(),
        metrics_summary: metricForm.value.metrics_summary.trim(),
        parameters: metricForm.value.parameters.trim() || null,
      })

    if (!error) {
      showMetricModal.value = false
      metricForm.value = { model_name: '', metrics_summary: '', parameters: '' }
      await fetchResearchData()
    }
  } catch (err) {
    console.error('Gagal mencatat metrik model:', err)
  } finally {
    saving.value = false
  }
}

async function deleteMetric(id: number) {
  if (!confirm('Hapus hasil benchmark ini?')) return
  try {
    await supabase.from('experiment_metrics').delete().eq('id', id)
    metrics.value = metrics.value.filter(m => m.id !== id)
  } catch (err) {
    console.error('Gagal menghapus metrik:', err)
  }
}

// Export Table Functions (LaTeX & Markdown)
function copyLatexTable() {
  if (metrics.value.length === 0) return
  let latex = '\\begin{table}[h]\n\\centering\n\\begin{tabular}{|l|l|l|}\n\\hline\n\\textbf{Model} & \\textbf{Metrics} & \\textbf{Parameters} \\\\\n\\hline\n'
  metrics.value.forEach(m => {
    const name = m.model_name.replace(/_/g, '\\_')
    const met = m.metrics_summary.replace(/_/g, '\\_')
    const par = (m.parameters || '-').replace(/_/g, '\\_')
    latex += `${name} & ${met} & ${par} \\\\\n\\hline\n`
  })
  latex += '\\end{tabular}\n\\caption{Tabel Perbandingan Hasil Eksperimen Model AI}\n\\label{tab:model_experiments}\n\\end{table}'

  navigator.clipboard.writeText(latex)
  copyNotification.value = '✓ Format tabel LaTeX berhasil disalin ke clipboard!'
  setTimeout(() => { copyNotification.value = null }, 3500)
}

function copyMarkdownTable() {
  if (metrics.value.length === 0) return
  let md = '| Model Architecture | Evaluation Metrics | Parameters |\n| :--- | :--- | :--- |\n'
  metrics.value.forEach(m => {
    md += `| **${m.model_name}** | ${m.metrics_summary} | ${m.parameters || '-'} |\n`
  })
  navigator.clipboard.writeText(md)
  copyNotification.value = '✓ Format tabel Markdown berhasil disalin ke clipboard!'
  setTimeout(() => { copyNotification.value = null }, 3500)
}

// Computeds
const totalThesisProgress = computed(() => {
  if (chapters.value.length === 0) return 0
  const sum = chapters.value.reduce((acc, c) => acc + c.progress, 0)
  return Math.round(sum / chapters.value.length)
})

const daysSinceLastSupervision = computed(() => {
  if (supervisionLogs.value.length === 0) return null
  const latestDate = new Date(supervisionLogs.value[0].created_at)
  const now = new Date()
  return Math.floor((now.getTime() - latestDate.getTime()) / (1000 * 60 * 60 * 24))
})

const antiGhostingStatus = computed(() => {
  const days = daysSinceLastSupervision.value
  if (days === null) return { text: 'Belum pernah bimbingan', color: 'bg-gray-100 text-gray-600 border-gray-200' }
  if (days <= 7) return { text: `🟢 Konsisten (${days} hari lalu)`, color: 'bg-emerald-50 text-emerald-800 border-emerald-300 font-bold' }
  if (days <= 14) return { text: `🟡 Waktunya Hubungi Dosen (${days} hari lalu)`, color: 'bg-amber-50 text-amber-800 border-amber-300 font-bold' }
  return { text: `🔴 Peringatan: ${days} hari tanpa bimbingan!`, color: 'bg-rose-50 text-rose-800 border-rose-300 font-bold animate-pulse' }
})

onMounted(() => {
  fetchResearchData()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header Banner -->
    <div class="rounded-2xl border border-gray-200 bg-white p-5 shadow-xs sm:p-6">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div class="flex items-center gap-2">
            <span class="text-2xl">🔬</span>
            <h2 class="text-lg font-bold text-gray-900 sm:text-xl">Research Lab &amp; Thesis Progression</h2>
            <span class="rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-semibold text-purple-800">Prioritas #3</span>
          </div>
          <p class="mt-1 text-xs text-gray-500 sm:text-sm">
            Pantau progres penulisan 5 bab naskah skripsi, log interaktif arahan dospem (anti-ghosting), dan benchmark metrik eksperimen AI.
          </p>
        </div>
        <div class="flex flex-wrap gap-2">
          <button
            type="button"
            @click="openDospemModal('request_schedule')"
            class="inline-flex items-center gap-1.5 rounded-xl border border-purple-200 bg-purple-50 px-3.5 py-2 text-xs font-semibold text-purple-900 hover:bg-purple-100 transition-colors cursor-pointer"
          >
            <span>💬</span>
            <span>Draft WA Dospem</span>
          </button>
          <button
            @click="showSupervisionModal = true"
            class="inline-flex items-center gap-1.5 rounded-xl bg-gray-900 px-3.5 py-2 text-xs font-semibold text-white shadow-xs hover:bg-gray-800 transition-colors cursor-pointer"
          >
            <span>👨‍🏫</span>
            <span>Catat Bimbingan</span>
          </button>
          <button
            @click="showMetricModal = true"
            class="inline-flex items-center gap-1.5 rounded-xl border border-gray-300 bg-white px-3.5 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50 transition-colors cursor-pointer"
          >
            <span>🧪</span>
            <span>Benchmark Model</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Toast Notification Copy -->
    <div
      v-if="copyNotification"
      class="fixed bottom-5 right-5 z-50 rounded-xl bg-gray-900 text-white px-4 py-2.5 text-xs shadow-xl flex items-center gap-2 border border-gray-700 animate-bounce"
    >
      <span>📋</span>
      <span>{{ copyNotification }}</span>
    </div>

    <div v-if="loading" class="flex justify-center py-12">
      <div class="h-8 w-8 animate-spin rounded-full border-4 border-gray-900 border-t-transparent"></div>
    </div>

    <div v-else class="space-y-6">
      <!-- 1. Thesis Chapter Progress Tracker -->
      <div class="rounded-2xl border border-gray-200 bg-white p-5 shadow-xs sm:p-6">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-4 border-b border-gray-100">
          <div>
            <div class="flex items-center gap-2">
              <span class="text-xl">📖</span>
              <h3 class="text-sm font-bold text-gray-900">Progres Naskah Skripsi / Thesis</h3>
            </div>
            <p class="text-xs text-gray-500 mt-0.5">Kelola status dan geser persentase tiap bab. Progres otomatis tersimpan ke cloud.</p>
          </div>
          <div class="flex items-center gap-3">
            <span class="text-xs font-semibold text-gray-600">Total Progres Naskah:</span>
            <span class="text-2xl font-black text-purple-700">{{ totalThesisProgress }}%</span>
          </div>
        </div>

        <!-- Master Progress Bar -->
        <div class="mt-4 h-3.5 w-full rounded-full bg-gray-100 overflow-hidden relative">
          <div
            class="h-full rounded-full bg-gradient-to-r from-purple-500 to-indigo-600 transition-all duration-300"
            :style="{ width: `${totalThesisProgress}%` }"
          ></div>
        </div>

        <!-- 5 Chapters Cards -->
        <div class="mt-6 space-y-3.5">
          <div
            v-for="chap in chapters"
            :key="chap.id"
            class="rounded-xl border border-gray-200 p-4 bg-gray-50/50 flex flex-col lg:flex-row lg:items-center justify-between gap-4 hover:bg-gray-50 transition-colors"
          >
            <div class="min-w-64">
              <div class="flex items-center gap-2">
                <span class="text-xs font-bold text-gray-900">Bab {{ chap.chapter_num }}: {{ chap.title }}</span>
              </div>
              <div class="text-[11px] text-gray-400 mt-0.5">
                Update: {{ new Date(chap.updated_at).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) }}
              </div>
            </div>

            <!-- Status Dropdown & Slider & Quick Presets -->
            <div class="flex flex-1 flex-col sm:flex-row items-center gap-3">
              <select
                v-model="chap.status"
                @change="updateChapter(chap)"
                class="w-full sm:w-44 rounded-lg border border-gray-300 bg-white p-1.5 text-xs font-semibold text-gray-800 focus:outline-none focus:ring-2 focus:ring-purple-500 cursor-pointer"
              >
                <option value="Belum Mulai">⚪ Belum Mulai</option>
                <option value="Drafting">🔵 Drafting Naskah</option>
                <option value="Revisi Dospem">🟡 Revisi Dospem</option>
                <option value="ACC / Selesai">🟢 ACC / Selesai</option>
              </select>

              <!-- Slider Range -->
              <div class="flex-1 flex items-center gap-2 w-full">
                <input
                  v-model.number="chap.progress"
                  @change="updateChapter(chap)"
                  type="range"
                  min="0"
                  max="100"
                  step="5"
                  class="w-full accent-purple-600 cursor-pointer"
                />
                <span class="text-xs font-mono font-bold text-gray-800 w-11 text-right shrink-0">{{ chap.progress }}%</span>
              </div>

              <!-- Quick Jump Buttons (25%, 50%, 75%, 100%) -->
              <div class="hidden md:flex items-center gap-1 shrink-0">
                <button
                  v-for="p in [25, 50, 75, 100]"
                  :key="p"
                  type="button"
                  @click="updateChapter(chap, p)"
                  class="rounded px-1.5 py-0.5 text-[10px] font-bold border border-gray-200 bg-white hover:bg-purple-50 hover:text-purple-700 hover:border-purple-300 cursor-pointer"
                >
                  {{ p }}%
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 2. Supervision Logbook & Anti-Ghosting Radar -->
      <div class="grid grid-cols-1 gap-6 md:grid-cols-2">
        <div class="rounded-2xl border border-gray-200 bg-white p-5 shadow-xs sm:p-6 flex flex-col justify-between">
          <div>
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-gray-100">
              <div class="flex items-center gap-2">
                <span class="text-xl">👨‍🏫</span>
                <h3 class="text-sm font-bold text-gray-900">Catatan Bimbingan Dospem</h3>
              </div>
              <div class="flex items-center gap-2">
                <button
                  type="button"
                  @click="openDospemModal(daysSinceLastSupervision && daysSinceLastSupervision >= 14 ? 'gentle_followup' : 'request_schedule')"
                  class="text-[11px] font-bold text-purple-700 hover:text-purple-900 cursor-pointer flex items-center gap-1 hover:underline"
                  title="Buat draf pesan chat WhatsApp ke dosen"
                >
                  <span>💬 Chat Dospem</span>
                </button>
                <span
                  class="text-xs px-2.5 py-0.5 rounded-full border shadow-2xs"
                  :class="antiGhostingStatus.color"
                >
                  {{ antiGhostingStatus.text }}
                </span>
              </div>
            </div>

            <!-- Anti-Ghosting Urgent Alert Banner (>= 14 hari) -->
            <div
              v-if="daysSinceLastSupervision !== null && daysSinceLastSupervision >= 14"
              class="mt-3 rounded-xl border border-rose-200 bg-rose-50/80 p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 animate-pulse"
            >
              <div class="flex items-center gap-2">
                <span class="text-lg">⚠️</span>
                <p class="text-xs text-rose-900 leading-snug">
                  <strong>Radar Anti-Ghosting:</strong> Sudah <strong>{{ daysSinceLastSupervision }} hari</strong> tidak bimbingan. Hubungi dospem hari ini agar skripsi tidak macet!
                </p>
              </div>
              <button
                type="button"
                @click="openDospemModal('gentle_followup')"
                class="shrink-0 rounded-lg bg-rose-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-rose-700 transition-colors cursor-pointer flex items-center justify-center gap-1.5 shadow-2xs"
              >
                <span>💬</span>
                <span>Follow-Up Santun</span>
              </button>
            </div>

            <div v-if="supervisionLogs.length === 0" class="py-8 text-center text-xs text-gray-400">
              Belum ada catatan bimbingan. Klik "Catat Bimbingan" di atas untuk menambahkan arahan dosen.
            </div>

            <div v-else class="mt-4 space-y-3.5 max-h-96 overflow-y-auto pr-1">
              <div
                v-for="log in supervisionLogs"
                :key="log.id"
                class="rounded-xl border border-gray-200 p-4 bg-gray-50/60 space-y-2.5 group hover:bg-gray-50 transition-colors"
              >
                <div class="flex items-center justify-between text-[11px] text-gray-500">
                  <span class="font-bold text-gray-800 flex items-center gap-1.5">
                    <span>📅</span>
                    <span>{{ new Date(log.created_at).toLocaleDateString('id-ID', { weekday: 'long', day: 'numeric', month: 'short', year: 'numeric' }) }}</span>
                  </span>
                  <button
                    type="button"
                    @click="deleteSupervision(log.id)"
                    class="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-rose-600 text-xs transition-opacity cursor-pointer p-0.5"
                    title="Hapus log ini"
                  >
                    🗑️
                  </button>
                </div>

                <div class="text-xs text-gray-800 whitespace-pre-wrap leading-relaxed">
                  {{ log.notes }}
                </div>

                <!-- Interactive Action Items Checklist -->
                <div v-if="parsedActionItems[log.id] && parsedActionItems[log.id].length > 0" class="pt-2.5 border-t border-gray-200 text-xs space-y-1.5">
                  <div class="font-bold text-purple-800 flex items-center justify-between text-[11px]">
                    <span>Action Items Revisi:</span>
                    <span class="font-normal text-gray-400">
                      {{ parsedActionItems[log.id].filter(i => i.done).length }}/{{ parsedActionItems[log.id].length }} Selesai
                    </span>
                  </div>
                  <div class="space-y-1">
                    <label
                      v-for="(item, idx) in parsedActionItems[log.id]"
                      :key="idx"
                      class="flex items-start gap-2 cursor-pointer p-1 rounded hover:bg-white transition-colors"
                    >
                      <input
                        type="checkbox"
                        :checked="item.done"
                        @change="toggleActionItem(log.id, idx)"
                        class="mt-0.5 h-3.5 w-3.5 rounded border-gray-300 text-purple-600 focus:ring-purple-500 cursor-pointer"
                      />
                      <span class="text-xs" :class="item.done ? 'line-through text-gray-400' : 'text-gray-700'">
                        {{ item.text }}
                      </span>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 3. Experiment Metrics & Benchmark Table -->
        <div class="rounded-2xl border border-gray-200 bg-white p-5 shadow-xs sm:p-6 flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between pb-3 border-b border-gray-100">
              <div class="flex items-center gap-2">
                <span class="text-xl">🧪</span>
                <h3 class="text-sm font-bold text-gray-900">Benchmark Model AI &amp; Metrik</h3>
              </div>
              <div class="flex items-center gap-1.5">
                <button
                  @click="copyLatexTable"
                  :disabled="metrics.length === 0"
                  class="rounded-lg border border-gray-200 bg-gray-50 hover:bg-gray-100 px-2 py-1 text-[11px] font-semibold text-gray-700 cursor-pointer disabled:opacity-40"
                  title="Salin dalam format tabel LaTeX"
                >
                  LaTeX
                </button>
                <button
                  @click="copyMarkdownTable"
                  :disabled="metrics.length === 0"
                  class="rounded-lg border border-gray-200 bg-gray-50 hover:bg-gray-100 px-2 py-1 text-[11px] font-semibold text-gray-700 cursor-pointer disabled:opacity-40"
                  title="Salin dalam format tabel Markdown"
                >
                  Markdown
                </button>
                <button
                  @click="showMetricModal = true"
                  class="rounded-lg bg-purple-600 hover:bg-purple-700 text-white px-2.5 py-1 text-[11px] font-semibold cursor-pointer"
                >
                  + Tambah
                </button>
              </div>
            </div>

            <div v-if="metrics.length === 0" class="py-8 text-center text-xs text-gray-400">
              Belum ada log benchmark model. Klik "+ Tambah" untuk memasukkan metrik.
            </div>

            <div v-else class="mt-4 space-y-3 max-h-96 overflow-y-auto pr-1">
              <div
                v-for="met in metrics"
                :key="met.id"
                class="rounded-xl border border-gray-200 p-3.5 bg-gray-50/60 space-y-2 group hover:bg-gray-50 transition-colors"
              >
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <span class="text-xs font-bold text-gray-900">{{ met.model_name }}</span>
                    <span v-if="met.model_name.toLowerCase().includes('fine-tune') || met.model_name.toLowerCase().includes('transformer')" class="rounded-full bg-amber-100 text-amber-900 px-1.5 py-0.2 text-[10px] font-bold">
                      ⭐ Champion
                    </span>
                  </div>
                  <div class="flex items-center gap-2">
                    <span class="text-[10px] text-gray-400">
                      {{ new Date(met.created_at).toLocaleDateString('id-ID', { day: 'numeric', month: 'short' }) }}
                    </span>
                    <button
                      type="button"
                      @click="deleteMetric(met.id)"
                      class="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-rose-600 text-xs transition-opacity cursor-pointer"
                      title="Hapus metrik ini"
                    >
                      🗑️
                    </button>
                  </div>
                </div>

                <div class="text-xs text-purple-900 font-mono bg-purple-50 p-2.5 rounded-lg border border-purple-100 font-semibold">
                  {{ met.metrics_summary }}
                </div>

                <div v-if="met.parameters" class="text-[11px] text-gray-500">
                  ⚙️ <span class="font-medium text-gray-700">Hyperparams:</span> {{ met.parameters }}
                </div>
              </div>
            </div>
          </div>

          <div class="mt-4 pt-3 border-t border-gray-100 text-center">
            <span class="text-[11px] text-gray-400">💡 Gunakan tombol <strong>LaTeX</strong> untuk langsung paste tabel komparasi ke Bab 4 naskah skripsi!</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Form Catat Bimbingan -->
    <div
      v-if="showSupervisionModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/40 backdrop-blur-xs p-4"
    >
      <div class="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl border border-gray-200 space-y-4">
        <div class="flex items-center justify-between pb-3 border-b border-gray-100">
          <div class="flex items-center gap-2">
            <span class="text-xl">👨‍🏫</span>
            <h3 class="text-sm font-bold text-gray-900">Catat Arahan &amp; Bimbingan Dospem</h3>
          </div>
          <button @click="showSupervisionModal = false" class="text-gray-400 hover:text-gray-600 text-sm cursor-pointer">✕</button>
        </div>

        <form @submit.prevent="submitSupervision" class="space-y-3 text-xs">
          <div>
            <label class="block font-semibold text-gray-700 mb-1">Catatan &amp; Feedback Dosen</label>
            <textarea
              v-model="supervisionForm.notes"
              rows="4"
              required
              placeholder="Contoh: Bab 2 perlu ditambahkan perbandingan metode evaluasi F1-Score vs Precision pada imbalanced data."
              class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-gray-900 focus:outline-none"
            ></textarea>
          </div>

          <div>
            <label class="block font-semibold text-gray-700 mb-1">Action Items / Poin Revisi (1 baris per item)</label>
            <textarea
              v-model="supervisionForm.action_items"
              rows="3"
              placeholder="Cari 3 paper IEEE 2024 terkait baseline&#10;Tambahkan tabel komparasi metrik evaluasi&#10;Perbaiki sitasi APA style"
              class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-gray-900 focus:outline-none"
            ></textarea>
          </div>

          <div class="pt-3 flex gap-2 justify-end">
            <button
              type="button"
              @click="showSupervisionModal = false"
              class="rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-semibold text-gray-700 hover:bg-gray-50 cursor-pointer"
            >
              Batal
            </button>
            <button
              type="submit"
              :disabled="saving"
              class="rounded-lg bg-gray-900 px-4 py-1.5 text-xs font-semibold text-white shadow-xs hover:bg-gray-800 disabled:opacity-50 cursor-pointer"
            >
              {{ saving ? 'Menyimpan...' : 'Simpan Bimbingan' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal Form Catat Metrik Model AI -->
    <div
      v-if="showMetricModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/40 backdrop-blur-xs p-4"
    >
      <div class="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl border border-gray-200 space-y-4">
        <div class="flex items-center justify-between pb-3 border-b border-gray-100">
          <div class="flex items-center gap-2">
            <span class="text-xl">🧪</span>
            <h3 class="text-sm font-bold text-gray-900">Catat Benchmark Model AI</h3>
          </div>
          <button @click="showMetricModal = false" class="text-gray-400 hover:text-gray-600 text-sm cursor-pointer">✕</button>
        </div>

        <form @submit.prevent="submitMetric" class="space-y-3 text-xs">
          <div>
            <label class="block font-semibold text-gray-700 mb-1">Nama Model / Arsitektur</label>
            <input
              v-model="metricForm.model_name"
              type="text"
              required
              placeholder="Contoh: Fine-tuned RoBERTa + LoRA"
              class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-gray-900 focus:outline-none"
            />
          </div>

          <div>
            <label class="block font-semibold text-gray-700 mb-1">Ringkasan Metrik (F1, Accuracy, Latency, Loss)</label>
            <input
              v-model="metricForm.metrics_summary"
              type="text"
              required
              placeholder="Contoh: Accuracy: 94.2% | F1: 0.938 | Latency: 45ms"
              class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-gray-900 focus:outline-none"
            />
          </div>

          <div>
            <label class="block font-semibold text-gray-700 mb-1">Parameter Pelatihan (Opsional)</label>
            <input
              v-model="metricForm.parameters"
              type="text"
              placeholder="Contoh: Epoch: 20, LR: 2e-5, Batch: 32, Optimizer: AdamW"
              class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-gray-900 focus:outline-none"
            />
          </div>

          <div class="pt-3 flex gap-2 justify-end">
            <button
              type="button"
              @click="showMetricModal = false"
              class="rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-semibold text-gray-700 hover:bg-gray-50 cursor-pointer"
            >
              Batal
            </button>
            <button
              type="submit"
              :disabled="saving"
              class="rounded-lg bg-gray-900 px-4 py-1.5 text-xs font-semibold text-white shadow-xs hover:bg-gray-800 disabled:opacity-50 cursor-pointer"
            >
              {{ saving ? 'Menyimpan...' : 'Simpan Metrik' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Dospem WhatsApp Generator Modal -->
    <DospemFollowupModal
      ref="dospemModalRef"
      :user-id="props.userId"
      :last-supervision-days="daysSinceLastSupervision"
      :active-chapters="chapters"
    />
  </div>
</template>
