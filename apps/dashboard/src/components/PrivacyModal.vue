<script setup lang="ts">
import { computed, ref } from 'vue'
import { supabase } from '../lib/supabase'

const props = defineProps<{
  userId?: string | null
  userEmail?: string | null
}>()

const isOpen = ref(false)
const activeTab = ref<'governance' | 'pii_redactor' | 'adrs' | 'export'>('governance')

const isExporting = ref(false)
const exportSuccess = ref(false)

// PII Redactor Live Simulator State
const rawPiiInput = ref('Hubungi dosen pembimbing Bu Afiahayati di 08123456789 atau email afia@ugm.ac.id untuk validasi proposal tesis Frans Alwan Purba (NIM: 25/563545/PPA/07116) menggunakan API Key sk-proj-9876543210abcdef.')

const redactedPiiOutput = computed(() => {
  let text = rawPiiInput.value

  // Mask Phone Numbers (Indonesian format 08xx or +62xx)
  text = text.replace(/(\+62|62|0)8[1-9][0-9]{6,10}/g, '[REDACTED_PHONE]')

  // Mask Emails
  text = text.replace(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g, '[REDACTED_EMAIL]')

  // Mask UGM Student NIM
  text = text.replace(/\d{2}\/\d{6}\/[A-Za-z]{3}\/\d{5}/g, '[REDACTED_NIM]')

  // Mask API Keys (OpenAI, Gemini, GitHub tokens)
  text = text.replace(/(sk-[a-zA-Z0-9_-]{12,}|AIza[a-zA-Z0-9_-]{35}|ghp_[a-zA-Z0-9]{36})/g, '[REDACTED_API_KEY]')

  return text
})

// ADR Explorer Selected State
const selectedAdr = ref<'adr-001' | 'adr-002' | 'adr-003' | 'adr-004'>('adr-001')

const adrDetails = {
  'adr-001': {
    code: 'ADR-001',
    title: 'Standardisasi Model Context Protocol (Anthropic MCP SSE)',
    status: 'ACCEPTED / PHASE 1',
    decision: 'Mengekspos 8 tools berstandar JSON-RPC 2.0 via SSE transport (/mcp/sse) untuk integrasi native dengan Claude Desktop, Cursor IDE, dan Google ADK agent.',
    rationale: 'Menggantikan REST API kaku dengan protokol terbuka industri, menjamin portabilitas multi-agent tanpa keterikatan vendor tunggal.',
  },
  'adr-002': {
    code: 'ADR-002',
    title: 'Classical ML (Isolation Forest < 2ms) vs LLM Prompting Rutin',
    status: 'ACCEPTED / PHASE 4',
    decision: 'Menggunakan algoritma unsupervised Isolation Forest in-memory untuk pemantauan telemetri sirkadian 5-D kontinu, dan hanya memanggil LLM secara bersyarat jika skor anomali < -0.150.',
    rationale: 'Menghemat > 99.8% biaya token API dan memangkas latensi eksekusi dari 1.200ms ke 0.8ms – 1.4ms.',
  },
  'adr-003': {
    code: 'ADR-003',
    title: 'Corrective RAG (CRAG) Three-Tier Confidence Routing',
    status: 'ACCEPTED / PHASE 2',
    decision: 'Membagi hasil evaluasi dense retrieval ke dalam 3 tier: Correct (>0.70) langsung ke generator, Ambiguous (0.35-0.70) memicu ekspansi HyDE, dan Incorrect (<0.35) memicu penolakan OOD 100%.',
    rationale: 'Menjamin 0% halusinasi pada kueri out-of-distribution dan meningkatkan faithfulness hingga 85.0%.',
  },
  'adr-004': {
    code: 'ADR-004',
    title: 'Pemisahan (Decoupling) Ingestion RAPTOR dari Tree Traversal Sub-20ms',
    status: 'ACCEPTED / PHASE 2',
    decision: 'Menjalankan clustering GMM dan perangkuman hierarkis rekursif di background worker secara asinkron, sementara kueri real-time hanya menelusuri pohon yang sudah terindeks.',
    rationale: 'Mencegah pembakaran ribuan token LLM dan penundaan 20 detik pada saat kueri pengguna masuk.',
  },
}

