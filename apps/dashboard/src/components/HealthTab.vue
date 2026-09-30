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
  bedtime: '23:00',
  waketime: '06:30',
  hours: 7.5,
  quality: 'Nyenyak',
  notes: '',
})

function calculateDurationFromTimes() {
  if (!sleepForm.value.bedtime || !sleepForm.value.waketime) return
  const [bH, bM] = sleepForm.value.bedtime.split(':').map(Number)
  const [wH, wM] = sleepForm.value.waketime.split(':').map(Number)
  let diffMin = (wH * 60 + wM) - (bH * 60 + bM)
  if (diffMin < 0) diffMin += 24 * 60
  sleepForm.value.hours = +(diffMin / 60).toFixed(1)
}

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

    // 2. Sleep logs last 14 days
    const { data: sleepData } = await supabase
      .from('sleep_logs')
      .select('*')
      .eq('user_id', props.userId)
      .order('date', { ascending: false })
      .limit(14)

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
async function setHydrationGlasses(targetValue: number) {
  const val = Math.max(0, targetValue)
  const prevVal = hydration.value?.glasses ?? 0
  const target = hydration.value?.target_glasses ?? 8

  // Optimistic update
  if (!hydration.value) {
    hydration.value = {
      id: 0,
      date: todayIso,
      glasses: val,
      target_glasses: target,
    }
  } else {
    hydration.value.glasses = val
  }

  try {
    const { data: existing } = await supabase
      .from('hydration_logs')
      .select('id')
      .eq('user_id', props.userId)
      .eq('date', todayIso)
      .maybeSingle()

    if (existing?.id) {
      const { data } = await supabase
        .from('hydration_logs')
        .update({
          glasses: val,
          target_glasses: target,
          updated_at: new Date().toISOString(),
        })
        .eq('id', existing.id)
        .select()
        .single()
      if (data) hydration.value = data
    } else {
      const { data } = await supabase
        .from('hydration_logs')
        .insert({
          user_id: props.userId,
          date: todayIso,
          glasses: val,
          target_glasses: target,
        })
        .select()
        .single()
      if (data) hydration.value = data
    }
  } catch (err) {
    console.error('Gagal update hidrasi:', err)
    if (hydration.value) {
      hydration.value.glasses = prevVal
    }
  }
}

function handleGlassClick(i: number) {
  const current = hydration.value?.glasses ?? 0
  if (current === i) {
    setHydrationGlasses(i - 1)
  } else {
    setHydrationGlasses(i)
  }
}

