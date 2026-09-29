<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  (e: 'navigate-tab', tab: 'overview' | 'health' | 'coursework' | 'research' | 'hobby'): void
  (e: 'open-quick-capture'): void
  (e: 'open-privacy', tab?: 'policy' | 'export' | 'delete'): void
}>()

const activeSection = ref<'all' | 'routine' | 'pillars' | 'quickcapture' | 'privacy' | 'faq'>('all')

const copiedIndex = ref<number | null>(null)

function copyText(text: string, index: number) {
  navigator.clipboard.writeText(text)
  copiedIndex.value = index
  setTimeout(() => {
    if (copiedIndex.value === index) {
      copiedIndex.value = null
    }
  }, 2000)
}

const faqs = ref([
  {
    question: 'Apakah data saya tersimpan aman di cloud?',
    answer:
      'Ya! Semua data tugas kuliah, catatan riset, hidrasi, dan waktu tidur tersimpan di database Supabase PostgreSQL dengan proteksi Row Level Security (RLS). Hanya kamu yang memiliki hak akses untuk membaca dan mengubah data akunmu.',
    isOpen: true,
  },
  {
    question: 'Bagaimana cara menggunakan aplikasi ini di Smartphone / HP?',
    answer:
      'Buka browser di HP (Chrome di Android, atau Safari di iOS), kunjungi https://second-brain-agent.netlify.app/. Kamu bisa memilih menu browser "Tambahkan ke Layar Utama" (Add to Home Screen) agar aplikasi ini bisa dibuka seperti aplikasi native dengan 1 tap.',
    isOpen: false,
  },
  {
    question: 'Kenapa fitur Telegram dan AI disembunyikan?',
    answer:
      'Kami merombak Second Brain menjadi 100% Standalone Web App agar kamu tidak perlu repot setup bot atau bayar kuota token AI. Semua fitur utama (Quick Capture regex, pengenalan suara browser, pusat notifikasi, audio chime) berjalan langsung di perangkatmu tanpa pihak ketiga.',
    isOpen: false,
  },
  {
    question: 'Apakah aplikasi ini gratis untuk mahasiswa?',
    answer:
      '100% Gratis dan Open-Source! Aplikasi ini dibangun dengan stack serverless tier gratis (Netlify & Supabase) sehingga mahasiswa bisa memanfaatkannya tanpa biaya langganan sepeserpun.',
    isOpen: false,
  },
  {
    question: 'Bagaimana jika saya menemukan kendala atau punya ide fitur baru?',
    answer:
      'Cukup klik tombol melayang "💬 Curhat / Request Fitur" di pojok kiri bawah layar kapan saja. Masukanmu akan langsung tersimpan dan dibaca langsung oleh developer sebagai prioritas update.',
    isOpen: false,
  },
])

function toggleFaq(index: number) {
  faqs.value[index].isOpen = !faqs.value[index].isOpen
}
</script>

