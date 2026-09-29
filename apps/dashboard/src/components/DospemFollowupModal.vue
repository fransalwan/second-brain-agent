<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

const props = defineProps<{
  userId: string
  lastSupervisionDays: number | null
  activeChapters?: Array<{ chapter_num: number, title: string, status: string }>
}>()

const isOpen = ref(false)
const copied = ref(false)

// State form dospem
const form = ref({
  dospemName: '',
  dospemPhone: '',
  studentName: '',
  studentNim: '',
  studentMajor: '',
  thesisTitle: '',
  topicConsult: '',
  preferredTime: '',
  templateType: 'request_schedule' as 'request_schedule' | 'submit_draft' | 'gentle_followup' | 'exam_approval',
})

// Load saved dospem profile from localStorage
const STORAGE_KEY = computed(() => `sb_dospem_profile_${props.userId}`)

function loadSavedProfile() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY.value)
    if (raw) {
      const data = JSON.parse(raw)
      form.value.dospemName = data.dospemName || ''
      form.value.dospemPhone = data.dospemPhone || ''
      form.value.studentName = data.studentName || ''
      form.value.studentNim = data.studentNim || ''
      form.value.studentMajor = data.studentMajor || ''
      form.value.thesisTitle = data.thesisTitle || ''
    }
  } catch (e) {
    console.error('Failed to load dospem profile', e)
  }
}

function saveProfile() {
  try {
    const data = {
      dospemName: form.value.dospemName,
      dospemPhone: form.value.dospemPhone,
      studentName: form.value.studentName,
      studentNim: form.value.studentNim,
      studentMajor: form.value.studentMajor,
      thesisTitle: form.value.thesisTitle,
    }
    localStorage.setItem(STORAGE_KEY.value, JSON.stringify(data))
  } catch (e) {
    console.error('Failed to save dospem profile', e)
  }
}

watch(
  () => [
    form.value.dospemName,
    form.value.dospemPhone,
    form.value.studentName,
    form.value.studentNim,
    form.value.studentMajor,
    form.value.thesisTitle,
  ],
  () => {
    saveProfile()
  }
)

onMounted(() => {
  loadSavedProfile()
  if (!form.value.topicConsult && props.activeChapters && props.activeChapters.length > 0) {
    // Cari bab yang sedang berstatus Drafting atau Revisi
    const inProgress = props.activeChapters.find(
      c => c.status === 'Revisi Dospem' || c.status === 'Drafting'
    )
    if (inProgress) {
      form.value.topicConsult = `Revisi Bab ${inProgress.chapter_num} (${inProgress.title})`
    }
  }
})

function openModal(defaultTemplate?: 'request_schedule' | 'submit_draft' | 'gentle_followup' | 'exam_approval') {
  if (defaultTemplate) {
    form.value.templateType = defaultTemplate
  }
  loadSavedProfile()
  isOpen.value = true
}

function closeModal() {
  isOpen.value = false
}

defineExpose({
  openModal,
  closeModal,
})

// Generator salam berdasarkan waktu saat ini
const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour >= 4 && hour < 11) return 'Selamat pagi'
  if (hour >= 11 && hour < 15) return 'Selamat siang'
  if (hour >= 15 && hour < 18) return 'Selamat sore'
  return 'Selamat malam'
})

