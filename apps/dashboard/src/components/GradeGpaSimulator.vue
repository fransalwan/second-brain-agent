<script setup lang="ts">
import { computed, ref, watch } from 'vue'

const props = defineProps<{
  userId: string
  existingCourses?: string[]
}>()

// Sub-Tab Simulator
const activeTab = ref<'grade_target' | 'gpa_calc'>('grade_target')

// ----------------------------------------------------
// 1. STATE & LOGIC: TARGET NILAI PER MATA KULIAH
// ----------------------------------------------------
interface GradeTargetState {
  courseName: string
  targetGrade: 'A' | 'AB' | 'B' | 'BC' | 'C'
  weightAssignment: number
  scoreAssignment: number | null
  weightQuiz: number
  scoreQuiz: number | null
  weightMidterm: number
  scoreMidterm: number | null
  weightFinal: number
}

const gradeThresholds: Record<'A' | 'AB' | 'B' | 'BC' | 'C', number> = {
  A: 85,
  AB: 78,
  B: 70,
  BC: 63,
  C: 55,
}

const STORAGE_KEY_GRADE = `secondbrain_grade_sim_${props.userId}`

function loadGradeState(): GradeTargetState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY_GRADE)
    if (raw) return JSON.parse(raw)
  } catch {}
  return {
    courseName: props.existingCourses?.[0] || 'Kalkulus / Algoritma',
    targetGrade: 'A',
    weightAssignment: 20,
    scoreAssignment: 85,
    weightQuiz: 15,
    scoreQuiz: 80,
    weightMidterm: 30,
    scoreMidterm: 75,
    weightFinal: 35,
  }
}

const gradeState = ref<GradeTargetState>(loadGradeState())

watch(
  gradeState,
  (val) => {
    try {
      localStorage.setItem(STORAGE_KEY_GRADE, JSON.stringify(val))
    } catch {}
  },
  { deep: true }
)

const totalWeight = computed(() => {
  return (
    (gradeState.value.weightAssignment || 0) +
    (gradeState.value.weightQuiz || 0) +
    (gradeState.value.weightMidterm || 0) +
    (gradeState.value.weightFinal || 0)
  )
})

const currentSecuredScore = computed(() => {
  const asg = ((gradeState.value.scoreAssignment || 0) * (gradeState.value.weightAssignment || 0)) / 100
  const quiz = ((gradeState.value.scoreQuiz || 0) * (gradeState.value.weightQuiz || 0)) / 100
  const mid = ((gradeState.value.scoreMidterm || 0) * (gradeState.value.weightMidterm || 0)) / 100
  return Number((asg + quiz + mid).toFixed(2))
})

const maxPossibleScore = computed(() => {
  const finalMax = (100 * (gradeState.value.weightFinal || 0)) / 100
  return Number((currentSecuredScore.value + finalMax).toFixed(2))
})

const targetThreshold = computed(() => gradeThresholds[gradeState.value.targetGrade])

const neededFinalScore = computed(() => {
  const wFinal = gradeState.value.weightFinal || 0
  if (wFinal <= 0) return 0
  const neededWeightContribution = targetThreshold.value - currentSecuredScore.value
  const score = (neededWeightContribution * 100) / wFinal
  return Number(score.toFixed(1))
})

// ----------------------------------------------------
// 2. STATE & LOGIC: SIMULATOR IPK SEMESTER & KUMULATIF
// ----------------------------------------------------
interface CourseSemesterItem {
  id: number
  name: string
  credits: number // SKS (1-6)
  grade: 'A' | 'AB' | 'B' | 'BC' | 'C' | 'D' | 'E'
}

interface GpaState {
  prevCgpa: number | null
  prevCredits: number | null
  courses: CourseSemesterItem[]
}

const gradePoints: Record<'A' | 'AB' | 'B' | 'BC' | 'C' | 'D' | 'E', number> = {
  A: 4.0,
  AB: 3.5,
  B: 3.0,
  BC: 2.5,
  C: 2.0,
  D: 1.0,
  E: 0.0,
}

const STORAGE_KEY_GPA = `secondbrain_gpa_sim_${props.userId}`

