<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { supabase } from '../lib/supabase'

interface ProfileItem {
  full_name: string | null
}

interface NoteItem {
  id: number
  content: string
  tags: string[] | null
  created_at: string
}

interface TimeLogItem {
  id: number
  project_name: string
  started_at: string
  ended_at: string | null
  duration_minutes: number | null
}

const userEmail = ref<string | null>(null)
const profile = ref<ProfileItem | null>(null)
const profileLoaded = ref(false)

const notes = ref<NoteItem[]>([])
const notesLoading = ref(true)
const notesError = ref<string | null>(null)

const timeLogs = ref<TimeLogItem[]>([])
const timeLogsLoading = ref(true)
const timeLogsError = ref<string | null>(null)

const loggingOut = ref(false)

const dateTimeFormatter = new Intl.DateTimeFormat(undefined, {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
})

function formatDateTime(isoString: string | null): string {
  if (!isoString) return '-'
  try {
    return dateTimeFormatter.format(new Date(isoString))
  } catch {
    return '-'
  }
}

const activeTimer = computed(() => {
  return timeLogs.value.find((t) => t.ended_at === null) ?? null
})

async function fetchData() {
  const {
    data: { session },
  } = await supabase.auth.getSession()

  if (!session) return
  userEmail.value = session.user?.email ?? null

  const profilePromise = supabase
    .from('profiles')
    .select('full_name')
    .maybeSingle()

  const notesPromise = supabase
    .from('notes')
    .select('id, content, tags, created_at')
    .order('created_at', { ascending: false })
    .limit(20)

  const timeLogsPromise = supabase
    .from('time_logs')
    .select('id, project_name, started_at, ended_at, duration_minutes')
    .order('started_at', { ascending: false })
    .limit(20)

  const [profileRes, notesRes, timeLogsRes] = await Promise.allSettled([
    profilePromise,
    notesPromise,
    timeLogsPromise,
  ])

  profileLoaded.value = true

  // 1. Profil
  if (profileRes.status === 'fulfilled') {
    const { data, error } = profileRes.value
    if (!error && data) {
      profile.value = data
    } else {
      profile.value = null
    }
  } else {
    profile.value = null
  }

  // 2. Notes
  notesLoading.value = false
  if (notesRes.status === 'fulfilled') {
    const { data, error } = notesRes.value
    if (error) {
      notesError.value = 'Gagal memuat catatan.'
    } else {
      notes.value = data ?? []
    }
  } else {
    notesError.value = 'Gagal memuat catatan.'
  }

  // 3. Time Logs
  timeLogsLoading.value = false
  if (timeLogsRes.status === 'fulfilled') {
    const { data, error } = timeLogsRes.value
    if (error) {
      timeLogsError.value = 'Gagal memuat catatan waktu.'
    } else {
      timeLogs.value = data ?? []
    }
  } else {
    timeLogsError.value = 'Gagal memuat catatan waktu.'
  }
}