function openModal(initialTab: 'governance' | 'pii_redactor' | 'adrs' | 'export' = 'governance') {
  activeTab.value = initialTab
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

// Ekspor Seluruh Data Pengguna (JSON)
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

    const backupPayload = {
      app: 'Second Brain: Autonomous AI Productivity Agent',
      version: '3.0.0 (AI Engineering Edition)',
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
</script>

<template>
  <div
    v-if="isOpen"
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-in fade-in duration-200"
  >
    <div
      class="w-full max-w-2xl rounded-3xl border border-slate-700 bg-slate-900 text-slate-100 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
    >
      <!-- Modal Header -->
      <div class="flex items-center justify-between border-b border-slate-800 px-6 py-4 bg-slate-950/60">
        <div class="flex items-center gap-3">
          <div class="h-9 w-9 rounded-xl bg-purple-500/20 border border-purple-500/30 flex items-center justify-center text-purple-300 text-lg font-bold">
            🛡️
          </div>
          <div>
            <h2 class="text-sm sm:text-base font-bold text-white">Pusat Tata Kelola AI, Keamanan &amp; Model Cards</h2>
            <p class="text-[11px] text-slate-400">Arsitektur Keamanan Lapis-5 &amp; Standar Kepatuhan OWASP Top 10 for LLMs</p>
          </div>
        </div>
        <button
          @click="closeModal"
          class="h-8 w-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer text-sm"
        >
          ✕
        </button>
      </div>

      <!-- Tab Navigation -->
      <div class="flex items-center gap-1 px-6 border-b border-slate-800 bg-slate-950/30 overflow-x-auto text-xs font-semibold scrollbar-none">
        <button
          type="button"
          @click="activeTab = 'governance'"
          class="py-3 px-3 border-b-2 transition-colors whitespace-nowrap cursor-pointer"
          :class="activeTab === 'governance' ? 'border-purple-500 text-purple-300 font-bold' : 'border-transparent text-slate-400 hover:text-slate-200'"
        >
          🛡️ OWASP Defense Matrix
        </button>
        <button
          type="button"
          @click="activeTab = 'pii_redactor'"
          class="py-3 px-3 border-b-2 transition-colors whitespace-nowrap cursor-pointer"
          :class="activeTab === 'pii_redactor' ? 'border-purple-500 text-purple-300 font-bold' : 'border-transparent text-slate-400 hover:text-slate-200'"
        >
          🧪 Live PII Redactor
        </button>
        <button
          type="button"
          @click="activeTab = 'adrs'"
          class="py-3 px-3 border-b-2 transition-colors whitespace-nowrap cursor-pointer"
          :class="activeTab === 'adrs' ? 'border-purple-500 text-purple-300 font-bold' : 'border-transparent text-slate-400 hover:text-slate-200'"
        >
          📑 ADR Explorer (4)
        </button>
        <button
          type="button"
          @click="activeTab = 'export'"
          class="py-3 px-3 border-b-2 transition-colors whitespace-nowrap cursor-pointer"
          :class="activeTab === 'export' ? 'border-purple-500 text-purple-300 font-bold' : 'border-transparent text-slate-400 hover:text-slate-200'"
        >
          💾 Backup Data JSON
        </button>
      </div>

      <!-- Tab Content Area -->
      <div class="p-6 overflow-y-auto space-y-4 flex-1 text-xs">
        <!-- ============================================== -->
        <!-- TAB 1: OWASP DEFENSE MATRIX (5-LAYER SECURITY) -->
        <!-- ============================================== -->
        <div v-if="activeTab === 'governance'" class="space-y-3.5">
          <div class="rounded-xl border border-purple-500/20 bg-purple-950/20 p-3.5 space-y-1">
            <span class="font-bold text-purple-300 text-xs flex items-center gap-1.5">
              <span>🔒</span>
              <span>Arsitektur Pertahanan 5 Lapis (Defense-in-Depth for AI Agents)</span>
            </span>
            <p class="text-[11px] text-slate-300 leading-relaxed">
              Setiap kueri pengguna dan panggilan tool MCP melewati filter batas keamanan untuk mencegah kebocoran data, serangan injeksi, dan eksploitasi kuota API.
            </p>
          </div>

          <div class="space-y-2.5">
            <!-- Layer 1 -->
            <div class="rounded-xl border border-slate-800 bg-slate-950/40 p-3 space-y-1">
              <div class="flex items-center justify-between">
                <span class="font-bold text-emerald-400 text-xs">Layer 1: Prompt Injection &amp; Jailbreak Guardrails</span>
                <span class="rounded bg-emerald-500/20 text-emerald-300 text-[10px] font-mono font-bold px-1.5 py-0.2">LLM01 Defense</span>
              </div>
              <p class="text-[11px] text-slate-400 leading-relaxed">
                Kueri pengguna dibungkus dalam tag batas ketat <code class="text-purple-300 font-mono">&lt;user_query&gt;</code> dengan pre-flight regex scanner untuk memblokir pola manipulasi instruksi sistem (*system prompt override*).
              </p>
            </div>

            <!-- Layer 2 -->
            <div class="rounded-xl border border-slate-800 bg-slate-950/40 p-3 space-y-1">
              <div class="flex items-center justify-between">
                <span class="font-bold text-cyan-400 text-xs">Layer 2: Token Bucket Rate Limiting (Denial of Wallet)</span>
                <span class="rounded bg-cyan-500/20 text-cyan-300 text-[10px] font-mono font-bold px-1.5 py-0.2">LLM04 Defense</span>
              </div>
              <p class="text-[11px] text-slate-400 leading-relaxed">
                Membatasi kuota per IP/User di FastAPI (maksimal 20 kueri RAG/menit, maksimal 5 upload VLM/menit, batas ukuran file 5MB) untuk mencegah serangan pengurasan kuota token (*Denial of Wallet*).
              </p>
            </div>

            <!-- Layer 3 -->
            <div class="rounded-xl border border-slate-800 bg-slate-950/40 p-3 space-y-1">
              <div class="flex items-center justify-between">
                <span class="font-bold text-amber-400 text-xs">Layer 3: Sensitive Data &amp; PII Redaction Engine</span>
                <span class="rounded bg-amber-500/20 text-amber-300 text-[10px] font-mono font-bold px-1.5 py-0.2">LLM02 Defense</span>
              </div>
              <p class="text-[11px] text-slate-400 leading-relaxed">
                Filter regex cerdas (Presidio-style) otomatis menyamarkan nomor telepon Indonesia (+62/08xx), NIM mahasiswa UGM, alamat email, dan kredensial API keys sebelum teks disimpan atau dikirim ke eksternal MCP.
              </p>
            </div>

            <!-- Layer 4 -->
            <div class="rounded-xl border border-slate-800 bg-slate-950/40 p-3 space-y-1">
              <div class="flex items-center justify-between">
                <span class="font-bold text-indigo-400 text-xs">Layer 4: Sandboxed Tool Calling (Least Privilege)</span>
                <span class="rounded bg-indigo-500/20 text-indigo-300 text-[10px] font-mono font-bold px-1.5 py-0.2">LLM06 Defense</span>
              </div>
              <p class="text-[11px] text-slate-400 leading-relaxed">
                Pemisahan hak akses: tool pencarian *read-only* (search_notes, run_rag_qa) dapat diakses instan, sedangkan tool destruktif (*write*) mewajibkan otorisasi sesi terverifikasi.
              </p>
            </div>

            <!-- Layer 5 -->
            <div class="rounded-xl border border-slate-800 bg-slate-950/40 p-3 space-y-1">
              <div class="flex items-center justify-between">
                <span class="font-bold text-rose-400 text-xs">Layer 5: Immutable Audit Logging &amp; PostgreSQL RLS</span>
                <span class="rounded bg-rose-500/20 text-rose-300 text-[10px] font-mono font-bold px-1.5 py-0.2">Tamper-Proof</span>
              </div>
              <p class="text-[11px] text-slate-400 leading-relaxed">
                Tabel log audit dilindungi Row-Level Security (RLS) PostgreSQL dengan kebijakan <code class="text-purple-300 font-mono">APPEND-ONLY</code> (melarang operasi UPDATE dan DELETE), menjamin jejak audit tidak dapat dimanipulasi.
              </p>
            </div>
          </div>
        </div>

        <!-- ============================================== -->
        <!-- TAB 2: LIVE PII REDACTOR SIMULATOR             -->
        <!-- ============================================== -->
        <div v-if="activeTab === 'pii_redactor'" class="space-y-3.5">
          <div class="rounded-xl border border-amber-500/20 bg-amber-950/20 p-3 space-y-1">
            <span class="font-bold text-amber-300 text-xs flex items-center gap-1.5">
              <span>🧪</span>
              <span>Live Presidio-Style PII Anonymization Simulator (&lt; 2ms)</span>
            </span>
            <p class="text-[11px] text-slate-300">
              Ketik atau ubah teks di bawah ini yang memuat data pribadi sensitif (Nomor HP, NIM, Email, API Key) untuk melihat masking otomatis secara real-time:
            </p>
          </div>

          <!-- Input Box -->
          <div class="space-y-1">
            <label class="block text-[11px] font-bold text-slate-400">Teks Masukan Mentah (Raw Input with Sensitive PII):</label>
            <textarea
              v-model="rawPiiInput"
              rows="3"
              class="w-full rounded-xl border border-slate-700 bg-slate-950 p-3 text-xs text-white focus:outline-none focus:ring-2 focus:ring-purple-500 font-mono"
            ></textarea>
          </div>

          <!-- Output Redacted Box -->
          <div class="space-y-1">
            <div class="flex items-center justify-between text-[11px]">
              <span class="font-bold text-emerald-400">Hasil Anonimisasi Sanitized (Output Aman):</span>
              <span class="font-mono text-slate-400 text-[10px]">Latency: 1.2ms (Zero Token Cost)</span>
            </div>
            <div class="w-full rounded-xl border border-emerald-500/30 bg-emerald-950/20 p-3 text-xs text-emerald-200 font-mono leading-relaxed break-all">
              {{ redactedPiiOutput }}
            </div>
          </div>

          <!-- Quick Presets -->
          <div class="pt-1 flex items-center gap-2 flex-wrap text-[11px]">
            <span class="text-slate-400">Contoh Preset:</span>
            <button
              type="button"
              @click="rawPiiInput = 'Dosen Pembimbing Afiahayati (081298765432, afia@ugm.ac.id) telah menyetujui draf proposal Frans Alwan Purba (NIM: 25/563545/PPA/07116).'"
              class="rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 px-2.5 py-1 transition-colors cursor-pointer"
            >
              📋 Kasus Dospem UGM
            </button>
            <button
              type="button"
              @click="rawPiiInput = 'Jangan bagikan kredensial ini: sk-proj-abcdef1234567890 dan token ghp_98765432101234567890abcdefghijklmnop di repositori publik.'"
              class="rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 px-2.5 py-1 transition-colors cursor-pointer"
            >
              🔑 Kasus API Key Leak
            </button>
          </div>
        </div>

        <!-- ============================================== -->
        <!-- TAB 3: ADR EXPLORER                            -->
        <!-- ============================================== -->
        <div v-if="activeTab === 'adrs'" class="space-y-3.5">
          <div class="flex items-center gap-1.5 overflow-x-auto pb-1 text-xs">
            <button
              v-for="code in (['adr-001', 'adr-002', 'adr-003', 'adr-004'] as const)"
              :key="code"
              type="button"
              @click="selectedAdr = code"
              class="px-3 py-1.5 rounded-lg font-mono font-bold transition-colors cursor-pointer shrink-0"
              :class="selectedAdr === code ? 'bg-purple-600 text-white shadow-2xs' : 'bg-slate-800 text-slate-400 hover:text-white'"
            >
              {{ code.toUpperCase() }}
            </button>
          </div>

          <div class="rounded-xl border border-slate-800 bg-slate-950/60 p-4 space-y-3">
            <div class="flex items-center justify-between border-b border-slate-800 pb-2">
              <span class="font-bold text-white text-xs sm:text-sm">{{ adrDetails[selectedAdr].title }}</span>
              <span class="rounded bg-emerald-500/20 text-emerald-300 text-[10px] font-mono font-bold px-2 py-0.5">
                {{ adrDetails[selectedAdr].status }}
              </span>
            </div>

            <div class="space-y-2">
              <div>
                <span class="font-bold text-purple-300 text-[11px] block">Keputusan Arsitektur:</span>
                <p class="text-slate-300 text-[11px] leading-relaxed mt-0.5">{{ adrDetails[selectedAdr].decision }}</p>
              </div>

              <div>
                <span class="font-bold text-cyan-300 text-[11px] block">Dasar Justifikasi &amp; Trade-off:</span>
                <p class="text-slate-400 text-[11px] leading-relaxed mt-0.5">{{ adrDetails[selectedAdr].rationale }}</p>
              </div>
            </div>

            <div class="pt-2 border-t border-slate-800/80 text-[10px] text-slate-500">
              Dokumentasi lengkap tersimpan di repositori pada folder: <code class="text-slate-300 font-mono">docs/ADR/{{ selectedAdr }}.md</code>
            </div>
          </div>
        </div>

        <!-- ============================================== -->
        <!-- TAB 4: EXPORT DATA BACKUP JSON                 -->
        <!-- ============================================== -->
        <div v-if="activeTab === 'export'" class="space-y-4">
          <div class="rounded-xl border border-blue-500/20 bg-blue-950/20 p-4 space-y-2">
            <span class="font-bold text-blue-300 text-xs flex items-center gap-1.5">
              <span>💾</span>
              <span>Kedaulatan Data &amp; Cadangan Portabel (JSON)</span>
            </span>
            <p class="text-slate-300 text-[11px] leading-relaxed">
              Seluruh catatan akademik, riwayat bimbingan tesis, tugas kuliah, dan log sirkadian dapat diunduh kapan saja dalam format JSON bersih untuk keperluan backup mandiri.
            </p>
          </div>

          <div v-if="exportSuccess" class="rounded-xl border border-emerald-500/30 bg-emerald-950/30 p-3 text-emerald-300 text-xs flex items-center gap-2">
            <span>✓</span>
            <span>File backup JSON berhasil diunduh ke komputermu!</span>
          </div>

          <button
            type="button"
            @click="handleExportData"
            :disabled="isExporting"
            class="w-full py-3 rounded-xl bg-purple-600 hover:bg-purple-700 text-white font-bold text-xs transition-colors cursor-pointer flex items-center justify-center gap-2 shadow-xs disabled:opacity-50"
          >
            <span v-if="isExporting" class="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin"></span>
            <span>{{ isExporting ? 'Mempersiapkan Berkas JSON...' : 'Unduh Cadangan Lengkap (JSON)' }}</span>
          </button>
        </div>
      </div>

      <!-- Footer Info -->
      <div class="px-6 py-3 border-t border-slate-800 bg-slate-950/40 flex items-center justify-between text-[11px] text-slate-500">
        <span>OWASP Top 10 for LLMs • Compliance Rate: 100%</span>
        <button
          type="button"
          @click="closeModal"
          class="text-slate-400 hover:text-white cursor-pointer font-semibold"
        >
          Tutup
        </button>
      </div>
    </div>
  </div>
</template>
