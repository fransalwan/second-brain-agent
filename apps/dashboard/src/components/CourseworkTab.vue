<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { supabase } from '../lib/supabase'

const props = defineProps<{
  userId: string
}>()

interface Assignment {
  id: number
  course_name: string
  title: string
  assignment_type: string
  deadline: string | null
  weight_percent: number | null
  status: string
  notes: string | null
  completed_at: string | null
}

interface ExamTopic {
  name: string
  mastered: boolean
}

interface Exam {
  id: number
  course_name: string
  exam_type: string
  exam_date: string
  room_or_link: string | null
  rules: string | null
  topics: ExamTopic[] | null
  target_score: number | null
}

interface ProjectMilestone {
  step: string
  status: 'done' | 'in_progress' | 'pending'
  pic?: string
}

interface ProjectDeliverable {
  item: string
  done: boolean
}

interface CourseProject {
  id: number
  course_name: string
  title: string
  deadline: string | null
  milestones: ProjectMilestone[] | null
  deliverables: ProjectDeliverable[] | null
  status: string
}

const loading = ref(true)
const saving = ref(false)

const assignments = ref<Assignment[]>([])
const exams = ref<Exam[]>([])
const projects = ref<CourseProject[]>([])

// Sub-View Switcher: Tasks/Exams vs Simulator
import GradeGpaSimulator from './GradeGpaSimulator.vue'
const activeSubView = ref<'tasks' | 'simulator'>('tasks')

// Filter & Sort
const assignmentFilter = ref<'all' | 'pending' | 'completed'>('pending')
const courseFilter = ref<string>('all')
const sortBy = ref<'deadline' | 'weight'>('deadline')

const showAssignmentModal = ref(false)
const showExamModal = ref(false)
const showProjectModal = ref(false)

// Forms
const assignmentForm = ref({
  course_name: '',
  title: '',
  assignment_type: 'Individu',
  deadline: '',
  weight_percent: 15,
  notes: '',
})

const examForm = ref({
  course_name: '',
  exam_type: 'UTS',
  exam_date: '',
  room_or_link: '',
  rules: 'Closed Book',
  target_score: 85,
  topics_text: 'Topik 1, Topik 2, Topik 3',
})

const projectForm = ref({
  course_name: '',
  title: '',
  deadline: '',
  milestones_text: 'Proposal Arsitektur, Backend & AI Model, Frontend Dashboard, Laporan Akhir',
  deliverables_text: 'Repository Git, Naskah Laporan PDF, Slide Pitching, Video Demo',
})

// Inline new topic input states per exam
const newTopicInputs = ref<Record<number, string>>({})

async function fetchCourseworkData() {
  loading.value = true
  try {
    // 1. Assignments
    const { data: assData } = await supabase
      .from('course_assignments')
      .select('*')
      .eq('user_id', props.userId)
      .order('deadline', { ascending: true })

    assignments.value = assData || []

    // 2. Exams
    const { data: exData } = await supabase
      .from('course_exams')
      .select('*')
      .eq('user_id', props.userId)
      .order('exam_date', { ascending: true })

    exams.value = exData || []

    // 3. Projects
    const { data: prData } = await supabase
      .from('course_projects')
      .select('*')
      .eq('user_id', props.userId)
      .order('created_at', { ascending: false })

    projects.value = prData || []
  } catch (err) {
    console.error('Gagal mengambil data perkuliahan:', err)
  } finally {
    loading.value = false
  }
}

// Assignment actions
async function toggleAssignmentStatus(assignment: Assignment) {
  if (saving.value) return
  saving.value = true
  const nextStatus = assignment.status === 'completed' ? 'pending' : 'completed'
  const completedAt = nextStatus === 'completed' ? new Date().toISOString() : null

  try {
    const { error } = await supabase
      .from('course_assignments')
      .update({
        status: nextStatus,
        completed_at: completedAt,
      })
      .eq('id', assignment.id)

    if (!error) {
      assignment.status = nextStatus
      assignment.completed_at = completedAt
    }
  } catch (err) {
    console.error('Gagal update status tugas:', err)
  } finally {
    saving.value = false
  }
}

async function deleteAssignment(id: number) {
  if (!confirm('Hapus tugas kuliah ini?')) return
  try {
    await supabase.from('course_assignments').delete().eq('id', id)
    assignments.value = assignments.value.filter(a => a.id !== id)
  } catch (err) {
    console.error('Gagal menghapus tugas:', err)
  }
}

