<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { supabase } from '../lib/supabase'
import { playNotificationSound } from '../lib/notifications'

const props = defineProps<{
  userId: string
  areas: any[]
}>()

const emit = defineEmits<{
  (e: 'created', payload: { type: string; data?: any }): void
}>()

const isOpen = ref(false)
const rawInput = ref('')
const isSubmitting = ref(false)
const isListening = ref(false)
const inputRef = ref<HTMLInputElement | null>(null)
let recognition: any = null

// 1. Keyboard Shortcut listener: Ctrl+K / Cmd+K
function handleKeyDown(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault()
    toggleModal()
  } else if (e.key === 'Escape' && isOpen.value) {
    closeModal()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
  initSpeechRecognition()
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
  if (recognition) {
    try {
      recognition.stop()
    } catch {}
  }
})

function initSpeechRecognition() {
  const SpeechRec = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
  if (SpeechRec) {
    recognition = new SpeechRec()
    recognition.lang = 'id-ID'
    recognition.continuous = false
    recognition.interimResults = false

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript
      rawInput.value = transcript
      isListening.value = false
    }

    recognition.onerror = () => {
      isListening.value = false
    }

    recognition.onend = () => {
      isListening.value = false
    }
  }
}

function toggleVoice() {
  if (!recognition) {
    alert('Browser kamu belum mendukung Web Speech Recognition. Gunakan Chrome atau Edge untuk fitur suara.')
    return
  }
  if (isListening.value) {
    recognition.stop()
    isListening.value = false
  } else {
    isListening.value = true
    try {
      recognition.start()
    } catch {
      isListening.value = false
    }
  }
}

function toggleModal() {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    nextTick(() => {
      inputRef.value?.focus()
    })
  } else {
    rawInput.value = ''
    if (isListening.value && recognition) {
      recognition.stop()
      isListening.value = false
    }
  }
}

function closeModal() {
  isOpen.value = false
  rawInput.value = ''
  if (isListening.value && recognition) {
    recognition.stop()
    isListening.value = false
  }
}

// 2. Smart Client-Side Parser
interface ParsedIntent {
  type: 'task' | 'hydration' | 'sleep' | 'timer' | 'note'
  title: string
  deadline?: string
  isUrgent?: boolean
  amount?: number
  hours?: number
  projectName?: string
}

