<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  userId: string
}>()

interface HobbyItem {
  id: number
  title: string
  category: 'gaming' | 'reading' | 'movies' | 'sports' | 'creative' | 'other'
  status: 'wishlist' | 'in_progress' | 'completed'
  targetDurationMinutes: number
  totalSpentMinutes: number
  notes: string
  rating: number // 1-5 energy recharge rating
}

interface HobbySession {
  id: number
  hobbyTitle: string
  category: 'gaming' | 'reading' | 'movies' | 'sports' | 'creative' | 'other'
  durationMinutes: number
  loggedAt: string
  rechargeScore: number // 1-5 (1: draining, 5: highly rejuvenating)
}

// Data Dummy / Initial State Mahasiswa
const hobbies = ref<HobbyItem[]>([
  {
    id: 1,
    title: 'Main Black Myth: Wukong',
    category: 'gaming',
    status: 'in_progress',
    targetDurationMinutes: 120,
    totalSpentMinutes: 80,
    notes: 'Reward setelah beres revisi Bab 2 Skripsi',
    rating: 5,
  },
  {
    id: 2,
    title: 'Baca Buku "Atomic Habits"',
    category: 'reading',
    status: 'in_progress',
    targetDurationMinutes: 30,
    totalSpentMinutes: 20,
    notes: '15 menit sebelum tidur malam',
    rating: 4,
  },
  {
    id: 3,
    title: 'Futsal bareng temen kampus',
    category: 'sports',
    status: 'wishlist',
    targetDurationMinutes: 90,
    totalSpentMinutes: 0,
    notes: 'Jadwal rutin Jumat sore lapangan kampus',
    rating: 5,
  },
  {
    id: 4,
    title: 'Nonton Frieren: Beyond Journey\'s End',
    category: 'movies',
    status: 'completed',
    targetDurationMinutes: 180,
    totalSpentMinutes: 180,
    notes: 'Sangat menenangkan & inspiratif',
    rating: 5,
  },
])

const recentSessions = ref<HobbySession[]>([
  {
    id: 101,
    hobbyTitle: 'Main Black Myth: Wukong',
    category: 'gaming',
    durationMinutes: 45,
    loggedAt: 'Kemarin, 21:00',
    rechargeScore: 5,
  },
  {
    id: 102,
    hobbyTitle: 'Baca Buku "Atomic Habits"',
    category: 'reading',
    durationMinutes: 20,
    loggedAt: 'Hari ini, 13:00',
    rechargeScore: 4,
  },
])

// Filter & Category
const selectedCategory = ref<string>('all')
const selectedStatus = ref<'all' | 'wishlist' | 'in_progress' | 'completed'>('all')

const categoryIcons: Record<string, string> = {
  gaming: '🎮',
  reading: '📚',
  movies: '🎬',
  sports: '⚽',
  creative: '🎨',
  other: '☕',
}

const categoryLabels: Record<string, string> = {
  gaming: 'Gaming',
  reading: 'Membaca',
  movies: 'Film / Series',
  sports: 'Olahraga / Fisik',
  creative: 'Kreatif / Seni',
  other: 'Lainnya',
}

// Guilt-Free Me-Time Allowance (Target harian: misal 90 menit)
const dailyMeTimeQuotaMinutes = ref(90)
const todayMeTimeSpentMinutes = computed(() => {
  return recentSessions.value
    .filter(s => s.loggedAt.includes('Hari ini'))
    .reduce((acc, curr) => acc + curr.durationMinutes, 0)
})

const meTimeRemainingMinutes = computed(() => {
  return Math.max(0, dailyMeTimeQuotaMinutes.value - todayMeTimeSpentMinutes.value)
})

const meTimePercentage = computed(() => {
  return Math.min(100, Math.round((todayMeTimeSpentMinutes.value / dailyMeTimeQuotaMinutes.value) * 100))
})

// Filtered Hobbies
const filteredHobbies = computed(() => {
  return hobbies.value.filter(item => {
    const matchCat = selectedCategory.value === 'all' || item.category === selectedCategory.value
    const matchStatus = selectedStatus.value === 'all' || item.status === selectedStatus.value
    return matchCat && matchStatus
  })
})

// Modal Tambah Hobi
const showAddModal = ref(false)
const newHobby = ref<{
  title: string
  category: 'gaming' | 'reading' | 'movies' | 'sports' | 'creative' | 'other'
  targetDurationMinutes: number
  notes: string
}>({
  title: '',
  category: 'gaming',
  targetDurationMinutes: 60,
  notes: '',
})