async function adjustHydration(delta: number) {
  const currentGlasses = hydration.value?.glasses ?? 0
  await setHydrationGlasses(currentGlasses + delta)
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

async function setBurnoutScore(score: number) {
  if (saving.value) return
  saving.value = true
  try {
    const current = healthCheck.value
    const { data, error } = await supabase
      .from('health_check_logs')
      .upsert({
        user_id: props.userId,
        date: todayIso,
        took_vitamin: current?.took_vitamin ?? false,
        did_stretch: current?.did_stretch ?? false,
        burnout_score: Math.max(0, Math.min(100, score)),
      }, { onConflict: 'user_id,date' })
      .select()
      .single()

    if (!error && data) {
      healthCheck.value = data
    }
  } catch (err) {
    console.error('Gagal update skor burnout:', err)
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

async function deleteSleepLog(id: number) {
  if (!confirm('Hapus catatan tidur ini?')) return
  try {
    await supabase.from('sleep_logs').delete().eq('id', id)
    sleepLogs.value = sleepLogs.value.filter(s => s.id !== id)
  } catch (err) {
    console.error('Gagal menghapus log tidur:', err)
  }
}

// Computed Values
const hydrationPercent = computed(() => {
  const g = hydration.value?.glasses ?? 0
  const t = hydration.value?.target_glasses ?? 8
  return Math.min(100, Math.round((g / t) * 100))
})

const totalMl = computed(() => {
  return (hydration.value?.glasses || 0) * 250
})

const targetMl = computed(() => {
  return (hydration.value?.target_glasses || 8) * 250
})

const averageSleepHours = computed(() => {
  if (sleepLogs.value.length === 0) return 0
  const total = sleepLogs.value.reduce((acc, s) => acc + Number(s.hours), 0)
  return +(total / sleepLogs.value.length).toFixed(1)
})

const sleepDebtHours = computed(() => {
  if (sleepLogs.value.length === 0) return 0
  // Target 7 jam/hari
  const debt = sleepLogs.value.reduce((acc, s) => acc + (7 - Number(s.hours)), 0)
  return +(debt).toFixed(1)
})

const latestSleep = computed(() => {
  return sleepLogs.value[0] || null
})

const burnoutScore = computed(() => {
  return healthCheck.value?.burnout_score ?? 20
})

const burnoutBadge = computed(() => {
  const score = burnoutScore.value
  if (score <= 30) return {
    label: 'Rendah (Kondisi Prima 🟢)',
    color: 'text-emerald-700 bg-emerald-50 border-emerald-200',
    advice: 'Energi dan fokus Anda sangat stabil. Waktu yang tepat untuk mengerjakan tugas dengan bobot tinggi.',
  }
  if (score <= 60) return {
    label: 'Sedang (Perlu Jeda 🟡)',
    color: 'text-amber-700 bg-amber-50 border-amber-200',
    advice: 'Mulai terasa kelelahan. Gunakan jeda Pomodoro 5 menit dan pastikan minum air serta peregangan.',
  }
  return {
    label: 'Tinggi (Kritis Burnout 🔴)',
    color: 'text-rose-700 bg-rose-50 border-rose-200',
    advice: 'Beban kerja terlalu tinggi dengan tidur minim. Hentikan deep work sekarang dan prioritaskan tidur lebih awal.',
  }
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
            <h2 class="text-lg font-bold text-gray-900 sm:text-xl">Radar Kesehatan &amp; Energi Harian</h2>
            <span class="rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-800">Prioritas #1</span>
          </div>
          <p class="mt-1 text-xs text-gray-500 sm:text-sm">
            Pantau asupan hidrasi, kualitas tidur semalam, dan skor pemulihan fisik untuk menjaga performa kerja stabil.
          </p>
        </div>
        <button
          @click="showSleepModal = true"
          class="inline-flex items-center justify-center gap-1.5 rounded-xl bg-gray-900 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-gray-800 transition-colors cursor-pointer"
        >
          <span>➕</span>
          <span>Catat Tidur Semalam</span>
        </button>
      </div>
    </div>

    <div v-if="loading" class="flex justify-center py-12">
      <div class="h-8 w-8 animate-spin rounded-full border-4 border-gray-900 border-t-transparent"></div>
    </div>

    <div v-else class="grid grid-cols-1 gap-6 md:grid-cols-2">
      <!-- 1. Interactive Hydration Station -->
      <div class="rounded-2xl border border-gray-200 bg-white p-5 shadow-xs sm:p-6 flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span class="text-xl">💧</span>
              <h3 class="text-sm font-bold text-gray-900">Hydration Tracker (Hari Ini)</h3>
            </div>
            <span
              class="text-xs font-semibold px-2.5 py-0.5 rounded-full border"
              :class="hydrationPercent >= 100 ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-blue-50 text-blue-700 border-blue-200'"
            >
              {{ totalMl }} / {{ targetMl }} ml ({{ hydrationPercent }}%)
            </span>
          </div>

          <div class="mt-5">
            <div class="flex justify-between items-baseline mb-2">
              <span class="text-3xl font-extrabold text-gray-900">
                {{ hydration?.glasses || 0 }}
                <span class="text-base font-normal text-gray-500">/ {{ hydration?.target_glasses || 8 }} Gelas</span>
              </span>
              <span v-if="hydrationPercent >= 100" class="text-xs font-bold text-emerald-600 flex items-center gap-1">
                ✓ Target Terpenuhi!
              </span>
              <span v-else class="text-xs font-medium text-gray-500">
                Kurang {{ Math.max(0, targetMl - totalMl) }} ml lagi
              </span>
            </div>

            <!-- Animated Water Fill Bar -->
            <div class="h-3.5 w-full rounded-full bg-gray-100 overflow-hidden relative">
              <div
                class="h-full rounded-full bg-gradient-to-r from-blue-400 to-blue-600 transition-all duration-300"
                :style="{ width: `${hydrationPercent}%` }"
              ></div>
            </div>
          </div>

          <!-- Interactive 8 Glass Icons (Click to Jump) -->
          <div class="mt-5">
            <div class="text-[11px] text-gray-400 mb-2 font-medium">Klik gelas untuk set langsung:</div>
            <div class="grid grid-cols-8 gap-1.5">
              <button
                v-for="i in (hydration?.target_glasses || 8)"
                :key="i"
                type="button"
                @click="handleGlassClick(i)"
                :title="`Klik untuk set/toggle ${i} gelas (${i * 250} ml)`"
                class="h-10 rounded-lg flex flex-col items-center justify-center text-xs border transition-all cursor-pointer hover:scale-105"
                :class="i <= (hydration?.glasses || 0)
                  ? 'bg-blue-500 text-white border-blue-600 shadow-2xs font-bold'
                  : 'bg-gray-50 text-gray-300 border-gray-200 hover:border-blue-300'"
              >
                <span>🥛</span>
                <span class="text-[9px] mt-0.5 leading-none">{{ i }}</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Hydration Quick Presets -->
        <div class="mt-6 pt-4 border-t border-gray-100 space-y-2">
          <div class="flex items-center gap-2">
            <button
              @click="adjustHydration(1)"
              :disabled="saving"
              class="flex-2 rounded-xl bg-blue-600 py-2.5 text-xs font-semibold text-white shadow-xs hover:bg-blue-700 disabled:opacity-50 transition-colors flex items-center justify-center gap-1.5 cursor-pointer"
            >
              <span>💧</span>
              <span>+1 Gelas (250ml)</span>
            </button>
            <button
              @click="adjustHydration(2)"
              :disabled="saving"
              class="flex-1 rounded-xl bg-blue-50 border border-blue-200 py-2.5 text-xs font-semibold text-blue-700 hover:bg-blue-100 disabled:opacity-50 transition-colors cursor-pointer"
            >
              +500ml Botol
            </button>
          </div>
          <div class="flex items-center justify-between text-xs pt-1">
            <button
              @click="adjustHydration(-1)"
              :disabled="saving || (hydration?.glasses || 0) <= 0"
              class="text-gray-500 hover:text-gray-800 disabled:opacity-30 cursor-pointer"
            >
              - 1 Gelas
            </button>
            <button
              @click="setHydrationGlasses(0)"
              :disabled="saving || (hydration?.glasses || 0) <= 0"
              class="text-gray-400 hover:text-rose-600 disabled:opacity-30 text-[11px] cursor-pointer"
            >
              Reset Hari Ini
            </button>
          </div>
        </div>
      </div>

      <!-- 2. Recovery & Burnout Radar Card -->
      <div class="rounded-2xl border border-gray-200 bg-white p-5 shadow-xs sm:p-6 flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span class="text-xl">🧘</span>
              <h3 class="text-sm font-bold text-gray-900">Recovery &amp; Burnout Radar</h3>
            </div>
            <span
              class="text-xs font-bold px-2.5 py-0.5 rounded-full border"
              :class="burnoutBadge.color"
            >
              Skor {{ burnoutScore }}/100
            </span>
          </div>

          <!-- Dynamic Advice Box -->
          <div class="mt-4 rounded-xl p-3.5 bg-gray-50 border border-gray-200 space-y-1">
            <div class="flex items-center justify-between text-xs">
              <span class="font-medium text-gray-500">Status Pemulihan:</span>
              <span class="font-bold text-gray-900">{{ burnoutBadge.label }}</span>
            </div>
            <p class="text-[11px] text-gray-600 leading-relaxed">
              {{ burnoutBadge.advice }}
            </p>
          </div>

          <!-- Interactive Burnout Level Presets -->
          <div class="mt-3.5 space-y-1.5">
            <span class="text-[11px] font-bold text-gray-700">Set Tingkat Kelelahan Mental Hari Ini:</span>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-1.5 text-xs">
              <button
                type="button"
                @click="setBurnoutScore(20)"
                class="rounded-xl px-2 py-1.5 text-[11px] font-bold border transition-all cursor-pointer text-center"
                :class="burnoutScore <= 30 ? 'bg-emerald-600 text-white border-emerald-600 shadow-2xs' : 'bg-white text-gray-700 border-gray-200 hover:bg-emerald-50'"
              >
                🟢 Prima (20)
              </button>
              <button
                type="button"
                @click="setBurnoutScore(50)"
                class="rounded-xl px-2 py-1.5 text-[11px] font-bold border transition-all cursor-pointer text-center"
                :class="burnoutScore > 30 && burnoutScore <= 60 ? 'bg-amber-600 text-white border-amber-600 shadow-2xs' : 'bg-white text-gray-700 border-gray-200 hover:bg-amber-50'"
              >
                🟡 Lelah (50)
              </button>
              <button
                type="button"
                @click="setBurnoutScore(75)"
                class="rounded-xl px-2 py-1.5 text-[11px] font-bold border transition-all cursor-pointer text-center"
                :class="burnoutScore > 60 && burnoutScore <= 80 ? 'bg-orange-600 text-white border-orange-600 shadow-2xs' : 'bg-white text-gray-700 border-gray-200 hover:bg-orange-50'"
              >
                🟠 Ngebul (75)
              </button>
              <button
                type="button"
                @click="setBurnoutScore(95)"
                class="rounded-xl px-2 py-1.5 text-[11px] font-bold border transition-all cursor-pointer text-center"
                :class="burnoutScore > 80 ? 'bg-rose-600 text-white border-rose-600 shadow-2xs' : 'bg-white text-gray-700 border-gray-200 hover:bg-rose-50'"
              >
                🔴 Drop (95)
              </button>
            </div>
          </div>

          <!-- Daily Health Check Items -->
          <div class="mt-5 space-y-2.5">
            <h4 class="text-xs font-bold uppercase tracking-wider text-gray-400">Checklist Pemulihan Hari Ini</h4>

            <label
              class="flex items-center justify-between p-3 rounded-xl border border-gray-200 hover:bg-gray-50 cursor-pointer transition-colors"
              :class="healthCheck?.took_vitamin ? 'bg-emerald-50/60 border-emerald-300' : ''"
            >
              <div class="flex items-center gap-3">
                <input
                  type="checkbox"
                  :checked="healthCheck?.took_vitamin"
                  @change="toggleHealthCheck('took_vitamin')"
                  :disabled="saving"
                  class="h-4 w-4 rounded border-gray-300 text-emerald-600 focus:ring-emerald-500 cursor-pointer"
                />
                <div>
                  <div class="text-xs font-semibold text-gray-800">Minum Vitamin &amp; Suplemen</div>
                  <div class="text-[11px] text-gray-400">Menjaga daya tahan tubuh saat beban kuliah &amp; riset tinggi</div>
                </div>
              </div>
              <span class="text-xl">💊</span>
            </label>

            <label
              class="flex items-center justify-between p-3 rounded-xl border border-gray-200 hover:bg-gray-50 cursor-pointer transition-colors"
              :class="healthCheck?.did_stretch ? 'bg-emerald-50/60 border-emerald-300' : ''"
            >
              <div class="flex items-center gap-3">
                <input
                  type="checkbox"
                  :checked="healthCheck?.did_stretch"
                  @change="toggleHealthCheck('did_stretch')"
                  :disabled="saving"
                  class="h-4 w-4 rounded border-gray-300 text-emerald-600 focus:ring-emerald-500 cursor-pointer"
                />
                <div>
                  <div class="text-xs font-semibold text-gray-800">Peregangan (Stretching 5 Menit)</div>
                  <div class="text-[11px] text-gray-400">Rileksasi otot bahu, leher, dan mata dari monitor</div>
                </div>
              </div>
              <span class="text-xl">🧘</span>
            </label>
          </div>
        </div>

        <div class="mt-5 pt-3 flex items-center justify-between text-[11px] text-gray-400 border-t border-gray-100">
          <span>🌙 Night Cutoff Otomatis: <strong>22:30 WIB</strong></span>
          <span class="text-gray-300">•</span>
          <span>☀️ Brief Pagi: <strong>07:00 WIB</strong></span>
        </div>
      </div>

      <!-- 3. Sleep Log History & Sleep Debt Analysis -->
      <div class="md:col-span-2 rounded-2xl border border-gray-200 bg-white p-5 shadow-xs sm:p-6">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-4 border-b border-gray-100">
          <div>
            <div class="flex items-center gap-2">
              <span class="text-xl">💤</span>
              <h3 class="text-sm font-bold text-gray-900">Riwayat Tidur &amp; Analisis Hutang Tidur (Sleep Debt)</h3>
            </div>
            <div class="flex flex-wrap items-center gap-2 text-xs text-gray-500 mt-1">
              <span>Rata-rata: <strong class="text-gray-900">{{ averageSleepHours }} jam/hari</strong></span>
              <span class="text-gray-300">•</span>
              <span v-if="sleepDebtHours <= 0" class="text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                ✓ Tidak ada hutang tidur (Kondisi Segar)
              </span>
              <span v-else class="text-amber-800 font-semibold bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
                ⚠️ Hutang Tidur: {{ sleepDebtHours }} jam (rekomendasi tidur lebih awal)
              </span>
            </div>
          </div>

          <div v-if="latestSleep" class="flex items-center gap-2 bg-indigo-50 border border-indigo-200 rounded-xl px-3 py-1.5 text-xs text-indigo-900 shrink-0">
            <span>Semalam: <strong>{{ latestSleep.hours }} jam</strong> ({{ latestSleep.quality }})</span>
          </div>
        </div>

        <!-- Sleep List -->
        <div v-if="sleepLogs.length === 0" class="py-8 text-center text-xs text-gray-400">
          Belum ada riwayat tidur tercatat. Klik tombol "Catat Tidur Semalam" untuk memasukkan data.
        </div>

        <div v-else class="mt-4 divide-y divide-gray-100">
          <div
            v-for="log in sleepLogs"
            :key="log.id"
            class="py-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 group"
          >
            <div class="flex items-center gap-3">
              <div
                class="h-9 w-9 rounded-xl flex items-center justify-center text-xs font-extrabold shrink-0"
                :class="log.hours >= 7 ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'"
              >
                {{ log.hours }}j
              </div>
              <div>
                <div class="text-xs font-bold text-gray-900">{{ log.date }}</div>
                <div class="text-[11px] text-gray-500 flex flex-wrap items-center gap-1.5">
                  <span class="font-medium text-gray-700">Kualitas: {{ log.quality }}</span>
                  <span v-if="log.notes" class="text-gray-400">• "{{ log.notes }}"</span>
                </div>
              </div>
            </div>

            <!-- Mini Visual Bar & Delete -->
            <div class="flex items-center gap-3 sm:w-64">
              <div class="h-2 w-full rounded-full bg-gray-100 overflow-hidden">
                <div
                  class="h-full rounded-full transition-all duration-300"
                  :class="log.hours >= 7 ? 'bg-emerald-500' : 'bg-amber-500'"
                  :style="{ width: `${Math.min(100, (log.hours / 10) * 100)}%` }"
                ></div>
              </div>
              <span class="text-xs font-mono font-semibold text-gray-700 w-12 text-right shrink-0">{{ log.hours }} jam</span>
              <button
                type="button"
                @click="deleteSleepLog(log.id)"
                class="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-rose-600 text-xs transition-opacity cursor-pointer"
                title="Hapus log ini"
              >
                🗑️
              </button>
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
            class="text-gray-400 hover:text-gray-600 text-sm cursor-pointer"
          >
            ✕
          </button>
        </div>

        <form @submit.prevent="submitSleepLog" class="space-y-3.5 text-xs">
          <div>
            <label class="block font-semibold text-gray-700 mb-1">Tanggal Bangun</label>
            <input
              v-model="sleepForm.date"
              type="date"
              required
              class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-gray-900 focus:outline-none"
            />
          </div>

          <!-- Bedtime & Waketime Calculator -->
          <div class="grid grid-cols-2 gap-2.5">
            <div>
              <label class="block font-semibold text-gray-700 mb-1">Mulai Tidur (Malam)</label>
              <input
                v-model="sleepForm.bedtime"
                type="time"
                @change="calculateDurationFromTimes"
                class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-gray-900 focus:outline-none"
              />
            </div>
            <div>
              <label class="block font-semibold text-gray-700 mb-1">Bangun (Pagi)</label>
              <input
                v-model="sleepForm.waketime"
                type="time"
                @change="calculateDurationFromTimes"
                class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-gray-900 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <div class="flex justify-between items-center mb-1">
              <label class="font-semibold text-gray-700">Durasi Tidur (Jam)</label>
              <span class="font-bold text-indigo-700">{{ sleepForm.hours }} Jam</span>
            </div>
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
              <option value="Sangat Kurang">Sangat Kurang (Terbangun berulang kali)</option>
              <option value="Kurang">Kurang (Gelisah / Tidak lelap)</option>
              <option value="Cukup">Cukup (Biasa saja)</option>
              <option value="Nyenyak">Nyenyak (Segar saat bangun)</option>
              <option value="Sangat Nyenyak">Sangat Nyenyak (Optimal &amp; Bugar)</option>
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
              class="rounded-lg border border-gray-300 px-3.5 py-1.5 text-xs font-semibold text-gray-700 hover:bg-gray-50 cursor-pointer"
            >
              Batal
            </button>
            <button
              type="submit"
              :disabled="saving"
              class="rounded-lg bg-gray-900 px-4 py-1.5 text-xs font-semibold text-white shadow-xs hover:bg-gray-800 disabled:opacity-50 cursor-pointer"
            >
              {{ saving ? 'Menyimpan...' : 'Simpan Data Tidur' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
