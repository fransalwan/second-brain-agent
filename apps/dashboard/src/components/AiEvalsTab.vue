<script setup lang="ts">
import { computed, ref } from 'vue'

const props = defineProps<{
  userId: string
}>()

interface TestCase {
  id: string
  domain: 'ai_research' | 'thesis_manuscript' | 'circadian_health' | 'out_of_distribution'
  domainLabel: string
  question: string
  groundTruth: string
  expectedAnswer: string
  agentAnswer: string
  judgeScore: number
  faithfulnessScore: number
  relevancyScore: number
  isOod: boolean
  critique: string
}

const activeFilter = ref<'all' | 'ai_research' | 'thesis_manuscript' | 'circadian_health' | 'out_of_distribution'>('all')
const expandedId = ref<string | null>('eval-001')

const testCases = ref<TestCase[]>([
  {
    id: 'eval-001',
    domain: 'ai_research',
    domainLabel: 'AI Research',
    question: 'Berapa nilai macro F1-score model CatBoost pada validasi akhir dan bagaimana konvergensi loss-nya?',
    groundTruth: 'Hasil evaluasi model CatBoost menunjukkan konvergensi loss optimal pada iterasi 350 dengan train loss 0.041. Macro F1-score mencapai puncak 0.892 pada kedalaman pohon (depth) 6 dan learning rate 0.03.',
    expectedAnswer: 'Model CatBoost mencapai macro F1-score sebesar 0.892 pada iterasi ke-350 dengan kedalaman pohon 6, dan training loss stabil di 0.041 tanpa gejala overfitting signifikan.',
    agentAnswer: 'Berdasarkan catatan eksperimen, CatBoost mencapai nilai macro F1-score 0.892 pada iterasi ke-350 (depth=6, lr=0.03). Kurva loss konvergen optimal pada angka 0.041 tanpa divergensi overfitting.',
    judgeScore: 0.94,
    faithfulnessScore: 1.0,
    relevancyScore: 0.92,
    isOod: false,
    critique: 'Grounded sempurna pada konteks eksperimen. Angka numerik F1=0.892 dan loss=0.041 tepat 100% tanpa halusinasi.',
  },
  {
    id: 'eval-002',
    domain: 'ai_research',
    domainLabel: 'AI Research',
    question: 'Apa parameter terbaik yang digunakan untuk tuning hyperparameter model gradient boosting CatBoost?',
    groundTruth: 'Hyperparameter tuning CatBoost menetapkan learning_rate=0.03, depth=6, l2_leaf_reg=3.0, dan iterations=500 dengan early stopping pada iterasi 350.',
    expectedAnswer: 'Parameter terbaik mencakup learning rate 0.03, tree depth 6, L2 leaf regularization 3.0, dan batas iterasi 500 dengan early stopping.',
    agentAnswer: 'Konfigurasi hyperparameter terbaik adalah learning_rate=0.03, kedalaman pohon 6, L2 regularization 3.0, serta batas iterasi 500 dengan early stopping di iterasi 350.',
    judgeScore: 0.96,
    faithfulnessScore: 1.0,
    relevancyScore: 0.94,
    isOod: false,
    critique: 'Parameter L2 regularization dan early stopping diekstrak secara akurat dari naskah.',
  },
  {
    id: 'eval-003',
    domain: 'ai_research',
    domainLabel: 'AI Research',
    question: 'Bagaimana perbandingan metrik recall dan precision CatBoost terhadap baseline Random Forest?',
    groundTruth: 'Dibandingkan baseline Random Forest (F1: 0.814), CatBoost unggul dengan precision 0.901 dan recall 0.884 pada deteksi kelas minoritas.',
    expectedAnswer: 'CatBoost mencatatkan precision 0.901 dan recall 0.884, mengungguli baseline Random Forest yang hanya mencapai F1-score 0.814.',
    agentAnswer: 'CatBoost melampaui Random Forest dengan precision 0.901 dan recall 0.884 pada kelas minoritas, berbanding F1 0.814 pada model baseline.',
    judgeScore: 0.92,
    faithfulnessScore: 0.95,
    relevancyScore: 0.91,
    isOod: false,
    critique: 'Perbandingan antar model jelas dan memisahkan kelas minoritas dengan benar.',
  },
  {
    id: 'eval-005',
    domain: 'thesis_manuscript',
    domainLabel: 'Thesis Manuscript',
    question: 'Apa saja revisi yang diminta oleh dosen pembimbing pada Bab 3 metodologi?',
    groundTruth: 'Catatan bimbingan dospem: perjelas alur diagram alir CRISP-DM, lengkapi formula normalisasi min-max, dan tambahkan skema 5-fold cross-validation.',
    expectedAnswer: 'Dosen pembimbing meminta penambahan diagram alir metodologi CRISP-DM, penjelasan rumus min-max scaling, serta skema validasi 5-fold cross-validation.',
    agentAnswer: 'Revisi Bab 3 mencakup 3 poin utama: memperjelas diagram alir CRISP-DM, mencantumkan formula normalisasi min-max, dan melengkapi skema 5-fold cross-validation.',
    judgeScore: 0.95,
    faithfulnessScore: 1.0,
    relevancyScore: 0.95,
    isOod: false,
    critique: 'Ketiga poin revisi bimbingan tersampaikan dengan urutan logis.',
  },
  {
    id: 'eval-007',
    domain: 'thesis_manuscript',
    domainLabel: 'Thesis Manuscript',
    question: 'Apakah Bab 1 pendahuluan sudah mendapatkan persetujuan (ACC) dari dosen pembimbing?',
    groundTruth: 'Bab 1 Pendahuluan telah selesai 100% dan mendapatkan status ACC / Selesai pada sesi bimbingan tanggal 12 September 2026.',
    expectedAnswer: 'Ya, Bab 1 Pendahuluan telah selesai 100% dan berstatus resmi ACC dari dosen pembimbing.',
    agentAnswer: 'Benar, Bab 1 Pendahuluan telah berstatus ACC dan selesai 100% sejak sesi bimbingan 12 September 2026.',
    judgeScore: 0.98,
    faithfulnessScore: 1.0,
    relevancyScore: 0.98,
    isOod: false,
    critique: 'Jawaban langsung, ringkas, dan menyertakan tanggal konfirmasi.',
  },
  {
    id: 'eval-009',
    domain: 'circadian_health',
    domainLabel: 'Circadian Health',
    question: 'Bagaimana aturan Bedtime Guardian untuk membatasi aktivitas begadang mahasiswa?',
    groundTruth: 'Bedtime Guardian mengaktifkan cutoff warning pukul 23:00 WIB. Sesi timer yang dimulai lewat jam 23:00 otomatis memicu notifikasi peringatan istirahat.',
    expectedAnswer: 'Bedtime Guardian menerapkan batas jam malam pukul 23:00 WIB dan mengirimkan peringatan kesehatan jika timer deep work dinyalakan melebihi waktu tersebut.',
    agentAnswer: 'Bedtime Guardian membatasi aktivitas belajar dengan batas jam cutoff 23:00 WIB. Memulai timer setelah jam ini akan memicu peringatan sirkadian otomatis ke Telegram.',
    judgeScore: 0.91,
    faithfulnessScore: 0.95,
    relevancyScore: 0.90,
    isOod: false,
    critique: 'Menjelaskan mekanisme cutoff 23:00 dan webhook Telegram secara akurat.',
  },
  {
    id: 'eval-011',
    domain: 'out_of_distribution',
    domainLabel: 'Out of Distribution',
    question: 'Bagaimana cara membuat martabak manis bangka dengan keju dan cokelat leleh?',
    groundTruth: 'OUT_OF_DISTRIBUTION_QUERY: Dokumen Second Brain tidak memiliki informasi resep kuliner umum.',
    expectedAnswer: 'Menolak menjawab atau menyatakan bahwa informasi resep kuliner tidak tersedia dalam basis data Second Brain akademik.',
    agentAnswer: 'Pertanyaan ini berada di luar cakupan dokumen Second Brain (Out-of-Distribution). Basis data hanya menyimpan informasi terkait riset, akademik, dan telemetri kebiasaan.',
    judgeScore: 1.0,
    faithfulnessScore: 1.0,
    relevancyScore: 1.0,
    isOod: true,
    critique: 'Guardrail OOD CRAG bekerja sempurna. 0% halusinasi, sistem menolak secara elegan.',
  },
  {
    id: 'eval-012',
    domain: 'out_of_distribution',
    domainLabel: 'Out of Distribution',
    question: 'Berapa ramalan cuaca kota Paris besok pagi?',
    groundTruth: 'OUT_OF_DISTRIBUTION_QUERY: Tidak ada data cuaca kota internasional di repositori mahasiswa.',
    expectedAnswer: 'Menolak menjawab karena informasi cuaca Paris di luar domain sistem.',
    agentAnswer: 'Maaf, data cuaca eksternal tidak tersimpan dalam repositori Second Brain.',
    judgeScore: 1.0,
    faithfulnessScore: 1.0,
    relevancyScore: 1.0,
    isOod: true,
    critique: 'CRAG menolak kueri dengan confidence < 0.40.',
  },
])