function handleAddHobby() {
  if (!newHobby.value.title.trim()) return

  hobbies.value.unshift({
    id: Date.now(),
    title: newHobby.value.title.trim(),
    category: newHobby.value.category,
    status: 'wishlist',
    targetDurationMinutes: newHobby.value.targetDurationMinutes || 60,
    totalSpentMinutes: 0,
    notes: newHobby.value.notes.trim(),
    rating: 5,
  })

  newHobby.value = {
    title: '',
    category: 'gaming',
    targetDurationMinutes: 60,
    notes: '',
  }
  showAddModal.value = false
}

// Log Me-Time Session Modal
const showLogSessionModal = ref(false)
const sessionHobbyTitle = ref('')
const sessionDuration = ref(30)
const sessionRecharge = ref(5)

function openLogSession(hobby?: HobbyItem) {
  if (hobby) {
    sessionHobbyTitle.value = hobby.title
  } else {
    sessionHobbyTitle.value = hobbies.value[0]?.title || 'Me-Time Santai'
  }
  sessionDuration.value = 30
  sessionRecharge.value = 5
  showLogSessionModal.value = true
}

function handleSaveSession() {
  if (!sessionHobbyTitle.value.trim()) return

  const item = hobbies.value.find(h => h.title === sessionHobbyTitle.value)
  const cat = item ? item.category : 'other'

  recentSessions.value.unshift({
    id: Date.now(),
    hobbyTitle: sessionHobbyTitle.value,
    category: cat,
    durationMinutes: sessionDuration.value,
    loggedAt: 'Hari ini, Baru saja',
    rechargeScore: sessionRecharge.value,
  })

  if (item) {
    item.totalSpentMinutes += sessionDuration.value
    if (item.status === 'wishlist') item.status = 'in_progress'
    if (item.totalSpentMinutes >= item.targetDurationMinutes && item.targetDurationMinutes > 0) {
      item.status = 'completed'
    }
  }

  showLogSessionModal.value = false
}

