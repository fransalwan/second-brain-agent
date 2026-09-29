<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../lib/supabase'

const props = defineProps<{
  userId?: string | null
  userEmail?: string | null
}>()

const router = useRouter()

const isOpen = ref(false)
const activeTab = ref<'policy' | 'export' | 'delete'>('policy')

const isExporting = ref(false)
const exportSuccess = ref(false)

const deleteConfirmation = ref('')
const isDeleting = ref(false)
const deleteError = ref('')

function openModal(initialTab: 'policy' | 'export' | 'delete' = 'policy') {
  activeTab.value = initialTab
  deleteConfirmation.value = ''
  deleteError.value = ''
  exportSuccess.value = false
  isOpen.value = true
}

function closeModal() {
  isOpen.value = false
}

defineExpose({
  openModal,
  closeModal,
})

// 1. Ekspor Seluruh Data Pengguna (JSON)
async function handleExportData() {
  if (!props.userId) return
  isExporting.value = true
  exportSuccess.value = false

  try {
    const [tasksRes, notesRes, timeLogsRes, habitsRes, habitLogsRes] = await Promise.all([
      supabase.from('tasks').select('*').eq('user_id', props.userId),
      supabase.from('notes').select('*').eq('user_id', props.userId),
      supabase.from('time_logs').select('*').eq('user_id', props.userId),
      supabase.from('habits').select('*').eq('user_id', props.userId),
      supabase.from('habit_logs').select('*'),
    ])

    // Ambil data localStorage per user jika ada
    let localHobbies: any[] = []
    let localSessions: any[] = []
    try {
      const hRaw = localStorage.getItem(`secondbrain_hobbies_${props.userId}`)
      if (hRaw) localHobbies = JSON.parse(hRaw)
      const sRaw = localStorage.getItem(`secondbrain_hobby_sessions_${props.userId}`)
      if (sRaw) localSessions = JSON.parse(sRaw)
    } catch {}

    const backupPayload = {
      app: 'Second Brain (Student Edition)',
      version: '2.1.0',
      exportedAt: new Date().toISOString(),
      account: {
        id: props.userId,
        email: props.userEmail,
      },
      data: {
        tasks: tasksRes.data ?? [],
        notes: notesRes.data ?? [],
        timeLogs: timeLogsRes.data ?? [],
        habits: habitsRes.data ?? [],
        habitLogs: habitLogsRes.data ?? [],
        hobbies: localHobbies,
        hobbySessions: localSessions,
      },
    }

    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(backupPayload, null, 2))
    const downloadAnchor = document.createElement('a')
    const fileName = `secondbrain_backup_${new Date().toISOString().split('T')[0]}.json`
    downloadAnchor.setAttribute('href', dataStr)
    downloadAnchor.setAttribute('download', fileName)
    document.body.appendChild(downloadAnchor)
    downloadAnchor.click()
    downloadAnchor.remove()

    exportSuccess.value = true
  } catch (err: any) {
    console.error('Failed to export user data:', err)
  } finally {
    isExporting.value = false
  }
}

// 2. Hapus Akun & Seluruh Data Secara Permanen (Self-Destruct)
async function handleDeleteAllData() {
  if (deleteConfirmation.value.trim().toUpperCase() !== 'HAPUS') {
    deleteError.value = 'Silakan ketik "HAPUS" dengan huruf kapital untuk mengonfirmasi.'
    return
  }

  if (!props.userId) return
  isDeleting.value = true
  deleteError.value = ''

  try {
    // Hapus seluruh baris di database Supabase yang dimiliki user
    await Promise.all([
      supabase.from('tasks').delete().eq('user_id', props.userId),
      supabase.from('notes').delete().eq('user_id', props.userId),
      supabase.from('time_logs').delete().eq('user_id', props.userId),
      supabase.from('habit_logs').delete().eq('user_id', props.userId),
      supabase.from('habits').delete().eq('user_id', props.userId),
      supabase.from('profiles').delete().eq('id', props.userId),
    ])

    // Bersihkan penyimpanan browser
    try {
      localStorage.removeItem(`secondbrain_hobbies_${props.userId}`)
      localStorage.removeItem(`secondbrain_hobby_sessions_${props.userId}`)
      localStorage.removeItem('sb_notifications_read')
      localStorage.removeItem('sb_notifications_dismissed')
    } catch {}

    // Sign out akun
    await supabase.auth.signOut()

    closeModal()
    router.push({ name: 'login' })
  } catch (err: any) {
    deleteError.value = err.message || 'Gagal menghapus data. Silakan coba lagi.'
  } finally {
    isDeleting.value = false
  }
}
</script>