// Generated Message Text
const generatedMessage = computed(() => {
  const dospem = form.value.dospemName.trim() || 'Bapak/Ibu Dosen Pembimbing'
  const name = form.value.studentName.trim() || '[Nama Anda]'
  const nim = form.value.studentNim.trim() || '[NIM]'
  const major = form.value.studentMajor.trim() || '[Program Studi]'
  const title = form.value.thesisTitle.trim() || '[Judul/Topik Tugas Akhir]'
  const topic = form.value.topicConsult.trim() || 'progres naskah skripsi'
  const time = form.value.preferredTime.trim() || 'pada hari dan jam luang Bapak/Ibu'

  if (form.value.templateType === 'request_schedule') {
    return `${greeting.value} ${dospem}, mohon maaf mengganggu waktunya.

Perkenalkan saya ${name}, mahasiswa bimbingan Bapak/Ibu dari program studi ${major} (NIM: ${nim}).

Saat ini saya telah menyelesaikan perbaikan untuk bagian *${topic}* terkait tugas akhir saya yang berjudul *"${title}"*.

Jika berkenan dan ada waktu luang, apakah saya diperbolehkan mengajukan permohonan bimbingan/konsultasi bersama Bapak/Ibu? Untuk waktu saya siap menyesuaikan dengan jadwal Bapak/Ibu (misal: ${time}).

Terima kasih banyak atas arahan dan waktu yang Bapak/Ibu berikan. Semoga Bapak/Ibu senantiasa sehat selalu.`
  }

  if (form.value.templateType === 'submit_draft') {
    return `${greeting.value} ${dospem}, mohon maaf mengganggu waktu dan aktivitas Bapak/Ibu.

Saya ${name} (NIM: ${nim}) dari prodi ${major}, mahasiswa bimbingan skripsi Bapak/Ibu.

Melalui pesan ini, saya bermaksud mengabarkan bahwa saya telah menyelesaikan draf *${topic}* untuk judul skripsi *"${title}"*. File naskah dan ringkasan revisi telah saya kirimkan ke email Bapak/Ibu.

Mohon kesediaan dan arahan Bapak/Ibu terhadap perbaikan yang telah saya buat saat Bapak/Ibu senggang.

Terima kasih banyak atas bimbingan Bapak/Ibu selama ini.`
  }

  if (form.value.templateType === 'gentle_followup') {
    return `${greeting.value} ${dospem}, mohon maaf mengganggu waktunya kembali.

Saya ${name} (NIM: ${nim}), mahasiswa bimbingan tugas akhir Bapak/Ibu.

Izin melakukan *follow-up* dengan santun terkait draf naskah *${topic}* yang sebelumnya telah saya kirimkan. 

Apabila Bapak/Ibu sudah berkesempatan meninjau draf tersebut, saya siap menerima masukan atau menghadap sesuai jadwal yang Bapak/Ibu tentukan. Namun apabila Bapak/Ibu masih memiliki agenda padat, saya sangat mengerti dan siap menunggu arahan selanjutnya.

Terima kasih banyak atas waktu dan perhatian Bapak/Ibu.`
  }

  // exam_approval
  return `${greeting.value} ${dospem}, mohon izin menghubungi Bapak/Ibu.

Saya ${name} (NIM: ${nim}) mahasiswa bimbingan skripsi Bapak/Ibu.

Alhamdulillah seluruh poin revisi naskah untuk *"${title}"* telah saya selesaikan sesuai dengan masukan pada sesi bimbingan terakhir. 

Mengingat batas pendaftaran ujian/seminar proposal yang semakin dekat, saya bermaksud memohon kesediaan Bapak/Ibu untuk memeriksa kelayakan naskah akhir dan permohonan lembar persetujuan (ACC).

Apakah kiranya saya diperkenankan menghadap ruangan Bapak/Ibu atau mengirimkan berkasnya secara online?

Terima kasih banyak atas kebaikan dan bimbingan Bapak/Ibu.`
})

function copyToClipboard() {
  navigator.clipboard.writeText(generatedMessage.value)
  copied.value = true
  setTimeout(() => {
    copied.value = false
  }, 2500)
}

function openWhatsApp() {
  const cleanPhone = form.value.dospemPhone.replace(/[^0-9]/g, '')
  const encodedText = encodeURIComponent(generatedMessage.value)
  if (cleanPhone) {
    // Normalisasi awalan nomor: 08xxx -> 628xxx
    let finalPhone = cleanPhone
    if (finalPhone.startsWith('0')) {
      finalPhone = '62' + finalPhone.slice(1)
    }
    window.open(`https://wa.me/${finalPhone}?text=${encodedText}`, '_blank')
  } else {
    window.open(`https://wa.me/?text=${encodedText}`, '_blank')
  }
}
</script>