<template>
  <div class="space-y-6">
    <!-- Hero Banner Panduan -->
    <div class="relative overflow-hidden rounded-3xl border border-indigo-100 bg-gradient-to-br from-indigo-900 via-indigo-950 to-slate-900 p-6 sm:p-8 text-white shadow-xl">
      <div class="relative z-10 max-w-2xl space-y-3">
        <div class="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-semibold backdrop-blur-md border border-white/10">
          <span>📖</span>
          <span>Buku Panduan Mahasiswa</span>
        </div>
        <h2 class="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
          Kuasai Ritme Kuliah & Hidupmu Tanpa Burnout
        </h2>
        <p class="text-xs sm:text-sm text-indigo-200 leading-relaxed">
          Second Brain dirancang khusus untuk memecahkan masalah mental mahasiswa: tugas menumpuk, skripsi macet, pola tidur berantakan, dan rasa bersalah saat istirahat. Ikuti panduan praktis ini untuk memaksimalkan setiap fiturnya!
        </p>
        <div class="pt-2 flex flex-wrap items-center gap-2.5">
          <button
            type="button"
            @click="emit('open-quick-capture')"
            class="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2 text-xs font-bold text-indigo-950 shadow-md hover:bg-indigo-50 active:scale-95 transition-all cursor-pointer"
          >
            <span>⚡</span>
            <span>Coba Quick Capture (Ctrl+K)</span>
          </button>
          <button
            type="button"
            @click="emit('navigate-tab', 'overview')"
            class="inline-flex items-center gap-1.5 rounded-xl border border-white/20 bg-white/10 px-3.5 py-2 text-xs font-semibold text-white hover:bg-white/20 transition-all cursor-pointer backdrop-blur-xs"
          >
            <span>🏠</span>
            <span>Ke Dashboard Ringkasan</span>
          </button>
        </div>
      </div>

      <!-- Background Accent Illustration -->
      <div class="absolute -right-8 -bottom-10 select-none opacity-20 pointer-events-none text-9xl">
        🧠
      </div>
    </div>

    <!-- Quick Navigation Filter Chips -->
    <div class="flex items-center gap-2 overflow-x-auto no-scrollbar py-1">
      <button
        type="button"
        @click="activeSection = 'all'"
        class="rounded-xl px-3 py-1.5 text-xs font-bold transition-all cursor-pointer whitespace-nowrap"
        :class="activeSection === 'all' ? 'bg-indigo-600 text-white shadow-xs' : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'"
      >
        ✨ Semua Topik
      </button>
      <button
        type="button"
        @click="activeSection = 'routine'"
        class="rounded-xl px-3 py-1.5 text-xs font-bold transition-all cursor-pointer whitespace-nowrap"
        :class="activeSection === 'routine' ? 'bg-indigo-600 text-white shadow-xs' : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'"
      >
        🌅 Alur Sehari-hari
      </button>
      <button
        type="button"
        @click="activeSection = 'pillars'"
        class="rounded-xl px-3 py-1.5 text-xs font-bold transition-all cursor-pointer whitespace-nowrap"
        :class="activeSection === 'pillars' ? 'bg-indigo-600 text-white shadow-xs' : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'"
      >
        🎯 4 Pilar Utama
      </button>
      <button
        type="button"
        @click="activeSection = 'quickcapture'"
        class="rounded-xl px-3 py-1.5 text-xs font-bold transition-all cursor-pointer whitespace-nowrap"
        :class="activeSection === 'quickcapture' ? 'bg-indigo-600 text-white shadow-xs' : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'"
      >
        ⚡ Cheat Sheet Input
      </button>
      <button
        type="button"
        @click="activeSection = 'privacy'"
        class="rounded-xl px-3 py-1.5 text-xs font-bold transition-all cursor-pointer whitespace-nowrap"
        :class="activeSection === 'privacy' ? 'bg-indigo-600 text-white shadow-xs' : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'"
      >
        🛡️ Privasi & Data
      </button>
      <button
        type="button"
        @click="activeSection = 'faq'"
        class="rounded-xl px-3 py-1.5 text-xs font-bold transition-all cursor-pointer whitespace-nowrap"
        :class="activeSection === 'faq' ? 'bg-indigo-600 text-white shadow-xs' : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'"
      >
        ❓ Tanya Jawab (FAQ)
      </button>
    </div>

    <!-- 1. Alur Sehari-Hari Mahasiswa (Workflow) -->
    <section v-if="activeSection === 'all' || activeSection === 'routine'" class="space-y-3">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-bold text-gray-900 flex items-center gap-2">
          <span>🌅</span>
          <span>Alur Sehari-hari: Dari Bangun Pagi Sampai Tidur Nyenyak</span>
        </h3>
        <span class="text-[11px] text-gray-500">4 Langkah Praktis</span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <!-- Step 1 -->
        <div class="rounded-2xl border border-gray-200 bg-white p-4 shadow-xs flex flex-col justify-between hover:border-indigo-300 transition-all">
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-extrabold text-amber-600 uppercase tracking-wider">01 • Pagi Hari</span>
              <span class="text-lg">☀️</span>
            </div>
            <h4 class="text-xs font-bold text-gray-900">Briefing & Minum Air</h4>
            <p class="text-[11px] text-gray-600 leading-relaxed">
              Buka tab <strong>Ringkasan</strong>. Baca <em>Daily Briefing Card</em> untuk mengetahui tugas yang mendekati deadline hari ini. Minum 1 gelas air (300ml) dan catat segera.
            </p>
          </div>
          <div class="pt-3 border-t border-gray-100 mt-2">
            <button
              type="button"
              @click="emit('navigate-tab', 'overview')"
              class="w-full rounded-xl bg-amber-50 py-1.5 text-[11px] font-bold text-amber-800 hover:bg-amber-100 transition-colors text-center cursor-pointer"
            >
              Lihat Ringkasan Pagi ➔
            </button>
          </div>
        </div>

        <!-- Step 2 -->
        <div class="rounded-2xl border border-gray-200 bg-white p-4 shadow-xs flex flex-col justify-between hover:border-indigo-300 transition-all">
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-extrabold text-blue-600 uppercase tracking-wider">02 • Siang Hari</span>
              <span class="text-lg">🎓</span>
            </div>
            <h4 class="text-xs font-bold text-gray-900">Catat Tugas Cepat</h4>
            <p class="text-[11px] text-gray-600 leading-relaxed">
              Dapat info tugas dari dosen atau asisten lab? Tekan <strong>Ctrl + K</strong> (atau tombol <strong>+</strong> di HP) dan ketik 1 baris bebas atau ucapkan via suara mic.
            </p>
          </div>
          <div class="pt-3 border-t border-gray-100 mt-2">
            <button
              type="button"
              @click="emit('open-quick-capture')"
              class="w-full rounded-xl bg-blue-50 py-1.5 text-[11px] font-bold text-blue-800 hover:bg-blue-100 transition-colors text-center cursor-pointer"
            >
              Coba Ctrl+K ➔
            </button>
          </div>
        </div>

        <!-- Step 3 -->
        <div class="rounded-2xl border border-gray-200 bg-white p-4 shadow-xs flex flex-col justify-between hover:border-indigo-300 transition-all">
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-extrabold text-purple-600 uppercase tracking-wider">03 • Sore Hari</span>
              <span class="text-lg">⏱️</span>
            </div>
            <h4 class="text-xs font-bold text-gray-900">Fokus Deep Work</h4>
            <p class="text-[11px] text-gray-600 leading-relaxed">
              Mulai sesi fokus 25–50 menit untuk mengerjakan revisi skripsi atau modul koding. Nyalakan Pomodoro Timer di dashboard agar waktu terukur jelas.
            </p>
          </div>
          <div class="pt-3 border-t border-gray-100 mt-2">
            <button
              type="button"
              @click="emit('navigate-tab', 'research')"
              class="w-full rounded-xl bg-purple-50 py-1.5 text-[11px] font-bold text-purple-800 hover:bg-purple-100 transition-colors text-center cursor-pointer"
            >
              Buka Hub Riset ➔
            </button>
          </div>
        </div>

        <!-- Step 4 -->
        <div class="rounded-2xl border border-gray-200 bg-white p-4 shadow-xs flex flex-col justify-between hover:border-indigo-300 transition-all">
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-xs font-extrabold text-indigo-600 uppercase tracking-wider">04 • Malam Hari</span>
              <span class="text-lg">🌙</span>
            </div>
            <h4 class="text-xs font-bold text-gray-900">Me-Time & Night Cutoff</h4>
            <p class="text-[11px] text-gray-600 leading-relaxed">
              Nikmati kuota 90 menit santai tanpa rasa bersalah di tab <strong>Hobby</strong>. Di atas jam 23:00, hentikan laptop dan tidur cukup demi kesehatan otak besok.
            </p>
          </div>
          <div class="pt-3 border-t border-gray-100 mt-2">
            <button
              type="button"
              @click="emit('navigate-tab', 'hobby')"
              class="w-full rounded-xl bg-indigo-50 py-1.5 text-[11px] font-bold text-indigo-800 hover:bg-indigo-100 transition-colors text-center cursor-pointer"
            >
              Lihat Kuota Me-Time ➔
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- 2. Penjelasan 4 Pilar Utama -->
    <section v-if="activeSection === 'all' || activeSection === 'pillars'" class="space-y-3">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-bold text-gray-900 flex items-center gap-2">
          <span>🎯</span>
          <span>4 Pilar Utama Produktivitas Mahasiswa</span>
        </h3>
        <span class="text-[11px] text-gray-500">Filosofi Prioritas</span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Pilar 1: Kesehatan -->
        <div class="rounded-2xl border border-emerald-200 bg-gradient-to-br from-emerald-50/50 to-white p-5 shadow-xs flex flex-col justify-between space-y-4">
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="text-2xl">🩺</span>
                <div>
                  <h4 class="text-sm font-bold text-emerald-950">Prioritas #1: Kesehatan & Tidur</h4>
                  <p class="text-[11px] text-emerald-700">Health First Foundation</p>
                </div>
              </div>
              <span class="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-bold text-emerald-800">#1</span>
            </div>
            <p class="text-xs text-gray-700 leading-relaxed">
              <strong>Kenapa nomor satu?</strong> Otak mahasiswa yang kurang tidur atau dehidrasi kehilangan daya ingat hingga 40%. Kamu tidak akan bisa paham materi kuliah jika tubuhmu lemas.
            </p>
            <ul class="text-xs text-gray-600 space-y-1 pl-4 list-disc">
              <li><strong>Target Air:</strong> 2.500 ml per hari. Tersedia tombol cepat 250ml & 500ml.</li>
              <li><strong>Kalkulator Bangun:</strong> Prediksi waktu bangun sesuai siklus tidur 90 menit.</li>
              <li><strong>Night Cutoff:</strong> Alarm mandiri pukul 23:00 agar tidak terjerumus begadang tanpa arah.</li>
            </ul>
          </div>

          <div class="pt-2">
            <button
              type="button"
              @click="emit('navigate-tab', 'health')"
              class="inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 px-3.5 py-2 text-xs font-bold text-white hover:bg-emerald-700 transition-colors cursor-pointer shadow-xs"
            >
              <span>🩺</span>
              <span>Buka Tab Kesehatan ➔</span>
            </button>
          </div>
        </div>

        <!-- Pilar 2: Kuliah -->
        <div class="rounded-2xl border border-blue-200 bg-gradient-to-br from-blue-50/50 to-white p-5 shadow-xs flex flex-col justify-between space-y-4">
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="text-2xl">🎓</span>
                <div>
                  <h4 class="text-sm font-bold text-blue-950">Prioritas #2: Kuliah & Tugas</h4>
                  <p class="text-[11px] text-blue-700">Coursework & Deadline Tracker</p>
                </div>
              </div>
              <span class="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-bold text-blue-800">#2</span>
            </div>
            <p class="text-xs text-gray-700 leading-relaxed">
              <strong>Bebas panik deadline:</strong> Jangan simpan tanggal kuis dan praktikum di kepala. Kumpulkan semua mata kuliah dan tugasmu di satu tempat yang jelas.
            </p>
            <ul class="text-xs text-gray-600 space-y-1 pl-4 list-disc">
              <li><strong>Mata Kuliah:</strong> Kelompokkan tugas berdasarkan semester & mata kuliah.</li>
              <li><strong>Badge Urgent:</strong> Tandai tugas penting yang mendekati batas waktu penyerahan.</li>
              <li><strong>1-Tap Checklist:</strong> Centang tugas langsung dari dashboard untuk merayakan pencapaian.</li>
            </ul>
          </div>

          <div class="pt-2">
            <button
              type="button"
              @click="emit('navigate-tab', 'coursework')"
              class="inline-flex items-center gap-1.5 rounded-xl bg-blue-600 px-3.5 py-2 text-xs font-bold text-white hover:bg-blue-700 transition-colors cursor-pointer shadow-xs"
            >
              <span>🎓</span>
              <span>Buka Tab Kuliah ➔</span>
            </button>
          </div>
        </div>

        <!-- Pilar 3: Riset & Skripsi -->
        <div class="rounded-2xl border border-purple-200 bg-gradient-to-br from-purple-50/50 to-white p-5 shadow-xs flex flex-col justify-between space-y-4">
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="text-2xl">🔬</span>
                <div>
                  <h4 class="text-sm font-bold text-purple-950">Prioritas #3: Riset & Skripsi</h4>
                  <p class="text-[11px] text-purple-700">Thesis & Knowledge Graph</p>
                </div>
              </div>
              <span class="rounded-full bg-purple-100 px-2 py-0.5 text-xs font-bold text-purple-800">#3</span>
            </div>
            <p class="text-xs text-gray-700 leading-relaxed">
              <strong>Solusi skripsi macet:</strong> Riset skripsi bukan tentang hafalan, melainkan menghubungkan konsep, metodologi, dan telaah jurnal secara berkesinambungan.
            </p>
            <ul class="text-xs text-gray-600 space-y-1 pl-4 list-disc">
              <li><strong>Knowledge Graph:</strong> Simpul-simpul catatan saling terhubung membentuk peta pikiran visual.</li>
              <li><strong>Bab & Metodologi:</strong> Simpan kutipan penting, rumus, atau catatan revisi dosen pembimbing.</li>
              <li><strong>Pencarian Instan:</strong> Temukan referensi lampau dalam hitungan detik.</li>
            </ul>
          </div>

          <div class="pt-2">
            <button
              type="button"
              @click="emit('navigate-tab', 'research')"
              class="inline-flex items-center gap-1.5 rounded-xl bg-purple-600 px-3.5 py-2 text-xs font-bold text-white hover:bg-purple-700 transition-colors cursor-pointer shadow-xs"
            >
              <span>🔬</span>
              <span>Buka Tab Riset ➔</span>
            </button>
          </div>
        </div>

        <!-- Pilar 4: Hobby & Rest -->
        <div class="rounded-2xl border border-amber-200 bg-gradient-to-br from-amber-50/50 to-white p-5 shadow-xs flex flex-col justify-between space-y-4">
          <div class="space-y-2">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="text-2xl">🎨</span>
                <div>
                  <h4 class="text-sm font-bold text-amber-950">Prioritas #4: Hobby & Rest</h4>
                  <p class="text-[11px] text-amber-700">Guilt-Free Me-Time Hub</p>
                </div>
              </div>
              <span class="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-bold text-amber-800">#4</span>
            </div>
            <p class="text-xs text-gray-700 leading-relaxed">
              <strong>Istirahat bukan dosa:</strong> Otak butuh <em>diffuse mode</em> (mode relaksasi) untuk memecahkan problem koding atau kalkulus yang buntu. Jangan biarkan dirimu burnout!
            </p>
            <ul class="text-xs text-gray-600 space-y-1 pl-4 list-disc">
              <li><strong>Kuota 90 Menit:</strong> Alokasi santai harian terukur tanpa rasa bersalah.</li>
              <li><strong>Wishlist Bersih:</strong> Tambahkan game, novel, anime, atau olahraga yang ingin kamu nikmati.</li>
              <li><strong>Energy Return Score:</strong> Beri nilai 1–5 ⚡ seberapa segar energimu setelah bersenang-senang.</li>
            </ul>
          </div>

          <div class="pt-2">
            <button
              type="button"
              @click="emit('navigate-tab', 'hobby')"
              class="inline-flex items-center gap-1.5 rounded-xl bg-amber-600 px-3.5 py-2 text-xs font-bold text-white hover:bg-amber-700 transition-colors cursor-pointer shadow-xs"
            >
              <span>🎨</span>
              <span>Buka Tab Hobby ➔</span>
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- 3. Cheat Sheet Quick Capture & Suara -->
    <section v-if="activeSection === 'all' || activeSection === 'quickcapture'" class="space-y-3">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-bold text-gray-900 flex items-center gap-2">
          <span>⚡</span>
          <span>Universal Quick Capture (`Ctrl + K` & Suara)</span>
        </h3>
        <button
          type="button"
          @click="emit('open-quick-capture')"
          class="text-xs font-bold text-indigo-600 hover:text-indigo-800 hover:underline cursor-pointer"
        >
          Buka Palette Sekarang ↗
        </button>
      </div>

      <div class="rounded-2xl border border-gray-200 bg-white p-5 shadow-xs space-y-4">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <h4 class="text-xs font-bold text-gray-900 mb-1">Cara Mengakses:</h4>
            <ul class="text-xs text-gray-600 space-y-1.5">
              <li class="flex items-center gap-2">
                <kbd class="rounded border border-gray-300 bg-gray-100 px-1.5 py-0.5 text-[10px] font-mono font-bold text-gray-800">Ctrl + K</kbd>
                <span>(atau <kbd class="rounded border border-gray-300 bg-gray-100 px-1.5 py-0.5 text-[10px] font-mono font-bold text-gray-800">Cmd + K</kbd> di Mac) untuk membuka command bar.</span>
              </li>
              <li class="flex items-center gap-2">
                <span class="rounded-full bg-indigo-600 text-white w-5 h-5 flex items-center justify-center text-[10px] font-bold">+</span>
                <span>Tap tombol bulat di pojok kanan bawah jika menggunakan Smartphone / HP.</span>
              </li>
              <li class="flex items-center gap-2">
                <span class="text-base">🎤</span>
                <span>Klik tombol mic untuk dikte suara dalam Bahasa Indonesia (0 biaya).</span>
              </li>
            </ul>
          </div>

          <div>
            <h4 class="text-xs font-bold text-gray-900 mb-1">Smart Regex Auto-Categorizer:</h4>
            <p class="text-xs text-gray-600 leading-relaxed">
              Ketik kalimat bebas seperti berbicara pada teman. Sistem otomatis mendeteksi apakah itu tugas, air minum, tidur, catatan riset, atau timer fokus.
            </p>
          </div>
        </div>

        <!-- Cheat Sheet Examples -->
        <div class="space-y-2 pt-2 border-t border-gray-100">
          <label class="block text-xs font-bold text-gray-700">Contoh Perintah Instan (Klik untuk Salin):</label>
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 text-xs">
            <!-- Example 1 -->
            <div
              @click="copyText('tugas kuis kalkulus besok mendesak', 1)"
              class="group relative rounded-xl border border-gray-200 bg-gray-50/80 p-2.5 hover:bg-indigo-50/60 hover:border-indigo-300 transition-all cursor-pointer"
            >
              <div class="flex items-center justify-between text-[11px] text-gray-500 mb-1">
                <span>🎓 Tugas Kuliah Urgent</span>
                <span class="text-[10px] text-indigo-600 font-semibold opacity-0 group-hover:opacity-100 transition-opacity">
                  {{ copiedIndex === 1 ? 'Tersalin! ✓' : 'Salin 📋' }}
                </span>
              </div>
              <code class="text-xs font-mono font-bold text-gray-900">tugas kuis kalkulus besok mendesak</code>
            </div>

            <!-- Example 2 -->
            <div
              @click="copyText('minum 300ml', 2)"
              class="group relative rounded-xl border border-gray-200 bg-gray-50/80 p-2.5 hover:bg-indigo-50/60 hover:border-indigo-300 transition-all cursor-pointer"
            >
              <div class="flex items-center justify-between text-[11px] text-gray-500 mb-1">
                <span>💧 Catat Air Minum</span>
                <span class="text-[10px] text-indigo-600 font-semibold opacity-0 group-hover:opacity-100 transition-opacity">
                  {{ copiedIndex === 2 ? 'Tersalin! ✓' : 'Salin 📋' }}
                </span>
              </div>
              <code class="text-xs font-mono font-bold text-gray-900">minum 300ml</code>
            </div>

            <!-- Example 3 -->
            <div
              @click="copyText('tidur 7.5 jam', 3)"
              class="group relative rounded-xl border border-gray-200 bg-gray-50/80 p-2.5 hover:bg-indigo-50/60 hover:border-indigo-300 transition-all cursor-pointer"
            >
              <div class="flex items-center justify-between text-[11px] text-gray-500 mb-1">
                <span>😴 Catat Jam Tidur</span>
                <span class="text-[10px] text-indigo-600 font-semibold opacity-0 group-hover:opacity-100 transition-opacity">
                  {{ copiedIndex === 3 ? 'Tersalin! ✓' : 'Salin 📋' }}
                </span>
              </div>
              <code class="text-xs font-mono font-bold text-gray-900">tidur 7.5 jam</code>
            </div>

            <!-- Example 4 -->
            <div
              @click="copyText('fokus: revisi bab 2 skripsi', 4)"
              class="group relative rounded-xl border border-gray-200 bg-gray-50/80 p-2.5 hover:bg-indigo-50/60 hover:border-indigo-300 transition-all cursor-pointer"
            >
              <div class="flex items-center justify-between text-[11px] text-gray-500 mb-1">
                <span>⏱️ Nyalakan Timer Fokus</span>
                <span class="text-[10px] text-indigo-600 font-semibold opacity-0 group-hover:opacity-100 transition-opacity">
                  {{ copiedIndex === 4 ? 'Tersalin! ✓' : 'Salin 📋' }}
                </span>
              </div>
              <code class="text-xs font-mono font-bold text-gray-900">fokus: revisi bab 2 skripsi</code>
            </div>

            <!-- Example 5 -->
            <div
              @click="copyText('ide: integrasi graph neural network', 5)"
              class="group relative rounded-xl border border-gray-200 bg-gray-50/80 p-2.5 hover:bg-indigo-50/60 hover:border-indigo-300 transition-all cursor-pointer"
            >
              <div class="flex items-center justify-between text-[11px] text-gray-500 mb-1">
                <span>💡 Catatan Ide Riset</span>
                <span class="text-[10px] text-indigo-600 font-semibold opacity-0 group-hover:opacity-100 transition-opacity">
                  {{ copiedIndex === 5 ? 'Tersalin! ✓' : 'Salin 📋' }}
                </span>
              </div>
              <code class="text-xs font-mono font-bold text-gray-900">ide: integrasi graph neural network</code>
            </div>

            <!-- Example 6 -->
            <div
              @click="copyText('tugas laporan fisika lusa', 6)"
              class="group relative rounded-xl border border-gray-200 bg-gray-50/80 p-2.5 hover:bg-indigo-50/60 hover:border-indigo-300 transition-all cursor-pointer"
            >
              <div class="flex items-center justify-between text-[11px] text-gray-500 mb-1">
                <span>📅 Deadline 2 Hari Lagi</span>
                <span class="text-[10px] text-indigo-600 font-semibold opacity-0 group-hover:opacity-100 transition-opacity">
                  {{ copiedIndex === 6 ? 'Tersalin! ✓' : 'Salin 📋' }}
                </span>
              </div>
              <code class="text-xs font-mono font-bold text-gray-900">tugas laporan fisika lusa</code>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 4. Privasi, Keamanan & Kedaulatan Data -->
    <section v-if="activeSection === 'all' || activeSection === 'privacy'" class="space-y-3">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-bold text-gray-900 flex items-center gap-2">
          <span>🛡️</span>
          <span>Privasi, Keamanan & Kedaulatan Data Mahasiswa</span>
        </h3>
        <button
          type="button"
          @click="emit('open-privacy', 'policy')"
          class="text-xs font-bold text-indigo-600 hover:text-indigo-800 hover:underline cursor-pointer"
        >
          Buka Janji Privasi ↗
        </button>
      </div>

      <div class="rounded-2xl border border-gray-200 bg-white p-5 shadow-xs space-y-4">
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div class="rounded-xl border border-gray-100 bg-gray-50/70 p-3.5 space-y-1.5">
            <div class="flex items-center gap-2">
              <span class="text-lg">🚫</span>
              <h4 class="text-xs font-bold text-gray-900">Zero Commercial Ads</h4>
            </div>
            <p class="text-[11px] text-gray-500 leading-relaxed">
              100% bebas iklan dan tidak pernah menjual atau membagikan data catatan skripsimu kepada pengiklan pihak ketiga.
            </p>
          </div>

          <div class="rounded-xl border border-gray-100 bg-gray-50/70 p-3.5 space-y-1.5">
            <div class="flex items-center gap-2">
              <span class="text-lg">🔒</span>
              <h4 class="text-xs font-bold text-gray-900">Row Level Security (RLS)</h4>
            </div>
            <p class="text-[11px] text-gray-500 leading-relaxed">
              Setiap catatan dan tugas dilindungi aturan PostgreSQL RLS ketat. Hanya akunmu yang memiliki hak baca dan tulis.
            </p>
          </div>

          <div class="rounded-xl border border-gray-100 bg-gray-50/70 p-3.5 space-y-1.5">
            <div class="flex items-center gap-2">
              <span class="text-lg">💻</span>
              <h4 class="text-xs font-bold text-gray-900">Client-Side First</h4>
            </div>
            <p class="text-[11px] text-gray-500 leading-relaxed">
              Regex Quick Capture & Speech-to-Text diproses langsung di RAM browsermu tanpa merekam audio ke cloud.
            </p>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="pt-2 border-t border-gray-100 flex flex-wrap items-center justify-between gap-3">
          <div class="text-[11px] text-gray-500">
            Ingin cadangkan datamu atau memeriksa matriks privasi lengkap?
          </div>
          <div class="flex items-center gap-2">
            <button
              type="button"
              @click="emit('open-privacy', 'export')"
              class="inline-flex items-center gap-1.5 rounded-xl border border-gray-200 bg-white px-3 py-1.5 text-xs font-bold text-gray-800 hover:bg-gray-50 shadow-2xs transition-colors cursor-pointer"
            >
              <span>📦</span>
              <span>Unduh Backup JSON</span>
            </button>
            <button
              type="button"
              @click="emit('open-privacy', 'policy')"
              class="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-3.5 py-1.5 text-xs font-bold text-white hover:bg-indigo-700 shadow-xs transition-colors cursor-pointer"
            >
              <span>🛡️</span>
              <span>Pusat Kedaulatan Data</span>
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- 5. Tanya Jawab Mahasiswa (FAQ) -->
    <section v-if="activeSection === 'all' || activeSection === 'faq'" class="space-y-3">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-bold text-gray-900 flex items-center gap-2">
          <span>❓</span>
          <span>Tanya Jawab Populer (FAQ)</span>
        </h3>
        <span class="text-[11px] text-gray-500">Bantuan & Solusi</span>
      </div>

      <div class="space-y-2.5">
        <div
          v-for="(faq, idx) in faqs"
          :key="idx"
          class="rounded-2xl border border-gray-200 bg-white p-4 shadow-xs transition-colors hover:border-gray-300"
        >
          <button
            type="button"
            @click="toggleFaq(idx)"
            class="flex w-full items-center justify-between text-left text-xs font-bold text-gray-900 cursor-pointer"
          >
            <span>{{ faq.question }}</span>
            <span class="text-base text-gray-400 select-none ml-2">{{ faq.isOpen ? '−' : '+' }}</span>
          </button>
          <div v-if="faq.isOpen" class="mt-2.5 pt-2 border-t border-gray-100 text-xs text-gray-600 leading-relaxed">
            {{ faq.answer }}
          </div>
        </div>
      </div>
    </section>

    <!-- Footer Support Callout -->
    <div class="rounded-2xl border border-indigo-200 bg-indigo-50/60 p-5 text-center space-y-2">
      <div class="text-2xl select-none">💬</div>
      <h4 class="text-sm font-bold text-gray-900">Punya Saran atau Butuh Fitur Tambahan?</h4>
      <p class="text-xs text-gray-600 max-w-lg mx-auto">
        Kritik, saran, maupun curhat seputar masalah kuliah sangat berharga untuk perbaikan aplikasi ini. Klik tombol <strong>💬 Curhat / Request Fitur</strong> di pojok kiri bawah.
      </p>
    </div>
  </div>
</template>
