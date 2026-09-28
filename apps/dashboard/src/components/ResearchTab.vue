<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { supabase } from '../lib/supabase'

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

const chapters = ref<ThesisChapter[]>([])
const supervisionLogs = ref<SupervisionLog[]>([])
const metrics = ref<ExperimentMetric[]>([])

const showSupervisionModal = ref(false)
const showMetricModal = ref(false)

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
async function updateChapter(chapter: ThesisChapter) {
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

// Submit Supervision Log
async function submitSupervision() {
  if (saving.value) return
  saving.value = true
  try {
    const { error } = await supabase
      .from('supervision_logs')
      .insert({
        user_id: props.userId,
        notes: supervisionForm.value.notes.trim(),
        action_items: supervisionForm.value.action_items.trim() || null,
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
  if (days <= 7) return { text: `🟢 Aman (${days} hari lalu)`, color: 'bg-emerald-50 text-emerald-800 border-emerald-200' }
  if (days <= 14) return { text: `🟡 Waktunya Jadwalkan (${days} hari lalu)`, color: 'bg-amber-50 text-amber-800 border-amber-200' }
  return { text: `🔴 Peringatan: ${days} hari tanpa bimbingan!`, color: 'bg-rose-50 text-rose-800 border-rose-200' }
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
            Pantau progres penulisan 5 bab naskah skripsi, log interaktif arahan dospem, dan tabel komparasi metrik eksperimen AI.
          </p>
        </div>
        <div class="flex flex-wrap gap-2">
          <button
            @click="showSupervisionModal = true"
            class="inline-flex items-center gap-1.5 rounded-xl bg-gray-900 px-3.5 py-2 text-xs font-semibold text-white shadow-xs hover:bg-gray-800 transition-colors"
          >
            <span>👨‍🏫</span>
            <span>Catat Bimbingan</span>
          </button>
          <button
            @click="showMetricModal = true"
            class="inline-flex items-center gap-1.5 rounded-xl border border-gray-300 bg-white px-3.5 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <span>🧪</span>
            <span>Benchmark Model</span>
          </button>
        </div>
      </div>
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
            <p class="text-xs text-gray-500 mt-0.5">Geser persentase atau perbarui status tiap bab naskah secara realtime.</p>
          </div>
          <div class="flex items-center gap-3">
            <span class="text-xs font-semibold text-gray-600">Total Progres:</span>
            <span class="text-lg font-extrabold text-purple-700">{{ totalThesisProgress }}%</span>
          </div>
        </div>

        <!-- Master Progress Bar -->
        <div class="mt-4 h-3 w-full rounded-full bg-gray-100 overflow-hidden">
          <div
            class="h-full rounded-full bg-purple-600 transition-all duration-300"
            :style="{ width: `${totalThesisProgress}%` }"
          ></div>
        </div>

        <!-- Chapters List -->
        <div class="mt-5 space-y-3">
          <div
            v-for="chap in chapters"
            :key="chap.id"
            class="rounded-xl border border-gray-200 p-4 bg-gray-50/50 flex flex-col md:flex-row md:items-center justify-between gap-3"
          >
            <div class="min-w-56">
              <div class="flex items-center gap-2">
                <span class="text-xs font-bold text-gray-900">Bab {{ chap.chapter_num }}: {{ chap.title }}</span>
              </div>
              <div class="text-[11px] text-gray-400 mt-0.5">
                Terakhir diperbarui: {{ new Date(chap.updated_at).toLocaleDateString('id-ID', { day: 'numeric', month: 'short' }) }}
              </div>
            </div>

            <!-- Status Dropdown & Slider -->
            <div class="flex flex-1 flex-col sm:flex-row items-center gap-3">
              <select
                v-model="chap.status"
                @change="updateChapter(chap)"
                class="w-full sm:w-40 rounded-lg border border-gray-300 bg-white p-1.5 text-xs font-medium text-gray-700 focus:outline-none focus:ring-1 focus:ring-purple-500"
              >
                <option value="Belum Mulai">⚪ Belum Mulai</option>
                <option value="Drafting">🔵 Drafting</option>
                <option value="Revisi Dospem">🟡 Revisi Dospem</option>
                <option value="ACC / Selesai">🟢 ACC / Selesai</option>
              </select>

              <div class="flex-1 flex items-center gap-2.5 w-full">
                <input
                  v-model.number="chap.progress"
                  @change="updateChapter(chap)"
                  type="range"
                  min="0"
                  max="100"
                  step="5"
                  class="w-full accent-purple-600 cursor-pointer"
                />
                <span class="text-xs font-mono font-bold text-gray-700 w-10 text-right">{{ chap.progress }}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 2. Supervision Logbook & Anti-Ghosting Radar -->
      <div class="grid grid-cols-1 gap-6 md:grid-cols-2">
        <div class="rounded-2xl border border-gray-200 bg-white p-5 shadow-xs sm:p-6 flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between pb-3 border-b border-gray-100">
              <div class="flex items-center gap-2">
                <span class="text-xl">👨‍🏫</span>
                <h3 class="text-sm font-bold text-gray-900">Catatan Bimbingan Dospem</h3>
              </div>
              <span
                class="text-xs font-semibold px-2.5 py-0.5 rounded-full border"
                :class="antiGhostingStatus.color"
              >
                {{ antiGhostingStatus.text }}
              </span>
            </div>

            <div v-if="supervisionLogs.length === 0" class="py-8 text-center text-xs text-gray-400">
              Belum ada catatan bimbingan. Klik "Catat Bimbingan" untuk menambahkan.
            </div>

            <div v-else class="mt-4 space-y-3 max-h-96 overflow-y-auto pr-1">
              <div
                v-for="log in supervisionLogs"
                :key="log.id"
                class="rounded-xl border border-gray-200 p-3.5 bg-gray-50/60 space-y-2"
              >
                <div class="flex items-center justify-between text-[11px] text-gray-500">
                  <span class="font-bold text-gray-800">
                    📅 {{ new Date(log.created_at).toLocaleDateString('id-ID', { weekday: 'long', day: 'numeric', month: 'short' }) }}
                  </span>
                </div>
                <div class="text-xs text-gray-700 whitespace-pre-wrap leading-relaxed">
                  {{ log.notes }}
                </div>
                <div v-if="log.action_items" class="pt-2 border-t border-gray-200/60 text-[11px]">
                  <span class="font-bold text-purple-700">Action Items:</span>
                  <p class="text-gray-600 mt-0.5 whitespace-pre-wrap">{{ log.action_items }}</p>
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
              <button
                @click="showMetricModal = true"
                class="text-xs font-semibold text-purple-600 hover:text-purple-800"
              >
                + Tambah Hasil
              </button>
            </div>

            <div v-if="metrics.length === 0" class="py-8 text-center text-xs text-gray-400">
              Belum ada log eksperimen model.
            </div>

            <div v-else class="mt-4 space-y-3 max-h-96 overflow-y-auto pr-1">
              <div
                v-for="met in metrics"
                :key="met.id"
                class="rounded-xl border border-gray-200 p-3.5 bg-gray-50/60 space-y-1.5"
              >
                <div class="flex items-center justify-between">
                  <span class="text-xs font-bold text-gray-900">{{ met.model_name }}</span>
                  <span class="text-[10px] text-gray-400">{{ new Date(met.created_at).toLocaleDateString('id-ID', { day: 'numeric', month: 'short' }) }}</span>
                </div>
                <div class="text-xs text-purple-900 font-mono bg-purple-50 p-2 rounded-lg border border-purple-100">
                  {{ met.metrics_summary }}
                </div>
                <div v-if="met.parameters" class="text-[11px] text-gray-500">
                  ⚙️ <span class="font-medium">Params:</span> {{ met.parameters }}
                </div>
              </div>
            </div>
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
          <button @click="showSupervisionModal = false" class="text-gray-400 hover:text-gray-600 text-sm">✕</button>
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
            <label class="block font-semibold text-gray-700 mb-1">Action Items / Daftar Revisi</label>
            <textarea
              v-model="supervisionForm.action_items"
              rows="3"
              placeholder="Contoh: [1] Cari 3 paper IEEE 2024&#10;[2] Tambahkan tabel komparasi algoritma"
              class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-gray-900 focus:outline-none"
            ></textarea>
          </div>

          <div class="pt-3 flex gap-2 justify-end">
            <button
              type="button"
              @click="showSupervisionModal = false"
              class="rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-semibold text-gray-700 hover:bg-gray-50"
            >
              Batal
            </button>
            <button
              type="submit"
              :disabled="saving"
              class="rounded-lg bg-gray-900 px-4 py-1.5 text-xs font-semibold text-white shadow-xs hover:bg-gray-800 disabled:opacity-50"
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
          <button @click="showMetricModal = false" class="text-gray-400 hover:text-gray-600 text-sm">✕</button>
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
            <label class="block font-semibold text-gray-700 mb-1">Ringkasan Metrik</label>
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
              class="rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-semibold text-gray-700 hover:bg-gray-50"
            >
              Batal
            </button>
            <button
              type="submit"
              :disabled="saving"
              class="rounded-lg bg-gray-900 px-4 py-1.5 text-xs font-semibold text-white shadow-xs hover:bg-gray-800 disabled:opacity-50"
            >
              {{ saving ? 'Menyimpan...' : 'Simpan Metrik' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