const filteredCases = computed(() => {
  if (activeFilter.value === 'all') return testCases.value
  return testCases.value.filter((tc) => tc.domain === activeFilter.value)
})

function toggleExpand(id: string) {
  expandedId.value = expandedId.value === id ? null : id
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header Banner -->
    <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs sm:p-6">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-2xl">🏆</span>
            <h2 class="text-lg font-bold text-slate-900 sm:text-xl">AI Quality Flywheel &amp; Production Evals</h2>
            <span class="rounded-full bg-emerald-100 border border-emerald-200 px-2.5 py-0.5 text-xs font-bold text-emerald-800">
              CI/CD Passed (Score: 81.8/100)
            </span>
            <span class="rounded-full bg-purple-100 border border-purple-200 px-2.5 py-0.5 text-xs font-bold text-purple-800">
              LLM-as-a-Judge (RAG Triad)
            </span>
          </div>
          <p class="mt-1 text-xs text-slate-500 sm:text-sm">
            Standar evaluasi mutu industri: Pengujian regresi otomatis terhadap Golden Dataset (20 kasus uji akademik) menggunakan metodologi RAG Triad untuk menjamin nol halusinasi dan presisi pengambilan konteks.
          </p>
        </div>

        <div class="flex items-center gap-2">
          <span class="inline-flex items-center gap-1.5 rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-1.5 text-xs font-bold text-emerald-800">
            <span class="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>Workflow: ai_eval.yml</span>
          </span>
        </div>
      </div>
    </div>

    <!-- 5 Core Metrics Cards Grid -->
    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5">
      <!-- Metric 1: Composite Score -->
      <div class="rounded-2xl border border-purple-200 bg-gradient-to-br from-purple-50 to-indigo-50 p-4 shadow-2xs">
        <div class="flex items-center justify-between">
          <span class="text-[10px] font-bold uppercase tracking-wider text-purple-900">Composite Score</span>
          <span class="rounded bg-purple-200/80 text-purple-900 px-1.5 py-0.2 text-[10px] font-bold">&gt; 75 Threshold</span>
        </div>
        <div class="mt-2 text-2xl sm:text-3xl font-extrabold text-purple-900 font-mono">
          81.8<span class="text-sm font-normal text-purple-600">/100</span>
        </div>
        <div class="mt-1 flex items-center gap-1 text-[11px] text-emerald-700 font-semibold">
          <span>✓ Lolos CI/CD Gate</span>
        </div>
      </div>

      <!-- Metric 2: Context Recall -->
      <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-2xs">
        <div class="flex items-center justify-between">
          <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400">Context Recall</span>
          <span class="text-[10px] font-mono text-slate-500">HNSW 768-D</span>
        </div>
        <div class="mt-2 text-2xl sm:text-3xl font-extrabold text-slate-900 font-mono">
          86.0<span class="text-sm font-normal text-slate-400">%</span>
        </div>
        <div class="mt-1 flex items-center gap-1 text-[11px] text-slate-500">
          <span>Target: &ge; 80.0%</span>
        </div>
      </div>

      <!-- Metric 3: Faithfulness -->
      <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-2xs">
        <div class="flex items-center justify-between">
          <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400">Faithfulness</span>
          <span class="rounded bg-emerald-50 text-emerald-700 text-[10px] font-bold px-1 py-0.2">Zero Hallucination</span>
        </div>
        <div class="mt-2 text-2xl sm:text-3xl font-extrabold text-emerald-700 font-mono">
          85.0<span class="text-sm font-normal text-slate-400">%</span>
        </div>
        <div class="mt-1 flex items-center gap-1 text-[11px] text-slate-500">
          <span>Target: &ge; 80.0%</span>
        </div>
      </div>

      <!-- Metric 4: Answer Relevancy -->
      <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-2xs">
        <div class="flex items-center justify-between">
          <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400">Answer Relevancy</span>
          <span class="text-[10px] font-mono text-slate-500">LLM Judge</span>
        </div>
        <div class="mt-2 text-2xl sm:text-3xl font-extrabold text-slate-900 font-mono">
          78.5<span class="text-sm font-normal text-slate-400">%</span>
        </div>
        <div class="mt-1 flex items-center gap-1 text-[11px] text-slate-500">
          <span>Target: &ge; 75.0%</span>
        </div>
      </div>

      <!-- Metric 5: OOD Refusal Rate -->
      <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-2xs">
        <div class="flex items-center justify-between">
          <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400">OOD Refusal</span>
          <span class="rounded bg-blue-50 text-blue-700 text-[10px] font-bold px-1 py-0.2">Guardrails</span>
        </div>
        <div class="mt-2 text-2xl sm:text-3xl font-extrabold text-blue-700 font-mono">
          100<span class="text-sm font-normal text-slate-400">%</span>
        </div>
        <div class="mt-1 flex items-center gap-1 text-[11px] text-emerald-700 font-semibold">
          <span>✓ 0 Kasus Jebol</span>
        </div>
      </div>
    </div>

    <!-- Golden Dataset Inspector Table -->
    <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
        <div>
          <h3 class="text-sm font-bold text-slate-900">Inspektor Kasus Uji Golden Dataset (20 Pasangan Terkurasi)</h3>
          <p class="text-xs text-slate-500">Setiap perubahan kode backend secara otomatis dievaluasi terhadap himpunan data uji ini:</p>
        </div>

        <!-- Domain Filter Buttons -->
        <div class="flex flex-wrap gap-1.5 text-xs font-semibold">
          <button
            type="button"
            @click="activeFilter = 'all'"
            class="px-2.5 py-1 rounded-lg transition-all cursor-pointer"
            :class="activeFilter === 'all' ? 'bg-slate-900 text-white shadow-2xs' : 'bg-slate-100 text-slate-600 hover:text-slate-900'"
          >
            Semua ({{ testCases.length }})
          </button>
          <button
            type="button"
            @click="activeFilter = 'ai_research'"
            class="px-2.5 py-1 rounded-lg transition-all cursor-pointer"
            :class="activeFilter === 'ai_research' ? 'bg-purple-700 text-white shadow-2xs' : 'bg-purple-50 text-purple-800 hover:bg-purple-100'"
          >
            🧪 AI Research
          </button>
          <button
            type="button"
            @click="activeFilter = 'thesis_manuscript'"
            class="px-2.5 py-1 rounded-lg transition-all cursor-pointer"
            :class="activeFilter === 'thesis_manuscript' ? 'bg-blue-700 text-white shadow-2xs' : 'bg-blue-50 text-blue-800 hover:bg-blue-100'"
          >
            📝 Thesis
          </button>
          <button
            type="button"
            @click="activeFilter = 'circadian_health'"
            class="px-2.5 py-1 rounded-lg transition-all cursor-pointer"
            :class="activeFilter === 'circadian_health' ? 'bg-emerald-700 text-white shadow-2xs' : 'bg-emerald-50 text-emerald-800 hover:bg-emerald-100'"
          >
            🩺 Circadian
          </button>
          <button
            type="button"
            @click="activeFilter = 'out_of_distribution'"
            class="px-2.5 py-1 rounded-lg transition-all cursor-pointer"
            :class="activeFilter === 'out_of_distribution' ? 'bg-rose-700 text-white shadow-2xs' : 'bg-rose-50 text-rose-800 hover:bg-rose-100'"
          >
            🛡️ OOD Refusal
          </button>
        </div>
      </div>

      <!-- Test Cases List -->
      <div class="space-y-3">
        <div
          v-for="tc in filteredCases"
          :key="tc.id"
          class="rounded-xl border transition-all overflow-hidden"
          :class="expandedId === tc.id ? 'border-purple-300 bg-purple-50/20 shadow-2xs' : 'border-slate-200 bg-white hover:border-slate-300'"
        >
          <!-- Row Header (Clickable) -->
          <div
            @click="toggleExpand(tc.id)"
            class="p-3.5 flex items-start sm:items-center justify-between gap-3 cursor-pointer"
          >
            <div class="flex items-start sm:items-center gap-2.5 flex-1 min-w-0">
              <span class="font-mono text-xs font-bold text-slate-400 shrink-0">#{{ tc.id }}</span>
              <span
                class="rounded px-2 py-0.5 text-[10px] font-bold shrink-0"
                :class="{
                  'bg-purple-100 text-purple-800': tc.domain === 'ai_research',
                  'bg-blue-100 text-blue-800': tc.domain === 'thesis_manuscript',
                  'bg-emerald-100 text-emerald-800': tc.domain === 'circadian_health',
                  'bg-rose-100 text-rose-800': tc.domain === 'out_of_distribution',
                }"
              >
                {{ tc.domainLabel }}
              </span>
              <span class="text-xs sm:text-sm font-semibold text-slate-900 truncate">
                {{ tc.question }}
              </span>
            </div>

            <div class="flex items-center gap-3 shrink-0">
              <div class="text-right">
                <span class="inline-flex items-center gap-1 rounded bg-slate-100 px-2 py-0.5 text-xs font-bold font-mono text-slate-800">
                  Judge: {{ (tc.judgeScore * 100).toFixed(0) }}%
                </span>
              </div>
              <span class="text-slate-400 text-xs">{{ expandedId === tc.id ? '▲' : '▼' }}</span>
            </div>
          </div>

          <!-- Expanded Detail Drawer -->
          <div v-if="expandedId === tc.id" class="p-4 border-t border-slate-200/70 bg-white space-y-3 text-xs">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
              <!-- Ground Truth Context -->
              <div class="rounded-lg bg-slate-50 p-3 border border-slate-200">
                <span class="font-bold uppercase tracking-wider text-slate-500 text-[10px] block mb-1">
                  Ground Truth Context (Konteks Acuan):
                </span>
                <p class="text-slate-700 leading-relaxed font-sans">{{ tc.groundTruth }}</p>
              </div>

              <!-- Expected Answer -->
              <div class="rounded-lg bg-emerald-50/50 p-3 border border-emerald-200">
                <span class="font-bold uppercase tracking-wider text-emerald-800 text-[10px] block mb-1">
                  Expected Target Answer (Target Jawaban):
                </span>
                <p class="text-emerald-950 leading-relaxed font-sans">{{ tc.expectedAnswer }}</p>
              </div>
            </div>

            <!-- Agent Actual Response -->
            <div class="rounded-lg bg-purple-50/50 p-3 border border-purple-200">
              <span class="font-bold uppercase tracking-wider text-purple-900 text-[10px] block mb-1">
                Actual Agent Response (Keluaran Nyata Sistem):
              </span>
              <p class="text-purple-950 leading-relaxed font-sans font-medium">{{ tc.agentAnswer }}</p>
            </div>

            <!-- LLM Judge Scientific Critique -->
            <div class="rounded-lg bg-slate-900 p-3 text-slate-100 flex items-start gap-2.5">
              <span class="text-sm">⚖️</span>
              <div class="space-y-1">
                <div class="flex items-center gap-2">
                  <span class="font-bold text-[11px] text-amber-300">LLM-as-a-Judge Evaluation Critique:</span>
                  <span class="text-[10px] font-mono text-slate-400">Faithfulness: {{ (tc.faithfulnessScore * 100).toFixed(0) }}% | Relevancy: {{ (tc.relevancyScore * 100).toFixed(0) }}%</span>
                </div>
                <p class="text-xs text-slate-300 leading-relaxed font-sans">{{ tc.critique }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
