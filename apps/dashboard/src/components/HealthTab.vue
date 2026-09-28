<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { supabase } from '../lib/supabase'

const props = defineProps<{
  userId: string
}>()

interface SleepLog {
  id: number
  date: string
  hours: number
  quality: string
  notes: string | null
}

interface HydrationLog {
  id: number
  date: string
  glasses: number
  target_glasses: number
}

interface HealthCheckLog {
  id: number
  date: string
  took_vitamin: boolean
  did_stretch: boolean
  burnout_score: number
  notes: string | null
}

const loading = ref(true)
const saving = ref(false)
const showSleepModal = ref(false)

// Data states
const todayIso = new Date().toISOString().split('T')[0]
const hydration = ref<HydrationLog | null>(null)
const sleepLogs = ref<SleepLog[]>([])
const healthCheck = ref<HealthCheckLog | null>(null)

// Sleep Modal Form
const sleepForm = ref({
  date: todayIso,
  hours: 7.0,
  quality: 'Nyenyak',
  notes: '',
})

async function fetchHealthData() {
  loading.value = true
  try {
    // 1. Hydration today
    const { data: hydraData } = await supabase
      .from('hydration_logs')
      .select('*')
      .eq('user_id', props.userId)
      .eq('date', todayIso)
      .maybeSingle()

    hydration.value = hydraData

    // 2. Sleep logs last 7 days
    const { data: sleepData } = await supabase
      .from('sleep_logs')
      .select('*')
      .eq('user_id', props.userId)
      .order('date', { ascending: false })
      .limit(7)

    sleepLogs.value = sleepData || []

    // 3. Health check today
    const { data: hcData } = await supabase
      .from('health_check_logs')
      .select('*')
      .eq('user_id', props.userId)
      .eq('date', todayIso)
      .maybeSingle()

    healthCheck.value = hcData
  } catch (err) {
    console.error('Gagal mengambil data kesehatan:', err)
  } finally {
    loading.value = false
  }
}

// Hydration actions
async function adjustHydration(delta: number) {
  if (saving.value) return
  saving.value = true
  try {
    const currentGlasses = hydration.value?.glasses ?? 0
    const newGlasses = Math.max(0, currentGlasses + delta)
    const target = hydration.value?.target_glasses ?? 8

    const { data, error } = await supabase
      .from('hydration_logs')
      .upsert({
        user_id: props.userId,
        date: todayIso,
        glasses: newGlasses,
        target_glasses: target,
      }, { onConflict: 'user_id,date' })
      .select()
      .single()

    if (!error && data) {
      hydration.value = data
    }
  } catch (err) {
    console.error('Gagal update hidrasi:', err)
  } finally {
    saving.value = false
  }
}

// Health check toggles
async function toggleHealthCheck(field: 'took_vitamin' | 'did_stretch') {
  if (saving.value) return
  saving.value = true
  try {
    const current = healthCheck.value
    const updatedVitamin = field === 'took_vitamin' ? !current?.took_vitamin : (current?.took_vitamin ?? false)
    const updatedStretch = field === 'did_stretch' ? !current?.did_stretch : (current?.did_stretch ?? false)
    const burnout = current?.burnout_score ?? 20

    const { data, error } = await supabase
      .from('health_check_logs')
      .upsert({
        user_id: props.userId,
        date: todayIso,
        took_vitamin: updatedVitamin,
        did_stretch: updatedStretch,
        burnout_score: burnout,
      }, { onConflict: 'user_id,date' })
      .select()
      .single()

    if (!error && data) {
      healthCheck.value = data
    }
  } catch (err) {
    console.error('Gagal update health check:', err)
  } finally {
    saving.value = false
  }
}

// Sleep Modal Submit
async function submitSleepLog() {
  if (saving.value) return
  saving.value = true
  try {
    const { error } = await supabase
      .from('sleep_logs')
      .upsert({
        user_id: props.userId,
        date: sleepForm.value.date,
        hours: sleepForm.value.hours,
        quality: sleepForm.value.quality,
        notes: sleepForm.value.notes.trim() || null,
      }, { onConflict: 'user_id,date' })

    if (!error) {
      showSleepModal.value = false
      await fetchHealthData()
    }
  } catch (err) {
    console.error('Gagal menyimpan log tidur:', err)
  } finally {
    saving.value = false
  }
}

// Computed
const hydrationPercent = computed(() => {
  const g = hydration.value?.glasses ?? 0
  const t = hydration.value?.target_glasses ?? 8
  return Math.min(100, Math.round((g / t) * 100))
})