const parsedIntent = computed<ParsedIntent>(() => {
  const text = rawInput.value.trim().toLowerCase()
  if (!text) {
    return { type: 'note', title: '' }
  }

  // A. Hydration
  if (text.startsWith('minum') || text.includes('air minum') || text.endsWith('ml')) {
    const match = text.match(/(\d+)\s*(ml|gelas)?/)
    let amount = 250
    if (match) {
      const num = parseInt(match[1], 10)
      amount = match[2] === 'gelas' ? num * 250 : num
    }
    return {
      type: 'hydration',
      title: `Catat minum air ${amount} ml`,
      amount,
    }
  }

  // B. Sleep Log
  if (text.startsWith('tidur') || text.includes('jam tidur') || text.includes('sleep')) {
    const match = text.match(/(\d+(\.\d+)?)\s*(jam|hours)?/)
    const hours = match ? parseFloat(match[1]) : 7.0
    return {
      type: 'sleep',
      title: `Catat durasi tidur ${hours} jam`,
      hours,
    }
  }

  // C. Start Timer
  if (text.startsWith('fokus') || text.startsWith('mulai')) {
    const cleanProject = text.replace(/^(fokus|mulai)\s*(pada|ke)?\s*/i, '').trim() || 'Sesi Belajar'
    return {
      type: 'timer',
      title: `Mulai sesi fokus: ${cleanProject}`,
      projectName: cleanProject,
    }
  }

  // D. Task
  const isTaskKeyword =
    text.startsWith('tugas') ||
    text.startsWith('kuis') ||
    text.startsWith('pr') ||
    text.startsWith('praktikum') ||
    text.includes('deadline') ||
    text.includes('besok') ||
    text.includes('jumat') ||
    text.includes('senin') ||
    text.includes('rabu') ||
    text.includes('kamis') ||
    text.includes('sabtu') ||
    text.includes('minggu') ||
    text.includes('mendesak') ||
    text.includes('urgent')

  if (isTaskKeyword) {
    let isUrgent = text.includes('mendesak') || text.includes('urgent') || text.includes('penting')
    let deadlineDate: string | undefined = undefined

    const today = new Date()
    if (text.includes('besok')) {
      const d = new Date()
      d.setDate(today.getDate() + 1)
      deadlineDate = d.toISOString().split('T')[0]
    } else if (text.includes('lusa')) {
      const d = new Date()
      d.setDate(today.getDate() + 2)
      deadlineDate = d.toISOString().split('T')[0]
    } else if (text.includes('hari ini')) {
      deadlineDate = today.toISOString().split('T')[0]
    }

    // Clean title
    let cleanTitle = rawInput.value
      .replace(/^(tugas|kuis|pr|praktikum)\s*:\s*/i, '')
      .replace(/^(tugas|kuis|pr|praktikum)\s+/i, '')
      .replace(/\s*(deadline|tenggat|besok|lusa|hari ini|mendesak|urgent).*/i, '')
      .trim()

    if (!cleanTitle) {
      cleanTitle = rawInput.value.trim()
    }

    return {
      type: 'task',
      title: cleanTitle,
      deadline: deadlineDate,
      isUrgent,
    }
  }

  // E. Note (Default)
  let cleanNote = rawInput.value.replace(/^(ide|catatan|note)\s*:\s*/i, '').trim()
  return {
    type: 'note',
    title: cleanNote || rawInput.value.trim(),
  }
})

// 3. Execution to Supabase
async function handleSubmit() {
  if (!rawInput.value.trim() || !props.userId || isSubmitting.value) return
  isSubmitting.value = true

  const intent = parsedIntent.value
  try {
    if (intent.type === 'task') {
      const kuliahArea = props.areas.find(
        (a) => a.name.toLowerCase().includes('kuliah') || a.name.toLowerCase().includes('tugas')
      )
      const areaId = kuliahArea?.id ?? props.areas[0]?.id ?? null

      const { data, error } = await supabase
        .from('tasks')
        .insert({
          user_id: props.userId,
          area_id: areaId,
          title: intent.title,
          deadline: intent.deadline || null,
          is_urgent: !!intent.isUrgent,
          status: 'pending',
        })
        .select()
        .single()

      if (!error && data) {
        emit('created', { type: 'task', data })
      }
    } else if (intent.type === 'hydration') {
      const { data, error } = await supabase
        .from('hydration_logs')
        .insert({
          user_id: props.userId,
          amount_ml: intent.amount || 250,
          logged_at: new Date().toISOString(),
        })
        .select()
        .single()

      if (!error && data) {
        emit('created', { type: 'hydration', data })
      }
    } else if (intent.type === 'sleep') {
      const { data, error } = await supabase
        .from('sleep_logs')
        .insert({
          user_id: props.userId,
          duration_hours: intent.hours || 7.0,
          quality_score: 4,
          bedtime: new Date(Date.now() - (intent.hours || 7) * 3600 * 1000).toISOString(),
          wake_time: new Date().toISOString(),
        })
        .select()
        .single()

      if (!error && data) {
        emit('created', { type: 'sleep', data })
      }
    } else if (intent.type === 'timer') {
      const { data, error } = await supabase
        .from('time_logs')
        .insert({
          user_id: props.userId,
          project_name: intent.projectName || 'Sesi Fokus',
          started_at: new Date().toISOString(),
          ended_at: null,
          duration_minutes: null,
        })
        .select()
        .single()

      if (!error && data) {
        emit('created', { type: 'timer', data })
      }
    } else {
      // Note
      const { data, error } = await supabase
        .from('notes')
        .insert({
          user_id: props.userId,
          content: intent.title,
          tags: ['quick-capture'],
        })
        .select()
        .single()

      if (!error && data) {
        emit('created', { type: 'note', data })
      }
    }

    playNotificationSound('chime')
    closeModal()
  } catch (err) {
    console.error('Quick capture error:', err)
  } finally {
    isSubmitting.value = false
  }
}