<template>
  <div>
    <!-- Modal Backdrop -->
    <div
      v-if="isOpen"
      class="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/50 backdrop-blur-xs p-4 overflow-y-auto"
    >
      <div class="w-full max-w-2xl rounded-2xl bg-white p-5 sm:p-6 shadow-2xl border border-gray-200 space-y-4 my-6">
        <!-- Modal Header -->
        <div class="flex items-center justify-between pb-3 border-b border-gray-100">
          <div class="flex items-center gap-2.5">
            <span class="text-2xl p-1.5 rounded-xl bg-purple-50 border border-purple-100">💬</span>
            <div>
              <h3 class="text-sm font-bold text-gray-900 sm:text-base">Anti-Ghosting Dospem Chat Generator</h3>
              <p class="text-[11px] text-gray-500">Draft WhatsApp sopan beretika akademik sesuai kaidah perguruan tinggi</p>
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

        <!-- Template Selector Buttons -->
        <div class="space-y-1.5">
          <label class="block text-xs font-bold text-gray-700">Pilih Tujuan Pesan:</label>
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
            <button
              type="button"
              @click="form.templateType = 'request_schedule'"
              class="p-2 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between"
              :class="form.templateType === 'request_schedule' ? 'border-purple-600 bg-purple-50/80 text-purple-900 font-bold shadow-2xs' : 'border-gray-200 hover:bg-gray-50 text-gray-700'"
            >
              <span class="text-base mb-1">📅</span>
              <span class="text-[11px] leading-tight">Minta Jadwal Bimbingan</span>
            </button>
            <button
              type="button"
              @click="form.templateType = 'submit_draft'"
              class="p-2 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between"
              :class="form.templateType === 'submit_draft' ? 'border-purple-600 bg-purple-50/80 text-purple-900 font-bold shadow-2xs' : 'border-gray-200 hover:bg-gray-50 text-gray-700'"
            >
              <span class="text-base mb-1">📄</span>
              <span class="text-[11px] leading-tight">Kirim Draft & Revisi</span>
            </button>
            <button
              type="button"
              @click="form.templateType = 'gentle_followup'"
              class="p-2 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between"
              :class="form.templateType === 'gentle_followup' ? 'border-rose-500 bg-rose-50/80 text-rose-900 font-bold shadow-2xs' : 'border-gray-200 hover:bg-gray-50 text-gray-700'"
            >
              <span class="text-base mb-1">⏰</span>
              <span class="text-[11px] leading-tight">Follow-Up Santun (Anti-Ghost)</span>
            </button>
            <button
              type="button"
              @click="form.templateType = 'exam_approval'"
              class="p-2 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between"
              :class="form.templateType === 'exam_approval' ? 'border-purple-600 bg-purple-50/80 text-purple-900 font-bold shadow-2xs' : 'border-gray-200 hover:bg-gray-50 text-gray-700'"
            >
              <span class="text-base mb-1">🎓</span>
              <span class="text-[11px] leading-tight">Persetujuan ACC / Sempro</span>
            </button>
          </div>
        </div>

        <!-- Form Parameter Inputs -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs pt-1">
          <div>
            <label class="block font-semibold text-gray-700 mb-1">Nama Dosen Pembimbing & Gelar</label>
            <input
              v-model="form.dospemName"
              type="text"
              placeholder="Contoh: Prof. Dr. Ir. Budi Santoso, M.Kom"
              class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-purple-600 focus:outline-none"
            />
          </div>

          <div>
            <label class="block font-semibold text-gray-700 mb-1">No. WhatsApp Dospem (Opsional)</label>
            <input
              v-model="form.dospemPhone"
              type="tel"
              placeholder="Contoh: 08123456789 (Disimpan lokal di HP)"
              class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-purple-600 focus:outline-none"
            />
          </div>

          <div>
            <label class="block font-semibold text-gray-700 mb-1">Nama Mahasiswa & NIM</label>
            <div class="grid grid-cols-2 gap-2">
              <input
                v-model="form.studentName"
                type="text"
                placeholder="Nama Lengkap"
                class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-purple-600 focus:outline-none"
              />
              <input
                v-model="form.studentNim"
                type="text"
                placeholder="NIM"
                class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-purple-600 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label class="block font-semibold text-gray-700 mb-1">Program Studi / Jurusan</label>
            <input
              v-model="form.studentMajor"
              type="text"
              placeholder="Contoh: Teknik Informatika / Ilmu Komputer"
              class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-purple-600 focus:outline-none"
            />
          </div>

          <div class="sm:col-span-2">
            <label class="block font-semibold text-gray-700 mb-1">Bab / Bagian yang Dikonsultasikan</label>
            <input
              v-model="form.topicConsult"
              type="text"
              placeholder="Contoh: Revisi Bab 3 Metodologi Penelitian & Desain Eksperimen"
              class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-purple-600 focus:outline-none"
            />
          </div>

          <div class="sm:col-span-2">
            <label class="block font-semibold text-gray-700 mb-1">Usulan Waktu Luang Mahasiswa (Opsional)</label>
            <input
              v-model="form.preferredTime"
              type="text"
              placeholder="Contoh: Hari Rabu atau Kamis pukul 10.00 - 14.00 WIB"
              class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-purple-600 focus:outline-none"
            />
          </div>
        </div>

        <!-- Generated Message Preview -->
        <div class="space-y-1.5 pt-2 border-t border-gray-100">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-gray-800 flex items-center gap-1.5">
              <span>📱</span>
              <span>Preview Pesan WhatsApp:</span>
            </span>
            <span class="text-[10px] text-gray-400">Siap dikirim tanpa perlu mengarang kata</span>
          </div>

          <div class="rounded-xl border border-emerald-200 bg-emerald-50/40 p-3.5 text-xs text-gray-800 whitespace-pre-wrap leading-relaxed font-sans shadow-inner select-text">
            {{ generatedMessage }}
          </div>
        </div>

        <!-- Actions -->
        <div class="pt-2 flex flex-col sm:flex-row items-center justify-between gap-3">
          <span class="text-[11px] text-gray-500 hidden sm:inline">
            🔒 Disimpan secara privat di browser kamu (*localStorage*).
          </span>
          <div class="flex items-center gap-2 w-full sm:w-auto justify-end">
            <button
              type="button"
              @click="closeModal"
              class="rounded-xl border border-gray-200 px-3 py-2 text-xs font-semibold text-gray-600 hover:bg-gray-50 cursor-pointer"
            >
              Tutup
            </button>
            <button
              type="button"
              @click="copyToClipboard"
              class="rounded-xl border border-gray-300 bg-white px-3.5 py-2 text-xs font-bold text-gray-800 hover:bg-gray-50 transition-all cursor-pointer flex items-center gap-1.5 shadow-2xs"
            >
              <span>{{ copied ? '✅' : '📋' }}</span>
              <span>{{ copied ? 'Tersalin ke Clipboard!' : 'Salin Teks' }}</span>
            </button>
            <button
              type="button"
              @click="openWhatsApp"
              class="rounded-xl bg-emerald-600 px-4 py-2 text-xs font-bold text-white hover:bg-emerald-700 active:scale-95 transition-all cursor-pointer flex items-center gap-1.5 shadow-xs"
            >
              <span>💬</span>
              <span>Buka WhatsApp</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