const averageSleepHours = computed(() => {
  if (sleepLogs.value.length === 0) return 0
  const total = sleepLogs.value.reduce((acc, s) => acc + Number(s.hours), 0)
  return +(total / sleepLogs.value.length).toFixed(1)
})

const latestSleep = computed(() => {
  return sleepLogs.value[0] || null
})

const burnoutScore = computed(() => {
  return healthCheck.value?.burnout_score ?? 20
})

const burnoutBadge = computed(() => {
  const score = burnoutScore.value
  if (score <= 30) return { label: 'Rendah (Kondisi Prima 🟢)', color: 'text-emerald-700 bg-emerald-50 border-emerald-200' }
  if (score <= 60) return { label: 'Sedang (Perlu Jeda 🟡)', color: 'text-amber-700 bg-amber-50 border-amber-200' }
  return { label: 'Tinggi (Kritis Burnout 🔴)', color: 'text-rose-700 bg-rose-50 border-rose-200' }
})

onMounted(() => {
  fetchHealthData()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header Banner -->
    <div class="rounded-2xl border border-gray-200 bg-white p-5 shadow-xs sm:p-6">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div class="flex items-center gap-2">
            <span class="text-2xl">🩺</span>
            <h2 class="text-lg font-bold text-gray-900 sm:text-xl">Radar Kesehatan & Energi Harian</h2>
            <span class="rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-800">Prioritas #1</span>
          </div>
          <p class="mt-1 text-xs text-gray-500 sm:text-sm">
            Pantau asupan hidrasi, kualitas tidur, dan status pemulihan fisik untuk menjaga performa optimal.
          </p>
        </div>
        <button
          @click="showSleepModal = true"
          class="inline-flex items-center justify-center gap-1.5 rounded-xl bg-gray-900 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-gray-800 transition-colors"
        >
          <span>➕</span>
          <span>Catat Tidur</span>
        </button>
      </div>
    </div>

    <div v-if="loading" class="flex justify-center py-12">
      <div class="h-8 w-8 animate-spin rounded-full border-4 border-gray-900 border-t-transparent"></div>
    </div>

    <div v-else class="grid grid-cols-1 gap-6 md:grid-cols-2">
      <!-- 1. Hydration Tracker Card -->
      <div class="rounded-2xl border border-gray-200 bg-white p-5 shadow-xs sm:p-6 flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span class="text-xl">💧</span>
              <h3 class="text-sm font-bold text-gray-900">Hydration Tracker (Hari Ini)</h3>
            </div>
            <span class="text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full border border-blue-200">
              {{ (hydration?.glasses || 0) * 250 }} / {{ (hydration?.target_glasses || 8) * 250 }} ml
            </span>
          </div>

          <div class="mt-5">
            <div class="flex justify-between items-baseline mb-2">
              <span class="text-3xl font-extrabold text-gray-900">{{ hydration?.glasses || 0 }} <span class="text-base font-normal text-gray-500">/ {{ hydration?.target_glasses || 8 }} Gelas</span></span>
              <span class="text-sm font-bold text-blue-600">{{ hydrationPercent }}%</span>
            </div>
            <!-- Progress Bar -->
            <div class="h-3 w-full rounded-full bg-gray-100 overflow-hidden">
              <div
                class="h-full rounded-full bg-blue-500 transition-all duration-300"
                :style="{ width: `${hydrationPercent}%` }"
              ></div>
            </div>
          </div>

          <!-- Glass Icons Visualizer -->
          <div class="mt-5 grid grid-cols-8 gap-1.5">
            <div
              v-for="i in (hydration?.target_glasses || 8)"
              :key="i"
              class="h-10 rounded-lg flex items-center justify-center text-sm border transition-all"
              :class="i <= (hydration?.glasses || 0) ? 'bg-blue-500 text-white border-blue-600 shadow-xs' : 'bg-gray-50 text-gray-300 border-gray-200'"
            >
              🥛
            </div>
          </div>
        </div>

        <div class="mt-6 flex items-center gap-3 pt-4 border-t border-gray-100">
          <button
            @click="adjustHydration(-1)"
            :disabled="saving || (hydration?.glasses || 0) <= 0"
            class="flex-1 rounded-xl border border-gray-300 bg-white py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-40 transition-colors"
          >
            - 1 Gelas
          </button>
          <button
            @click="adjustHydration(1)"
            :disabled="saving"
            class="flex-2 rounded-xl bg-blue-600 py-2 text-xs font-semibold text-white shadow-xs hover:bg-blue-700 disabled:opacity-50 transition-colors flex items-center justify-center gap-1.5"
          >
            <span>💧</span>
            <span>+ Tambah Gelas (250ml)</span>
          </button>
        </div>
      </div>

      <!-- 2. Recovery & Burnout Radar Card -->
      <div class="rounded-2xl border border-gray-200 bg-white p-5 shadow-xs sm:p-6 flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span class="text-xl">🧘</span>
              <h3 class="text-sm font-bold text-gray-900">Recovery & Burnout Radar</h3>
            </div>
            <span
              class="text-xs font-semibold px-2 py-0.5 rounded-full border"
              :class="burnoutBadge.color"
            >
              Skor {{ burnoutScore }}/100
            </span>
          </div>

          <!-- Burnout Explanation -->
          <div class="mt-4 rounded-xl p-3.5 bg-gray-50 border border-gray-200">
            <div class="flex items-center justify-between text-xs">
              <span class="font-medium text-gray-600">Status Beban Pikiran:</span>
              <span class="font-bold text-gray-900">{{ burnoutBadge.label }}</span>
            </div>
            <p class="mt-1 text-[11px] text-gray-500">
              Dihitung berdasarkan keseimbangan jam tidur dan intensitas waktu fokus kerja harian.
            </p>
          </div>

          <!-- Daily Health Check Items -->
          <div class="mt-5 space-y-2.5">
            <h4 class="text-xs font-bold uppercase tracking-wider text-gray-400">Checklist Pemulihan Hari Ini</h4>
            
            <label
              class="flex items-center justify-between p-3 rounded-xl border border-gray-200 hover:bg-gray-50 cursor-pointer transition-colors"
              :class="healthCheck?.took_vitamin ? 'bg-emerald-50/50 border-emerald-200' : ''"
            >
              <div class="flex items-center gap-3">
                <input
                  type="checkbox"
                  :checked="healthCheck?.took_vitamin"
                  @change="toggleHealthCheck('took_vitamin')"
                  :disabled="saving"
                  class="h-4 w-4 rounded border-gray-300 text-emerald-600 focus:ring-emerald-500"
                />
                <div>
                  <div class="text-xs font-semibold text-gray-800">Minum Vitamin &amp; Suplemen</div>
                  <div class="text-[11px] text-gray-400">Menjaga imunitas saat jadwal padat</div>
                </div>
              </div>
              <span class="text-lg">💊</span>
            </label>

            <label
              class="flex items-center justify-between p-3 rounded-xl border border-gray-200 hover:bg-gray-50 cursor-pointer transition-colors"
              :class="healthCheck?.did_stretch ? 'bg-emerald-50/50 border-emerald-200' : ''"
            >
              <div class="flex items-center gap-3">
                <input
                  type="checkbox"
                  :checked="healthCheck?.did_stretch"
                  @change="toggleHealthCheck('did_stretch')"
                  :disabled="saving"
                  class="h-4 w-4 rounded border-gray-300 text-emerald-600 focus:ring-emerald-500"
                />
                <div>
                  <div class="text-xs font-semibold text-gray-800">Peregangan (Stretching 5 Menit)</div>
                  <div class="text-[11px] text-gray-400">Rileksasi leher, bahu, dan mata dari layar</div>
                </div>
              </div>
              <span class="text-lg">🧘</span>
            </label>
          </div>
        </div>

        <div class="mt-5 pt-3 text-center border-t border-gray-100">
          <span class="text-[11px] text-gray-400">💡 Night Cutoff otomatis menyala pukul 22:30 WIB</span>
        </div>
      </div>

      <!-- 3. Sleep Log History (Span 2 Cols) -->
      <div class="md:col-span-2 rounded-2xl border border-gray-200 bg-white p-5 shadow-xs sm:p-6">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-4 border-b border-gray-100">
          <div>
            <div class="flex items-center gap-2">
              <span class="text-xl">💤</span>
              <h3 class="text-sm font-bold text-gray-900">Riwayat Tidur &amp; Analisis Kualitas (7 Hari Terakhir)</h3>
            </div>
            <p class="text-xs text-gray-500 mt-0.5">
              Rata-rata 7 hari: <strong class="text-gray-900">{{ averageSleepHours }} jam/hari</strong>
              <span v-if="averageSleepHours >= 7" class="text-emerald-600 font-medium ml-1.5">✓ Target tercukupi</span>
              <span v-else class="text-amber-600 font-medium ml-1.5">⚠️ Kurang tidur (target minimal 7 jam)</span>
            </p>
          </div>

          <div v-if="latestSleep" class="flex items-center gap-2 bg-indigo-50 border border-indigo-200 rounded-xl px-3 py-1.5 text-xs text-indigo-900">
            <span>Terakhir: <strong>{{ latestSleep.hours }} jam</strong> ({{ latestSleep.quality }})</span>
          </div>
        </div>

        <!-- Sleep Table / List -->
        <div v-if="sleepLogs.length === 0" class="py-8 text-center text-xs text-gray-400">
          Belum ada riwayat tidur tercatat. Klik tombol "Catat Tidur" untuk memasukkan data.
        </div>

        <div v-else class="mt-4 divide-y divide-gray-100">
          <div
            v-for="log in sleepLogs"
            :key="log.id"
            class="py-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2"
          >
            <div class="flex items-center gap-3">
              <div
                class="h-8 w-8 rounded-lg flex items-center justify-center text-xs font-bold"
                :class="log.hours >= 7 ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'"
              >
                {{ log.hours }}h
              </div>
              <div>
                <div class="text-xs font-bold text-gray-900">{{ log.date }}</div>
                <div class="text-[11px] text-gray-500">
                  Kualitas: <span class="font-medium text-gray-700">{{ log.quality }}</span>
                  <span v-if="log.notes" class="text-gray-400 ml-1">• "{{ log.notes }}"</span>
                </div>
              </div>
            </div>

            <!-- Mini Visual Bar -->
            <div class="flex items-center gap-2 sm:w-48">
              <div class="h-2 w-full rounded-full bg-gray-100 overflow-hidden">
                <div
                  class="h-full rounded-full"
                  :class="log.hours >= 7 ? 'bg-emerald-500' : 'bg-amber-500'"
                  :style="{ width: `${Math.min(100, (log.hours / 10) * 100)}%` }"
                ></div>
              </div>
              <span class="text-[11px] font-mono text-gray-500">{{ log.hours }} jam</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Form Catat Tidur -->
    <div
      v-if="showSleepModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/40 backdrop-blur-xs p-4"
    >
      <div class="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl border border-gray-200 space-y-4">
        <div class="flex items-center justify-between pb-3 border-b border-gray-100">
          <div class="flex items-center gap-2">
            <span class="text-xl">💤</span>
            <h3 class="text-sm font-bold text-gray-900">Catat Tidur Semalam</h3>
          </div>
          <button
            @click="showSleepModal = false"
            class="text-gray-400 hover:text-gray-600 text-sm"
          >
            ✕
          </button>
        </div>

        <form @submit.prevent="submitSleepLog" class="space-y-3.5 text-xs">
          <div>
            <label class="block font-semibold text-gray-700 mb-1">Tanggal</label>
            <input
              v-model="sleepForm.date"
              type="date"
              required
              class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-gray-900 focus:outline-none"
            />
          </div>

          <div>
            <label class="block font-semibold text-gray-700 mb-1">Durasi Tidur (Jam)</label>
            <input
              v-model.number="sleepForm.hours"
              type="number"
              step="0.5"
              min="1"
              max="16"
              required
              class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-gray-900 focus:outline-none"
            />
          </div>

          <div>
            <label class="block font-semibold text-gray-700 mb-1">Kualitas Tidur</label>
            <select
              v-model="sleepForm.quality"
              class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-gray-900 focus:outline-none"
            >
              <option value="Sangat Kurang">Sangat Kurang (Terbangun-bangun)</option>
              <option value="Kurang">Kurang (Gelisah)</option>
              <option value="Cukup">Cukup (Biasa)</option>
              <option value="Nyenyak">Nyenyak (Segar saat bangun)</option>
              <option value="Sangat Nyenyak">Sangat Nyenyak (Optimal)</option>
            </select>
          </div>

          <div>
            <label class="block font-semibold text-gray-700 mb-1">Catatan Tambahan (Opsional)</label>
            <input
              v-model="sleepForm.notes"
              type="text"
              placeholder="Contoh: Tidur jam 23:00 setelah minum teh chamomile"
              class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-gray-900 focus:outline-none"
            />
          </div>

          <div class="pt-3 flex gap-2 justify-end">
            <button
              type="button"
              @click="showSleepModal = false"
              class="rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-semibold text-gray-700 hover:bg-gray-50"
            >
              Batal
            </button>
            <button
              type="submit"
              :disabled="saving"
              class="rounded-lg bg-gray-900 px-4 py-1.5 text-xs font-semibold text-white shadow-xs hover:bg-gray-800 disabled:opacity-50"
            >
              {{ saving ? 'Menyimpan...' : 'Simpan Data Tidur' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
