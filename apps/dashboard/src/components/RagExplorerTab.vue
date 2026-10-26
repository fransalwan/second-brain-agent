<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  userId: string
}>()

interface RagHit {
  id: number
  title: string
  content: string
  cluster: string
  initialRank: number
  rerankScore: number
  finalRank: number
  matchType: 'Semantic (768-D)' | 'Hybrid (RRF)' | 'RAPTOR Summary'
}

interface RaptorCluster {
  id: string
  name: string
  summary: string
  leafCount: number
  badgeColor: string
}

const queryInput = ref('Bagaimana evaluasi konvergensi loss dan F1-Score pada model CatBoost?')
const isEvaluating = ref(false)
const selectedCluster = ref<string | null>(null)

// Sample RAPTOR Knowledge Tree Clusters
const raptorClusters = ref<RaptorCluster[]>([
  {
    id: 'cluster-catboost',
    name: 'Klaster A: CatBoost & Predictive ML',
    summary: 'Rangkuman sintetis: Eksperimen model ensemble pohon keputusan (CatBoost & LightGBM) menunjukkan konvergensi stabil pada epoch 350 dengan akurasi 95.1% dan F1-Score 94.4%. Hyperparameter regularization L2=3.0 terbukti mencegah overfitting.',
    leafCount: 4,
    badgeColor: 'bg-purple-100 text-purple-800 border-purple-200',
  },
  {
    id: 'cluster-thesis',
    name: 'Klaster B: Naskah Tesis & Arsitektur RAG',
    summary: 'Rangkuman sintetis: Metodologi Bab 3 memanfaatkan PostgreSQL pgvector dengan indeks HNSW (m=16, ef_construction=64) dan Reciprocal Rank Fusion (RRF k=60). Format sitasi mengikuti kaidah IEEE Transactions.',
    leafCount: 5,
    badgeColor: 'bg-blue-100 text-blue-800 border-blue-200',
  },
  {
    id: 'cluster-circadian',
    name: 'Klaster C: Telemetri Sirkadian & Performa Kognitif',
    summary: 'Rangkuman sintetis: Analisis korelasi menemukan sleep debt > 6 jam menurunkan durasi deep work rata-rata 38%. Pemotongan aktivitas layar pada pukul 23:00 meningkatkan efisiensi komputasi riset esok hari.',
    leafCount: 3,
    badgeColor: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  },
])

// CRAG State
const cragState = ref<{
  confidence: number
  action: 'CORRECT' | 'AMBIGUOUS' | 'INCORRECT'
  hydePrompt: string | null
  executionLatencyMs: number
  generatedAnswer: string
  citations: string[]
  hits: RagHit[]
}>({
  confidence: 0.892,
  action: 'CORRECT',
  hydePrompt: null,
  executionLatencyMs: 18.4,
  generatedAnswer:
    'Berdasarkan naskah eksperimen Bab 4 dan log model CatBoost, kurva loss menunjukkan penurunan monotonik dari 0.450 ke 0.118 pada iterasi ke-350. Evaluasi pada test split mencapai Akurasi 95.1%, F1-Score 94.4%, dan AUC-ROC 0.972. Cross-Encoder memvalidasi konsistensi hasil terhadap metrik baseline XGBoost.',
  citations: ['Eksperimen CatBoost Epoch 500 (#exp-104)', 'Bab 4 Hasil & Pembahasan (#thesis-ch4)'],
  hits: [
    {
      id: 1,
      title: 'Eksperimen CatBoost: Telemetri Epoch 1 s.d. 500',
      content: 'Metrik evaluasi: Loss konvergen di 0.118 (epoch 350). Akurasi=95.1%, F1-Score=94.4%, AUC=0.972. Tidak terdeteksi tanda-tanda overfitting pada validasi 5-fold cross validation.',
      cluster: 'Klaster A: CatBoost & Predictive ML',
      initialRank: 2,
      rerankScore: 0.945,
      finalRank: 1,
      matchType: 'Hybrid (RRF)',
    },
    {
      id: 2,
      title: 'Bab 4: Komparasi Model Ensemble & Tree-based',
      content: 'CatBoost melampaui Random Forest dan XGBoost standar sebesar +2.3% dalam macro F1-score pada penanganan fitur kategorikal akademik.',
      cluster: 'Klaster B: Naskah Tesis & Arsitektur RAG',
      initialRank: 1,
      rerankScore: 0.892,
      finalRank: 2,
      matchType: 'Semantic (768-D)',
    },
    {
      id: 3,
      title: 'Ringkasan Klaster RAPTOR: Optimasi Model ML',
      content: 'Sintesis tingkat tinggi mencakup trade-off waktu pelatihan versus daya inferensi real-time di GPU/CPU.',
      cluster: 'Klaster A: CatBoost & Predictive ML',
      initialRank: 5,
      rerankScore: 0.812,
      finalRank: 3,
      matchType: 'RAPTOR Summary',
    },
  ],
})