async function submitAssignment() {
  if (saving.value) return
  saving.value = true
  try {
    const dl = assignmentForm.value.deadline ? new Date(assignmentForm.value.deadline).toISOString() : null
    const { error } = await supabase
      .from('course_assignments')
      .insert({
        user_id: props.userId,
        course_name: assignmentForm.value.course_name.trim(),
        title: assignmentForm.value.title.trim(),
        assignment_type: assignmentForm.value.assignment_type,
        deadline: dl,
        weight_percent: assignmentForm.value.weight_percent,
        notes: assignmentForm.value.notes.trim() || null,
        status: 'pending',
      })

    if (!error) {
      showAssignmentModal.value = false
      assignmentForm.value = { course_name: '', title: '', assignment_type: 'Individu', deadline: '', weight_percent: 15, notes: '' }
      await fetchCourseworkData()
    }
  } catch (err) {
    console.error('Gagal menyimpan tugas:', err)
  } finally {
    saving.value = false
  }
}

// Exam actions
async function toggleExamTopic(exam: Exam, topicIndex: number) {
  if (!exam.topics || !exam.topics[topicIndex]) return
  exam.topics[topicIndex].mastered = !exam.topics[topicIndex].mastered

  try {
    await supabase
      .from('course_exams')
      .update({ topics: exam.topics })
      .eq('id', exam.id)
  } catch (err) {
    console.error('Gagal update topik ujian:', err)
  }
}

async function addInlineTopic(exam: Exam) {
  const text = (newTopicInputs.value[exam.id] || '').trim()
  if (!text) return

  const topicsList = exam.topics || []
  topicsList.push({ name: text, mastered: false })
  exam.topics = topicsList
  newTopicInputs.value[exam.id] = ''

  try {
    await supabase
      .from('course_exams')
      .update({ topics: exam.topics })
      .eq('id', exam.id)
  } catch (err) {
    console.error('Gagal menambah topik ujian:', err)
  }
}

async function deleteExam(id: number) {
  if (!confirm('Hapus jadwal ujian ini?')) return
  try {
    await supabase.from('course_exams').delete().eq('id', id)
    exams.value = exams.value.filter(e => e.id !== id)
  } catch (err) {
    console.error('Gagal menghapus ujian:', err)
  }
}

async function submitExam() {
  if (saving.value) return
  saving.value = true
  try {
    const parsedTopics = examForm.value.topics_text
      .split(',')
      .map(t => t.trim())
      .filter(t => t.length > 0)
      .map(name => ({ name, mastered: false }))

    const { error } = await supabase
      .from('course_exams')
      .insert({
        user_id: props.userId,
        course_name: examForm.value.course_name.trim(),
        exam_type: examForm.value.exam_type,
        exam_date: new Date(examForm.value.exam_date).toISOString(),
        room_or_link: examForm.value.room_or_link.trim() || null,
        rules: examForm.value.rules,
        target_score: examForm.value.target_score,
        topics: parsedTopics,
      })

    if (!error) {
      showExamModal.value = false
      examForm.value = { course_name: '', exam_type: 'UTS', exam_date: '', room_or_link: '', rules: 'Closed Book', target_score: 85, topics_text: '' }
      await fetchCourseworkData()
    }
  } catch (err) {
    console.error('Gagal menjadwalkan ujian:', err)
  } finally {
    saving.value = false
  }
}

// Project Actions
async function toggleProjectDeliverable(proj: CourseProject, index: number) {
  if (!proj.deliverables || !proj.deliverables[index]) return
  proj.deliverables[index].done = !proj.deliverables[index].done

  try {
    await supabase
      .from('course_projects')
      .update({ deliverables: proj.deliverables })
      .eq('id', proj.id)
  } catch (err) {
    console.error('Gagal update deliverable project:', err)
  }
}

async function cycleMilestoneStatus(proj: CourseProject, index: number) {
  if (!proj.milestones || !proj.milestones[index]) return
  const current = proj.milestones[index].status
  const cycle: Array<'pending' | 'in_progress' | 'done'> = ['pending', 'in_progress', 'done']
  const next = cycle[(cycle.indexOf(current) + 1) % cycle.length]
  proj.milestones[index].status = next

  try {
    await supabase
      .from('course_projects')
      .update({ milestones: proj.milestones })
      .eq('id', proj.id)
  } catch (err) {
    console.error('Gagal update milestone:', err)
  }
}

async function submitProject() {
  if (saving.value) return
  saving.value = true
  try {
    const parsedMilestones = projectForm.value.milestones_text
      .split(',')
      .map(s => s.trim())
      .filter(s => s.length > 0)
      .map((step, idx) => ({ step, status: (idx === 0 ? 'in_progress' : 'pending') as 'in_progress' | 'pending', pic: 'Tim' }))

    const parsedDeliverables = projectForm.value.deliverables_text
      .split(',')
      .map(d => d.trim())
      .filter(d => d.length > 0)
      .map(item => ({ item, done: false }))

    const dl = projectForm.value.deadline ? new Date(projectForm.value.deadline).toISOString() : null

    const { error } = await supabase
      .from('course_projects')
      .insert({
        user_id: props.userId,
        course_name: projectForm.value.course_name.trim(),
        title: projectForm.value.title.trim(),
        deadline: dl,
        milestones: parsedMilestones,
        deliverables: parsedDeliverables,
        status: 'in_progress',
      })

    if (!error) {
      showProjectModal.value = false
      projectForm.value = { course_name: '', title: '', deadline: '', milestones_text: '', deliverables_text: '' }
      await fetchCourseworkData()
    }
  } catch (err) {
    console.error('Gagal menyimpan tubes:', err)
  } finally {
    saving.value = false
  }
}