function loadGpaState(): GpaState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY_GPA)
    if (raw) return JSON.parse(raw)
  } catch {}
  return {
    prevCgpa: 3.42,
    prevCredits: 58,
    courses: [
      { id: 1, name: 'Struktur Data & Algoritma', credits: 3, grade: 'A' },
      { id: 2, name: 'Sistem Operasi', credits: 3, grade: 'AB' },
      { id: 3, name: 'Metodologi Penelitian', credits: 2, grade: 'A' },
      { id: 4, name: 'Probabilitas & Statistika', credits: 3, grade: 'B' },
      { id: 5, name: 'Kecerdasan Buatan', credits: 3, grade: 'A' },
    ],
  }
}

const gpaState = ref<GpaState>(loadGpaState())

watch(
  gpaState,
  (val) => {
    try {
      localStorage.setItem(STORAGE_KEY_GPA, JSON.stringify(val))
    } catch {}
  },
  { deep: true }
)

function addCourseRow() {
  gpaState.value.courses.push({
    id: Date.now(),
    name: '',
    credits: 3,
    grade: 'A',
  })
}

function removeCourseRow(id: number) {
  gpaState.value.courses = gpaState.value.courses.filter((c) => c.id !== id)
}

function resetCourseRows() {
  gpaState.value.courses = [
    { id: 1, name: 'Mata Kuliah 1', credits: 3, grade: 'A' },
    { id: 2, name: 'Mata Kuliah 2', credits: 3, grade: 'A' },
    { id: 3, name: 'Mata Kuliah 3', credits: 2, grade: 'B' },
  ]
}

const totalSemesterCredits = computed(() => {
  return gpaState.value.courses.reduce((sum, c) => sum + (Number(c.credits) || 0), 0)
})

const semesterGpa = computed(() => {
  const totalCredits = totalSemesterCredits.value
  if (totalCredits <= 0) return 0
  const totalWeightedPoints = gpaState.value.courses.reduce(
    (sum, c) => sum + (Number(c.credits) || 0) * gradePoints[c.grade],
    0
  )
  return Number((totalWeightedPoints / totalCredits).toFixed(2))
})

const newCumulativeGpa = computed(() => {
  const prevCreds = Number(gpaState.value.prevCredits) || 0
  const prevGpa = Number(gpaState.value.prevCgpa) || 0
  const semCreds = totalSemesterCredits.value
  const semGpaVal = semesterGpa.value

  const totalCreds = prevCreds + semCreds
  if (totalCreds <= 0) return semGpaVal

  const totalQualityPoints = prevCreds * prevGpa + semCreds * semGpaVal
  return Number((totalQualityPoints / totalCreds).toFixed(2))
})

const gpaDifference = computed(() => {
  const prevGpa = Number(gpaState.value.prevCgpa) || 0
  if (prevGpa <= 0) return null
  const diff = newCumulativeGpa.value - prevGpa
  return Number(diff.toFixed(2))
})

const academicHonors = computed(() => {
  const gpa = newCumulativeGpa.value
  if (gpa >= 3.51) return { title: 'Potensi Cum Laude (Dengan Pujian)', color: 'text-amber-600', badge: 'bg-amber-100 text-amber-800' }
  if (gpa >= 3.0) return { title: 'Sangat Memuaskan', color: 'text-blue-600', badge: 'bg-blue-100 text-blue-800' }
  if (gpa >= 2.76) return { title: 'Memuaskan', color: 'text-emerald-600', badge: 'bg-emerald-100 text-emerald-800' }
  return { title: 'Cukup', color: 'text-gray-600', badge: 'bg-gray-100 text-gray-800' }
})
</script>

