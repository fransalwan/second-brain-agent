<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  fullName?: string | null
  email?: string | null
  briefTime?: string | null
  nightCutoffTime?: string | null
  tasks: any[]
  timeLogs: any[]
  habits: any[]
  habitLogs: any[]
}>()

const emit = defineEmits<{
  (e: 'navigate-tab', tab: 'overview' | 'health' | 'coursework' | 'research' | 'hobby'): void
  (e: 'toggle-task', taskId: number): void
}>()

const now = new Date()
const currentHour = now.getHours()
const todayIso = now.toISOString().split('T')[0]

const isMorning = computed(() => currentHour >= 5 && currentHour < 12)
const isAfternoon = computed(() => currentHour >= 12 && currentHour < 18)
const isNight = computed(() => currentHour >= 18 || currentHour < 5)

const greeting = computed(() => {
  const name = props.fullName || props.email?.split('@')[0] || 'Kawan'
  if (isMorning.value) return `Selamat Pagi, ${name}! ☀️`
  if (isAfternoon.value) return `Selamat Beraktivitas, ${name}! 🚀`
  return `Waktu Recharge & Istirahat, ${name} 🌙`
})

const pendingTasks = computed(() => {
  return props.tasks.filter((t) => t.status === 'pending')
})

const completedTodayTasks = computed(() => {
  return props.tasks.filter(
    (t) => t.status === 'completed' && t.completed_at?.startsWith(todayIso)
  )
})

const totalFocusMinutesToday = computed(() => {
  return props.timeLogs
    .filter((t) => t.started_at.startsWith(todayIso) && t.duration_minutes !== null)
    .reduce((acc, t) => acc + (t.duration_minutes || 0), 0)
})

const todayCompletedHabits = computed(() => {
  return props.habitLogs.filter((l) => l.completed_date === todayIso).length
})

const urgentTasks = computed(() => {
  return pendingTasks.value.filter((t) => t.is_urgent).slice(0, 3)
})
</script>

<template>
  <div
    class="rounded-3xl border transition-all shadow-xs p-5 sm:p-6"
    :class="{
      'border-amber-200 bg-gradient-to-br from-amber-50/80 via-orange-50/40 to-white': isMorning,
      'border-blue-200 bg-gradient-to-br from-blue-50/70 via-indigo-50/30 to-white': isAfternoon,
      'border-purple-200 bg-gradient-to-br from-purple-50/80 via-indigo-50/40 to-white': isNight,
    }"
  >
    <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-5">
      <!-- Left side: Greeting & Metrics -->
      <div class="space-y-3 max-w-xl">
        <div class="flex items-center gap-2.5">
          <span class="text-2xl select-none">
            {{ isMorning ? '☀️' : isAfternoon ? '🚀' : '🌙' }}
          </span>
          <div>
            <h2 class="text-lg font-bold text-gray-900 tracking-tight">
              {{ greeting }}
            </h2>
            <p class="text-xs text-gray-600 mt-0.5">
              <span v-if="isMorning">
                Briefing harian aktif. Mulai hari dengan fokus pada prioritas terpenting.
              </span>
              <span v-else-if="isAfternoon">
                Pertahankan ritme kerja. Waktunya eksekusi tugas sebelum sore berakhir.
              </span>
              <span v-else>
                Waktu evaluasi dan istirahat. Hindari memaksakan diri larut malam agar esok hari optimal.
              </span>
            </p>
          </div>
        </div>

        <!-- Quick Metrics Pills -->
        <div class="flex flex-wrap items-center gap-2 pt-1">
          <div class="inline-flex items-center gap-1.5 rounded-xl bg-white px-3 py-1.5 border border-gray-200/80 shadow-2xs text-xs font-semibold text-gray-800">
            <span>📋 Pending:</span>
            <span class="font-bold text-gray-900">{{ pendingTasks.length }}</span>
          </div>

          <div class="inline-flex items-center gap-1.5 rounded-xl bg-white px-3 py-1.5 border border-gray-200/80 shadow-2xs text-xs font-semibold text-gray-800">
            <span>✅ Selesai Hari Ini:</span>
            <span class="font-bold text-emerald-600">{{ completedTodayTasks.length }}</span>
          </div>

          <div class="inline-flex items-center gap-1.5 rounded-xl bg-white px-3 py-1.5 border border-gray-200/80 shadow-2xs text-xs font-semibold text-gray-800">
            <span>⏱️ Fokus:</span>
            <span class="font-bold text-indigo-600">{{ totalFocusMinutesToday }}m</span>
          </div>

          <div class="inline-flex items-center gap-1.5 rounded-xl bg-white px-3 py-1.5 border border-gray-200/80 shadow-2xs text-xs font-semibold text-gray-800">
            <span>🧘 Habit:</span>
            <span class="font-bold text-purple-600">{{ todayCompletedHabits }}/{{ habits.length }}</span>
          </div>
        </div>
      </div>

      <!-- Right side: Quick Action Card -->
      <div class="w-full lg:w-80 rounded-2xl bg-white/95 p-4 border border-gray-200/80 shadow-2xs space-y-2.5 shrink-0">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold text-gray-800">
            {{ urgentTasks.length > 0 ? '🚨 Prioritas Mendesak' : '✨ Siap Fokus' }}
          </span>
          <button
            type="button"
            @click="emit('navigate-tab', 'coursework')"
            class="text-[11px] font-semibold text-indigo-600 hover:text-indigo-800 hover:underline cursor-pointer"
          >
            Buka Kuliah ↗
          </button>
        </div>

        <!-- If there are urgent tasks, show quick tick list -->
        <div v-if="urgentTasks.length > 0" class="space-y-1.5">
          <div
            v-for="task in urgentTasks"
            :key="task.id"
            class="flex items-center justify-between gap-2 p-2 rounded-xl bg-rose-50/60 border border-rose-100 text-xs"
          >
            <span class="font-medium text-rose-900 truncate">
              {{ task.title }}
            </span>
            <button
              type="button"
              @click="emit('toggle-task', task.id)"
              class="shrink-0 rounded-lg bg-white px-2 py-0.5 text-[10px] font-bold text-rose-700 border border-rose-200 hover:bg-rose-100 cursor-pointer"
            >
              Ceklis
            </button>
          </div>
        </div>

        <!-- Default encouragement -->
        <div v-else class="text-xs text-gray-500 py-1">
          Tidak ada tugas genting. Kamu bisa mulai sesi Pomodoro atau mencicil materi kuliah.
        </div>

        <!-- Fast navigation action -->
        <div class="flex items-center gap-2 pt-1 border-t border-gray-100 text-[11px]">
          <button
            type="button"
            @click="emit('navigate-tab', 'health')"
            class="flex-1 rounded-xl bg-gray-50 py-1.5 font-semibold text-gray-700 hover:bg-gray-100 text-center transition-colors cursor-pointer"
          >
            🩺 Cek Kesehatan
          </button>
          <button
            type="button"
            @click="emit('navigate-tab', 'research')"
            class="flex-1 rounded-xl bg-gray-50 py-1.5 font-semibold text-gray-700 hover:bg-gray-100 text-center transition-colors cursor-pointer"
          >
            🔬 Cek Riset
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