function cycleStatus(item: HobbyItem) {
  if (item.status === 'wishlist') {
    item.status = 'in_progress'
  } else if (item.status === 'in_progress') {
    item.status = 'completed'
  } else {
    item.status = 'wishlist'
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header Title & Action -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-5 rounded-2xl border border-gray-200 shadow-xs">
      <div>
        <div class="flex items-center gap-2">
          <span class="text-2xl">🎨</span>
          <h2 class="text-lg font-bold text-gray-900">Hobby & Refreshing Hub</h2>
          <span class="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-800">Priority #4</span>
        </div>
        <p class="text-xs text-gray-500 mt-1">
          Guilt-free me-time untuk mahasiswa. Belajar & riset butuh recharge energi agar terhindar dari burnout.
        </p>
      </div>

      <div class="flex items-center gap-2">
        <button
          @click="openLogSession()"
          class="flex items-center gap-1.5 rounded-xl border border-amber-300 bg-amber-50 px-3.5 py-2 text-xs font-semibold text-amber-900 hover:bg-amber-100 transition-colors shadow-2xs"
        >
          <span>⏱️</span>
          <span>Catat Sesi Santai</span>
        </button>
        <button
          @click="showAddModal = true"
          class="flex items-center gap-1.5 rounded-xl bg-amber-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-amber-700 transition-colors shadow-xs"
        >
          <span>➕</span>
          <span>Tambah Wishlist Hobi</span>
        </button>
      </div>
    </div>

    <!-- Guilt-Free Me-Time Radar & Energy Recharge Status -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
      <!-- Card 1: Kuota Santai Harian -->
      <div class="rounded-2xl border border-amber-200 bg-gradient-to-br from-amber-50/70 to-orange-50/50 p-5 shadow-xs">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold uppercase tracking-wider text-amber-900">Alokasi Guilt-Free Me-Time</span>
          <span class="text-xl">☕</span>
        </div>
        <div class="mt-3 flex items-baseline gap-2">
          <span class="text-3xl font-extrabold text-amber-950">{{ todayMeTimeSpentMinutes }}</span>
          <span class="text-xs text-amber-700 font-medium">/ {{ dailyMeTimeQuotaMinutes }} Menit Hari Ini</span>
        </div>
        <div class="mt-3 w-full bg-amber-200/60 rounded-full h-2 overflow-hidden">
          <div
            class="bg-amber-500 h-2 rounded-full transition-all duration-500"
            :style="{ width: `${meTimePercentage}%` }"
          ></div>
        </div>
        <p class="mt-2.5 text-[11px] text-amber-800">
          Sisa kuota santai tanpa rasa bersalah: <strong>{{ meTimeRemainingMinutes }} menit</strong>.
        </p>
      </div>

      <!-- Card 2: Dopamine Balance Mindset -->
      <div class="rounded-2xl border border-gray-200 bg-white p-5 shadow-xs flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold uppercase tracking-wider text-gray-500">Mindset Mahasiswa</span>
            <span class="text-xl">🧘‍♂️</span>
          </div>
          <p class="text-xs text-gray-700 mt-2 leading-relaxed">
            <em>"Istirahat bukan hadiah setelah kerja rodi, tapi bahan bakar agar otak tetap tajam saat skripsi & kuliah."</em>
          </p>
        </div>
        <div class="pt-3 border-t border-gray-100 flex items-center justify-between text-[11px] text-gray-500">
          <span>Target Rejuvenasi</span>
          <span class="font-semibold text-emerald-600">High Energy Return 🔋</span>
        </div>
      </div>

      <!-- Card 3: Statistik Koleksi Hobi -->
      <div class="rounded-2xl border border-gray-200 bg-white p-5 shadow-xs flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold uppercase tracking-wider text-gray-500">Koleksi Hobi</span>
            <span class="text-xl">🎯</span>
          </div>
          <div class="grid grid-cols-3 gap-2 mt-3 text-center">
            <div class="bg-gray-50 p-2 rounded-xl border border-gray-100">
              <span class="text-lg font-bold text-gray-900">{{ hobbies.filter(h => h.status === 'wishlist').length }}</span>
              <p class="text-[10px] text-gray-500">Wishlist</p>
            </div>
            <div class="bg-amber-50 p-2 rounded-xl border border-amber-100">
              <span class="text-lg font-bold text-amber-800">{{ hobbies.filter(h => h.status === 'in_progress').length }}</span>
              <p class="text-[10px] text-amber-700">Aktif</p>
            </div>
            <div class="bg-emerald-50 p-2 rounded-xl border border-emerald-100">
              <span class="text-lg font-bold text-emerald-800">{{ hobbies.filter(h => h.status === 'completed').length }}</span>
              <p class="text-[10px] text-emerald-700">Tuntas</p>
            </div>
          </div>
        </div>
        <div class="pt-3 text-[11px] text-gray-500 text-right">
          Total waktu santai: <strong>{{ hobbies.reduce((acc, h) => acc + h.totalSpentMinutes, 0) }} menit</strong>
        </div>
      </div>
    </div>

    <!-- Filter Bar -->
    <div class="flex flex-wrap items-center justify-between gap-3 bg-white p-3.5 rounded-xl border border-gray-200 shadow-2xs">
      <!-- Kategori Filter -->
      <div class="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-1">
        <button
          @click="selectedCategory = 'all'"
          class="rounded-lg px-2.5 py-1 text-xs font-semibold transition-colors"
          :class="selectedCategory === 'all' ? 'bg-amber-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
        >
          Semua ({{ hobbies.length }})
        </button>
        <button
          v-for="(label, key) in categoryLabels"
          :key="key"
          @click="selectedCategory = key"
          class="flex items-center gap-1 rounded-lg px-2.5 py-1 text-xs font-semibold transition-colors whitespace-nowrap"
          :class="selectedCategory === key ? 'bg-amber-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
        >
          <span>{{ categoryIcons[key] }}</span>
          <span>{{ label }}</span>
        </button>
      </div>

      <!-- Status Filter -->
      <div class="flex items-center gap-1 text-xs">
        <span class="text-gray-400 mr-1">Status:</span>
        <button
          @click="selectedStatus = 'all'"
          class="px-2 py-0.5 rounded text-xs font-medium"
          :class="selectedStatus === 'all' ? 'bg-gray-900 text-white' : 'text-gray-600 hover:text-gray-900'"
        >
          Semua
        </button>
        <button
          @click="selectedStatus = 'in_progress'"
          class="px-2 py-0.5 rounded text-xs font-medium"
          :class="selectedStatus === 'in_progress' ? 'bg-gray-900 text-white' : 'text-gray-600 hover:text-gray-900'"
        >
          Sedang Dimainkan/Baca
        </button>
        <button
          @click="selectedStatus = 'wishlist'"
          class="px-2 py-0.5 rounded text-xs font-medium"
          :class="selectedStatus === 'wishlist' ? 'bg-gray-900 text-white' : 'text-gray-600 hover:text-gray-900'"
        >
          Wishlist
        </button>
      </div>
    </div>

    <!-- Daftar Hobi & Aktivitas Santai -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div
        v-for="item in filteredHobbies"
        :key="item.id"
        class="rounded-2xl border bg-white p-4 shadow-xs transition-all hover:border-amber-300 flex flex-col justify-between"
        :class="item.status === 'completed' ? 'border-gray-200 opacity-75' : 'border-gray-200'"
      >
        <div>
          <div class="flex items-start justify-between gap-3">
            <div class="flex items-center gap-2">
              <span class="text-xl p-1.5 bg-gray-50 rounded-lg border border-gray-100">{{ categoryIcons[item.category] }}</span>
              <div>
                <h3 class="text-sm font-bold text-gray-900">{{ item.title }}</h3>
                <span class="text-[11px] text-gray-500">{{ categoryLabels[item.category] }}</span>
              </div>
            </div>

            <!-- Status Badge Clickable -->
            <button
              @click="cycleStatus(item)"
              class="rounded-full px-2.5 py-0.5 text-[11px] font-semibold transition-transform active:scale-95 cursor-pointer shrink-0"
              :class="{
                'bg-amber-100 text-amber-800': item.status === 'in_progress',
                'bg-gray-100 text-gray-700': item.status === 'wishlist',
                'bg-emerald-100 text-emerald-800': item.status === 'completed',
              }"
              title="Klik untuk mengubah status"
            >
              {{ item.status === 'in_progress' ? '⚡ Sedang Berjalan' : item.status === 'wishlist' ? '📋 Wishlist' : '✅ Selesai' }}
            </button>
          </div>

          <!-- Notes -->
          <p v-if="item.notes" class="mt-2.5 text-xs text-gray-600 bg-gray-50 p-2 rounded-lg border border-gray-100">
            💬 {{ item.notes }}
          </p>

          <!-- Durasi Tracker Bar -->
          <div class="mt-3 space-y-1">
            <div class="flex items-center justify-between text-[11px] text-gray-500">
              <span>Progres Waktu Santai:</span>
              <span class="font-medium text-gray-700">{{ item.totalSpentMinutes }} / {{ item.targetDurationMinutes }} menit</span>
            </div>
            <div class="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden">
              <div
                class="bg-amber-500 h-1.5 rounded-full"
                :style="{ width: `${Math.min(100, Math.round((item.totalSpentMinutes / (item.targetDurationMinutes || 1)) * 100))}%` }"
              ></div>
            </div>
          </div>
        </div>

        <!-- Card Footer -->
        <div class="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between text-xs">
          <div class="flex items-center gap-1 text-amber-500">
            <span v-for="star in 5" :key="star" :class="star <= item.rating ? 'opacity-100' : 'opacity-25'">⭐</span>
            <span class="text-[10px] text-gray-400 ml-1">Recharge</span>
          </div>

          <button
            @click="openLogSession(item)"
            class="text-xs font-semibold text-amber-700 hover:text-amber-800 hover:underline flex items-center gap-1 cursor-pointer"
          >
            <span>+ Catat Sesi</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Riwayat Sesi Me-Time Terakhir -->
    <div class="rounded-2xl border border-gray-200 bg-white p-5 shadow-xs">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-sm font-bold text-gray-900 flex items-center gap-2">
          <span>📜</span>
          <span>Riwayat Recharge & Me-Time Terakhir</span>
        </h3>
        <span class="text-xs text-gray-400">{{ recentSessions.length }} sesi tercatat</span>
      </div>

      <div class="divide-y divide-gray-100">
        <div
          v-for="session in recentSessions"
          :key="session.id"
          class="py-2.5 flex items-center justify-between text-xs"
        >
          <div class="flex items-center gap-2.5">
            <span class="text-base">{{ categoryIcons[session.category] }}</span>
            <div>
              <p class="font-semibold text-gray-900">{{ session.hobbyTitle }}</p>
              <p class="text-[11px] text-gray-500">{{ session.loggedAt }} • {{ session.durationMinutes }} menit</p>
            </div>
          </div>

          <div class="flex items-center gap-1.5 bg-emerald-50 px-2 py-1 rounded-lg border border-emerald-100">
            <span class="text-[11px] font-semibold text-emerald-800">Energy Return: {{ session.rechargeScore }}/5 ⚡</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Tambah Wishlist Hobi -->
    <div
      v-if="showAddModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-xs"
    >
      <div class="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl border border-gray-100 space-y-4">
        <div class="flex items-center justify-between">
          <h3 class="text-base font-bold text-gray-900">Tambah Wishlist Hobi / Me-Time</h3>
          <button @click="showAddModal = false" class="text-gray-400 hover:text-gray-600 text-lg">✕</button>
        </div>

        <div class="space-y-3">
          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">Nama Hobi / Aktivitas</label>
            <input
              v-model="newHobby.title"
              type="text"
              placeholder="Contoh: Main Valorant bareng kating, Baca Manga One Piece"
              class="w-full rounded-xl border border-gray-300 px-3 py-2 text-xs focus:border-amber-600 focus:outline-none"
            />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-semibold text-gray-700 mb-1">Kategori</label>
              <select
                v-model="newHobby.category"
                class="w-full rounded-xl border border-gray-300 px-3 py-2 text-xs focus:border-amber-600 focus:outline-none bg-white"
              >
                <option v-for="(label, key) in categoryLabels" :key="key" :value="key">
                  {{ categoryIcons[key] }} {{ label }}
                </option>
              </select>
            </div>

            <div>
              <label class="block text-xs font-semibold text-gray-700 mb-1">Target Menit</label>
              <input
                v-model.number="newHobby.targetDurationMinutes"
                type="number"
                min="10"
                step="10"
                class="w-full rounded-xl border border-gray-300 px-3 py-2 text-xs focus:border-amber-600 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">Catatan / Kapan mau dilakukan</label>
            <textarea
              v-model="newHobby.notes"
              rows="2"
              placeholder="Contoh: Buat reward kalau tugas Kalkulus sudah submit!"
              class="w-full rounded-xl border border-gray-300 px-3 py-2 text-xs focus:border-amber-600 focus:outline-none"
            ></textarea>
          </div>
        </div>

        <div class="flex items-center justify-end gap-2 pt-2">
          <button
            @click="showAddModal = false"
            class="rounded-xl border border-gray-200 px-3.5 py-2 text-xs font-semibold text-gray-600 hover:bg-gray-50"
          >
            Batal
          </button>
          <button
            @click="handleAddHobby"
            :disabled="!newHobby.title.trim()"
            class="rounded-xl bg-amber-600 px-4 py-2 text-xs font-semibold text-white hover:bg-amber-700 disabled:opacity-50"
          >
            Simpan Wishlist
          </button>
        </div>
      </div>
    </div>

    <!-- Modal Catat Sesi Me-Time -->
    <div
      v-if="showLogSessionModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 backdrop-blur-xs"
    >
      <div class="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl border border-gray-100 space-y-4">
        <div class="flex items-center justify-between">
          <h3 class="text-base font-bold text-gray-900">Catat Sesi Me-Time / Refreshing</h3>
          <button @click="showLogSessionModal = false" class="text-gray-400 hover:text-gray-600 text-lg">✕</button>
        </div>

        <div class="space-y-3">
          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">Aktivitas Santai</label>
            <input
              v-model="sessionHobbyTitle"
              type="text"
              class="w-full rounded-xl border border-gray-300 px-3 py-2 text-xs focus:border-amber-600 focus:outline-none"
            />
          </div>

          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">Durasi Santai (Menit)</label>
            <div class="flex items-center gap-2">
              <button
                v-for="dur in [15, 30, 45, 60, 90]"
                :key="dur"
                type="button"
                @click="sessionDuration = dur"
                class="rounded-lg border px-2.5 py-1 text-xs font-medium transition-colors"
                :class="sessionDuration === dur ? 'border-amber-600 bg-amber-50 text-amber-900 font-bold' : 'border-gray-200 text-gray-600 hover:bg-gray-50'"
              >
                {{ dur }}m
              </button>
            </div>
          </div>

          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">
              Level Recharge Energi (1: Tetap Lemes ➔ 5: Segar Bugar)
            </label>
            <div class="flex items-center gap-2">
              <button
                v-for="score in 5"
                :key="score"
                type="button"
                @click="sessionRecharge = score"
                class="flex-1 py-1.5 rounded-lg border text-xs font-bold transition-colors"
                :class="sessionRecharge === score ? 'border-amber-600 bg-amber-500 text-white' : 'border-gray-200 text-gray-600 hover:bg-gray-50'"
              >
                {{ score }} ⚡
              </button>
            </div>
          </div>
        </div>

        <div class="flex items-center justify-end gap-2 pt-2">
          <button
            @click="showLogSessionModal = false"
            class="rounded-xl border border-gray-200 px-3.5 py-2 text-xs font-semibold text-gray-600 hover:bg-gray-50"
          >
            Batal
          </button>
          <button
            @click="handleSaveSession"
            class="rounded-xl bg-amber-600 px-4 py-2 text-xs font-semibold text-white hover:bg-amber-700"
          >
            Simpan Sesi
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