function applyPreset(query: string) {
  queryInput.value = query
  runCragSimulation()
}

function runCragSimulation() {
  const q = queryInput.value.trim().toLowerCase()
  isEvaluating.value = true

  setTimeout(() => {
    isEvaluating.value = false

    if (q.includes('martabak') || q.includes('resep') || q.includes('cuaca') || q.includes('wisata')) {
      // Out of distribution / Incorrect scenario
      cragState.value = {
        confidence: 0.142,
        action: 'INCORRECT',
        hydePrompt: null,
        executionLatencyMs: 8.2,
        generatedAnswer:
          '⚠️ [CRAG Guardrail Triggered] Pertanyaan ini berada di luar ranah pengetahuan Second Brain (Out-of-Distribution, confidence: 14.2% < 40%). Sistem menolak menghasilkan jawaban halusinatif demi menjaga integritas akademik.',
        citations: [],
        hits: [],
      }
    } else if (q.includes('kafein') || q.includes('tidur') || q.includes('rem') || q.includes('sirkadian')) {
      // Ambiguous / HyDE scenario
      cragState.value = {
        confidence: 0.684,
        action: 'AMBIGUOUS',
        hydePrompt: 'Korelasi konsumsi kafein sore hari dengan gangguan tidur gelombang lambat (slow-wave sleep) dan dampak kognitif belajar mahasiswa...',
        executionLatencyMs: 32.1,
        generatedAnswer:
          'Melalui ekspansi HyDE (Hypothetical Document Embeddings), ditemukan korelasi bahwa konsumsi kafein setelah jam 18:00 menunda sekresi melatonin rata-rata 40 menit, memangkas tidur tahap N3 (Deep Sleep), dan menurunkan efektivitas deep work riset esok harinya hingga 25%.',
        citations: ['Log Sirkadian & Bedtime Guardian', 'Klaster C: Telemetri Sirkadian'],
        hits: [
          {
            id: 201,
            title: 'Catatan Fisiologi: Kafein & Waktu Paruh Adenosin',
            content: 'Waktu paruh kafein mencapai 5-7 jam. Konsumsi pukul 19:00 menyisakan ~50% kadar dalam plasma darah saat fase tidur malam dimulai.',
            cluster: 'Klaster C: Telemetri Sirkadian & Performa Kognitif',
            initialRank: 4,
            rerankScore: 0.865,
            finalRank: 1,
            matchType: 'Hybrid (RRF)',
          },
          {
            id: 202,
            title: 'Analisis Korelasi Deep Work vs Jam Istirahat',
            content: 'Sesi fokus 90 menit berhasil diselesaikan jika bedtime cutoff jam 23:00 dipatuhi.',
            cluster: 'Klaster C: Telemetri Sirkadian & Performa Kognitif',
            initialRank: 2,
            rerankScore: 0.781,
            finalRank: 2,
            matchType: 'Semantic (768-D)',
          },
        ],
      }
    } else {
      // Standard Correct / High Confidence scenario
      cragState.value = {
        confidence: 0.915,
        action: 'CORRECT',
        hydePrompt: null,
        executionLatencyMs: 14.8,
        generatedAnswer:
          'Berdasarkan naskah Bab 3 & Bab 4, arsitektur RAG memanfaatkan indeks HNSW (Hierarchical Navigable Small World) pada vektor 768-D Gemini di PostgreSQL pgvector. Hasil pencarian digabungkan dengan BM25 menggunakan algoritma Reciprocal Rank Fusion (RRF k=60), menghasilkan Mean Reciprocal Rank (MRR) 0.884.',
        citations: ['Naskah Bab 3 Metodologi HNSW', 'Klaster B: Naskah Tesis & Arsitektur RAG'],
        hits: [
          {
            id: 301,
            title: 'Metodologi Bab 3: HNSW Indexing Parameter',
            content: 'Konfigurasi pgvector: CREATE INDEX ON note_embeddings USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64).',
            cluster: 'Klaster B: Naskah Tesis & Arsitektur RAG',
            initialRank: 1,
            rerankScore: 0.962,
            finalRank: 1,
            matchType: 'Semantic (768-D)',
          },
          {
            id: 302,
            title: 'Evaluasi Formula RRF (Reciprocal Rank Fusion)',
            content: 'Skor fusi dihitung dengan RRF_Score = sum(1 / (k + rank_i)) dengan konstanta smoothing k=60.',
            cluster: 'Klaster B: Naskah Tesis & Arsitektur RAG',
            initialRank: 3,
            rerankScore: 0.895,
            finalRank: 2,
            matchType: 'Hybrid (RRF)',
          },
        ],
      }
    }
  }, 400)
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header Banner -->
    <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs sm:p-6">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-2xl">🧠</span>
            <h2 class="text-lg font-bold text-slate-900 sm:text-xl">Next-Gen RAG &amp; RAPTOR Knowledge Tree</h2>
            <span class="rounded-full bg-purple-100 border border-purple-200 px-2.5 py-0.5 text-xs font-bold text-purple-800">
              Corrective RAG (CRAG)
            </span>
            <span class="rounded-full bg-indigo-100 border border-indigo-200 px-2.5 py-0.5 text-xs font-bold text-indigo-800">
              Cross-Encoder Reranker
            </span>
          </div>
          <p class="mt-1 text-xs text-slate-500 sm:text-sm">
            Arsitektur pencarian semantik berstandar riset: Pengelompokan hirarkis dokumen via Gaussian Mixture Models (RAPTOR), routing evaluasi mandiri (CRAG), ekspansi kueri hipotesis (HyDE), dan reranking cross-encoder.
          </p>
        </div>

        <div class="flex items-center gap-2">
          <span class="inline-flex items-center gap-1.5 rounded-xl border border-purple-200 bg-purple-50 px-3 py-1.5 text-xs font-bold text-purple-800">
            <span class="h-2 w-2 rounded-full bg-purple-600 animate-pulse"></span>
            <span>HNSW 768-D Vector Ready</span>
          </span>
        </div>
      </div>
    </div>

    <!-- Interactive Query Tester & Presets -->
    <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <div>
          <h3 class="text-sm font-bold text-slate-900">Uji Coba Interaktif Pipeline CRAG</h3>
          <p class="text-xs text-slate-500">Pilih kueri preset riset atau masukkan pertanyaan kustom untuk melihat routing inferensi:</p>
        </div>
        <div class="flex items-center gap-2 text-xs text-slate-500">
          <span>Latensi: <strong>{{ cragState.executionLatencyMs }}ms</strong></span>
        </div>
      </div>

      <!-- Presets Pills -->
      <div class="flex flex-wrap gap-2">
        <button
          type="button"
          @click="applyPreset('Bagaimana evaluasi konvergensi loss dan F1-Score pada model CatBoost?')"
          class="rounded-lg border border-purple-200 bg-purple-50/70 hover:bg-purple-100 px-2.5 py-1 text-xs font-semibold text-purple-900 transition-colors cursor-pointer"
        >
          🧪 CatBoost Loss &amp; F1 (High Confidence)
        </button>
        <button
          type="button"
          @click="applyPreset('Bagaimana arsitektur HNSW pgvector diintegrasikan dengan RRF di PostgreSQL?')"
          class="rounded-lg border border-blue-200 bg-blue-50/70 hover:bg-blue-100 px-2.5 py-1 text-xs font-semibold text-blue-900 transition-colors cursor-pointer"
        >
          📝 HNSW &amp; RRF pgvector (Tesis Metodologi)
        </button>
        <button
          type="button"
          @click="applyPreset('Apakah kafein setelah jam 18:00 mengganggu fase tidur REM dan deep work?')"
          class="rounded-lg border border-emerald-200 bg-emerald-50/70 hover:bg-emerald-100 px-2.5 py-1 text-xs font-semibold text-emerald-900 transition-colors cursor-pointer"
        >
          🟡 Efek Kafein Malam (HyDE Expansion)
        </button>
        <button
          type="button"
          @click="applyPreset('Berapa resep membuat martabak manis keju cokelat super lezat?')"
          class="rounded-lg border border-rose-200 bg-rose-50/70 hover:bg-rose-100 px-2.5 py-1 text-xs font-semibold text-rose-900 transition-colors cursor-pointer"
        >
          🔴 Resep Martabak (Out-of-Distribution Refusal)
        </button>
      </div>

      <!-- Search Input Bar -->
      <div class="flex items-center gap-2">
        <div class="relative flex-1">
          <input
            v-model="queryInput"
            type="text"
            placeholder="Masukkan kueri akademik atau pertanyaan riset..."
            class="w-full rounded-xl border border-slate-300 bg-slate-50 px-4 py-2.5 text-xs sm:text-sm text-slate-900 placeholder-slate-400 focus:bg-white focus:border-purple-600 focus:outline-none"
            @keyup.enter="runCragSimulation"
          />
        </div>
        <button
          type="button"
          @click="runCragSimulation"
          :disabled="isEvaluating || !queryInput.trim()"
          class="rounded-xl bg-purple-700 hover:bg-purple-800 disabled:opacity-50 px-5 py-2.5 text-xs sm:text-sm font-bold text-white transition-colors cursor-pointer shadow-xs flex items-center gap-2 shrink-0"
        >
          <span v-if="isEvaluating">Menghitung...</span>
          <span v-else>Jalankan CRAG ➔</span>
        </button>
      </div>

      <!-- CRAG Routing State Banner -->
      <div
        class="rounded-xl border p-4 transition-all"
        :class="{
          'border-emerald-200 bg-emerald-50/80': cragState.action === 'CORRECT',
          'border-amber-200 bg-amber-50/80': cragState.action === 'AMBIGUOUS',
          'border-rose-200 bg-rose-50/80': cragState.action === 'INCORRECT',
        }"
      >
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div class="flex items-center gap-2">
            <span v-if="cragState.action === 'CORRECT'" class="h-3 w-3 rounded-full bg-emerald-600"></span>
            <span v-else-if="cragState.action === 'AMBIGUOUS'" class="h-3 w-3 rounded-full bg-amber-500 animate-ping"></span>
            <span v-else class="h-3 w-3 rounded-full bg-rose-600"></span>

            <span class="text-xs font-bold uppercase tracking-wider" :class="{
              'text-emerald-900': cragState.action === 'CORRECT',
              'text-amber-900': cragState.action === 'AMBIGUOUS',
              'text-rose-900': cragState.action === 'INCORRECT',
            }">
              CRAG State: {{ cragState.action }}
            </span>
            <span class="rounded-full bg-white/80 border px-2 py-0.5 text-[10px] font-bold">
              Confidence Score: {{ (cragState.confidence * 100).toFixed(1) }}%
            </span>
          </div>

          <span class="text-[11px] font-medium" :class="{
            'text-emerald-800': cragState.action === 'CORRECT',
            'text-amber-800': cragState.action === 'AMBIGUOUS',
            'text-rose-800': cragState.action === 'INCORRECT',
          }">
            <span v-if="cragState.action === 'CORRECT'">✓ Konteks valid (> 0.75) • Langsung diteruskan ke LLM Generator</span>
            <span v-else-if="cragState.action === 'AMBIGUOUS'">⚡ Ambigu (0.40 - 0.75) • Memicu ekspansi HyDE &amp; Query Rewriting</span>
            <span v-else>🛡️ Out-of-Distribution (&lt; 0.40) • Guardrail menolak halusinasi</span>
          </span>
        </div>

        <!-- HyDE Expansion details if triggered -->
        <div v-if="cragState.hydePrompt" class="mt-3 rounded-lg border border-amber-200 bg-white/90 p-3 text-xs text-amber-900">
          <div class="flex items-center gap-1.5 font-bold mb-1">
            <span>✨ HyDE (Hypothetical Document Embeddings) Expansion:</span>
          </div>
          <p class="font-mono text-[11px] text-amber-800">"{{ cragState.hydePrompt }}"</p>
        </div>
      </div>

      <!-- Generated Answer Box -->
      <div class="rounded-xl border border-slate-200 bg-slate-50/50 p-4 space-y-3">
        <div class="flex items-center justify-between">
          <span class="text-xs font-bold uppercase tracking-wider text-slate-500">Sintesis Jawaban Terverifikasi (Grounded AI)</span>
          <span class="text-[11px] text-slate-400">Zero-Hallucination Verification</span>
        </div>
        <p class="text-sm text-slate-800 leading-relaxed font-sans">
          {{ cragState.generatedAnswer }}
        </p>

        <!-- Citations Pills -->
        <div v-if="cragState.citations.length > 0" class="pt-2 border-t border-slate-200 flex flex-wrap items-center gap-1.5">
          <span class="text-[11px] font-semibold text-slate-500">Sitasi Terhubung:</span>
          <span
            v-for="cite in cragState.citations"
            :key="cite"
            class="rounded-md bg-white border border-slate-200 px-2 py-0.5 text-[10px] font-semibold text-slate-700 shadow-2xs"
          >
            📌 {{ cite }}
          </span>
        </div>
      </div>
    </div>

    <!-- 2 Kolom: RAPTOR Knowledge Tree (Kiri) vs Cross-Encoder Reranker Table (Kanan) -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
      <!-- Kolom Kiri (5 Cols): RAPTOR GMM Hierarchical Clusters -->
      <div class="lg:col-span-5 rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-4">
        <div class="border-b border-slate-100 pb-3">
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-bold text-slate-900">RAPTOR Hierarchical Clusters</h3>
            <span class="rounded bg-indigo-50 border border-indigo-200 text-indigo-700 px-1.5 py-0.5 text-[10px] font-bold">
              GMM &amp; K-Means
            </span>
          </div>
          <p class="mt-1 text-xs text-slate-500">
            Dokumen dikelompokkan secara semantik menggunakan Gaussian Mixture Models. Gemini merangkum tiap klaster menjadi simpul pohon (Tree Node) tingkat tinggi.
          </p>
        </div>

        <div class="space-y-3">
          <div
            v-for="cluster in raptorClusters"
            :key="cluster.id"
            @click="selectedCluster = selectedCluster === cluster.id ? null : cluster.id"
            class="rounded-xl border p-3.5 transition-all cursor-pointer hover:shadow-xs"
            :class="selectedCluster === cluster.id ? 'border-indigo-400 bg-indigo-50/40 ring-1 ring-indigo-400' : 'border-slate-200 bg-slate-50/60 hover:bg-white'"
          >
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-slate-800">{{ cluster.name }}</span>
              <span class="rounded-full px-2 py-0.2 text-[10px] font-bold border" :class="cluster.badgeColor">
                {{ cluster.leafCount }} Dokumen Leaf
              </span>
            </div>
            <p class="mt-2 text-xs text-slate-600 line-clamp-3">
              {{ cluster.summary }}
            </p>
            <div class="mt-2 flex items-center justify-between text-[10px] text-slate-400 border-t border-slate-200/60 pt-1.5">
              <span>Embedding: Gemini 768-D</span>
              <span class="text-indigo-600 font-semibold">{{ selectedCluster === cluster.id ? 'Tutup Detail' : 'Inspeksi Klaster ➔' }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Kolom Kanan (7 Cols): Cross-Encoder Reranker Visualizer -->
      <div class="lg:col-span-7 rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-4">
        <div class="border-b border-slate-100 pb-3">
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-bold text-slate-900">Cross-Encoder Reranker (Top-K Re-scoring)</h3>
            <span class="rounded bg-emerald-50 border border-emerald-200 text-emerald-700 px-1.5 py-0.5 text-[10px] font-bold">
              BGE / Flash Rerank
            </span>
          </div>
          <p class="mt-1 text-xs text-slate-500">
            Kandidat Top-10 dari pgvector dievaluasi ulang oleh Cross-Encoder untuk mengoreksi bias cosine similarity sebelum dikirim ke context window.
          </p>
        </div>

        <div v-if="cragState.hits.length === 0" class="py-12 text-center text-xs text-slate-400">
          Tidak ada kandidat dokumen yang memenuhi threshold relevansi untuk kueri ini.
        </div>

        <div v-else class="space-y-3">
          <div
            v-for="hit in cragState.hits"
            :key="hit.id"
            class="rounded-xl border border-slate-200 bg-white p-3.5 shadow-2xs hover:border-slate-300 transition-all space-y-2"
          >
            <div class="flex items-start justify-between gap-2">
              <div>
                <span class="text-xs font-bold text-slate-900">{{ hit.title }}</span>
                <span class="block text-[10px] text-slate-400">{{ hit.cluster }}</span>
              </div>
              <div class="text-right shrink-0">
                <span class="inline-flex items-center gap-1 rounded-md bg-purple-50 border border-purple-200 px-2 py-0.5 text-xs font-bold text-purple-900">
                  Skor: {{ hit.rerankScore.toFixed(3) }}
                </span>
                <div class="text-[10px] text-slate-500 mt-0.5">
                  Rank: <span class="line-through text-slate-400">#{{ hit.initialRank }}</span> ➔ <strong class="text-emerald-700">#{{ hit.finalRank }}</strong>
                </div>
              </div>
            </div>

            <p class="text-xs text-slate-600 line-clamp-2">
              "{{ hit.content }}"
            </p>

            <div class="flex items-center justify-between text-[10px] border-t border-slate-100 pt-1.5 text-slate-500">
              <span class="rounded bg-slate-100 px-1.5 py-0.5 text-slate-700 font-medium">Metode: {{ hit.matchType }}</span>
              <span class="text-emerald-600 font-semibold">✓ Lulus Reranker Threshold (&gt; 0.70)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