<template>
  <div>
    <!-- Modal Wrapper -->
    <div
      v-if="isOpen"
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
    >
      <!-- Backdrop -->
      <div
        class="fixed inset-0 bg-black/50 backdrop-blur-xs transition-opacity"
        @click="closeModal"
      ></div>

      <!-- Modal Card -->
      <div
        class="relative w-full max-w-xl rounded-3xl border border-gray-200 bg-white p-5 sm:p-7 shadow-2xl transition-all space-y-4 max-h-[90vh] overflow-y-auto no-scrollbar"
      >
        <!-- Modal Header -->
        <div class="flex items-center justify-between pb-3 border-b border-gray-100">
          <div class="flex items-center gap-2.5">
            <span class="text-2xl p-2 rounded-2xl bg-indigo-50 border border-indigo-100 select-none">🛡️</span>
            <div>
              <h3 class="text-base font-bold text-gray-900">Pusat Privasi & Kedaulatan Data</h3>
              <p class="text-xs text-gray-500">Data akademik & risetmu adalah milikmu sepenuhnya</p>
            </div>
          </div>
          <button
            type="button"
            @click="closeModal"
            class="text-gray-400 hover:text-gray-600 p-1.5 text-base cursor-pointer rounded-lg hover:bg-gray-100 transition-colors"
          >
            ✕
          </button>
        </div>

        <!-- Tab Selector -->
        <div class="grid grid-cols-3 gap-1 bg-gray-100 p-1 rounded-xl text-xs font-semibold">
          <button
            type="button"
            @click="activeTab = 'policy'"
            class="py-1.5 px-2 rounded-lg transition-all text-center cursor-pointer"
            :class="activeTab === 'policy' ? 'bg-white text-gray-900 shadow-2xs' : 'text-gray-600 hover:text-gray-900'"
          >
            📜 Janji Privasi
          </button>
          <button
            type="button"
            @click="activeTab = 'export'"
            class="py-1.5 px-2 rounded-lg transition-all text-center cursor-pointer"
            :class="activeTab === 'export' ? 'bg-white text-gray-900 shadow-2xs' : 'text-gray-600 hover:text-gray-900'"
          >
            📦 Unduh Data (Backup)
          </button>
          <button
            type="button"
            @click="activeTab = 'delete'"
            class="py-1.5 px-2 rounded-lg transition-all text-center cursor-pointer"
            :class="activeTab === 'delete' ? 'bg-white text-rose-700 shadow-2xs' : 'text-gray-600 hover:text-rose-600'"
          >
            🗑️ Hapus Permanen
          </button>
        </div>

        <!-- 1. Tab Janji Privasi & Matriks Keamanan -->
        <div v-if="activeTab === 'policy'" class="space-y-4 text-xs text-gray-700">
          <div class="rounded-2xl border border-indigo-100 bg-gradient-to-br from-indigo-50/70 to-white p-4 space-y-2">
            <h4 class="font-bold text-indigo-950 flex items-center gap-1.5">
              <span>🤝</span>
              <span>Janji Privasi Pengembang untuk Mahasiswa</span>
            </h4>
            <p class="leading-relaxed text-indigo-900/90 text-[11px]">
              Aplikasi ini dibangun independen secara open-source untuk memecahkan masalah mental kuliah, skripsi, dan burnout. Kami <strong>tidak mencari profit dari data pengguna</strong>, tidak memasang tracker analitik pihak ketiga, dan tidak pernah membagikan catatan akademikmu kepada siapa pun.
            </p>
          </div>

          <!-- Matriks Transparansi Data -->
          <div class="space-y-2">
            <h4 class="font-bold text-gray-900">Transparansi: Apa yang Disimpan vs Tidak Pernah Dilacak</h4>
            <div class="border border-gray-200 rounded-2xl overflow-hidden divide-y divide-gray-100">
              <div class="grid grid-cols-2 bg-gray-50 p-2.5 font-bold text-[11px] text-gray-700">
                <span>✅ Disimpan untuk Akunmu</span>
                <span>❌ Tidak Pernah Dilakukan</span>
              </div>
              <div class="grid grid-cols-2 p-2.5 text-[11px] text-gray-600 gap-2">
                <span>Daftar mata kuliah, deadline kuis, dan catatan tugas</span>
                <span class="text-rose-700 font-medium">Tidak merekam mikrofon / suara ke server (100% diproses di browser)</span>
              </div>
              <div class="grid grid-cols-2 p-2.5 text-[11px] text-gray-600 gap-2 bg-gray-50/50">
                <span>Catatan riset skripsi & simpul Knowledge Graph</span>
                <span class="text-rose-700 font-medium">Tidak memonitor riwayat browsing atau tab browser lain</span>
              </div>
              <div class="grid grid-cols-2 p-2.5 text-[11px] text-gray-600 gap-2">
                <span>Target hidrasi air & log jam tidur</span>
                <span class="text-rose-700 font-medium">Tidak membaca clipboard perangkat tanpa izin</span>
              </div>
              <div class="grid grid-cols-2 p-2.5 text-[11px] text-gray-600 gap-2 bg-gray-50/50">
                <span>Wishlist hobi (tersimpan privat di browser lokal)</span>
                <span class="text-rose-700 font-medium">Tidak ada Google Analytics, Facebook Pixel, atau iklan komersial</span>
              </div>
            </div>
          </div>

          <!-- Keamanan Database RLS -->
          <div class="rounded-xl border border-gray-200 p-3 bg-white space-y-1">
            <h5 class="font-bold text-gray-900 flex items-center gap-1.5">
              <span>🔒</span>
              <span>Proteksi Row Level Security (RLS) PostgreSQL</span>
            </h5>
            <p class="text-[11px] text-gray-500 leading-relaxed">
              Database kami dilindungi aturan PostgreSQL Row Level Security ketat. Setiap baris data memiliki kunci unik pemilik akun, sehingga pengguna lain mustahil dapat membaca catatanmu.
            </p>
          </div>
        </div>

        <!-- 2. Tab Ekspor & Backup Mandiri (Data Portability) -->
        <div v-else-if="activeTab === 'export'" class="space-y-4 text-xs">
          <div class="space-y-1">
            <h4 class="font-bold text-gray-900">Kedaulatan Data: Unduh Seluruh Datamu Kapan Saja</h4>
            <p class="text-gray-600 leading-relaxed">
              Kamu tidak terkunci di dalam aplikasi ini. Kapan pun kamu butuh salinan fisik seluruh tugas kuliah, catatan riset, atau riwayat waktu fokus, unduh semuanya dalam format JSON standar.
            </p>
          </div>

          <div class="rounded-2xl border border-gray-200 bg-gray-50/80 p-4 space-y-2">
            <div class="flex items-center justify-between text-gray-700 font-semibold">
              <span>Isi Paket Ekspor JSON:</span>
              <span class="text-[10px] text-indigo-600 font-bold">100% Lengkap</span>
            </div>
            <ul class="text-[11px] text-gray-500 space-y-1 list-disc pl-4">
              <li>Semua daftar tugas & deadline akademik</li>
              <li>Seluruh catatan riset & simpul graf skripsi</li>
              <li>Log hidrasi, kebiasaan, dan jam tidur</li>
              <li>Riwayat sesi fokus Pomodoro timer</li>
              <li>Daftar wishlist hobi & recharge sesi</li>
            </ul>
          </div>

          <div v-if="exportSuccess" class="rounded-xl bg-emerald-50 border border-emerald-200 p-3 text-emerald-900 flex items-center gap-2">
            <span class="text-base select-none">✅</span>
            <span class="text-xs font-semibold">File backup berhasil diunduh ke foldermu!</span>
          </div>

          <button
            type="button"
            @click="handleExportData"
            :disabled="isExporting || !userId"
            class="w-full rounded-2xl bg-indigo-600 py-3 text-xs font-bold text-white shadow-md hover:bg-indigo-700 active:scale-95 disabled:opacity-50 transition-all cursor-pointer flex items-center justify-center gap-2"
          >
            <span>📦</span>
            <span>{{ isExporting ? 'Menyiapkan Data Backup...' : 'Unduh File JSON Sekarang' }}</span>
          </button>
        </div>

        <!-- 3. Tab Hapus Akun & Data Permanen (Right to Erasure) -->
        <div v-else-if="activeTab === 'delete'" class="space-y-4 text-xs">
          <div class="rounded-2xl border border-rose-200 bg-rose-50/60 p-4 space-y-2">
            <div class="flex items-center gap-2 text-rose-900 font-bold">
              <span>⚠️</span>
              <span>Penghapusan Permanen (Zero-Trace Deletion)</span>
            </div>
            <p class="text-rose-800 leading-relaxed text-[11px]">
              Tindakan ini bersifat <strong>tidak dapat dibatalkan</strong>. Semua tugas, catatan skripsi, riwayat fokus, dan profilmu akan dihapus seketika dari database Supabase dan penyimpanan browsermu.
            </p>
          </div>

          <div class="space-y-2">
            <label class="block font-semibold text-gray-800">
              Ketik kata <span class="font-mono font-bold text-rose-600">HAPUS</span> di bawah ini untuk mengonfirmasi:
            </label>
            <input
              v-model="deleteConfirmation"
              type="text"
              placeholder="Ketik HAPUS di sini..."
              class="w-full rounded-xl border border-gray-300 px-3.5 py-2.5 text-xs font-semibold text-gray-900 placeholder-gray-400 focus:border-rose-600 focus:outline-none"
            />
          </div>

          <div v-if="deleteError" class="text-xs font-bold text-rose-600">
            {{ deleteError }}
          </div>

          <button
            type="button"
            @click="handleDeleteAllData"
            :disabled="deleteConfirmation.trim().toUpperCase() !== 'HAPUS' || isDeleting || !userId"
            class="w-full rounded-2xl bg-rose-600 py-3 text-xs font-bold text-white shadow-md hover:bg-rose-700 active:scale-95 disabled:opacity-40 transition-all cursor-pointer flex items-center justify-center gap-2"
          >
            <span>🗑️</span>
            <span>{{ isDeleting ? 'Menghapus Semua Data...' : 'Hapus Semua Data & Akun Saya Permanen' }}</span>
          </button>
        </div>

        <!-- Modal Footer -->
        <div class="pt-2 border-t border-gray-100 flex items-center justify-between text-[11px] text-gray-500">
          <span>Lisensi MIT • Kode Terbuka & Terverifikasi</span>
          <a
            href="https://github.com/fransalwan/second-brain-agent"
            target="_blank"
            class="text-indigo-600 font-semibold hover:underline"
          >
            Audit di GitHub ↗
          </a>
        </div>
      </div>
    </div>
  </div>
</template>