async function handleLogout() {
  loggingOut.value = true
  try {
    await supabase.auth.signOut()
  } finally {
    loggingOut.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="min-h-screen bg-gray-50 text-gray-900">
    <!-- Header -->
    <header class="border-b border-gray-200 bg-white">
      <div class="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
        <div>
          <h1 class="text-xl font-bold tracking-tight text-gray-900">Second Brain</h1>
          <p class="text-xs text-gray-500">
            <span v-if="profile?.full_name" class="font-semibold text-gray-800">
              {{ profile.full_name }}
            </span>
            <span v-if="profile?.full_name" class="mx-1.5 text-gray-300">•</span>
            <span>{{ userEmail || '...' }}</span>
          </p>
        </div>
        <button
          @click="handleLogout"
          :disabled="loggingOut"
          class="rounded-lg border border-gray-300 bg-white px-3.5 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:ring-offset-2 disabled:opacity-50"
        >
          {{ loggingOut ? 'Keluar...' : 'Logout' }}
        </button>
      </div>
    </header>

    <main class="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      <!-- Banner jika akun belum connect Telegram -->
      <div
        v-if="profileLoaded && !profile"
        class="mb-8 rounded-xl border border-amber-200 bg-amber-50 p-4 text-amber-900 shadow-sm"
      >
        <div class="flex items-start gap-3">
          <span class="text-lg">ℹ️</span>
          <div>
            <h2 class="text-sm font-semibold">Akun Belum Terhubung ke Telegram</h2>
            <p class="mt-1 text-xs leading-relaxed text-amber-800">
              Akun Supabase ini belum ditautkan ke bot Telegram. Untuk menghubungkan profil kamu, kirim perintah
              <code class="rounded bg-amber-100 px-1.5 py-0.5 font-mono text-xs font-semibold text-amber-900">/connect KODE-UNDANGAN</code>
              ke bot Telegram Second Brain.
            </p>
          </div>
        </div>
      </div>

      <!-- Grid 2 Kolom: Time Logs & Notes -->
      <div class="grid grid-cols-1 gap-8 lg:grid-cols-2">
        <!-- Kolom 1: Deep Work & Time Logs -->
        <section class="space-y-4">
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-bold text-gray-900">Deep Work Tracker</h2>
            <span class="text-xs text-gray-500">20 sesi terbaru</span>
          </div>

          <!-- Highlight Timer Aktif -->
          <div
            v-if="activeTimer"
            class="relative overflow-hidden rounded-xl border border-emerald-200 bg-emerald-50/70 p-5 shadow-sm"
          >
            <div class="flex items-center justify-between">
              <span class="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-800">
                <span class="h-2 w-2 animate-pulse rounded-full bg-emerald-500"></span>
                Timer Sedang Berjalan
              </span>
              <span class="text-xs text-emerald-700">
                Dimulai: {{ formatDateTime(activeTimer.started_at) }}
              </span>
            </div>
            <h3 class="mt-2 text-xl font-bold text-emerald-950">
              {{ activeTimer.project_name }}
            </h3>
            <p class="mt-1 text-xs text-emerald-800">
              Kirim "udahan dulu" ke bot Telegram untuk menghentikan timer ini.
            </p>
          </div>

          <!-- Time Logs Content States -->
          <div class="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <div v-if="timeLogsLoading" class="py-8 text-center text-sm text-gray-500">
              Memuat data sesi kerja...
            </div>

            <div
              v-else-if="timeLogsError"
              class="rounded-lg bg-rose-50 p-4 text-sm text-rose-700 border border-rose-200"
            >
              {{ timeLogsError }}
            </div>

            <div
              v-else-if="timeLogs.length === 0"
              class="py-8 text-center text-sm text-gray-500"
            >
              Belum ada riwayat sesi deep work.<br />
              <span class="text-xs text-gray-400">
                Kirim pesan misalnya <em>"mulai ngoding second brain"</em> ke Telegram.
              </span>
            </div>

            <ul v-else class="divide-y divide-gray-100">
              <li
                v-for="item in timeLogs"
                :key="item.id"
                class="flex items-center justify-between py-3.5 first:pt-0 last:pb-0"
              >
                <div>
                  <div class="flex items-center gap-2">
                    <span class="font-medium text-gray-900">{{ item.project_name }}</span>
                    <span
                      v-if="item.ended_at === null"
                      class="rounded bg-emerald-100 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-800"
                    >
                      Aktif
                    </span>
                  </div>
                  <div class="mt-0.5 text-xs text-gray-500">
                    {{ formatDateTime(item.started_at) }}
                    <span v-if="item.ended_at"> → {{ formatDateTime(item.ended_at) }}</span>
                  </div>
                </div>
                <div class="text-right">
                  <span
                    v-if="item.duration_minutes !== null"
                    class="font-mono text-sm font-semibold text-gray-800"
                  >
                    {{ item.duration_minutes }} m
                  </span>
                  <span v-else class="text-xs text-emerald-600 font-medium">berjalan</span>
                </div>
              </li>
            </ul>
          </div>
        </section>

        <!-- Kolom 2: Notes & Ideas -->
        <section class="space-y-4">
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-bold text-gray-900">Catatan & Ide</h2>
            <span class="text-xs text-gray-500">20 catatan terbaru</span>
          </div>

          <!-- Notes Content States -->
          <div class="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
            <div v-if="notesLoading" class="py-8 text-center text-sm text-gray-500">
              Memuat catatan...
            </div>

            <div
              v-else-if="notesError"
              class="rounded-lg bg-rose-50 p-4 text-sm text-rose-700 border border-rose-200"
            >
              {{ notesError }}
            </div>

            <div
              v-else-if="notes.length === 0"
              class="py-8 text-center text-sm text-gray-500"
            >
              Belum ada catatan yang tersimpan.<br />
              <span class="text-xs text-gray-400">
                Kirim ide apa pun lewat Telegram untuk menyimpannya otomatis.
              </span>
            </div>

            <ul v-else class="divide-y divide-gray-100">
              <li
                v-for="note in notes"
                :key="note.id"
                class="py-3.5 first:pt-0 last:pb-0"
              >
                <p class="whitespace-pre-wrap text-sm leading-relaxed text-gray-800">
                  {{ note.content }}
                </p>
                <div class="mt-2 flex flex-wrap items-center justify-between gap-2">
                  <div class="flex flex-wrap gap-1.5">
                    <span
                      v-for="tag in note.tags ?? []"
                      :key="tag"
                      class="rounded-md bg-gray-100 px-2 py-0.5 text-xs text-gray-600"
                    >
                      #{{ tag }}
                    </span>
                  </div>
                  <span class="text-xs text-gray-400">
                    {{ formatDateTime(note.created_at) }}
                  </span>
                </div>
              </li>
            </ul>
          </div>
        </section>
      </div>
    </main>
  </div>
</template>
