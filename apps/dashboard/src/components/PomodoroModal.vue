<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { playNotificationSound, sendBrowserPush } from '../lib/notifications'

const props = defineProps<{
  userId: string
}>()

const isOpen = ref(false)

// Timer states
type PomodoroMode = 'focus' | 'short_break' | 'long_break'

const mode = ref<PomodoroMode>('focus')
const isRunning = ref(false)
const timeLeft = ref(25 * 60) // in seconds
const currentDuration = ref(25 * 60)
const focusTopic = ref('')
let timerInterval: any = null

// Custom presets for focus
const focusPresets = [
  { label: '25m (Standar)', minutes: 25 },
  { label: '45m (Deep Work)', minutes: 45 },
  { label: '50m (Skripsi)', minutes: 50 },
]

// Daily Statistics Persistence in localStorage
const todayKey = computed(() => {
  const today = new Date().toISOString().split('T')[0]
  return `sb_pomodoro_stats_${props.userId}_${today}`
})

const completedSessions = ref(0)
const totalFocusMinutes = ref(0)

function loadDailyStats() {
  try {
    const raw = localStorage.getItem(todayKey.value)
    if (raw) {
      const data = JSON.parse(raw)
      completedSessions.value = data.completedSessions || 0
      totalFocusMinutes.value = data.totalFocusMinutes || 0
    } else {
      completedSessions.value = 0
      totalFocusMinutes.value = 0
    }
  } catch {
    completedSessions.value = 0
    totalFocusMinutes.value = 0
  }
}

function saveDailyStats() {
  try {
    localStorage.setItem(
      todayKey.value,
      JSON.stringify({
        completedSessions: completedSessions.value,
        totalFocusMinutes: totalFocusMinutes.value,
      })
    )
  } catch (e) {
    console.error('Failed to save pomodoro stats', e)
  }
}

function setMode(newMode: PomodoroMode, minutes?: number) {
  pauseTimer()
  mode.value = newMode
  let mins = 25
  if (newMode === 'focus') {
    mins = minutes || 25
  } else if (newMode === 'short_break') {
    mins = 5
  } else if (newMode === 'long_break') {
    mins = 15
  }
  currentDuration.value = mins * 60
  timeLeft.value = mins * 60
}

function toggleTimer() {
  if (isRunning.value) {
    pauseTimer()
  } else {
    startTimer()
  }
}

function startTimer() {
  if (isRunning.value) return
  isRunning.value = true
  timerInterval = setInterval(() => {
    if (timeLeft.value > 0) {
      timeLeft.value--
    } else {
      handleTimerComplete()
    }
  }, 1000)
}

function pauseTimer() {
  isRunning.value = false
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
}

function resetTimer() {
  pauseTimer()
  timeLeft.value = currentDuration.value
}

function handleTimerComplete() {
  pauseTimer()
  playNotificationSound('chime')

  if (mode.value === 'focus') {
    const minsCompleted = Math.round(currentDuration.value / 60)
    completedSessions.value++
    totalFocusMinutes.value += minsCompleted
    saveDailyStats()

    const title = '🍅 Sesi Fokus Selesai!'
    const body = focusTopic.value
      ? `Hebat! Kamu telah menyelesaikan sesi fokus untuk: "${focusTopic.value}". Waktunya istirahat 5 menit.`
      : 'Hebat! Sesi fokus selesai. Waktunya istirahat 5 menit, regangkan otot, dan minum air.'

    sendBrowserPush(title, body)

    // Otomatis tawarkan istirahat
    if (completedSessions.value % 4 === 0) {
      setMode('long_break')
    } else {
      setMode('short_break')
    }
  } else {
    // Break complete
    sendBrowserPush('☕ Waktu Istirahat Selesai', 'Pikiran sudah segar kembali? Siap untuk sesi fokus berikutnya!')
    setMode('focus', 25)
  }
}