function setQuickTemplate(templateText: string) {
  rawInput.value = templateText
  nextTick(() => {
    inputRef.value?.focus()
  })
}
</script>

<template>
  <div>
    <!-- Floating Action Button (FAB) on Mobile & Desktop -->
    <button
      type="button"
      @click="toggleModal"
      class="fixed bottom-24 right-5 sm:bottom-7 sm:right-7 z-30 flex h-13 w-13 items-center justify-center rounded-2xl bg-gray-900 text-white shadow-xl hover:bg-black hover:scale-105 active:scale-95 transition-all cursor-pointer focus:outline-none focus:ring-4 focus:ring-gray-900/30"
      title="Quick Capture Kilat (Ctrl + K)"
      aria-label="Tambah Kilat"
    >
      <span class="text-2xl font-bold leading-none select-none">+</span>
    </button>

    <!-- Modal Command Palette -->
    <div
      v-if="isOpen"
      class="fixed inset-0 z-50 flex items-start justify-center p-4 pt-16 sm:pt-24"
    >
      <!-- Backdrop -->
      <div
        class="fixed inset-0 bg-black/40 backdrop-blur-sm transition-opacity"
        @click="closeModal"
      ></div>

      <!-- Dialog Card -->
      <div
        class="relative w-full max-w-xl rounded-3xl border border-gray-200 bg-white p-5 sm:p-6 shadow-2xl transition-all space-y-4"
      >
        <!-- Header -->
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-gray-900 text-white text-xs font-bold">
              ⚡
            </span>
            <div>
              <h3 class="text-sm font-bold text-gray-900">Universal Quick Capture</h3>
              <p class="text-[11px] text-gray-500">Ketik bebas: tugas, minum, tidur, atau ide kilat</p>
            </div>
          </div>

          <div class="flex items-center gap-1.5">
            <kbd class="hidden sm:inline-block rounded-md bg-gray-100 px-2 py-0.5 text-[10px] font-mono text-gray-500 border border-gray-200">
              ESC
            </kbd>
            <button
              type="button"
              @click="closeModal"
              class="p-1 text-gray-400 hover:text-gray-700 text-sm cursor-pointer"
            >
              ✕
            </button>
          </div>
        </div>

        <!-- Input Bar with Voice Button -->
        <div class="relative flex items-center">
          <input
            ref="inputRef"
            v-model="rawInput"
            type="text"
            placeholder="Contoh: tugas kalkulus kuis besok mendesak..."
            class="w-full rounded-2xl border border-gray-300 bg-gray-50/80 px-4 py-3.5 pr-24 text-sm sm:text-base text-gray-900 placeholder-gray-400 focus:bg-white focus:border-gray-900 focus:outline-none focus:ring-1 focus:ring-gray-900 transition-all min-h-[48px]"
            @keydown.enter="handleSubmit"
          />

          <div class="absolute right-2.5 flex items-center gap-1.5">
            <!-- Voice Dictation Button -->
            <button
              type="button"
              @click="toggleVoice"
              class="flex h-8 w-8 items-center justify-center rounded-xl transition-all cursor-pointer"
              :class="isListening ? 'bg-rose-600 text-white animate-pulse' : 'bg-gray-200/80 hover:bg-gray-300 text-gray-700'"
              title="Dikte Suara (Bicara)"
            >
              <span class="text-xs">🎤</span>
            </button>

            <!-- Submit Button -->
            <button
              type="button"
              @click="handleSubmit"
              :disabled="!rawInput.trim() || isSubmitting"
              class="rounded-xl bg-gray-900 px-3 py-1.5 text-xs font-bold text-white hover:bg-black disabled:opacity-40 transition-colors cursor-pointer shadow-xs min-h-[32px]"
            >
              {{ isSubmitting ? '...' : 'Simpan' }}
            </button>
          </div>
        </div>

        <!-- Voice Listening Banner -->
        <div
          v-if="isListening"
          class="rounded-xl bg-rose-50 border border-rose-200 p-2.5 flex items-center gap-2 text-xs text-rose-800"
        >
          <span class="h-2 w-2 rounded-full bg-rose-600 animate-ping"></span>
          <span class="font-medium">Mendengarkan ucapanmu dalam Bahasa Indonesia... Silakan bicara.</span>
        </div>

        <!-- Smart Intent Preview Pill -->
        <div v-if="rawInput.trim()" class="rounded-xl bg-gray-50 p-3 border border-gray-100 flex items-center justify-between text-xs">
          <div class="flex items-center gap-2 truncate">
            <span class="text-sm">
              {{
                parsedIntent.type === 'task'
                  ? '🎓'
                  : parsedIntent.type === 'hydration'
                  ? '💧'
                  : parsedIntent.type === 'sleep'
                  ? '😴'
                  : parsedIntent.type === 'timer'
                  ? '⏱️'
                  : '💡'
              }}
            </span>
            <span class="font-bold text-gray-800 capitalize">
              {{ parsedIntent.type }}:
            </span>
            <span class="text-gray-600 truncate">
              {{ parsedIntent.title }}
            </span>
          </div>

          <div class="flex items-center gap-1.5 shrink-0 text-[11px]">
            <span v-if="parsedIntent.deadline" class="rounded bg-indigo-50 px-1.5 py-0.5 text-indigo-700 font-semibold border border-indigo-100">
              📅 {{ parsedIntent.deadline }}
            </span>
            <span v-if="parsedIntent.isUrgent" class="rounded bg-rose-100 px-1.5 py-0.5 text-rose-700 font-bold">
              ⚠️ Urgent
            </span>
          </div>
        </div>

        <!-- Quick Template Chips -->
        <div class="pt-1 space-y-1.5">
          <p class="text-[11px] font-semibold text-gray-500 uppercase tracking-wider">Template Cepat:</p>
          <div class="flex flex-wrap gap-1.5 text-xs">
            <button
              type="button"
              @click="setQuickTemplate('tugas Kuliah: ')"
              class="rounded-lg bg-gray-100 px-2.5 py-1 text-gray-700 hover:bg-gray-200 cursor-pointer"
            >
              🎓 + Tugas Kuliah
            </button>
            <button
              type="button"
              @click="setQuickTemplate('minum 250ml')"
              class="rounded-lg bg-cyan-50 text-cyan-800 px-2.5 py-1 hover:bg-cyan-100 cursor-pointer border border-cyan-100"
            >
              💧 + Minum 250ml
            </button>
            <button
              type="button"
              @click="setQuickTemplate('tidur 7.5 jam')"
              class="rounded-lg bg-purple-50 text-purple-800 px-2.5 py-1 hover:bg-purple-100 cursor-pointer border border-purple-100"
            >
              😴 + Tidur 7.5 Jam
            </button>
            <button
              type="button"
              @click="setQuickTemplate('fokus: Belajar Mandiri')"
              class="rounded-lg bg-emerald-50 text-emerald-800 px-2.5 py-1 hover:bg-emerald-100 cursor-pointer border border-emerald-100"
            >
              ⏱️ + Mulai Timer
            </button>
            <button
              type="button"
              @click="setQuickTemplate('ide: ')"
              class="rounded-lg bg-amber-50 text-amber-800 px-2.5 py-1 hover:bg-amber-100 cursor-pointer border border-amber-100"
            >
              💡 + Catat Ide
            </button>
          </div>
        </div>

        <!-- Keyboard Hint -->
        <div class="text-[11px] text-gray-400 text-center pt-1 border-t border-gray-100">
          Tekan <kbd class="font-mono font-bold text-gray-600">Enter</kbd> untuk menyimpan seketika.
        </div>
      </div>
    </div>
  </div>
</template>