// Helpers
function formatDeadlineBadge(iso: string | null) {
  if (!iso) return { label: 'Tanpa Deadline', color: 'bg-gray-100 text-gray-600 border-gray-200' }
  const dl = new Date(iso)
  const now = new Date()
  const diffDays = Math.ceil((dl.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))

  if (diffDays < 0) return { label: 'Lewat Deadline', color: 'bg-gray-100 text-gray-500 border-gray-200' }
  if (diffDays <= 1) return { label: 'H-1 Kritis 🔥', color: 'bg-rose-100 text-rose-800 border-rose-300 font-bold animate-pulse' }
  if (diffDays <= 3) return { label: `H-${diffDays} ⏳`, color: 'bg-amber-100 text-amber-800 border-amber-300 font-semibold' }
  return { label: `H-${diffDays}`, color: 'bg-blue-50 text-blue-700 border-blue-200' }
}

const distinctCourses = computed(() => {
  const set = new Set<string>()
  assignments.value.forEach(a => set.add(a.course_name))
  exams.value.forEach(e => set.add(e.course_name))
  return Array.from(set)
})

const filteredAssignments = computed(() => {
  let list = assignments.value

  // Status Filter
  if (assignmentFilter.value === 'pending') list = list.filter(a => a.status === 'pending')
  else if (assignmentFilter.value === 'completed') list = list.filter(a => a.status === 'completed')

  // Course Filter
  if (courseFilter.value !== 'all') {
    list = list.filter(a => a.course_name.toLowerCase() === courseFilter.value.toLowerCase())
  }

  // Sorting
  return [...list].sort((a, b) => {
    if (sortBy.value === 'weight') {
      return (b.weight_percent || 0) - (a.weight_percent || 0)
    }
    // Default deadline sorting
    if (!a.deadline) return 1
    if (!b.deadline) return -1
    return new Date(a.deadline).getTime() - new Date(b.deadline).getTime()
  })
})