<template>
  <div class="space-y-6">
    <!-- Sub-Navbar Segmented Control -->
    <div class="flex flex-wrap items-center justify-between gap-3 bg-white p-3.5 rounded-2xl border border-gray-200 shadow-xs">
      <div class="flex items-center gap-1.5">
        <button
          type="button"
          @click="activeTab = 'grade_target'"
          class="inline-flex items-center gap-2 rounded-xl px-3.5 py-2 text-xs font-bold transition-all cursor-pointer"
          :class="activeTab === 'grade_target' ? 'bg-blue-600 text-white shadow-xs' : 'text-gray-600 hover:bg-gray-100'"
        >
          <span>🎯</span>
          <span>Target Nilai Ujian (Silabus)</span>
        </button>

        <button
          type="button"
          @click="activeTab = 'gpa_calc'"
          class="inline-flex items-center gap-2 rounded-xl px-3.5 py-2 text-xs font-bold transition-all cursor-pointer"
          :class="activeTab === 'gpa_calc' ? 'bg-blue-600 text-white shadow-xs' : 'text-gray-600 hover:bg-gray-100'"
        >
          <span>📈</span>
          <span>Simulator IPK Semester &amp; Kumulatif</span>
        </button>
      </div>

      <span class="text-[11px] text-gray-500 hidden sm:inline">
        Tersimpan otomatis per akun secara lokal
      </span>
    </div>

    <!-- ======================================================== -->
    <!-- 1. TAB SIMULATOR TARGET NILAI MATA KULIAH                -->
    <!-- ======================================================== -->
    <div v-if="activeTab === 'grade_target'" class="space-y-6">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Panel Input Form -->
        <div class="lg:col-span-2 rounded-2xl border border-gray-200 bg-white p-5 shadow-xs space-y-4">
          <div class="flex items-center justify-between pb-3 border-b border-gray-100">
            <div>
              <h3 class="text-sm font-bold text-gray-900 flex items-center gap-2">
                <span>📝</span>
                <span>Komponen &amp; Bobot Silabus Dosen</span>
              </h3>
              <p class="text-[11px] text-gray-500">Masukkan persentase bobot dan nilai yang sudah kamu peroleh</p>
            </div>

            <!-- Target Grade Selector -->
            <div class="flex items-center gap-1.5">
              <span class="text-xs font-semibold text-gray-700">Target Akhir:</span>
              <div class="flex rounded-xl bg-gray-100 p-1 text-xs font-bold">
                <button
                  v-for="grade in (['A', 'AB', 'B', 'BC', 'C'] as const)"
                  :key="grade"
                  type="button"
                  @click="gradeState.targetGrade = grade"
                  class="px-2.5 py-1 rounded-lg transition-all cursor-pointer"
                  :class="gradeState.targetGrade === grade ? 'bg-blue-600 text-white shadow-2xs' : 'text-gray-600 hover:text-gray-900'"
                >
                  {{ grade }}
                </button>
              </div>
            </div>
          </div>

          <!-- Course Name Field -->
          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">Nama Mata Kuliah</label>
            <input
              v-model="gradeState.courseName"
              type="text"
              placeholder="Contoh: Pemrograman Web, Kalkulus Lanjut, Jaringan Komputer"
              class="w-full rounded-xl border border-gray-300 px-3.5 py-2 text-xs font-medium focus:border-blue-600 focus:outline-none"
            />
          </div>

          <!-- Bobot Rows -->
          <div class="space-y-3">
            <!-- Row 1: Tugas -->
            <div class="grid grid-cols-12 gap-3 items-center bg-gray-50/70 p-3 rounded-xl border border-gray-100">
              <div class="col-span-4">
                <span class="text-xs font-bold text-gray-800">📂 Tugas &amp; PR</span>
                <p class="text-[10px] text-gray-400">Rata-rata tugas mandiri</p>
              </div>
              <div class="col-span-4">
                <label class="block text-[10px] text-gray-500 mb-0.5">Bobot (%)</label>
                <input
                  v-model.number="gradeState.weightAssignment"
                  type="number"
                  min="0"
                  max="100"
                  class="w-full rounded-lg border border-gray-200 bg-white px-2.5 py-1 text-xs font-semibold"
                />
              </div>
              <div class="col-span-4">
                <label class="block text-[10px] text-gray-500 mb-0.5">Nilai Didapat (0-100)</label>
                <input
                  v-model.number="gradeState.scoreAssignment"
                  type="number"
                  min="0"
                  max="100"
                  placeholder="85"
                  class="w-full rounded-lg border border-gray-200 bg-white px-2.5 py-1 text-xs font-semibold"
                />
              </div>
            </div>

            <!-- Row 2: Kuis / Praktikum -->
            <div class="grid grid-cols-12 gap-3 items-center bg-gray-50/70 p-3 rounded-xl border border-gray-100">
              <div class="col-span-4">
                <span class="text-xs font-bold text-gray-800">🧪 Kuis / Lab</span>
                <p class="text-[10px] text-gray-400">Modul praktikum &amp; responsi</p>
              </div>
              <div class="col-span-4">
                <label class="block text-[10px] text-gray-500 mb-0.5">Bobot (%)</label>
                <input
                  v-model.number="gradeState.weightQuiz"
                  type="number"
                  min="0"
                  max="100"
                  class="w-full rounded-lg border border-gray-200 bg-white px-2.5 py-1 text-xs font-semibold"
                />
              </div>
              <div class="col-span-4">
                <label class="block text-[10px] text-gray-500 mb-0.5">Nilai Didapat (0-100)</label>
                <input
                  v-model.number="gradeState.scoreQuiz"
                  type="number"
                  min="0"
                  max="100"
                  placeholder="80"
                  class="w-full rounded-lg border border-gray-200 bg-white px-2.5 py-1 text-xs font-semibold"
                />
              </div>
            </div>

            <!-- Row 3: UTS -->
            <div class="grid grid-cols-12 gap-3 items-center bg-gray-50/70 p-3 rounded-xl border border-gray-100">
              <div class="col-span-4">
                <span class="text-xs font-bold text-gray-800">📑 Ujian Tengah (UTS)</span>
                <p class="text-[10px] text-gray-400">Nilai tengah semester</p>
              </div>
              <div class="col-span-4">
                <label class="block text-[10px] text-gray-500 mb-0.5">Bobot (%)</label>
                <input
                  v-model.number="gradeState.weightMidterm"
                  type="number"
                  min="0"
                  max="100"
                  class="w-full rounded-lg border border-gray-200 bg-white px-2.5 py-1 text-xs font-semibold"
                />
              </div>
              <div class="col-span-4">
                <label class="block text-[10px] text-gray-500 mb-0.5">Nilai Didapat (0-100)</label>
                <input
                  v-model.number="gradeState.scoreMidterm"
                  type="number"
                  min="0"
                  max="100"
                  placeholder="75"
                  class="w-full rounded-lg border border-gray-200 bg-white px-2.5 py-1 text-xs font-semibold"
                />
              </div>
            </div>

            <!-- Row 4: UAS (Target yang dicari) -->
            <div class="grid grid-cols-12 gap-3 items-center bg-blue-50/60 p-3 rounded-xl border border-blue-200">
              <div class="col-span-4">
                <span class="text-xs font-bold text-blue-950">🎓 Ujian Akhir (UAS)</span>
                <p class="text-[10px] text-blue-700">Target nilai yang dicari</p>
              </div>
              <div class="col-span-4">
                <label class="block text-[10px] text-blue-800 mb-0.5">Bobot (%)</label>
                <input
                  v-model.number="gradeState.weightFinal"
                  type="number"
                  min="0"
                  max="100"
                  class="w-full rounded-lg border border-blue-300 bg-white px-2.5 py-1 text-xs font-bold text-blue-950"
                />
              </div>
              <div class="col-span-4 text-center">
                <span class="text-[10px] text-blue-700 font-semibold block">Target Nilai UAS:</span>
                <span class="text-sm font-extrabold text-blue-900">
                  {{ neededFinalScore > 100 ? '> 100 (Sulit)' : neededFinalScore <= 0 ? 'Aman (0)' : neededFinalScore }}
                </span>
              </div>
            </div>
          </div>

          <!-- Total Bobot Validation Warning -->
          <div class="flex items-center justify-between text-xs pt-1">
            <span class="text-gray-500">Total Bobot Komponen:</span>
            <span
              class="font-bold px-2 py-0.5 rounded-lg"
              :class="totalWeight === 100 ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'"
            >
              {{ totalWeight }}% {{ totalWeight === 100 ? '✓ Tepat 100%' : '⚠️ Harus pas 100%' }}
            </span>
          </div>
        </div>

        <!-- Panel Kalkulasi & Hasil Cerdas -->
        <div class="rounded-2xl border border-gray-200 bg-gradient-to-br from-gray-900 to-slate-900 text-white p-5 sm:p-6 shadow-xl flex flex-col justify-between space-y-5">
          <div class="space-y-4">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold uppercase tracking-wider text-slate-400">Hasil Analisis Akademik</span>
              <span class="text-2xl select-none">🏆</span>
            </div>

            <!-- Big Target Card -->
            <div class="rounded-2xl bg-white/10 p-4 border border-white/10 space-y-2 backdrop-blur-xs">
              <span class="text-xs text-slate-300">Target Akhir: <strong>Nilai {{ gradeState.targetGrade }}</strong> (Skor {{ targetThreshold }}+)</span>
              
              <div class="flex items-baseline gap-2">
                <span
                  class="text-4xl font-extrabold tracking-tight"
                  :class="neededFinalScore > 100 ? 'text-rose-400' : neededFinalScore <= 0 ? 'text-emerald-400' : 'text-blue-300'"
                >
                  {{ neededFinalScore > 100 ? '> 100' : Math.max(0, neededFinalScore) }}
                </span>
                <span class="text-xs text-slate-300">Minimal Nilai UAS</span>
              </div>

              <!-- Recommendation text -->
              <p class="text-xs text-slate-300 leading-relaxed pt-1 border-t border-white/10">
                <span v-if="neededFinalScore <= 0" class="text-emerald-300 font-semibold">
                  🎉 Luar biasa! Nilaimu sudah aman. Berapapun nilai UAS kamu, nilai {{ gradeState.targetGrade }} sudah terkunci di tangan.
                </span>
                <span v-else-if="neededFinalScore <= 100">
                  🎯 Kamu butuh mencetak skor minimal <strong>{{ neededFinalScore }}</strong> pada UAS untuk mengamankan <strong>Nilai {{ gradeState.targetGrade }} (Indeks {{ gradeState.targetGrade === 'A' ? '4.0' : gradeState.targetGrade === 'AB' ? '3.5' : '3.0' }})</strong>.
                </span>
                <span v-else class="text-rose-300">
                  ⚠️ Secara matematis skor maksimal yang bisa dicapai adalah <strong>{{ maxPossibleScore }}</strong>. Targetkan nilai di bawahnya agar usahamu tetap realistis.
                </span>
              </p>
            </div>

            <!-- Progress Poin Terkumpul -->
            <div class="space-y-1.5 text-xs">
              <div class="flex items-center justify-between text-slate-300">
                <span>Nilai Terkumpul Sejauh Ini:</span>
                <span class="font-bold text-white">{{ currentSecuredScore }} / 100 Poin</span>
              </div>
              <div class="w-full bg-white/20 rounded-full h-2 overflow-hidden">
                <div
                  class="bg-blue-400 h-2 rounded-full transition-all duration-500"
                  :style="{ width: `${Math.min(100, (currentSecuredScore / 100) * 100)}%` }"
                ></div>
              </div>
              <span class="text-[10px] text-slate-400">
                Maksimal nilai akhir jika UAS dapat 100: <strong>{{ maxPossibleScore }}</strong>
              </span>
            </div>
          </div>

          <div class="rounded-xl bg-white/5 p-3 border border-white/5 text-[11px] text-slate-400">
            💡 <em>Tips: Jangan ragu diskusi kisi-kisi UAS dengan dosen atau kerjakan tugas perbaikan jika bobot tugas masih bisa dinaikkan.</em>
          </div>
        </div>
      </div>
    </div>

    <!-- ======================================================== -->
    <!-- 2. TAB SIMULATOR IPK SEMESTER & KUMULATIF                -->
    <!-- ======================================================== -->
    <div v-else-if="activeTab === 'gpa_calc'" class="space-y-6">
      <!-- Summary Metrics Bar -->
      <div class="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <!-- Metric 1: Prediksi IPS -->
        <div class="rounded-2xl border border-blue-200 bg-gradient-to-br from-blue-50/70 to-white p-4 shadow-xs">
          <span class="text-xs font-bold text-blue-900 uppercase tracking-wider">Prediksi IPS Semester</span>
          <div class="mt-2 flex items-baseline gap-2">
            <span class="text-3xl font-extrabold text-blue-950">{{ semesterGpa }}</span>
            <span class="text-xs text-blue-700 font-semibold">/ 4.00</span>
          </div>
          <span class="text-[11px] text-blue-600 mt-1 block">Dari {{ totalSemesterCredits }} SKS Semester Ini</span>
        </div>

        <!-- Metric 2: Prediksi IPK Kumulatif -->
        <div class="rounded-2xl border border-indigo-200 bg-gradient-to-br from-indigo-50/70 to-white p-4 shadow-xs">
          <span class="text-xs font-bold text-indigo-900 uppercase tracking-wider">Prediksi IPK Kumulatif</span>
          <div class="mt-2 flex items-baseline gap-2">
            <span class="text-3xl font-extrabold text-indigo-950">{{ newCumulativeGpa }}</span>
            <span
              v-if="gpaDifference !== null"
              class="text-xs font-extrabold"
              :class="gpaDifference >= 0 ? 'text-emerald-600' : 'text-rose-600'"
            >
              {{ gpaDifference >= 0 ? `+${gpaDifference}` : gpaDifference }}
            </span>
          </div>
          <span class="text-[11px] text-indigo-600 mt-1 block">Total SKS Tempuh: {{ (Number(gpaState.prevCredits) || 0) + totalSemesterCredits }}</span>
        </div>

        <!-- Metric 3: Predikat Akademik -->
        <div class="rounded-2xl border border-amber-200 bg-gradient-to-br from-amber-50/70 to-white p-4 shadow-xs flex flex-col justify-between">
          <div>
            <span class="text-xs font-bold text-amber-900 uppercase tracking-wider">Status Predikat</span>
            <h4 class="text-xs font-bold text-gray-900 mt-2">{{ academicHonors.title }}</h4>
          </div>
          <span class="text-[11px] font-semibold text-amber-700 mt-2">Berdasarkan Standar Kemendikbud</span>
        </div>

        <!-- Metric 4: Tombol Aksi Cepat -->
        <div class="rounded-2xl border border-gray-200 bg-white p-4 shadow-xs flex flex-col justify-between">
          <span class="text-xs font-bold text-gray-500 uppercase tracking-wider">Tindakan Cepat</span>
          <div class="flex flex-col gap-2 mt-2">
            <button
              type="button"
              @click="addCourseRow"
              class="rounded-xl bg-blue-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-blue-700 transition-colors cursor-pointer text-center"
            >
              ➕ Tambah Matkul
            </button>
            <button
              type="button"
              @click="resetCourseRows"
              class="rounded-xl border border-gray-200 px-3 py-1 text-xs text-gray-600 hover:bg-gray-50 transition-colors cursor-pointer text-center"
            >
              Reset Matkul
            </button>
          </div>
        </div>
      </div>

      <!-- Main Semester Table & Baseline Inputs -->
      <div class="rounded-2xl border border-gray-200 bg-white p-5 shadow-xs space-y-4">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-gray-100">
          <div>
            <h3 class="text-sm font-bold text-gray-900">Daftar Mata Kuliah Semester Ini</h3>
            <p class="text-xs text-gray-500">Sesuaikan target nilai huruf untuk melihat pengaruhnya ke IPK</p>
          </div>

          <!-- Baseline Inputs -->
          <div class="flex items-center gap-3">
            <div class="flex items-center gap-1.5">
              <label class="text-xs text-gray-600 font-semibold whitespace-nowrap">IPK Lalu:</label>
              <input
                v-model.number="gpaState.prevCgpa"
                type="number"
                step="0.01"
                min="0"
                max="4"
                placeholder="3.40"
                class="w-20 rounded-lg border border-gray-300 px-2.5 py-1 text-xs font-bold text-gray-900 focus:border-blue-600 focus:outline-none"
              />
            </div>
            <div class="flex items-center gap-1.5">
              <label class="text-xs text-gray-600 font-semibold whitespace-nowrap">SKS Lalu:</label>
              <input
                v-model.number="gpaState.prevCredits"
                type="number"
                step="1"
                min="0"
                max="160"
                placeholder="54"
                class="w-16 rounded-lg border border-gray-300 px-2.5 py-1 text-xs font-bold text-gray-900 focus:border-blue-600 focus:outline-none"
              />
            </div>
          </div>
        </div>

        <!-- Table of Courses -->
        <div class="overflow-x-auto no-scrollbar">
          <table class="w-full text-left text-xs">
            <thead>
              <tr class="border-b border-gray-100 text-gray-400 font-bold uppercase text-[10px]">
                <th class="py-2.5 px-3">#</th>
                <th class="py-2.5 px-3">Nama Mata Kuliah</th>
                <th class="py-2.5 px-3 w-28 text-center">SKS</th>
                <th class="py-2.5 px-3 w-36 text-center">Target Nilai</th>
                <th class="py-2.5 px-3 w-24 text-center">Poin</th>
                <th class="py-2.5 px-3 w-16 text-center">Aksi</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr v-for="(course, idx) in gpaState.courses" :key="course.id" class="hover:bg-gray-50/60 transition-colors">
                <td class="py-2.5 px-3 text-gray-400 font-mono">{{ idx + 1 }}</td>
                <td class="py-2.5 px-3">
                  <input
                    v-model="course.name"
                    type="text"
                    placeholder="Nama Mata Kuliah"
                    class="w-full rounded-lg border border-gray-200 px-2.5 py-1.5 text-xs text-gray-900 font-medium focus:border-blue-600 focus:outline-none"
                  />
                </td>
                <td class="py-2.5 px-3 text-center">
                  <select
                    v-model.number="course.credits"
                    class="rounded-lg border border-gray-200 bg-white px-2 py-1.5 text-xs font-bold text-gray-800 focus:border-blue-600 focus:outline-none"
                  >
                    <option v-for="sks in [1, 2, 3, 4, 6]" :key="sks" :value="sks">
                      {{ sks }} SKS
                    </option>
                  </select>
                </td>
                <td class="py-2.5 px-3 text-center">
                  <select
                    v-model="course.grade"
                    class="rounded-lg border border-gray-200 bg-white px-2.5 py-1.5 text-xs font-extrabold focus:border-blue-600 focus:outline-none"
                    :class="{
                      'text-emerald-700 font-bold': course.grade === 'A',
                      'text-blue-700': course.grade === 'AB',
                      'text-indigo-700': course.grade === 'B',
                      'text-amber-700': course.grade === 'BC',
                      'text-rose-700': course.grade === 'C' || course.grade === 'D' || course.grade === 'E',
                    }"
                  >
                    <option value="A">A (4.00)</option>
                    <option value="AB">AB (3.50)</option>
                    <option value="B">B (3.00)</option>
                    <option value="BC">BC (2.50)</option>
                    <option value="C">C (2.00)</option>
                    <option value="D">D (1.00)</option>
                    <option value="E">E (0.00)</option>
                  </select>
                </td>
                <td class="py-2.5 px-3 text-center font-bold text-gray-800">
                  {{ (Number(course.credits) || 0) * gradePoints[course.grade] }}
                </td>
                <td class="py-2.5 px-3 text-center">
                  <button
                    type="button"
                    @click="removeCourseRow(course.id)"
                    class="text-gray-300 hover:text-rose-600 transition-colors p-1 cursor-pointer"
                    title="Hapus baris matkul"
                  >
                    ✕
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="pt-2 flex items-center justify-between text-xs text-gray-500">
          <button
            type="button"
            @click="addCourseRow"
            class="text-blue-600 hover:text-blue-800 font-bold hover:underline cursor-pointer"
          >
            + Tambah Baris Mata Kuliah
          </button>
          <span>Total SKS Semester Ini: <strong class="text-gray-900">{{ totalSemesterCredits }} SKS</strong></span>
        </div>
      </div>
    </div>
  </div>
</template>