// Formatted Time MM:SS
const formattedTime = computed(() => {
  const m = Math.floor(timeLeft.value / 60)
  const s = timeLeft.value % 60
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
})

const progressPercent = computed(() => {
  if (currentDuration.value === 0) return 0
  const elapsed = currentDuration.value - timeLeft.value
  return Math.min(100, Math.round((elapsed / currentDuration.value) * 100))
})

function openModal() {
  isOpen.value = true
}

function closeModal() {
  isOpen.value = false
}

defineExpose({
  openModal,
  closeModal,
  formattedTime,
  isRunning,
  mode,
})

onMounted(() => {
  loadDailyStats()
})

onUnmounted(() => {
  if (timerInterval) {
    clearInterval(timerInterval)
  }
})
</script>

<template>
  <div>
    <!-- Modal Window -->
    <div
      v-if="isOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/50 backdrop-blur-xs p-4"
    >
      <div class="w-full max-w-md rounded-2xl bg-white p-5 sm:p-6 shadow-2xl border border-gray-200 space-y-5">
        <!-- Header -->
        <div class="flex items-center justify-between pb-3 border-b border-gray-100">
          <div class="flex items-center gap-2">
            <span class="text-2xl">🍅</span>
            <div>
              <h3 class="text-sm font-bold text-gray-900 sm:text-base">Focus &amp; Pomodoro Hub</h3>
              <p class="text-[11px] text-gray-500">Jaga ritme belajar terstruktur tanpa memicu kelelahan otak</p>
            </div>
          </div>
          <button
            type="button"
            @click="closeModal"
            class="text-gray-400 hover:text-gray-600 text-sm p-1.5 rounded-lg hover:bg-gray-100 cursor-pointer"
          >
            ✕
          </button>
        </div>

        <!-- Mode Tabs -->
        <div class="flex rounded-xl bg-gray-100 p-1 text-xs font-bold">
          <button
            type="button"
            @click="setMode('focus', 25)"
            class="flex-1 py-1.5 rounded-lg transition-all cursor-pointer text-center"
            :class="mode === 'focus' ? 'bg-white text-rose-700 shadow-xs' : 'text-gray-600 hover:text-gray-900'"
          >
            🍅 Fokus
          </button>
          <button
            type="button"
            @click="setMode('short_break')"
            class="flex-1 py-1.5 rounded-lg transition-all cursor-pointer text-center"
            :class="mode === 'short_break' ? 'bg-white text-emerald-700 shadow-xs' : 'text-gray-600 hover:text-gray-900'"
          >
            ☕ Rehat 5m
          </button>
          <button
            type="button"
            @click="setMode('long_break')"
            class="flex-1 py-1.5 rounded-lg transition-all cursor-pointer text-center"
            :class="mode === 'long_break' ? 'bg-white text-indigo-700 shadow-xs' : 'text-gray-600 hover:text-gray-900'"
          >
            🌿 Rehat 15m
          </button>
        </div>

        <!-- Timer Display Card -->
        <div
          class="rounded-2xl border p-6 text-center transition-colors relative overflow-hidden flex flex-col items-center justify-center space-y-3"
          :class="{
            'border-rose-200 bg-gradient-to-b from-rose-50/60 to-white': mode === 'focus',
            'border-emerald-200 bg-gradient-to-b from-emerald-50/60 to-white': mode === 'short_break',
            'border-indigo-200 bg-gradient-to-b from-indigo-50/60 to-white': mode === 'long_break',
          }"
        >
          <!-- Mode Label -->
          <span
            class="text-[11px] font-extrabold tracking-wider uppercase px-3 py-1 rounded-full border"
            :class="{
              'text-rose-700 bg-rose-100/70 border-rose-200': mode === 'focus',
              'text-emerald-700 bg-emerald-100/70 border-emerald-200': mode === 'short_break',
              'text-indigo-700 bg-indigo-100/70 border-indigo-200': mode === 'long_break',
            }"
          >
            {{ mode === 'focus' ? 'Sesi Fokus Belajar' : (mode === 'short_break' ? 'Istirahat Singkat' : 'Istirahat Panjang') }}
          </span>

          <!-- Huge Digital Clock -->
          <div class="text-6xl font-black tracking-tight font-mono select-none"
            :class="{
              'text-rose-950': mode === 'focus',
              'text-emerald-950': mode === 'short_break',
              'text-indigo-950': mode === 'long_break',
            }"
          >
            {{ formattedTime }}
          </div>

          <!-- Progress Bar -->
          <div class="w-full max-w-xs h-2 rounded-full bg-gray-200 overflow-hidden">
            <div
              class="h-full transition-all duration-500 rounded-full"
              :class="{
                'bg-rose-500': mode === 'focus',
                'bg-emerald-500': mode === 'short_break',
                'bg-indigo-500': mode === 'long_break',
              }"
              :style="{ width: `${progressPercent}%` }"
            ></div>
          </div>

          <!-- Quick Presets for Focus Mode -->
          <div v-if="mode === 'focus'" class="pt-2 flex items-center justify-center gap-1.5">
            <button
              v-for="preset in focusPresets"
              :key="preset.minutes"
              type="button"
              @click="setMode('focus', preset.minutes)"
              class="rounded-lg px-2.5 py-1 text-[10px] font-bold border transition-colors cursor-pointer"
              :class="currentDuration === preset.minutes * 60 ? 'bg-rose-600 text-white border-rose-600' : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50'"
            >
              {{ preset.label }}
            </button>
          </div>
        </div>

        <!-- Task Focus Input -->
        <div v-if="mode === 'focus'" class="space-y-1">
          <label class="block text-xs font-semibold text-gray-700">Target Fokus Sesi Ini:</label>
          <input
            v-model="focusTopic"
            type="text"
            placeholder="Contoh: Mengerjakan Revisi Bab 2 atau Latihan Kuis Kalkulus"
            class="w-full rounded-xl border border-gray-300 px-3 py-2 text-xs focus:ring-2 focus:ring-rose-500 focus:outline-none"
          />
        </div>

        <!-- Timer Action Buttons -->
        <div class="flex items-center gap-2">
          <button
            type="button"
            @click="toggleTimer"
            class="flex-1 rounded-xl py-2.5 text-xs font-bold text-white shadow-md active:scale-95 transition-all cursor-pointer flex items-center justify-center gap-2"
            :class="isRunning ? 'bg-amber-600 hover:bg-amber-700' : (mode === 'focus' ? 'bg-rose-600 hover:bg-rose-700' : 'bg-emerald-600 hover:bg-emerald-700')"
          >
            <span>{{ isRunning ? '⏸️' : '▶️' }}</span>
            <span>{{ isRunning ? 'Jeda Timer' : (timeLeft < currentDuration ? 'Lanjutkan Fokus' : 'Mulai Sekarang') }}</span>
          </button>

          <button
            type="button"
            @click="resetTimer"
            class="rounded-xl border border-gray-300 px-3.5 py-2.5 text-xs font-bold text-gray-700 hover:bg-gray-50 active:scale-95 transition-all cursor-pointer"
            title="Reset Waktu"
          >
            🔄 Reset
          </button>
        </div>

        <!-- Daily Statistics Footer -->
        <div class="rounded-xl bg-gray-50 border border-gray-100 p-3 flex items-center justify-between text-xs text-gray-600">
          <div class="flex items-center gap-2">
            <span class="text-base">🔥</span>
            <div>
              <span class="font-bold text-gray-900">{{ completedSessions }} Sesi</span>
              <span class="text-[11px] text-gray-400"> ({{ totalFocusMinutes }} menit fokus) hari ini</span>
            </div>
          </div>
          <span class="text-[10px] text-gray-400 font-medium">Auto-Chime &amp; Push Aktif 🔔</span>
        </div>
      </div>
    </div>
  </div>
</template>