onMounted(() => {
  fetchCourseworkData()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Header Banner -->
    <div class="rounded-2xl border border-gray-200 bg-white p-5 shadow-xs sm:p-6">
      <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div class="flex items-center gap-2">
            <span class="text-2xl">🎓</span>
            <h2 class="text-lg font-bold text-gray-900 sm:text-xl">Smart Academic &amp; Coursework Hub</h2>
            <span class="rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-semibold text-blue-800">Prioritas #2</span>
          </div>
          <p class="mt-1 text-xs text-gray-500 sm:text-sm">
            Manajemen tugas kuliah prioritas tinggi, radar kisi-kisi UTS/UAS, dan pemantauan deliverable proyek tim (tubes).
          </p>
        </div>
        <div class="flex flex-wrap gap-2">
          <button
            @click="showAssignmentModal = true"
            class="inline-flex items-center gap-1.5 rounded-xl bg-gray-900 px-3.5 py-2 text-xs font-semibold text-white shadow-xs hover:bg-gray-800 transition-colors cursor-pointer"
          >
            <span>➕</span>
            <span>Tugas Kuliah</span>
          </button>
          <button
            @click="showExamModal = true"
            class="inline-flex items-center gap-1.5 rounded-xl border border-gray-300 bg-white px-3.5 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50 transition-colors cursor-pointer"
          >
            <span>🎯</span>
            <span>Jadwal Ujian</span>
          </button>
          <button
            @click="showProjectModal = true"
            class="inline-flex items-center gap-1.5 rounded-xl border border-blue-200 bg-blue-50 px-3.5 py-2 text-xs font-semibold text-blue-800 hover:bg-blue-100 transition-colors cursor-pointer"
          >
            <span>👥</span>
            <span>Final Project</span>
          </button>
        </div>
      </div>
    </div>

    <div v-if="loading" class="flex justify-center py-12">
      <div class="h-8 w-8 animate-spin rounded-full border-4 border-gray-900 border-t-transparent"></div>
    </div>

    <div v-else class="space-y-6">
      <!-- Sub-View Navigation Switcher -->
      <div class="flex items-center gap-2 border-b border-gray-200 pb-2">
        <button
          type="button"
          @click="activeSubView = 'tasks'"
          class="inline-flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold transition-all cursor-pointer"
          :class="activeSubView === 'tasks' ? 'bg-blue-600 text-white shadow-xs' : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50'"
        >
          <span>📋</span>
          <span>Tugas, Ujian &amp; Tubes</span>
        </button>

        <button
          type="button"
          @click="activeSubView = 'simulator'"
          class="inline-flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold transition-all cursor-pointer"
          :class="activeSubView === 'simulator' ? 'bg-blue-600 text-white shadow-xs' : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50'"
        >
          <span>🎯</span>
          <span>Simulator Nilai &amp; Target IPK</span>
          <span class="rounded-full bg-amber-400 text-amber-950 px-1.5 py-0.2 text-[10px] font-extrabold uppercase">Baru ✨</span>
        </button>
      </div>

      <!-- Tab Content: Simulator Nilai & IPK -->
      <GradeGpaSimulator
        v-if="activeSubView === 'simulator'"
        :user-id="props.userId"
        :existing-courses="distinctCourses"
      />

      <!-- Tab Content: Tugas, Ujian & Tubes -->
      <div v-else-if="activeSubView === 'tasks'" class="space-y-6">
        <!-- 1. Assignments Section -->
        <div class="rounded-2xl border border-gray-200 bg-white p-5 shadow-xs sm:p-6">
        <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 pb-4 border-b border-gray-100">
          <div>
            <div class="flex items-center gap-2">
              <span class="text-xl">📚</span>
              <h3 class="text-sm font-bold text-gray-900">Daftar Tugas Kuliah (Coursework)</h3>
            </div>
            <p class="text-xs text-gray-500 mt-0.5">Selesaikan tugas dengan bobot nilai tinggi terlebih dahulu untuk mengamankan IPK.</p>
          </div>

          <!-- Controls: Filter Status, Matkul, Sort -->
          <div class="flex flex-wrap items-center gap-2">
            <!-- Filter Matkul -->
            <select
              v-model="courseFilter"
              class="rounded-xl border border-gray-200 bg-gray-50 px-2.5 py-1.5 text-xs font-medium text-gray-700 focus:outline-none focus:ring-1 focus:ring-gray-900"
            >
              <option value="all">Semua Matkul</option>
              <option v-for="c in distinctCourses" :key="c" :value="c">{{ c }}</option>
            </select>

            <!-- Sort By -->
            <select
              v-model="sortBy"
              class="rounded-xl border border-gray-200 bg-gray-50 px-2.5 py-1.5 text-xs font-medium text-gray-700 focus:outline-none focus:ring-1 focus:ring-gray-900"
            >
              <option value="deadline">Urut: Deadline Terdekat</option>
              <option value="weight">Urut: Bobot Nilai Tertinggi</option>
            </select>

            <!-- Status Pills -->
            <div class="flex items-center gap-1 rounded-xl bg-gray-100 p-1 text-xs">
              <button
                @click="assignmentFilter = 'pending'"
                class="rounded-lg px-2.5 py-1 font-semibold transition-all cursor-pointer"
                :class="assignmentFilter === 'pending' ? 'bg-white text-gray-900 shadow-xs' : 'text-gray-500 hover:text-gray-900'"
              >
                Pending ({{ assignments.filter(a => a.status === 'pending').length }})
              </button>
              <button
                @click="assignmentFilter = 'completed'"
                class="rounded-lg px-2.5 py-1 font-semibold transition-all cursor-pointer"
                :class="assignmentFilter === 'completed' ? 'bg-white text-gray-900 shadow-xs' : 'text-gray-500 hover:text-gray-900'"
              >
                Selesai ({{ assignments.filter(a => a.status === 'completed').length }})
              </button>
              <button
                @click="assignmentFilter = 'all'"
                class="rounded-lg px-2.5 py-1 font-semibold transition-all cursor-pointer"
                :class="assignmentFilter === 'all' ? 'bg-white text-gray-900 shadow-xs' : 'text-gray-500 hover:text-gray-900'"
              >
                Semua
              </button>
            </div>
          </div>
        </div>

        <!-- Assignments List -->
        <div v-if="filteredAssignments.length === 0" class="py-10 text-center text-xs text-gray-400">
          Tidak ada tugas kuliah yang cocok dengan filter ini.
        </div>

        <div v-else class="mt-4 divide-y divide-gray-100">
          <div
            v-for="item in filteredAssignments"
            :key="item.id"
            class="py-3.5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 group hover:bg-gray-50/50 p-2 rounded-xl transition-colors"
          >
            <div class="flex items-start gap-3">
              <input
                type="checkbox"
                :checked="item.status === 'completed'"
                @change="toggleAssignmentStatus(item)"
                :disabled="saving"
                class="mt-1 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
              />
              <div>
                <div class="flex flex-wrap items-center gap-2">
                  <span class="text-xs font-bold" :class="item.status === 'completed' ? 'line-through text-gray-400' : 'text-gray-900'">
                    {{ item.title }}
                  </span>
                  <span class="rounded-full bg-gray-100 px-2 py-0.5 text-[11px] font-medium text-gray-600">
                    {{ item.course_name }}
                  </span>
                  <span class="rounded-full bg-indigo-50 border border-indigo-200 px-2 py-0.5 text-[11px] font-semibold text-indigo-700">
                    Bobot {{ item.weight_percent || 15 }}%
                  </span>
                  <span
                    v-if="item.status !== 'completed'"
                    class="rounded-full px-2 py-0.5 text-[11px] border"
                    :class="formatDeadlineBadge(item.deadline).color"
                  >
                    {{ formatDeadlineBadge(item.deadline).label }}
                  </span>
                </div>
                <div class="text-[11px] text-gray-400 mt-1 flex flex-wrap items-center gap-2">
                  <span>Tipe: <strong>{{ item.assignment_type }}</strong></span>
                  <span v-if="item.notes">• {{ item.notes }}</span>
                </div>
              </div>
            </div>

            <div class="flex items-center gap-3 self-end sm:self-center">
              <div class="text-right text-xs text-gray-400">
                <span v-if="item.deadline">
                  DL: {{ new Date(item.deadline).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) }}
                </span>
                <span v-else class="text-gray-300">Tanpa deadline</span>
              </div>
              <button
                type="button"
                @click="deleteAssignment(item.id)"
                class="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-rose-600 text-xs transition-opacity cursor-pointer p-1"
                title="Hapus tugas"
              >
                🗑️
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 2. Exam Radar & Preparation Checklist -->
      <div class="grid grid-cols-1 gap-6 md:grid-cols-2">
        <div class="rounded-2xl border border-gray-200 bg-white p-5 shadow-xs sm:p-6 flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between pb-3 border-b border-gray-100">
              <div class="flex items-center gap-2">
                <span class="text-xl">🎯</span>
                <h3 class="text-sm font-bold text-gray-900">Radar Jadwal Ujian (UTS / UAS)</h3>
              </div>
              <span class="text-xs font-semibold text-gray-500">{{ exams.length }} Ujian Terdaftar</span>
            </div>

            <div v-if="exams.length === 0" class="py-8 text-center text-xs text-gray-400">
              Belum ada jadwal ujian. Klik "Jadwal Ujian" di atas untuk menambah.
            </div>

            <div v-else class="mt-4 space-y-4">
              <div
                v-for="exam in exams"
                :key="exam.id"
                class="rounded-xl border border-gray-200 p-4 bg-gray-50/50 space-y-3 group"
              >
                <div class="flex items-start justify-between">
                  <div>
                    <div class="flex items-center gap-2">
                      <span class="text-xs font-bold text-gray-900">{{ exam.exam_type }} - {{ exam.course_name }}</span>
                      <span class="rounded-full bg-blue-100 px-2 py-0.2 text-[10px] font-semibold text-blue-800">{{ exam.rules }}</span>
                    </div>
                    <div class="text-[11px] text-gray-500 mt-0.5">
                      📅 {{ new Date(exam.exam_date).toLocaleDateString('id-ID', { weekday: 'long', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) }}
                      <span v-if="exam.room_or_link">• 📍 {{ exam.room_or_link }}</span>
                    </div>
                  </div>
                  <div class="flex items-center gap-2">
                    <span class="text-xs font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                      Target: {{ exam.target_score || 85 }}
                    </span>
                    <button
                      type="button"
                      @click="deleteExam(exam.id)"
                      class="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-rose-600 text-xs transition-opacity cursor-pointer"
                      title="Hapus ujian"
                    >
                      🗑️
                    </button>
                  </div>
                </div>

                <!-- Topics Checklist & Progress Mastery -->
                <div v-if="exam.topics && exam.topics.length > 0" class="pt-2 border-t border-gray-200/60">
                  <div class="flex items-center justify-between text-[11px] font-semibold text-gray-600 mb-1.5">
                    <span>Kisi-Kisi Topik ({{ exam.topics.filter(t => t.mastered).length }}/{{ exam.topics.length }} Dikuasai)</span>
                    <span class="text-blue-600 font-bold">
                      {{ Math.round((exam.topics.filter(t => t.mastered).length / exam.topics.length) * 100) }}%
                    </span>
                  </div>

                  <!-- Mastery Bar -->
                  <div class="h-2 w-full rounded-full bg-gray-200 overflow-hidden mb-2.5">
                    <div
                      class="h-full rounded-full bg-blue-600 transition-all duration-300"
                      :style="{ width: `${Math.round((exam.topics.filter(t => t.mastered).length / exam.topics.length) * 100)}%` }"
                    ></div>
                  </div>

                  <div class="space-y-1.5 max-h-40 overflow-y-auto pr-1">
                    <label
                      v-for="(t, idx) in exam.topics"
                      :key="idx"
                      class="flex items-center gap-2 text-xs text-gray-700 cursor-pointer hover:text-gray-900"
                    >
                      <input
                        type="checkbox"
                        :checked="t.mastered"
                        @change="toggleExamTopic(exam, idx)"
                        class="h-3.5 w-3.5 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                      />
                      <span :class="t.mastered ? 'line-through text-gray-400' : ''">{{ t.name }}</span>
                    </label>
                  </div>
                </div>

                <!-- Inline Add Topic -->
                <div class="flex items-center gap-1.5 pt-1">
                  <input
                    v-model="newTopicInputs[exam.id]"
                    @keyup.enter="addInlineTopic(exam)"
                    type="text"
                    placeholder="+ Tambah topik kisi-kisi..."
                    class="flex-1 rounded-lg border border-gray-300 bg-white px-2.5 py-1 text-xs text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                  <button
                    type="button"
                    @click="addInlineTopic(exam)"
                    class="rounded-lg bg-gray-100 hover:bg-gray-200 px-2.5 py-1 text-xs font-semibold text-gray-700 cursor-pointer"
                  >
                    Tambah
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 3. Final Projects (Tubes) Hub -->
        <div class="rounded-2xl border border-gray-200 bg-white p-5 shadow-xs sm:p-6 flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between pb-3 border-b border-gray-100">
              <div class="flex items-center gap-2">
                <span class="text-xl">👥</span>
                <h3 class="text-sm font-bold text-gray-900">Final Project &amp; Tubes Hub</h3>
              </div>
              <button
                @click="showProjectModal = true"
                class="text-xs font-semibold text-blue-600 hover:text-blue-800 cursor-pointer"
              >
                + Tambah Tubes
              </button>
            </div>

            <div v-if="projects.length === 0" class="py-8 text-center text-xs text-gray-400">
              Belum ada final project terdaftar.
            </div>

            <div v-else class="mt-4 space-y-4">
              <div
                v-for="proj in projects"
                :key="proj.id"
                class="rounded-xl border border-gray-200 p-4 bg-gray-50/50 space-y-3"
              >
                <div>
                  <div class="flex items-center justify-between">
                    <span class="text-xs font-bold text-gray-900">{{ proj.title }}</span>
                    <span v-if="proj.deadline" class="text-[11px] text-gray-500">
                      DL: {{ new Date(proj.deadline).toLocaleDateString('id-ID', { day: 'numeric', month: 'short' }) }}
                    </span>
                  </div>
                  <div class="text-[11px] text-gray-500">Mata Kuliah: {{ proj.course_name }}</div>
                </div>

                <!-- Milestone Stepper (Clickable Cycle) -->
                <div v-if="proj.milestones && proj.milestones.length > 0" class="pt-2 border-t border-gray-200/60">
                  <div class="text-[11px] font-bold text-gray-600 mb-2 uppercase tracking-wider">
                    Milestones (Klik untuk ubah status):
                  </div>
                  <div class="space-y-1.5">
                    <div
                      v-for="(m, idx) in proj.milestones"
                      :key="idx"
                      @click="cycleMilestoneStatus(proj, idx)"
                      class="flex items-center justify-between p-2 rounded-lg border text-xs cursor-pointer transition-colors"
                      :class="m.status === 'done' ? 'bg-emerald-50 border-emerald-200 text-emerald-900' : (m.status === 'in_progress' ? 'bg-blue-50 border-blue-200 text-blue-900 font-semibold' : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-100')"
                    >
                      <span class="flex items-center gap-1.5">
                        <span>{{ m.status === 'done' ? '✓' : (m.status === 'in_progress' ? '⏳' : '○') }}</span>
                        <span>{{ m.step }}</span>
                      </span>
                      <span class="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded" :class="m.status === 'done' ? 'bg-emerald-200 text-emerald-900' : (m.status === 'in_progress' ? 'bg-blue-200 text-blue-900' : 'bg-gray-100 text-gray-500')">
                        {{ m.status }}
                      </span>
                    </div>
                  </div>
                </div>

                <!-- Deliverables Checklist -->
                <div v-if="proj.deliverables && proj.deliverables.length > 0" class="pt-2 border-t border-gray-200/60">
                  <div class="text-[11px] font-bold text-gray-600 mb-1.5 uppercase tracking-wider">Deliverables Tim:</div>
                  <div class="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                    <label
                      v-for="(d, idx) in proj.deliverables"
                      :key="idx"
                      class="flex items-center gap-2 text-xs text-gray-700 cursor-pointer p-1.5 rounded-lg border border-gray-200 bg-white hover:bg-gray-50"
                    >
                      <input
                        type="checkbox"
                        :checked="d.done"
                        @change="toggleProjectDeliverable(proj, idx)"
                        class="h-3.5 w-3.5 rounded border-gray-300 text-blue-600 focus:ring-blue-500 cursor-pointer"
                      />
                      <span class="text-[11px]" :class="d.done ? 'line-through text-gray-400 font-normal' : 'font-semibold'">
                        {{ d.item }}
                      </span>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      </div>
    </div>

    <!-- Modal Form Tambah Tugas -->
    <div
      v-if="showAssignmentModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/40 backdrop-blur-xs p-4"
    >
      <div class="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl border border-gray-200 space-y-4">
        <div class="flex items-center justify-between pb-3 border-b border-gray-100">
          <div class="flex items-center gap-2">
            <span class="text-xl">📚</span>
            <h3 class="text-sm font-bold text-gray-900">Tambah Tugas Kuliah</h3>
          </div>
          <button @click="showAssignmentModal = false" class="text-gray-400 hover:text-gray-600 text-sm cursor-pointer">✕</button>
        </div>

        <form @submit.prevent="submitAssignment" class="space-y-3 text-xs">
          <div>
            <label class="block font-semibold text-gray-700 mb-1">Mata Kuliah</label>
            <input
              v-model="assignmentForm.course_name"
              type="text"
              placeholder="Contoh: Machine Learning"
              required
              class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-gray-900 focus:outline-none"
            />
          </div>

          <div>
            <label class="block font-semibold text-gray-700 mb-1">Judul Tugas</label>
            <input
              v-model="assignmentForm.title"
              type="text"
              placeholder="Contoh: Implementasi CNN ResNet"
              required
              class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-gray-900 focus:outline-none"
            />
          </div>

          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="block font-semibold text-gray-700 mb-1">Tipe</label>
              <select
                v-model="assignmentForm.assignment_type"
                class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-gray-900 focus:outline-none"
              >
                <option value="Individu">Individu</option>
                <option value="Kelompok">Kelompok</option>
              </select>
            </div>
            <div>
              <label class="block font-semibold text-gray-700 mb-1">Bobot Nilai (%)</label>
              <input
                v-model.number="assignmentForm.weight_percent"
                type="number"
                min="1"
                max="100"
                class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-gray-900 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label class="block font-semibold text-gray-700 mb-1">Deadline Pengumpulan</label>
            <input
              v-model="assignmentForm.deadline"
              type="datetime-local"
              class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-gray-900 focus:outline-none"
            />
          </div>

          <div>
            <label class="block font-semibold text-gray-700 mb-1">Catatan / Format Pengumpulan</label>
            <input
              v-model="assignmentForm.notes"
              type="text"
              placeholder="Contoh: Format PDF IEEE via portal kuliah"
              class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-gray-900 focus:outline-none"
            />
          </div>

          <div class="pt-3 flex gap-2 justify-end">
            <button
              type="button"
              @click="showAssignmentModal = false"
              class="rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-semibold text-gray-700 hover:bg-gray-50 cursor-pointer"
            >
              Batal
            </button>
            <button
              type="submit"
              :disabled="saving"
              class="rounded-lg bg-gray-900 px-4 py-1.5 text-xs font-semibold text-white shadow-xs hover:bg-gray-800 disabled:opacity-50 cursor-pointer"
            >
              {{ saving ? 'Menyimpan...' : 'Simpan Tugas' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal Form Jadwal Ujian -->
    <div
      v-if="showExamModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/40 backdrop-blur-xs p-4"
    >
      <div class="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl border border-gray-200 space-y-4">
        <div class="flex items-center justify-between pb-3 border-b border-gray-100">
          <div class="flex items-center gap-2">
            <span class="text-xl">🎯</span>
            <h3 class="text-sm font-bold text-gray-900">Jadwalkan Ujian Baru</h3>
          </div>
          <button @click="showExamModal = false" class="text-gray-400 hover:text-gray-600 text-sm cursor-pointer">✕</button>
        </div>

        <form @submit.prevent="submitExam" class="space-y-3 text-xs">
          <div>
            <label class="block font-semibold text-gray-700 mb-1">Mata Kuliah</label>
            <input
              v-model="examForm.course_name"
              type="text"
              placeholder="Contoh: Sistem Terdistribusi"
              required
              class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-gray-900 focus:outline-none"
            />
          </div>

          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="block font-semibold text-gray-700 mb-1">Tipe Ujian</label>
              <select
                v-model="examForm.exam_type"
                class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-gray-900 focus:outline-none"
              >
                <option value="UTS">UTS</option>
                <option value="UAS">UAS</option>
                <option value="Kuis">Kuis</option>
                <option value="Praktikum">Praktikum</option>
              </select>
            </div>
            <div>
              <label class="block font-semibold text-gray-700 mb-1">Aturan</label>
              <select
                v-model="examForm.rules"
                class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-gray-900 focus:outline-none"
              >
                <option value="Closed Book">Closed Book</option>
                <option value="Open Book">Open Book</option>
                <option value="Take-Home">Take-Home</option>
              </select>
            </div>
          </div>

          <div>
            <label class="block font-semibold text-gray-700 mb-1">Tanggal &amp; Waktu Ujian</label>
            <input
              v-model="examForm.exam_date"
              type="datetime-local"
              required
              class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-gray-900 focus:outline-none"
            />
          </div>

          <div>
            <label class="block font-semibold text-gray-700 mb-1">Ruangan / Link</label>
            <input
              v-model="examForm.room_or_link"
              type="text"
              placeholder="Lab Komputer 302 / Zoom"
              class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-gray-900 focus:outline-none"
            />
          </div>

          <div>
            <label class="block font-semibold text-gray-700 mb-1">Kisi-Kisi Topik (Pisahkan dengan koma)</label>
            <input
              v-model="examForm.topics_text"
              type="text"
              placeholder="Contoh: Raft Consensus, MapReduce, Vector Clocks"
              class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-gray-900 focus:outline-none"
            />
          </div>

          <div class="pt-3 flex gap-2 justify-end">
            <button
              type="button"
              @click="showExamModal = false"
              class="rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-semibold text-gray-700 hover:bg-gray-50 cursor-pointer"
            >
              Batal
            </button>
            <button
              type="submit"
              :disabled="saving"
              class="rounded-lg bg-gray-900 px-4 py-1.5 text-xs font-semibold text-white shadow-xs hover:bg-gray-800 disabled:opacity-50 cursor-pointer"
            >
              {{ saving ? 'Menyimpan...' : 'Jadwalkan Ujian' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal Form Tambah Tubes -->
    <div
      v-if="showProjectModal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/40 backdrop-blur-xs p-4"
    >
      <div class="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl border border-gray-200 space-y-4">
        <div class="flex items-center justify-between pb-3 border-b border-gray-100">
          <div class="flex items-center gap-2">
            <span class="text-xl">👥</span>
            <h3 class="text-sm font-bold text-gray-900">Tambah Final Project / Tubes</h3>
          </div>
          <button @click="showProjectModal = false" class="text-gray-400 hover:text-gray-600 text-sm cursor-pointer">✕</button>
        </div>

        <form @submit.prevent="submitProject" class="space-y-3 text-xs">
          <div>
            <label class="block font-semibold text-gray-700 mb-1">Mata Kuliah</label>
            <input
              v-model="projectForm.course_name"
              type="text"
              placeholder="Contoh: Pemrograman Web Lanjut"
              required
              class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-gray-900 focus:outline-none"
            />
          </div>

          <div>
            <label class="block font-semibold text-gray-700 mb-1">Judul Project</label>
            <input
              v-model="projectForm.title"
              type="text"
              placeholder="Contoh: Platform E-Commerce Rekomendasi AI"
              required
              class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-gray-900 focus:outline-none"
            />
          </div>

          <div>
            <label class="block font-semibold text-gray-700 mb-1">Deadline Akhir</label>
            <input
              v-model="projectForm.deadline"
              type="date"
              class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-gray-900 focus:outline-none"
            />
          </div>

          <div>
            <label class="block font-semibold text-gray-700 mb-1">Milestones (Pisahkan dengan koma)</label>
            <input
              v-model="projectForm.milestones_text"
              type="text"
              placeholder="Proposal, Desain Sistem, Implementasi, Laporan"
              class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-gray-900 focus:outline-none"
            />
          </div>

          <div>
            <label class="block font-semibold text-gray-700 mb-1">Deliverables (Pisahkan dengan koma)</label>
            <input
              v-model="projectForm.deliverables_text"
              type="text"
              placeholder="Repository Git, Naskah Laporan PDF, Slide Pitching"
              class="w-full rounded-lg border border-gray-300 p-2 text-xs focus:ring-2 focus:ring-gray-900 focus:outline-none"
            />
          </div>

          <div class="pt-3 flex gap-2 justify-end">
            <button
              type="button"
              @click="showProjectModal = false"
              class="rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-semibold text-gray-700 hover:bg-gray-50 cursor-pointer"
            >
              Batal
            </button>
            <button
              type="submit"
              :disabled="saving"
              class="rounded-lg bg-gray-900 px-4 py-1.5 text-xs font-semibold text-white shadow-xs hover:bg-gray-800 disabled:opacity-50 cursor-pointer"
            >
              {{ saving ? 'Menyimpan...' : 'Simpan Project' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
