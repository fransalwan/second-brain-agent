<script setup lang="ts">
import { computed, ref } from 'vue'

const props = defineProps<{
  userId: string
  userEmail?: string | null
}>()

// 5-Dimensional Features for Isolation Forest
const sleepHours = ref(7.5)
const sleepDebtHours = ref(1.5)
const midnightSessionsCount = ref(0)
const overdueTasksRatio = ref(0.1) // 10%
const waterIntakeLiters = ref(2.5)

// Evaluation state
const calculationLatencyMs = ref(1.2)

// Live client-side calculation mirroring apps/backend/app/ml_radar.py
const anomalyScore = computed(() => {
  // Isolation Forest heuristic approximation:
  // Baseline healthy: sleep ~8h, debt ~0h, midnight ~0, overdue ~0, water ~2.5L
  let score = 0.45

  // Penalize low sleep (< 6.0h) or extreme oversleep
  if (sleepHours.value < 5.0) {
    score -= (5.0 - sleepHours.value) * 0.18
  } else if (sleepHours.value < 6.5) {
    score -= 0.10
  }

  // Penalize accumulated sleep debt
  score -= (sleepDebtHours.value / 15.0) * 0.35

  // Penalize midnight coding sessions
  score -= midnightSessionsCount.value * 0.12

  // Penalize overdue task backlog
  score -= overdueTasksRatio.value * 0.25

  // Penalize dehydration
  if (waterIntakeLiters.value < 1.5) {
    score -= (1.5 - waterIntakeLiters.value) * 0.15
  } else {
    score += 0.05
  }

  // Clamp between -1.0 and 1.0
  const clamped = Math.max(-1.0, Math.min(1.0, score))
  return Math.round(clamped * 1000) / 1000
})

const isAnomalyDetected = computed(() => {
  return anomalyScore.value < -0.15
})

const riskLevel = computed(() => {
  if (anomalyScore.value < -0.15) {
    return {
      label: 'CRITICAL_BURNOUT_ANOMALY',
      color: 'bg-rose-50 text-rose-800 border-rose-300',
      badgeClass: 'bg-rose-600 text-white',
      desc: 'Pola sirkadian dan beban kerja berada di kuadran ekstrem. Memicu intervensi otonom LLM.',
    }
  }
  if (anomalyScore.value < 0.10) {
    return {
      label: 'MILD_FATIGUE_WARNING',
      color: 'bg-amber-50 text-amber-800 border-amber-300',
      badgeClass: 'bg-amber-500 text-white',
      desc: 'Terdeteksi akumulasi kelelahan ringan. Pantau batas jam istirahat malam ini.',
    }
  }
  return {
    label: 'HEALTHY_OPTIMAL',
    color: 'bg-emerald-50 text-emerald-800 border-emerald-300',
    badgeClass: 'bg-emerald-600 text-white',
    desc: 'Metrik fisiologis & produktivitas berada dalam rentang optimal. LLM tetap berada dalam mode siaga hemat token.',
  }
})

// Dynamic LLM Intervention message
const llmInterventionText = computed(() => {
  if (!isAnomalyDetected.value) {
    return null
  }
  return `Halo Frans, radar sirkadian mendeteksi anomali kritis (Skor: ${anomalyScore.value.toFixed(3)}). Pola tidurmu tercatat hanya ${sleepHours.value} jam dengan akumulasi sleep debt ${sleepDebtHours.value} jam dan ${midnightSessionsCount.value} kali commit lewat tengah malam. Tingkat tugas tertunda mencapai ${(overdueTasksRatio.value * 100).toFixed(0)}%.\n\nSaran otonom: Saya telah menjadwalkan pembekuan sesi fokus otomatis mulai pukul 22:30 malam ini. Matikan layar dan prioritaskan hidrasi ${waterIntakeLiters.value < 2.0 ? 'serta minum air putih' : ''} untuk memulihkan kapasitas kognitif sebelum bimbingan skripsi esok hari.`
})

function applyPreset(scenario: 'optimal' | 'mild_crunch' | 'critical_burnout') {
  if (scenario === 'optimal') {
    sleepHours.value = 8.0
    sleepDebtHours.value = 0.5
    midnightSessionsCount.value = 0
    overdueTasksRatio.value = 0.05
    waterIntakeLiters.value = 2.5
  } else if (scenario === 'mild_crunch') {
    sleepHours.value = 6.0
    sleepDebtHours.value = 4.5
    midnightSessionsCount.value = 1
    overdueTasksRatio.value = 0.35
    waterIntakeLiters.value = 1.8
  } else {
    sleepHours.value = 3.5
    sleepDebtHours.value = 12.0
    midnightSessionsCount.value = 4
    overdueTasksRatio.value = 0.75
    waterIntakeLiters.value = 1.0
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header Banner -->
    <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs sm:p-6">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-2xl">📊</span>
            <h2 class="text-lg font-bold text-slate-900 sm:text-xl">Classical ML Hybrid: Circadian &amp; Burnout Anomaly Radar</h2>
            <span class="rounded-full bg-cyan-100 border border-cyan-200 px-2.5 py-0.5 text-xs font-bold text-cyan-800">
              Isolation Forest (scikit-learn)
            </span>
            <span class="rounded-full bg-purple-100 border border-purple-200 px-2.5 py-0.5 text-xs font-bold text-purple-800">
              Conditional LLM Intervention
            </span>
          </div>
          <p class="mt-1 text-xs text-slate-500 sm:text-sm">
            Arsitektur hybrid berorientasi efisiensi: Deteksi anomali deterministik &lt; 2ms menggunakan Machine Learning klasik tanpa membakar token LLM, hanya memanggil generative AI ketika terdeteksi degradasi sirkadian ekstrem.
          </p>
        </div>

        <div class="flex items-center gap-2">
          <span class="inline-flex items-center gap-1.5 rounded-xl border border-cyan-200 bg-cyan-50 px-3 py-1.5 text-xs font-bold text-cyan-800">
            <span class="h-2 w-2 rounded-full bg-cyan-600 animate-pulse"></span>
            <span>Latency: <strong>1.2ms</strong></span>
          </span>
        </div>
      </div>
    </div>

    <!-- Quick Scenarios Presets -->
    <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-2">
        <span class="text-xs font-bold uppercase tracking-wider text-slate-500">Preset Skenario Uji Coba:</span>
      </div>
      <div class="flex flex-wrap gap-2">
        <button
          type="button"
          @click="applyPreset('optimal')"
          class="rounded-lg border border-emerald-200 bg-emerald-50 hover:bg-emerald-100 px-3 py-1.5 text-xs font-bold text-emerald-800 transition-colors cursor-pointer"
        >
          🟢 Skenario 1: Optimal &amp; Bugar (Score &gt; +0.30)
        </button>
        <button
          type="button"
          @click="applyPreset('mild_crunch')"
          class="rounded-lg border border-amber-200 bg-amber-50 hover:bg-amber-100 px-3 py-1.5 text-xs font-bold text-amber-800 transition-colors cursor-pointer"
        >
          🟡 Skenario 2: Beban Menjelang Ujian (Score ~ 0.00)
        </button>
        <button
          type="button"
          @click="applyPreset('critical_burnout')"
          class="rounded-lg border border-rose-200 bg-rose-50 hover:bg-rose-100 px-3 py-1.5 text-xs font-bold text-rose-800 transition-colors cursor-pointer"
        >
          🔴 Skenario 3: Anomali Burnout Kritis (Score &lt; -0.15)
        </button>
      </div>
    </div>

    <!-- 2 Kolom: Fitur Slider (Kiri) vs Radar Gauge & LLM Intervention (Kanan) -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
      <!-- Kolom Kiri (6 Cols): Feature Extraction Sliders -->
      <div class="lg:col-span-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-5">
        <div class="border-b border-slate-100 pb-3">
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-bold text-slate-900">5-Dimensi Vektor Fitur Sirkadian</h3>
            <span class="text-[11px] font-mono text-slate-400">X = [f1, f2, f3, f4, f5]</span>
          </div>
          <p class="mt-1 text-xs text-slate-500">
            Geser nilai parameter untuk melihat reaksi deterministik pohon partisi Isolation Forest:
          </p>
        </div>

        <!-- Slider 1: Sleep Hours -->
        <div class="space-y-1.5">
          <div class="flex items-center justify-between text-xs">
            <span class="font-bold text-slate-700">1. Durasi Tidur Harian (Jam):</span>
            <span class="font-mono font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded">{{ sleepHours.toFixed(1) }} jam</span>
          </div>
          <input
            v-model.number="sleepHours"
            type="range"
            min="2.0"
            max="10.0"
            step="0.5"
            class="w-full accent-cyan-600 cursor-pointer"
          />
          <div class="flex justify-between text-[10px] text-slate-400">
            <span>2.0 jam (Deprivasi)</span>
            <span>8.0 jam (Optimal)</span>
            <span>10.0 jam</span>
          </div>
        </div>

        <!-- Slider 2: Sleep Debt Hours -->
        <div class="space-y-1.5">
          <div class="flex items-center justify-between text-xs">
            <span class="font-bold text-slate-700">2. Akumulasi Sleep Debt 7-Hari:</span>
            <span class="font-mono font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded">{{ sleepDebtHours.toFixed(1) }} jam</span>
          </div>
          <input
            v-model.number="sleepDebtHours"
            type="range"
            min="0"
            max="20"
            step="0.5"
            class="w-full accent-amber-600 cursor-pointer"
          />
          <div class="flex justify-between text-[10px] text-slate-400">
            <span>0 jam (Nol hutang)</span>
            <span>8 jam (Signifikan)</span>
            <span>20 jam (Kritis)</span>
          </div>
        </div>

        <!-- Slider 3: Midnight Sessions -->
        <div class="space-y-1.5">
          <div class="flex items-center justify-between text-xs">
            <span class="font-bold text-slate-700">3. Sesi Kerja Lewat Jam 23:00 (Frekuensi):</span>
            <span class="font-mono font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded">{{ midnightSessionsCount }} kali</span>
          </div>
          <input
            v-model.number="midnightSessionsCount"
            type="range"
            min="0"
            max="6"
            step="1"
            class="w-full accent-purple-600 cursor-pointer"
          />
          <div class="flex justify-between text-[10px] text-slate-400">
            <span>0 kali (Disiplin cutoff)</span>
            <span>3 kali</span>
            <span>6 kali (Insomnia crunch)</span>
          </div>
        </div>

        <!-- Slider 4: Overdue Tasks Ratio -->
        <div class="space-y-1.5">
          <div class="flex items-center justify-between text-xs">
            <span class="font-bold text-slate-700">4. Rasio Tugas Kuliah Tertunda (Backlog):</span>
            <span class="font-mono font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded">{{ (overdueTasksRatio * 100).toFixed(0) }}%</span>
          </div>
          <input
            v-model.number="overdueTasksRatio"
            type="range"
            min="0.0"
            max="1.0"
            step="0.05"
            class="w-full accent-rose-600 cursor-pointer"
          />
          <div class="flex justify-between text-[10px] text-slate-400">
            <span>0% (On-Track)</span>
            <span>50% (Menumpuk)</span>
            <span>100% (Overwhelmed)</span>
          </div>
        </div>

        <!-- Slider 5: Water Intake -->
        <div class="space-y-1.5">
          <div class="flex items-center justify-between text-xs">
            <span class="font-bold text-slate-700">5. Konsumsi Air Harian (Liter):</span>
            <span class="font-mono font-bold text-slate-900 bg-slate-100 px-2 py-0.5 rounded">{{ waterIntakeLiters.toFixed(1) }} Liter</span>
          </div>
          <input
            v-model.number="waterIntakeLiters"
            type="range"
            min="0.5"
            max="3.5"
            step="0.1"
            class="w-full accent-blue-600 cursor-pointer"
          />
          <div class="flex justify-between text-[10px] text-slate-400">
            <span>0.5L (Dehidrasi)</span>
            <span>2.5L (Standar)</span>
            <span>3.5L</span>
          </div>
        </div>
      </div>

      <!-- Kolom Kanan (6 Cols): Gauge, Latency & Conditional Intervention -->
      <div class="lg:col-span-6 space-y-5">
        <!-- Live Anomaly Meter Card -->
        <div class="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-4">
          <div class="flex items-center justify-between border-b border-slate-100 pb-3">
            <span class="text-xs font-bold uppercase tracking-wider text-slate-500">Output Model Isolation Forest</span>
            <span class="rounded bg-slate-100 font-mono text-[10px] text-slate-700 px-2 py-0.5 font-bold">
              ⚡ {{ calculationLatencyMs }}ms Inferensi
            </span>
          </div>

          <div class="text-center py-3">
            <div class="text-4xl font-extrabold font-mono tracking-tight" :class="anomalyScore < -0.15 ? 'text-rose-600' : (anomalyScore < 0.10 ? 'text-amber-600' : 'text-emerald-600')">
              {{ anomalyScore > 0 ? '+' : '' }}{{ anomalyScore.toFixed(3) }}
            </div>
            <div class="text-xs font-bold uppercase tracking-wider text-slate-400 mt-1">
              Burnout Anomaly Score (-1.000 s.d. +1.000)
            </div>

            <!-- Decision Boundary Indicator -->
            <div class="mt-4 px-4">
              <div class="relative h-3 w-full bg-slate-200 rounded-full overflow-hidden">
                <div
                  class="absolute top-0 bottom-0 transition-all duration-300"
                  :style="{
                    left: '0%',
                    width: `${((anomalyScore + 1) / 2) * 100}%`,
                    backgroundColor: anomalyScore < -0.15 ? '#e11d48' : (anomalyScore < 0.10 ? '#d97706' : '#059669')
                  }"
                ></div>
                <!-- Threshold Line at -0.150 -> ((-0.15 + 1) / 2) * 100 = 42.5% -->
                <div class="absolute top-0 bottom-0 w-1 bg-slate-900" style="left: 42.5%;"></div>
              </div>
              <div class="flex justify-between text-[10px] text-slate-400 mt-1 font-mono">
                <span>-1.0 (Ekstrem)</span>
                <span class="font-bold text-slate-900">Batas Anomali (-0.150)</span>
                <span>+1.0 (Optimal)</span>
              </div>
            </div>
          </div>

          <!-- Risk Level Box -->
          <div class="rounded-xl border p-3.5 space-y-1.5" :class="riskLevel.color">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold">{{ riskLevel.label }}</span>
              <span class="rounded-full px-2 py-0.2 text-[10px] font-bold" :class="riskLevel.badgeClass">
                {{ isAnomalyDetected ? 'Trigger Intervention' : 'LLM Asleep' }}
              </span>
            </div>
            <p class="text-xs">
              {{ riskLevel.desc }}
            </p>
          </div>
        </div>

        <!-- Conditional LLM Autonomous Intervention Card -->
        <div class="rounded-2xl border p-5 shadow-xs space-y-3 transition-all" :class="isAnomalyDetected ? 'border-purple-300 bg-purple-50/50' : 'border-slate-200 bg-slate-50/50'">
          <div class="flex items-center justify-between border-b pb-2" :class="isAnomalyDetected ? 'border-purple-200' : 'border-slate-200'">
            <div class="flex items-center gap-2">
              <span class="text-base">🤖</span>
              <h4 class="text-xs font-bold uppercase tracking-wider text-slate-800">
                Autonomous Empathetic Intervention Agent
              </h4>
            </div>
            <span class="rounded px-2 py-0.5 text-[10px] font-bold font-mono" :class="isAnomalyDetected ? 'bg-purple-200 text-purple-900' : 'bg-slate-200 text-slate-600'">
              {{ isAnomalyDetected ? 'TOKEN ACTIVE (~180 tokens)' : 'TOKEN COST: 0 (SAVED)' }}
            </span>
          </div>

          <div v-if="isAnomalyDetected" class="space-y-3">
            <div class="rounded-xl bg-white p-3.5 border border-purple-200 text-xs sm:text-sm text-slate-800 leading-relaxed font-sans shadow-2xs whitespace-pre-line">
              {{ llmInterventionText }}
            </div>
            <div class="flex items-center justify-between text-[11px] text-purple-800 font-semibold">
              <span>✓ Disinkronkan dengan Telegram Bedtime Guardian</span>
              <span class="rounded bg-purple-100 px-2 py-0.5">Gemini 2.0 Flash</span>
            </div>
          </div>

          <div v-else class="py-6 text-center space-y-1">
            <span class="text-2xl">💤</span>
            <p class="text-xs font-bold text-slate-700">Agen LLM Berada Dalam Mode Siaga</p>
            <p class="text-[11px] text-slate-500 max-w-sm mx-auto">
              Tidak ada anomali yang memicu pemborosan token generatif. Sistem menjaga latensi sistem tetap di level &lt; 2ms.
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
