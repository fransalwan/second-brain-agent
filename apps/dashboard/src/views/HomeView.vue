<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '../lib/supabase'
import { getUserRole, setRoleOwner, clearAuthRole, OWNER_PASSKEY, type UserRole } from '../lib/authRole'
import RagExplorerTab from '../components/RagExplorerTab.vue'
import MultimodalVlmTab from '../components/MultimodalVlmTab.vue'
import MlRadarTab from '../components/MlRadarTab.vue'
import AiEvalsTab from '../components/AiEvalsTab.vue'
import ResearchTab from '../components/ResearchTab.vue'
import AgentOpsTab from '../components/AgentOpsTab.vue'
import NotificationCenter from '../components/NotificationCenter.vue'
import DailyBriefCard from '../components/DailyBriefCard.vue'
import QuickCaptureModal from '../components/QuickCaptureModal.vue'
import PrivacyModal from '../components/PrivacyModal.vue'
import BrainRagModal from '../components/BrainRagModal.vue'
import TechSpecsModal from '../components/TechSpecsModal.vue'
import RecruiterTourModal from '../components/RecruiterTourModal.vue'
import CommandPaletteModal from '../components/CommandPaletteModal.vue'

const router = useRouter()
const quickCaptureRef = ref<InstanceType<typeof QuickCaptureModal> | null>(null)
const privacyModalRef = ref<InstanceType<typeof PrivacyModal> | null>(null)
const brainRagModalRef = ref<InstanceType<typeof BrainRagModal> | null>(null)
const techSpecsModalRef = ref<InstanceType<typeof TechSpecsModal> | null>(null)
const recruiterTourRef = ref<InstanceType<typeof RecruiterTourModal> | null>(null)
const isDemoMode = ref(false)
const userRole = ref<UserRole>(getUserRole())
const showCommandPalette = ref(false)
const showMobileDrawer = ref(false)
const showDesktopMenu = ref(false)

function handleMobileNav(tab: string) {
  handleTabNavigate(tab)
  showMobileDrawer.value = false
}

const ownerUnlockInput = ref('')
const ownerUnlockError = ref('')

function handleUnlockAsOwner() {
  ownerUnlockError.value = ''
  if (!ownerUnlockInput.value) {
    ownerUnlockError.value = 'Password atau Master Passkey Pemilik wajib diisi.'
    return
  }
  if (ownerUnlockInput.value.trim() === OWNER_PASSKEY) {
    setRoleOwner()
    userRole.value = 'owner'
    isDemoMode.value = false
    userEmail.value = 'fransalwanpurba@mail.ugm.ac.id'
    currentUserId.value = 'owner-frans-ugm'
    profile.value = {
      id: 'owner-frans-ugm',
      email: 'fransalwanpurba@mail.ugm.ac.id',
      full_name: 'Frans Alwan Purba (Pemilik)',
      telegram_chat_id: 6745429419,
      brief_time: '07:00:00',
      night_cutoff_time: '23:00:00',
    }
    ownerUnlockInput.value = ''
  } else {
    ownerUnlockError.value = 'Passkey Pemilik salah. Akses riset tetap terproteksi.'
  }
}

function handleOpenRecruiterTour() {
  recruiterTourRef.value?.openTour()
}

function handleOpenTechSpecs() {
  techSpecsModalRef.value?.openModal()
}

function handleOpenBrainRag(query?: any) {
  const q = typeof query === 'string' ? query : undefined
  brainRagModalRef.value?.openModal(q)
}

function handleOpenQuickCapture() {
  quickCaptureRef.value?.openModal()
}

function handleOpenPrivacy(tab: 'governance' | 'pii_redactor' | 'adrs' | 'export' = 'governance') {
  privacyModalRef.value?.openModal(tab)
}

function handleQuickCreated(payload: { type: string; data?: any }) {
  if (payload.type === 'task' && payload.data) {
    tasks.value.unshift(payload.data)
  } else if (payload.type === 'note' && payload.data) {
    notes.value.unshift(payload.data)
    initGraphData()
  } else if (payload.type === 'timer' && payload.data) {
    timeLogs.value.unshift(payload.data)
  }
}

interface ProfileItem {
  id?: string
  email?: string | null
  full_name: string | null
  telegram_chat_id: number | null
  brief_time: string | null
  night_cutoff_time: string | null
}

interface AreaItem {
  id: number
  name: string
  position: number
}

interface TaskItem {
  id: number
  area_id: number | null
  title: string
  deadline: string | null
  is_urgent: boolean
  status: string
  completed_at: string | null
  created_at: string
}

interface HabitItem {
  id: number
  name: string
  is_active: boolean
  position: number
}

interface HabitLogItem {
  id: number
  habit_id: number
  completed_date: string
}

interface NoteItem {
  id: number
  content: string
  tags: string[] | null
  created_at: string
}

interface TimeLogItem {
  id: number
  project_name: string
  started_at: string
  ended_at: string | null
  duration_minutes: number | null
}

interface GraphNode {
  id: number
  label: string
  fullContent: string
  tags: string[]
  created_at: string
  x: number
  y: number
  vx: number
  vy: number
  radius: number
  color: string
}

interface GraphEdge {
  source: GraphNode
  target: GraphNode
  sharedTag?: string
}

const userEmail = ref<string | null>(null)
const currentUserId = ref<string>('')
const profile = ref<ProfileItem | null>(null)
const profileLoaded = ref(false)
const activeTab = ref<'overview' | 'rag' | 'vlm' | 'mlradar' | 'evals' | 'research' | 'agentops'>('overview')

function handleTabNavigate(tab: string) {
  if (tab === 'health') {
    activeTab.value = 'mlradar'
  } else if (tab === 'coursework') {
    activeTab.value = 'research'
  } else if (['overview', 'rag', 'vlm', 'mlradar', 'evals', 'research', 'agentops'].includes(tab)) {
    activeTab.value = tab as any
  } else {
    activeTab.value = 'overview'
  }
}

const areas = ref<AreaItem[]>([])
const tasks = ref<TaskItem[]>([])
const habits = ref<HabitItem[]>([])
const habitLogs = ref<HabitLogItem[]>([])
const notes = ref<NoteItem[]>([])
const timeLogs = ref<TimeLogItem[]>([])

const loading = ref(true)
const errorMsg = ref<string | null>(null)
const loggingOut = ref(false)
const taskFilter = ref<'all' | 'pending' | 'completed' | 'urgent'>('pending')
const notesTab = ref<'list' | 'graph'>('list')
const graphCanvas = ref<HTMLCanvasElement | null>(null)
const graphNodes = ref<GraphNode[]>([])
const graphEdges = ref<GraphEdge[]>([])
const selectedNode = ref<GraphNode | null>(null)
const hoveredNode = ref<GraphNode | null>(null)

const dateTimeFormatter = new Intl.DateTimeFormat('id-ID', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
})

const dateFormatter = new Intl.DateTimeFormat('id-ID', {
  weekday: 'long',
  day: 'numeric',
  month: 'short',
  year: 'numeric',
})

const todayHuman = dateFormatter.format(new Date())

function formatDateTime(isoString: string | null): string {
  if (!isoString) return '-'
  try {
    return dateTimeFormatter.format(new Date(isoString))
  } catch {
    return '-'
  }
}

function getTodayIso(): string {
  const d = new Date()
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const todayIso = getTodayIso()

async function handleToggleTask(taskId: number) {
  const target = tasks.value.find((t) => t.id === taskId)
  if (!target) return
  const newStatus = target.status === 'completed' ? 'pending' : 'completed'
  const completedAt = newStatus === 'completed' ? new Date().toISOString() : null

  target.status = newStatus
  target.completed_at = completedAt

  try {
    await supabase
      .from('tasks')
      .update({
        status: newStatus,
        completed_at: completedAt,
      })
      .eq('id', taskId)
  } catch (err) {
    console.error('Failed to update task status:', err)
  }
}

const newTimerProject = ref('')
const startingTimer = ref(false)
const stoppingTimer = ref(false)

async function handleStartTimer() {
  if (!newTimerProject.value.trim() || !currentUserId.value) return
  startingTimer.value = true
  try {
    const startedAt = new Date().toISOString()
    const { data } = await supabase
      .from('time_logs')
      .insert({
        user_id: currentUserId.value,
        project_name: newTimerProject.value.trim(),
        started_at: startedAt,
        ended_at: null,
        duration_minutes: null,
      })
      .select()
      .single()

    if (data) {
      timeLogs.value.unshift(data)
      newTimerProject.value = ''
    }
  } catch (err) {
    console.error('Failed to start timer:', err)
  } finally {
    startingTimer.value = false
  }
}

async function handleStopTimer(logId: number) {
  stoppingTimer.value = true
  try {
    const end = new Date()
    const target = timeLogs.value.find((t) => t.id === logId)
    if (target) {
      const start = new Date(target.started_at)
      const diffMinutes = Math.max(1, Math.round((end.getTime() - start.getTime()) / (1000 * 60)))
      target.ended_at = end.toISOString()
      target.duration_minutes = diffMinutes

      await supabase
        .from('time_logs')
        .update({
          ended_at: end.toISOString(),
          duration_minutes: diffMinutes,
        })
        .eq('id', logId)
    }
  } catch (err) {
    console.error('Failed to stop timer:', err)
  } finally {
    stoppingTimer.value = false
  }
}

async function handleToggleHabit(habitId: number) {
  const existingLogIndex = habitLogs.value.findIndex(
    (l) => l.habit_id === habitId && l.completed_date === todayIso
  )
  if (existingLogIndex >= 0) {
    const logId = habitLogs.value[existingLogIndex].id
    habitLogs.value.splice(existingLogIndex, 1)
    if (!isDemoMode.value) {
      await supabase.from('habit_logs').delete().eq('id', logId)
    }
  } else {
    if (isDemoMode.value) {
      habitLogs.value.push({ id: Date.now(), habit_id: habitId, completed_date: todayIso })
      return
    }
    const { data } = await supabase
      .from('habit_logs')
      .insert({
        habit_id: habitId,
        completed_date: todayIso,
      })
      .select()
      .single()
    if (data) {
      habitLogs.value.push(data)
    }
  }
}

const areaMap = computed(() => {
  const map: Record<number, string> = {}
  for (const a of areas.value) {
    map[a.id] = a.name
  }
  return map
})

const activeTimer = computed(() => {
  return timeLogs.value.find((t) => t.ended_at === null) ?? null
})

const totalFocusMinutesToday = computed(() => {
  return timeLogs.value
    .filter((t) => t.started_at.startsWith(todayIso) && t.duration_minutes !== null)
    .reduce((acc, t) => acc + (t.duration_minutes || 0), 0)
})

const pendingTasks = computed(() => {
  return tasks.value.filter((t) => t.status === 'pending')
})

const completedTasks = computed(() => {
  return tasks.value.filter((t) => t.status === 'completed')
})

const urgentCount = computed(() => {
  return pendingTasks.value.filter((t) => t.is_urgent).length
})

const filteredTasks = computed(() => {
  if (taskFilter.value === 'pending') return pendingTasks.value
  if (taskFilter.value === 'completed') return completedTasks.value
  if (taskFilter.value === 'urgent') return pendingTasks.value.filter((t) => t.is_urgent)
  return tasks.value
})

const habitsWithStatus = computed(() => {
  return habits.value.map((habit) => {
    const logs = habitLogs.value
      .filter((l) => l.habit_id === habit.id)
      .map((l) => l.completed_date)
    const logSet = new Set(logs)
    const isCompletedToday = logSet.has(todayIso)

    // Hitung streak sederhana
    let streak = 0
    let curr = new Date()
    if (!isCompletedToday) {
      curr.setDate(curr.getDate() - 1)
    }

    while (true) {
      const yr = curr.getFullYear()
      const mo = String(curr.getMonth() + 1).padStart(2, '0')
      const dy = String(curr.getDate()).padStart(2, '0')
      const dStr = `${yr}-${mo}-${dy}`
      if (logSet.has(dStr)) {
        streak += 1
        curr.setDate(curr.getDate() - 1)
      } else {
        break
      }
    }

    return {
      ...habit,
      isCompletedToday,
      streak,
    }
  })
})

const completedHabitsTodayCount = computed(() => {
  return habitsWithStatus.value.filter((h) => h.isCompletedToday).length
})

function formatDeadline(dl: string | null): { text: string; badgeClass: string } {
  if (!dl) return { text: 'Tanpa deadline', badgeClass: 'text-gray-400 bg-gray-50' }
  if (dl < todayIso) {
    return { text: `Terlambat (${dl})`, badgeClass: 'text-rose-700 bg-rose-50 border-rose-200' }
  }
  if (dl === todayIso) {
    return { text: 'Hari ini', badgeClass: 'text-amber-800 bg-amber-50 border-amber-200 font-semibold' }
  }
  return { text: dl, badgeClass: 'text-blue-700 bg-blue-50 border-blue-100' }
}

async function fetchData() {
  loading.value = true
  errorMsg.value = null

  userRole.value = getUserRole()
  isDemoMode.value = userRole.value === 'recruiter'

  if (userRole.value === 'owner' || isDemoMode.value) {
    const isOwner = userRole.value === 'owner'

    userEmail.value = isOwner ? 'fransalwanpurba@mail.ugm.ac.id' : 'recruiter@portfolio-eval.ugm.ac.id'
    currentUserId.value = isOwner ? 'owner-frans-ugm' : 'demo-recruiter-id'
    profile.value = {
      id: currentUserId.value,
      email: userEmail.value,
      full_name: isOwner ? 'Frans Alwan Purba (Pemilik)' : 'Recruiter / Reviewer (Guest Demo)',
      telegram_chat_id: isOwner ? 6745429419 : null,
      brief_time: '07:00:00',
      night_cutoff_time: '23:00:00',
    }
    profileLoaded.value = true
    areas.value = [
      { id: 1, name: 'Kesehatan & Vitalitas', position: 1 },
      { id: 2, name: 'Kuliah & AI Engineering', position: 2 },
      { id: 3, name: isOwner ? 'Riset & Skripsi S2' : 'Eksperimen Model AI', position: 3 },
      { id: 4, name: 'Agent Ops & Telemetry', position: 4 },
    ]
    tasks.value = [
      {
        id: 101,
        area_id: 3,
        title: isOwner
          ? 'Revisi Bab 3 Metodologi: Evaluasi F1-Score & Reciprocal Rank Fusion'
          : 'Verifikasi Evaluasi CRAG Self-Correction & Cross-Encoder Reranker',
        deadline: todayIso,
        is_urgent: true,
        status: 'pending',
        completed_at: null,
        created_at: new Date().toISOString(),
      },
      {
        id: 102,
        area_id: 2,
        title: 'Tubes Machine Learning: Pipeline Preprocessing Dataset Medis',
        deadline: new Date(Date.now() + 86400000).toISOString().slice(0, 10),
        is_urgent: true,
        status: 'pending',
        completed_at: null,
        created_at: new Date().toISOString(),
      },
      {
        id: 103,
        area_id: 1,
        title: 'Hidrasi Sehat: Minum 8 Gelas Air & Rutin Peregangan Leher',
        deadline: todayIso,
        is_urgent: false,
        status: 'pending',
        completed_at: null,
        created_at: new Date().toISOString(),
      },
      {
        id: 104,
        area_id: 1,
        title: 'Circadian Recharge & Cognitive Rest (Sesi Istirahat 60 Menit)',
        deadline: null,
        is_urgent: false,
        status: 'completed',
        completed_at: new Date().toISOString(),
        created_at: new Date().toISOString(),
      },
    ]
    habits.value = [
      { id: 1, name: 'Tidur Sebelum 23:00 (Bedtime Guardian)', is_active: true, position: 1 },
      { id: 2, name: 'Minum 2 Liter Air Putih', is_active: true, position: 2 },
      { id: 3, name: 'Deep Work Riset Tesis 90 Menit', is_active: true, position: 3 },
    ]
    habitLogs.value = [
      { id: 1, habit_id: 1, completed_date: todayIso },
      { id: 2, habit_id: 2, completed_date: todayIso },
    ]
    timeLogs.value = [
      {
        id: 1,
        project_name: 'Eksperimen Model AI & Evaluasi Latensi',
        started_at: new Date(Date.now() - 3600000 * 2).toISOString(),
        ended_at: new Date(Date.now() - 3600000).toISOString(),
        duration_minutes: 60,
      },
    ]
    notes.value = [
      {
        id: 1,
        content: 'Metodologi Bab 3: Menggunakan HNSW Index pada PostgreSQL pgvector untuk pencarian embedding 768 dimensi Gemini.',
        tags: ['skripsi', 'ai', 'rag'],
        created_at: new Date().toISOString(),
      },
      {
        id: 2,
        content: 'Arsitektur Concurrency: Golang telemetry daemon mengevaluasi deadline <24h dan sleep debt tanpa membebani Python runner.',
        tags: ['golang', 'backend', 'telemetri'],
        created_at: new Date().toISOString(),
      },
      {
        id: 3,
        content: 'Target revisi bimbingan: konsultasi bab 4 pembahasan hasil komparasi model transformer vs baseline.',
        tags: ['dospem', 'skripsi'],
        created_at: new Date().toISOString(),
      },
      {
        id: 4,
        content: 'Pola tidur dan hidrasi terbukti berkorelasi positif dengan fokus pengerjaan kode 90 menit deep work.',
        tags: ['kesehatan', 'fokus'],
        created_at: new Date().toISOString(),
      },
    ]
    loading.value = false
    initGraphData()
    return
  }

  const {
    data: { session },
  } = await supabase.auth.getSession()

  if (!session) {
    loading.value = false
    router.push({ name: 'login' })
    return
  }
  userEmail.value = session.user?.email ?? null
  currentUserId.value = session.user.id

  try {
    const [
      profileRes,
      areasRes,
      tasksRes,
      habitsRes,
      habitLogsRes,
      timeLogsRes,
      notesRes,
    ] = await Promise.all([
      supabase
        .from('profiles')
        .select('id, full_name, email, telegram_chat_id, brief_time, night_cutoff_time')
        .maybeSingle(),
      supabase.from('areas').select('id, name, position').order('position', { ascending: true }),
      supabase.from('tasks').select('*').order('created_at', { ascending: false }),
      supabase.from('habits').select('*').eq('is_active', true).order('position', { ascending: true }),
      supabase.from('habit_logs').select('*').order('completed_date', { ascending: false }),
      supabase.from('time_logs').select('*').order('started_at', { ascending: false }).limit(30),
      supabase.from('notes').select('*').order('created_at', { ascending: false }).limit(20),
    ])

    profileLoaded.value = true
    profile.value = profileRes.data ?? null
    const excludedAreaIds = new Set(
      (areasRes.data ?? [])
        .filter((a) => ['karir', 'usaha'].includes(a.name.trim().toLowerCase()))
        .map((a) => a.id)
    )
    areas.value = (areasRes.data ?? []).filter((a) => !excludedAreaIds.has(a.id))
    tasks.value = (tasksRes.data ?? []).filter((t) => !excludedAreaIds.has(t.area_id))
    habits.value = habitsRes.data ?? []
    habitLogs.value = habitLogsRes.data ?? []
    timeLogs.value = timeLogsRes.data ?? []
    notes.value = notesRes.data ?? []
  } catch (err: any) {
    errorMsg.value = err?.message || 'Gagal memuat data dashboard.'
  } finally {
    loading.value = false
  }
}

async function handleLogout() {
  loggingOut.value = true
  try {
    clearAuthRole()
    isDemoMode.value = false
    await supabase.auth.signOut()
    router.push({ name: 'login' })
  } catch (e) {
    // Fallback redirect
    router.push({ name: 'login' })
  } finally {
    loggingOut.value = false
  }
}

let animFrameId: number | null = null
let draggedNode: GraphNode | null = null
let dragStartX = 0
let dragStartY = 0
let hasMovedFar = false

function initGraphData() {
  const colorPalette = ['#38bdf8', '#34d399', '#fbbf24', '#a78bfa', '#f472b6', '#4ade80', '#fb923c']
  const count = notes.value.length
  if (count === 0) {
    graphNodes.value = []
    graphEdges.value = []
    return
  }

  const canvasWidth = graphCanvas.value?.clientWidth || 360
  const canvasHeight = graphCanvas.value?.clientHeight || 320
  const cx = canvasWidth / 2
  const cy = canvasHeight / 2

  const nodesList: GraphNode[] = notes.value.map((n, idx) => {
    let color = '#94a3b8'
    if (n.tags && n.tags.length > 0) {
      const hash = n.tags[0].split('').reduce((acc, c) => acc + c.charCodeAt(0), 0)
      color = colorPalette[hash % colorPalette.length]
    }
    const angle = (idx / count) * 2 * Math.PI
    const r = Math.min(cx, cy) * 0.65 * (0.6 + 0.4 * Math.random())
    return {
      id: n.id,
      label: n.content.length > 20 ? n.content.slice(0, 20) + '...' : n.content,
      fullContent: n.content,
      tags: n.tags || [],
      created_at: n.created_at,
      x: cx + Math.cos(angle) * r,
      y: cy + Math.sin(angle) * r,
      vx: (Math.random() - 0.5) * 1.5,
      vy: (Math.random() - 0.5) * 1.5,
      radius: 9 + Math.min((n.tags?.length || 0) * 2, 6),
      color,
    }
  })

  // Hubungkan simpul yang memiliki kesamaan tags atau keyword penting (> 4 huruf)
  const edgesList: GraphEdge[] = []
  for (let i = 0; i < nodesList.length; i++) {
    for (let j = i + 1; j < nodesList.length; j++) {
      const a = nodesList[i]
      const b = nodesList[j]
      const sharedTag = a.tags.find((t) => b.tags.includes(t))
      if (sharedTag) {
        edgesList.push({ source: a, target: b, sharedTag })
        continue
      }
      const wordsA = new Set(
        a.fullContent.toLowerCase().split(/\s+/).filter((w) => w.length > 4)
      )
      const wordsB = b.fullContent.toLowerCase().split(/\s+/).filter((w) => w.length > 4)
      const commonWord = wordsB.find((w) => wordsA.has(w))
      if (commonWord) {
        edgesList.push({ source: a, target: b, sharedTag: commonWord })
      }
    }
  }

  graphNodes.value = nodesList
  graphEdges.value = edgesList
}

function startSimulation() {
  stopSimulation()
  const canvas = graphCanvas.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const dpr = window.devicePixelRatio || 1
  const rect = canvas.getBoundingClientRect()
  canvas.width = rect.width * dpr
  canvas.height = rect.height * dpr

  function frame() {
    if (!canvas || !ctx) return
    const w = rect.width
    const h = rect.height
    const cx = w / 2
    const cy = h / 2

    // 1. Gaya tolak-menolak antar simpul (Coulomb repulsion)
    for (let i = 0; i < graphNodes.value.length; i++) {
      for (let j = i + 1; j < graphNodes.value.length; j++) {
        const a = graphNodes.value[i]
        const b = graphNodes.value[j]
        const dx = b.x - a.x
        const dy = b.y - a.y
        const dist = Math.sqrt(dx * dx + dy * dy) || 1
        if (dist < 180) {
          const force = ((180 - dist) / dist) * 0.5
          a.vx -= dx * force * 0.05
          a.vy -= dy * force * 0.05
          b.vx += dx * force * 0.05
          b.vy += dy * force * 0.05
        }
      }
    }

    // 2. Gaya tarik relasi (Spring attraction)
    for (const edge of graphEdges.value) {
      const a = edge.source
      const b = edge.target
      const dx = b.x - a.x
      const dy = b.y - a.y
      const dist = Math.sqrt(dx * dx + dy * dy) || 1
      const force = (dist - 75) * 0.03
      a.vx += (dx / dist) * force
      a.vy += (dy / dist) * force
      b.vx -= (dx / dist) * force
      b.vy -= (dy / dist) * force
    }

    // 3. Gravitasi sentral & redaman
    for (const node of graphNodes.value) {
      if (node !== draggedNode) {
        node.vx += (cx - node.x) * 0.006
        node.vy += (cy - node.y) * 0.006
        node.x += node.vx
        node.y += node.vy
        node.vx *= 0.88
        node.vy *= 0.88

        const pad = node.radius + 8
        if (node.x < pad) { node.x = pad; node.vx = 0 }
        if (node.x > w - pad) { node.x = w - pad; node.vx = 0 }
        if (node.y < pad) { node.y = pad; node.vy = 0 }
        if (node.y > h - pad) { node.y = h - pad; node.vy = 0 }
      }
    }

    // 4. Render canvas
    ctx.save()
    ctx.scale(dpr, dpr)
    ctx.clearRect(0, 0, w, h)

    // Gambar Garis Relasi (Edges)
    for (const edge of graphEdges.value) {
      const isConnectedToSelected =
        selectedNode.value &&
        (edge.source.id === selectedNode.value.id || edge.target.id === selectedNode.value.id)
      const isConnectedToHovered =
        hoveredNode.value &&
        (edge.source.id === hoveredNode.value.id || edge.target.id === hoveredNode.value.id)

      ctx.beginPath()
      ctx.moveTo(edge.source.x, edge.source.y)
      ctx.lineTo(edge.target.x, edge.target.y)
      if (isConnectedToSelected || isConnectedToHovered) {
        ctx.strokeStyle = 'rgba(96, 165, 250, 0.75)'
        ctx.lineWidth = 2
      } else {
        ctx.strokeStyle = 'rgba(148, 163, 184, 0.22)'
        ctx.lineWidth = 1
      }
      ctx.stroke()

      // Tampilkan label tag pada garis jika simpul disorot
      if ((isConnectedToSelected || isConnectedToHovered) && edge.sharedTag) {
        const midX = (edge.source.x + edge.target.x) / 2
        const midY = (edge.source.y + edge.target.y) / 2
        ctx.fillStyle = 'rgba(203, 213, 225, 0.9)'
        ctx.font = '10px Inter, sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText(`#${edge.sharedTag}`, midX, midY - 4)
      }
    }

    // Gambar Simpul (Nodes)
    for (const node of graphNodes.value) {
      const isSelected = selectedNode.value?.id === node.id
      const isHovered = hoveredNode.value?.id === node.id

      // Efek pendar (Halo glow) saat hover / selected
      if (isSelected || isHovered) {
        ctx.beginPath()
        ctx.arc(node.x, node.y, node.radius + 5, 0, 2 * Math.PI)
        ctx.fillStyle = isSelected ? 'rgba(59, 130, 246, 0.35)' : 'rgba(255, 255, 255, 0.15)'
        ctx.fill()
      }

      // Lingkaran utama
      ctx.beginPath()
      ctx.arc(node.x, node.y, node.radius, 0, 2 * Math.PI)
      ctx.fillStyle = node.color
      ctx.fill()
      ctx.lineWidth = isSelected ? 2.5 : 1.5
      ctx.strokeStyle = isSelected ? '#ffffff' : 'rgba(255, 255, 255, 0.7)'
      ctx.stroke()

      // Teks label simpul
      ctx.fillStyle = isSelected ? '#ffffff' : '#cbd5e1'
      ctx.font = isSelected ? 'bold 11px Inter, sans-serif' : '10px Inter, sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText(node.label, node.x, node.y + node.radius + 13)
    }

    ctx.restore()
    animFrameId = requestAnimationFrame(frame)
  }

  animFrameId = requestAnimationFrame(frame)
}

function stopSimulation() {
  if (animFrameId !== null) {
    cancelAnimationFrame(animFrameId)
    animFrameId = null
  }
}

function handleCanvasMouseDown(e: MouseEvent) {
  const canvas = graphCanvas.value
  if (!canvas) return
  const rect = canvas.getBoundingClientRect()
  const mouseX = e.clientX - rect.left
  const mouseY = e.clientY - rect.top

  for (const node of graphNodes.value) {
    const dx = node.x - mouseX
    const dy = node.y - mouseY
    if (Math.sqrt(dx * dx + dy * dy) <= node.radius + 5) {
      draggedNode = node
      dragStartX = mouseX
      dragStartY = mouseY
      hasMovedFar = false
      break
    }
  }
}

function handleCanvasMouseMove(e: MouseEvent) {
  const canvas = graphCanvas.value
  if (!canvas) return
  const rect = canvas.getBoundingClientRect()
  const mouseX = e.clientX - rect.left
  const mouseY = e.clientY - rect.top

  if (draggedNode) {
    const dx = mouseX - dragStartX
    const dy = mouseY - dragStartY
    if (Math.sqrt(dx * dx + dy * dy) > 5) {
      hasMovedFar = true
    }
    draggedNode.x = mouseX
    draggedNode.y = mouseY
    draggedNode.vx = 0
    draggedNode.vy = 0
  } else {
    let found: GraphNode | null = null
    for (const node of graphNodes.value) {
      const dx = node.x - mouseX
      const dy = node.y - mouseY
      if (Math.sqrt(dx * dx + dy * dy) <= node.radius + 5) {
        found = node
        break
      }
    }
    hoveredNode.value = found
  }
}

function handleCanvasMouseUp() {
  if (draggedNode) {
    if (!hasMovedFar) {
      selectedNode.value = selectedNode.value?.id === draggedNode.id ? null : draggedNode
    }
    draggedNode = null
  }
}

function handleCanvasMouseLeave() {
  draggedNode = null
  hoveredNode.value = null
}

function switchNotesTab(tab: 'list' | 'graph') {
  notesTab.value = tab
  if (tab === 'graph') {
    nextTick(() => {
      initGraphData()
      startSimulation()
    })
  } else {
    stopSimulation()
  }
}

watch(notes, () => {
  if (notesTab.value === 'graph') {
    initGraphData()
  }
})

function handleGlobalKeydown(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault()
    showCommandPalette.value = !showCommandPalette.value
  }
}

function handleDocumentClick(e: MouseEvent) {
  const target = e.target as HTMLElement | null
  if (target && !target.closest('.desktop-menu-container')) {
    showDesktopMenu.value = false
  }
}

onUnmounted(() => {
  stopSimulation()
  window.removeEventListener('keydown', handleGlobalKeydown)
  window.removeEventListener('click', handleDocumentClick)
})

onMounted(() => {
  fetchData()
  window.addEventListener('keydown', handleGlobalKeydown)
  window.addEventListener('click', handleDocumentClick)
})
</script>

<template>
  <div class="min-h-screen bg-gray-50 text-gray-900 pb-24 md:pb-16 relative">
    <!-- Header Navbar (Responsive, Clean SaaS Architecture) -->
    <header class="border-b border-slate-200/90 bg-white/95 sticky top-0 z-30 shadow-2xs backdrop-blur-md">
      <div class="mx-auto flex max-w-7xl items-center justify-between px-3.5 sm:px-6 h-14">
        
        <!-- Left: Brand & Compact Identity -->
        <div class="flex items-center gap-2.5 sm:gap-3 shrink-0">
          <div class="h-8.5 w-8.5 sm:h-9 sm:w-9 rounded-xl bg-slate-900 flex items-center justify-center text-white text-base sm:text-lg font-bold shadow-xs shrink-0">
            🧠
          </div>
          <div>
            <div class="flex items-center gap-1.5 sm:gap-2">
              <span class="text-sm sm:text-base font-extrabold tracking-tight text-slate-900">Second Brain</span>
              
              <!-- Subtle Role Badge -->
              <span
                v-if="userRole === 'owner'"
                class="rounded-full bg-purple-100 border border-purple-200 px-2 py-0.5 text-[10px] font-bold text-purple-800 flex items-center gap-1"
                title="Akses Administratif Pemilik"
              >
                <span>👑</span>
                <span class="hidden sm:inline">Pemilik</span>
              </span>
              <span
                v-else
                class="rounded-full bg-blue-50 border border-blue-200 px-2 py-0.5 text-[10px] font-bold text-blue-700 flex items-center gap-1"
                title="Mode Evaluasi Rekruter &amp; Hiring Manager"
              >
                <span>👔</span>
                <span class="hidden sm:inline">Mode Rekruter</span>
              </span>
            </div>
            <p class="text-[10px] text-slate-400 hidden sm:block truncate max-w-[200px]">
              Frans Alwan Purba · S2 AI UGM
            </p>
          </div>
        </div>

        <!-- Center: Omnibar Command Palette Trigger (Desktop only) -->
        <button
          type="button"
          @click="showCommandPalette = true"
          class="hidden md:flex items-center justify-between w-64 lg:w-72 xl:w-80 h-9 px-3 rounded-xl border border-slate-200 bg-slate-50/80 hover:bg-slate-100 hover:border-slate-300 text-slate-400 hover:text-slate-600 transition-all text-xs cursor-pointer shadow-2xs group"
          title="Buka Command Palette &amp; Pencarian Cepat (Ctrl+K)"
        >
          <span class="flex items-center gap-2 truncate">
            <span class="text-slate-400 group-hover:text-indigo-600 transition-colors">🔍</span>
            <span class="text-slate-500 font-medium truncate">Quick Command &amp; RAG...</span>
          </span>
          <kbd class="ml-1.5 rounded-md bg-white px-1.5 py-0.5 text-[10px] font-mono font-bold text-slate-500 border border-slate-200 shadow-2xs shrink-0">Ctrl+K</kbd>
        </button>

        <!-- Right (Desktop Action Buttons) -->
        <div class="hidden md:flex items-center gap-2">
          <!-- Recruiter Tour Button -->
          <button
            v-if="userRole === 'recruiter'"
            type="button"
            @click="handleOpenRecruiterTour"
            class="h-8.5 rounded-lg bg-amber-50 border border-amber-200 px-2.5 text-xs font-bold text-amber-800 flex items-center gap-1 hover:bg-amber-100 transition-colors cursor-pointer shadow-2xs whitespace-nowrap"
            title="Walkthrough Interaktif 60 Detik untuk Recruiter"
          >
            <span>✨ Tour 60s</span>
          </button>

          <!-- In-App Notification Center -->
          <NotificationCenter
            v-if="currentUserId"
            :user-id="currentUserId"
            :tasks="tasks"
            :habits="habits"
            :habit-logs="habitLogs"
            :profile="profile"
            :active-timer="activeTimer"
            @navigate-tab="handleTabNavigate"
          />

          <!-- Tanya AI Primary Button -->
          <button
            type="button"
            @click="handleOpenBrainRag"
            class="h-8.5 inline-flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 px-3 text-xs font-bold text-white hover:from-purple-500 hover:to-indigo-500 transition-all shadow-xs shadow-purple-600/20 whitespace-nowrap cursor-pointer"
            title="Tanya AI &amp; Semantic Search (pgvector)"
          >
            <span>🧠</span>
            <span>Tanya AI</span>
          </button>

          <!-- AI Governance Button -->
          <button
            type="button"
            @click="handleOpenPrivacy('governance')"
            class="h-8.5 inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 hover:text-indigo-600 hover:border-slate-300 transition-all shadow-2xs whitespace-nowrap cursor-pointer shrink-0"
            title="Pusat Tata Kelola AI, Keamanan &amp; Model Cards (OWASP LLM Defense)"
          >
            <span>🛡️</span>
            <span class="hidden xl:inline">AI Governance</span>
          </button>

          <!-- Desktop Settings & User Menu Dropdown -->
          <div class="relative desktop-menu-container">
            <button
              type="button"
              @click.stop="showDesktopMenu = !showDesktopMenu"
              class="h-8.5 inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 text-xs font-medium text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-colors shadow-2xs cursor-pointer"
              title="Menu Tambahan &amp; Opsi Akun"
            >
              <span>⚙️</span>
              <span class="text-[10px] text-slate-400">▼</span>
            </button>

            <!-- Dropdown Menu Box -->
            <div
              v-if="showDesktopMenu"
              class="absolute right-0 mt-1.5 w-60 rounded-2xl border border-slate-200 bg-white p-2 shadow-xl z-50 text-xs animate-in fade-in zoom-in-95 duration-150"
            >
              <div class="px-2.5 py-2 border-b border-slate-100 text-[11px] text-slate-500">
                <div class="font-bold text-slate-800 truncate">{{ profile?.full_name || 'Pengguna' }}</div>
                <div class="text-[10px] text-slate-400 truncate">{{ userEmail }}</div>
              </div>

              <div class="py-1 space-y-0.5">
                <button
                  type="button"
                  @click="handleOpenTechSpecs(); showDesktopMenu = false"
                  class="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg hover:bg-slate-50 text-slate-700 font-medium text-left cursor-pointer transition-colors"
                >
                  <span>🛠️</span>
                  <span>Tech Specs &amp; Arsitektur</span>
                </button>
                <button
                  type="button"
                  @click="handleOpenPrivacy('adrs'); showDesktopMenu = false"
                  class="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg hover:bg-slate-50 text-slate-700 font-medium text-left cursor-pointer transition-colors"
                >
                  <span>📁</span>
                  <span>Architectural Decision Records</span>
                </button>
                <div v-if="profile" class="px-2.5 py-1.5 text-[11px] text-slate-500 flex items-center justify-between bg-slate-50 rounded-lg">
                  <span>Ritme Sirkadian:</span>
                  <span class="font-mono font-semibold text-slate-700">☀️ {{ profile.brief_time?.slice(0, 5) }} | 🌙 {{ profile.night_cutoff_time?.slice(0, 5) }}</span>
                </div>
              </div>

              <div class="pt-1 border-t border-slate-100">
                <button
                  type="button"
                  @click="handleLogout"
                  class="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg hover:bg-rose-50 text-rose-600 font-semibold text-left cursor-pointer transition-colors"
                >
                  <span>🚪</span>
                  <span>{{ userRole === 'recruiter' ? 'Keluar Mode Demo' : 'Keluar (Logout)' }}</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Mobile Header Controls (Right side, Compact) -->
        <div class="flex md:hidden items-center gap-1.5">
          <!-- Search / Command Palette Icon -->
          <button
            type="button"
            @click="showCommandPalette = true"
            class="h-8.5 w-8.5 flex items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 shadow-2xs cursor-pointer"
            title="Pencarian Cepat (Ctrl+K)"
          >
            <span>🔍</span>
          </button>

          <!-- Tanya AI Compact Button -->
          <button
            type="button"
            @click="handleOpenBrainRag"
            class="h-8.5 px-2.5 flex items-center gap-1 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 text-white text-xs font-bold shadow-2xs shadow-purple-600/20 cursor-pointer"
            title="Tanya AI"
          >
            <span>🧠</span>
            <span class="text-[11px]">AI</span>
          </button>

          <!-- In-App Notification Center -->
          <NotificationCenter
            v-if="currentUserId"
            :user-id="currentUserId"
            :tasks="tasks"
            :habits="habits"
            :habit-logs="habitLogs"
            :profile="profile"
            :active-timer="activeTimer"
            @navigate-tab="handleTabNavigate"
          />

          <!-- Mobile Hamburger Toggle -->
          <button
            type="button"
            @click="showMobileDrawer = !showMobileDrawer"
            class="h-8.5 w-8.5 flex items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 shadow-2xs cursor-pointer text-sm font-bold"
            :class="showMobileDrawer ? 'bg-slate-100 border-slate-300' : ''"
            title="Buka Menu"
          >
            <span v-if="!showMobileDrawer">☰</span>
            <span v-else>✕</span>
          </button>
        </div>
      </div>

      <!-- Desktop Secondary Navigation Tabs Bar (Clean, Centered, Scrollable with Gradient Fade) -->
      <div class="hidden md:block border-t border-slate-100 bg-white relative">
        <div class="mx-auto flex max-w-7xl items-center gap-1.5 px-4 sm:px-6 overflow-x-auto no-scrollbar py-1">
          <button
            @click="activeTab = 'overview'"
            class="flex items-center gap-1.5 border-b-2 py-2 px-3 text-xs font-bold transition-all whitespace-nowrap cursor-pointer shrink-0"
            :class="activeTab === 'overview' ? 'border-slate-900 text-slate-900 bg-slate-50/60 rounded-t-lg' : 'border-transparent text-slate-500 hover:text-slate-900'"
          >
            <span>🏠</span>
            <span>Ringkasan AI</span>
          </button>

          <button
            @click="activeTab = 'rag'"
            class="flex items-center gap-1.5 border-b-2 py-2 px-3 text-xs font-bold transition-all whitespace-nowrap cursor-pointer shrink-0"
            :class="activeTab === 'rag' ? 'border-purple-600 text-purple-700 bg-purple-50/40 rounded-t-lg' : 'border-transparent text-slate-500 hover:text-slate-900'"
          >
            <span>🧠</span>
            <span>Next-Gen RAG</span>
            <span class="rounded-full bg-purple-100 px-1.5 py-0.2 text-[9px] font-bold text-purple-800">CRAG</span>
          </button>

          <button
            @click="activeTab = 'vlm'"
            class="flex items-center gap-1.5 border-b-2 py-2 px-3 text-xs font-bold transition-all whitespace-nowrap cursor-pointer shrink-0"
            :class="activeTab === 'vlm' ? 'border-blue-600 text-blue-700 bg-blue-50/40 rounded-t-lg' : 'border-transparent text-slate-500 hover:text-slate-900'"
          >
            <span>📸</span>
            <span>Multimodal VLM</span>
            <span class="rounded-full bg-blue-100 px-1.5 py-0.2 text-[9px] font-bold text-blue-800">Gemini 2.0</span>
          </button>

          <button
            @click="activeTab = 'mlradar'"
            class="flex items-center gap-1.5 border-b-2 py-2 px-3 text-xs font-bold transition-all whitespace-nowrap cursor-pointer shrink-0"
            :class="activeTab === 'mlradar' ? 'border-cyan-600 text-cyan-700 bg-cyan-50/40 rounded-t-lg' : 'border-transparent text-slate-500 hover:text-slate-900'"
          >
            <span>📊</span>
            <span>ML Radar</span>
            <span class="rounded-full bg-cyan-100 px-1.5 py-0.2 text-[9px] font-bold text-cyan-800">&lt;2ms</span>
          </button>

          <button
            @click="activeTab = 'evals'"
            class="flex items-center gap-1.5 border-b-2 py-2 px-3 text-xs font-bold transition-all whitespace-nowrap cursor-pointer shrink-0"
            :class="activeTab === 'evals' ? 'border-emerald-600 text-emerald-700 bg-emerald-50/40 rounded-t-lg' : 'border-transparent text-slate-500 hover:text-slate-900'"
          >
            <span>🏆</span>
            <span>AI Quality Flywheel</span>
            <span class="rounded-full bg-emerald-100 px-1.5 py-0.2 text-[9px] font-bold text-emerald-800">81.8</span>
          </button>

          <button
            @click="activeTab = 'research'"
            class="flex items-center gap-1.5 border-b-2 py-2 px-3 text-xs font-bold transition-all whitespace-nowrap cursor-pointer shrink-0"
            :class="activeTab === 'research' ? 'border-indigo-600 text-indigo-700 bg-indigo-50/40 rounded-t-lg' : 'border-transparent text-slate-500 hover:text-slate-900'"
          >
            <span>🔬</span>
            <span>Riset &amp; Thesis</span>
            <span v-if="userRole === 'recruiter'" class="rounded-full bg-rose-100 px-1.5 py-0.2 text-[9px] font-bold text-rose-700 flex items-center gap-0.5">🔒 Privat</span>
            <span v-else class="rounded-full bg-indigo-100 px-1.5 py-0.2 text-[9px] font-bold text-indigo-800">IDCS XAI</span>
          </button>

          <button
            @click="activeTab = 'agentops'"
            class="flex items-center gap-1.5 border-b-2 py-2 px-3 text-xs font-bold transition-all whitespace-nowrap cursor-pointer shrink-0"
            :class="activeTab === 'agentops' ? 'border-slate-800 text-slate-900 bg-slate-100 rounded-t-lg' : 'border-transparent text-slate-500 hover:text-slate-900'"
          >
            <span>🔌</span>
            <span>MCP &amp; Telemetry</span>
            <span class="rounded-full bg-slate-200 px-1.5 py-0.2 text-[9px] font-bold text-slate-800">SSE</span>
          </button>
        </div>
        <!-- Right side gradient fade for overflow indication -->
        <div class="pointer-events-none absolute right-0 top-0 bottom-0 w-8 bg-gradient-to-l from-white to-transparent"></div>
      </div>
    </header>

    <!-- Mobile Slide-Out Navigation Drawer (Modern Native App Experience) -->
    <div v-if="showMobileDrawer" class="md:hidden fixed inset-0 z-50 flex">
      <!-- Backdrop -->
      <div
        class="fixed inset-0 bg-slate-950/60 backdrop-blur-xs transition-opacity animate-in fade-in duration-150"
        @click="showMobileDrawer = false"
      ></div>

      <!-- Slide-over Drawer Panel -->
      <div class="relative ml-auto w-full max-w-xs bg-white h-full shadow-2xl flex flex-col justify-between p-5 overflow-y-auto animate-in slide-in-from-right duration-200 z-10">
        <div class="space-y-5">
          <!-- Drawer Top Header -->
          <div class="flex items-center justify-between pb-3 border-b border-slate-100">
            <div class="flex items-center gap-2.5">
              <div class="h-9 w-9 rounded-xl bg-slate-900 text-white flex items-center justify-center text-lg font-bold">
                🧠
              </div>
              <div>
                <div class="font-black text-sm text-slate-900">Second Brain</div>
                <div class="text-[10px] text-slate-400">AI Engineering OS</div>
              </div>
            </div>
            <button
              type="button"
              @click="showMobileDrawer = false"
              class="h-8 w-8 rounded-lg bg-slate-100 text-slate-500 hover:text-slate-900 flex items-center justify-center font-bold text-sm cursor-pointer"
            >
              ✕
            </button>
          </div>

          <!-- User Identity Card in Drawer -->
          <div class="p-3 rounded-2xl bg-slate-50 border border-slate-200/80 space-y-1.5">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-slate-800 truncate">
                {{ profile?.full_name || 'Pengguna' }}
              </span>
              <span
                v-if="userRole === 'owner'"
                class="rounded-full bg-purple-100 text-purple-800 px-2 py-0.5 text-[9px] font-bold"
              >
                👑 Pemilik
              </span>
              <span
                v-else
                class="rounded-full bg-blue-100 text-blue-800 px-2 py-0.5 text-[9px] font-bold"
              >
                👔 Rekruter
              </span>
            </div>
            <p class="text-[11px] text-slate-500 truncate">{{ userEmail }}</p>

            <button
              v-if="userRole === 'recruiter'"
              type="button"
              @click="handleOpenRecruiterTour(); showMobileDrawer = false"
              class="w-full mt-2 py-1.5 px-2.5 rounded-xl bg-amber-500 text-white font-bold text-xs flex items-center justify-center gap-1.5 shadow-xs cursor-pointer"
            >
              <span>✨</span>
              <span>Buka Demo Tour (60 Detik)</span>
            </button>
          </div>

          <!-- Quick Action Buttons -->
          <div class="grid grid-cols-2 gap-2">
            <button
              type="button"
              @click="handleOpenBrainRag(); showMobileDrawer = false"
              class="p-2.5 rounded-xl bg-purple-50 text-purple-900 border border-purple-200/70 font-bold text-xs flex items-center gap-2 cursor-pointer"
            >
              <span>🧠</span>
              <span>Tanya AI</span>
            </button>
            <button
              type="button"
              @click="showCommandPalette = true; showMobileDrawer = false"
              class="p-2.5 rounded-xl bg-slate-100 text-slate-800 border border-slate-200 font-bold text-xs flex items-center gap-2 cursor-pointer"
            >
              <span>🔍</span>
              <span>Cmd Palette</span>
            </button>
          </div>

          <!-- Navigation Links List -->
          <div class="space-y-1">
            <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400 px-2">Modul AI Engineering:</span>
            
            <button
              type="button"
              @click="handleMobileNav('overview')"
              class="w-full flex items-center justify-between p-2.5 rounded-xl text-xs font-semibold cursor-pointer transition-colors"
              :class="activeTab === 'overview' ? 'bg-slate-900 text-white font-bold' : 'text-slate-700 hover:bg-slate-100'"
            >
              <span class="flex items-center gap-2"><span>🏠</span><span>Ringkasan AI</span></span>
              <span class="text-[10px] opacity-70">Showcase</span>
            </button>

            <button
              type="button"
              @click="handleMobileNav('rag')"
              class="w-full flex items-center justify-between p-2.5 rounded-xl text-xs font-semibold cursor-pointer transition-colors"
              :class="activeTab === 'rag' ? 'bg-purple-600 text-white font-bold' : 'text-slate-700 hover:bg-slate-100'"
            >
              <span class="flex items-center gap-2"><span>🧠</span><span>Next-Gen RAG</span></span>
              <span class="text-[9px] rounded px-1.5 py-0.2" :class="activeTab === 'rag' ? 'bg-purple-700 text-white' : 'bg-purple-100 text-purple-800'">CRAG</span>
            </button>

            <button
              type="button"
              @click="handleMobileNav('vlm')"
              class="w-full flex items-center justify-between p-2.5 rounded-xl text-xs font-semibold cursor-pointer transition-colors"
              :class="activeTab === 'vlm' ? 'bg-blue-600 text-white font-bold' : 'text-slate-700 hover:bg-slate-100'"
            >
              <span class="flex items-center gap-2"><span>📸</span><span>Multimodal VLM</span></span>
              <span class="text-[9px] rounded px-1.5 py-0.2" :class="activeTab === 'vlm' ? 'bg-blue-700 text-white' : 'bg-blue-100 text-blue-800'">Gemini 2.0</span>
            </button>

            <button
              type="button"
              @click="handleMobileNav('mlradar')"
              class="w-full flex items-center justify-between p-2.5 rounded-xl text-xs font-semibold cursor-pointer transition-colors"
              :class="activeTab === 'mlradar' ? 'bg-cyan-600 text-white font-bold' : 'text-slate-700 hover:bg-slate-100'"
            >
              <span class="flex items-center gap-2"><span>📊</span><span>Classical ML Radar</span></span>
              <span class="text-[9px] rounded px-1.5 py-0.2" :class="activeTab === 'mlradar' ? 'bg-cyan-700 text-white' : 'bg-cyan-100 text-cyan-800'">&lt;2ms</span>
            </button>

            <button
              type="button"
              @click="handleMobileNav('evals')"
              class="w-full flex items-center justify-between p-2.5 rounded-xl text-xs font-semibold cursor-pointer transition-colors"
              :class="activeTab === 'evals' ? 'bg-emerald-600 text-white font-bold' : 'text-slate-700 hover:bg-slate-100'"
            >
              <span class="flex items-center gap-2"><span>🏆</span><span>AI Quality Flywheel</span></span>
              <span class="text-[9px] rounded px-1.5 py-0.2" :class="activeTab === 'evals' ? 'bg-emerald-700 text-white' : 'bg-emerald-100 text-emerald-800'">81.8</span>
            </button>

            <button
              type="button"
              @click="handleMobileNav('research')"
              class="w-full flex items-center justify-between p-2.5 rounded-xl text-xs font-semibold cursor-pointer transition-colors"
              :class="activeTab === 'research' ? 'bg-indigo-600 text-white font-bold' : 'text-slate-700 hover:bg-slate-100'"
            >
              <span class="flex items-center gap-2"><span>🔬</span><span>Riset &amp; Thesis S2</span></span>
              <span v-if="userRole === 'recruiter'" class="text-[9px] rounded bg-rose-100 text-rose-700 px-1.5 py-0.2 font-bold">🔒 Privat</span>
              <span v-else class="text-[9px] rounded bg-indigo-100 text-indigo-800 px-1.5 py-0.2 font-bold">IDCS</span>
            </button>

            <button
              type="button"
              @click="handleMobileNav('agentops')"
              class="w-full flex items-center justify-between p-2.5 rounded-xl text-xs font-semibold cursor-pointer transition-colors"
              :class="activeTab === 'agentops' ? 'bg-slate-900 text-white font-bold' : 'text-slate-700 hover:bg-slate-100'"
            >
              <span class="flex items-center gap-2"><span>🔌</span><span>MCP &amp; Telemetry</span></span>
              <span class="text-[9px] rounded bg-slate-200 text-slate-800 px-1.5 py-0.2 font-bold">SSE</span>
            </button>
          </div>

          <!-- Governance & Architecture Settings -->
          <div class="pt-2 border-t border-slate-100 space-y-1">
            <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400 px-2">Keamanan &amp; Spesifikasi:</span>

            <button
              type="button"
              @click="handleOpenPrivacy('governance'); showMobileDrawer = false"
              class="w-full flex items-center gap-2.5 p-2 rounded-xl text-xs font-semibold text-slate-700 hover:bg-slate-100 cursor-pointer"
            >
              <span>🛡️</span>
              <span>Pusat Tata Kelola AI (OWASP Defense)</span>
            </button>

            <button
              type="button"
              @click="handleOpenTechSpecs(); showMobileDrawer = false"
              class="w-full flex items-center gap-2.5 p-2 rounded-xl text-xs font-semibold text-slate-700 hover:bg-slate-100 cursor-pointer"
            >
              <span>🛠️</span>
              <span>Spesifikasi Polyglot &amp; Diagram</span>
            </button>
          </div>
        </div>

        <!-- Drawer Footer: Logout -->
        <div class="pt-4 border-t border-slate-200">
          <button
            type="button"
            @click="handleLogout"
            :disabled="loggingOut"
            class="w-full py-2.5 px-4 rounded-xl border border-rose-200 bg-rose-50 text-rose-600 font-bold text-xs flex items-center justify-center gap-2 hover:bg-rose-100 transition-colors cursor-pointer"
          >
            <span>🚪</span>
            <span>{{ userRole === 'recruiter' ? 'Keluar Mode Demo' : (loggingOut ? 'Keluar...' : 'Logout') }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Mobile Native Bottom Navigation Dock (Fixed at bottom on < md) -->
    <nav class="md:hidden fixed bottom-0 left-0 right-0 z-30 bg-white/95 backdrop-blur-md border-t border-slate-200/90 px-2 py-1 flex items-center justify-around shadow-lg">
      <button
        type="button"
        @click="activeTab = 'overview'"
        class="flex flex-col items-center justify-center flex-1 py-1 rounded-xl transition-all cursor-pointer"
        :class="activeTab === 'overview' ? 'text-indigo-600 font-extrabold' : 'text-slate-500 hover:text-slate-800 font-medium'"
      >
        <span class="text-lg">🏠</span>
        <span class="text-[10px]">Ringkasan</span>
      </button>

      <button
        type="button"
        @click="activeTab = 'rag'"
        class="flex flex-col items-center justify-center flex-1 py-1 rounded-xl transition-all cursor-pointer"
        :class="activeTab === 'rag' ? 'text-purple-600 font-extrabold' : 'text-slate-500 hover:text-slate-800 font-medium'"
      >
        <span class="text-lg">🧠</span>
        <span class="text-[10px]">CRAG</span>
      </button>

      <button
        type="button"
        @click="activeTab = 'mlradar'"
        class="flex flex-col items-center justify-center flex-1 py-1 rounded-xl transition-all cursor-pointer"
        :class="activeTab === 'mlradar' ? 'text-cyan-600 font-extrabold' : 'text-slate-500 hover:text-slate-800 font-medium'"
      >
        <span class="text-lg">📊</span>
        <span class="text-[10px]">Radar</span>
      </button>

      <button
        type="button"
        @click="activeTab = 'evals'"
        class="flex flex-col items-center justify-center flex-1 py-1 rounded-xl transition-all cursor-pointer"
        :class="activeTab === 'evals' ? 'text-emerald-600 font-extrabold' : 'text-slate-500 hover:text-slate-800 font-medium'"
      >
        <span class="text-lg">🏆</span>
        <span class="text-[10px]">Evals</span>
      </button>

      <button
        type="button"
        @click="showMobileDrawer = true"
        class="flex flex-col items-center justify-center flex-1 py-1 rounded-xl transition-all cursor-pointer"
        :class="showMobileDrawer ? 'text-slate-900 font-extrabold' : 'text-slate-500 hover:text-slate-800 font-medium'"
      >
        <span class="text-lg">☰</span>
        <span class="text-[10px]">Menu</span>
      </button>
    </nav>

    <main class="mx-auto max-w-6xl px-4 pt-6 sm:px-6 space-y-6">
      <!-- Tab 1: Next-Gen RAG & RAPTOR -->
      <RagExplorerTab
        v-if="activeTab === 'rag' && currentUserId"
        :user-id="currentUserId"
      />

      <!-- Tab 2: Multimodal VLM -->
      <MultimodalVlmTab
        v-else-if="activeTab === 'vlm' && currentUserId"
        :user-id="currentUserId"
        :user-email="userEmail"
      />

      <!-- Tab 3: Classical ML Radar -->
      <MlRadarTab
        v-else-if="activeTab === 'mlradar' && currentUserId"
        :user-id="currentUserId"
        :user-email="userEmail"
      />

      <!-- Tab 4: AI Quality Flywheel -->
      <AiEvalsTab
        v-else-if="activeTab === 'evals' && currentUserId"
        :user-id="currentUserId"
      />

      <!-- Tab 5: Riset & Tesis S2 (Akses Terproteksi Khusus Pemilik) -->
      <template v-else-if="activeTab === 'research'">
        <!-- Tampilan Terkunci untuk Rekruter / Mode Demo -->
        <div v-if="userRole === 'recruiter'" class="rounded-3xl border border-slate-200/90 bg-white p-6 sm:p-10 shadow-xs max-w-3xl mx-auto space-y-6">
          <div class="text-center space-y-3">
            <div class="inline-flex h-16 w-16 items-center justify-center rounded-3xl bg-rose-50 border border-rose-200 text-rose-600 text-3xl shadow-sm">
              🔒
            </div>
            
            <div class="space-y-1">
              <div class="inline-flex items-center gap-1.5 rounded-full bg-rose-50 border border-rose-200 px-3 py-0.5 text-xs font-bold text-rose-700">
                <span>Area Terproteksi</span>
                <span>•</span>
                <span>Riset &amp; Tesis Pribadi Mahasiswa</span>
              </div>
              <h2 class="text-xl sm:text-2xl font-black tracking-tight text-slate-900">
                Akses Dibatasi: Naskah Tesis S2 (FMIPA UGM)
              </h2>
              <p class="text-xs sm:text-sm text-slate-500 max-w-xl mx-auto leading-relaxed">
                Modul ini memuat naskah aktif tesis <em>Instance-Dependent Cost-Sensitive Explainable AI</em>, notulensi konsultasi dosen pembimbing (Afiahayati Ph.D &amp; Prof. Sri Hartati), draf proposal internal, dan token repositori privat Frans Alwan Purba.
              </p>
            </div>
          </div>

          <!-- Penjelasan RBAC & Portofolio Rekruter -->
          <div class="rounded-2xl bg-slate-50 border border-slate-200 p-4 sm:p-5 space-y-3 text-xs text-slate-700">
            <div class="flex items-center gap-2 text-slate-900 font-bold">
              <span>🛡️</span>
              <span>Kebijakan Privasi Portofolio:</span>
            </div>
            <p class="leading-relaxed">
              Sesuai desain keamanan sistem, <strong>Akun Demo Rekruter</strong> hanya diberikan akses evaluasi ke modul-modul rekayasa AI produksi tanpa mengekspos naskah riset akademik personal pemilik.
            </p>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-2 border-t border-slate-200">
              <button
                type="button"
                @click="activeTab = 'rag'"
                class="flex items-center gap-2.5 p-2.5 rounded-xl bg-white border border-slate-200 hover:border-purple-300 hover:bg-purple-50/40 text-left transition-all cursor-pointer"
              >
                <span class="text-purple-600 font-bold text-base">🧠</span>
                <div>
                  <div class="font-bold text-slate-800 text-[11px]">Next-Gen CRAG</div>
                  <div class="text-[10px] text-slate-500">RAPTOR GMM &amp; Reranker ↗</div>
                </div>
              </button>
              <button
                type="button"
                @click="activeTab = 'vlm'"
                class="flex items-center gap-2.5 p-2.5 rounded-xl bg-white border border-slate-200 hover:border-blue-300 hover:bg-blue-50/40 text-left transition-all cursor-pointer"
              >
                <span class="text-blue-600 font-bold text-base">📸</span>
                <div>
                  <div class="font-bold text-slate-800 text-[11px]">Multimodal VLM</div>
                  <div class="text-[10px] text-slate-500">Gemini 2.0 Flash Visual AI ↗</div>
                </div>
              </button>
              <button
                type="button"
                @click="activeTab = 'mlradar'"
                class="flex items-center gap-2.5 p-2.5 rounded-xl bg-white border border-slate-200 hover:border-cyan-300 hover:bg-cyan-50/40 text-left transition-all cursor-pointer"
              >
                <span class="text-cyan-600 font-bold text-base">📊</span>
                <div>
                  <div class="font-bold text-slate-800 text-[11px]">Classical ML Radar</div>
                  <div class="text-[10px] text-slate-500">Isolation Forest &lt; 2ms ↗</div>
                </div>
              </button>
              <button
                type="button"
                @click="activeTab = 'evals'"
                class="flex items-center gap-2.5 p-2.5 rounded-xl bg-white border border-slate-200 hover:border-emerald-300 hover:bg-emerald-50/40 text-left transition-all cursor-pointer"
              >
                <span class="text-emerald-600 font-bold text-base">🏆</span>
                <div>
                  <div class="font-bold text-slate-800 text-[11px]">AI Quality Flywheel</div>
                  <div class="text-[10px] text-slate-500">Benchmark 81.8 &amp; RAG Triad ↗</div>
                </div>
              </button>
            </div>
          </div>

          <!-- Quick Actions & Inline Owner Unlock -->
          <div class="pt-2 flex flex-col sm:flex-row items-center justify-between gap-3">
            <button
              type="button"
              @click="activeTab = 'overview'"
              class="w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 text-xs font-bold text-white hover:bg-black transition-colors cursor-pointer shadow-xs"
            >
              <span>🏠</span>
              <span>Kembali ke Ringkasan AI</span>
            </button>

            <!-- Inline Master Key Unlock (Untuk Frans jika ingin buka akses langsung di tab ini) -->
            <div class="w-full sm:w-auto flex items-center gap-2">
              <input
                v-model="ownerUnlockInput"
                type="password"
                placeholder="Master passkey pemilik..."
                @keydown.enter="handleUnlockAsOwner"
                class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-800 placeholder-slate-400 focus:border-purple-500 focus:outline-none w-full sm:w-44"
              />
              <button
                type="button"
                @click="handleUnlockAsOwner"
                class="inline-flex items-center gap-1 rounded-xl bg-purple-600 px-3 py-2 text-xs font-bold text-white hover:bg-purple-700 transition-colors cursor-pointer shrink-0 shadow-xs"
              >
                <span>🔑</span>
                <span>Buka</span>
              </button>
            </div>
          </div>
          <p v-if="ownerUnlockError" class="text-[11px] text-rose-600 font-medium text-right">{{ ownerUnlockError }}</p>
        </div>

        <!-- Tampilan Akses Penuh untuk Pemilik (Frans Alwan Purba) -->
        <ResearchTab
          v-else-if="currentUserId"
          :user-id="currentUserId"
        />
      </template>

      <!-- Tab 6: MCP Server & Telemetry -->
      <AgentOpsTab
        v-else-if="activeTab === 'agentops' && currentUserId"
        :user-id="currentUserId"
        :user-email="userEmail"
      />

      <!-- Shimmer Skeleton Loading State -->
      <div v-if="loading" class="space-y-6 animate-pulse">
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-5">
          <div class="lg:col-span-8 h-44 rounded-3xl bg-slate-200/80"></div>
          <div class="lg:col-span-4 h-44 rounded-3xl bg-slate-200/80"></div>
        </div>
        <div class="h-16 rounded-2xl bg-slate-200/60"></div>
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div class="lg:col-span-7 h-96 rounded-2xl bg-slate-200/70"></div>
          <div class="lg:col-span-5 h-96 rounded-2xl bg-slate-200/70"></div>
        </div>
      </div>

      <!-- Tab Overview (Default): Bento Grid 2.0 -->
      <div v-else-if="activeTab === 'overview'" class="space-y-6">
        <!-- Bento Top Row: Hero Daily Brief (8 cols) + Polyglot Telemetry Cluster (4 cols) -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-5">
          <!-- Hero Brief (8 Cols) -->
          <div class="lg:col-span-8 flex flex-col justify-between">
            <DailyBriefCard
              v-if="profileLoaded"
              :full-name="profile?.full_name?.replace(' (Demo Mode)', '')"
              :email="userEmail"
              :brief-time="profile?.brief_time"
              :night-cutoff-time="profile?.night_cutoff_time"
              :tasks="tasks"
              :time-logs="timeLogs"
              :habits="habits"
              :habit-logs="habitLogs"
              @navigate-tab="handleTabNavigate"
              @toggle-task="handleToggleTask"
            />
          </div>

          <!-- Polyglot Telemetry Cluster Card (4 Cols) -->
          <div class="lg:col-span-4 rounded-3xl border border-slate-200/90 bg-white p-5 shadow-xs flex flex-col justify-between">
            <div>
              <div class="flex items-center justify-between pb-3 border-b border-slate-100">
                <div class="flex items-center gap-2">
                  <span class="text-base">⚡</span>
                  <h3 class="text-xs font-bold uppercase tracking-wider text-slate-800">System Telemetry</h3>
                </div>
                <span class="inline-flex items-center gap-1 rounded-full bg-emerald-50 border border-emerald-200 px-2 py-0.5 text-[10px] font-bold text-emerald-700">
                  <span class="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                  <span>Cluster Active</span>
                </span>
              </div>

              <!-- Cluster Nodes -->
              <div class="mt-3 space-y-2 text-xs">
                <div class="flex items-center justify-between p-2 rounded-xl bg-slate-50 border border-slate-100">
                  <div class="flex items-center gap-1.5">
                    <span class="h-1.5 w-1.5 rounded-full bg-cyan-500"></span>
                    <span class="font-bold text-slate-800">Go Worker (:8085)</span>
                  </div>
                  <span class="rounded bg-cyan-100/70 text-cyan-900 px-1.5 py-0.2 text-[10px] font-bold">Goroutines Pool</span>
                </div>

                <div class="flex items-center justify-between p-2 rounded-xl bg-slate-50 border border-slate-100">
                  <div class="flex items-center gap-1.5">
                    <span class="h-1.5 w-1.5 rounded-full bg-purple-500"></span>
                    <span class="font-bold text-slate-800">FastAPI &amp; Gemini (:8000)</span>
                  </div>
                  <span class="rounded bg-purple-100/70 text-purple-900 px-1.5 py-0.2 text-[10px] font-bold">RAG Engine</span>
                </div>

                <div class="flex items-center justify-between p-2 rounded-xl bg-slate-50 border border-slate-100">
                  <div class="flex items-center gap-1.5">
                    <span class="h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
                    <span class="font-bold text-slate-800">PostgreSQL pgvector</span>
                  </div>
                  <span class="rounded bg-emerald-100/70 text-emerald-900 px-1.5 py-0.2 text-[10px] font-bold">768-D HNSW</span>
                </div>
              </div>

              <!-- Academic Git Sync Quick Pills -->
              <div class="mt-2.5 pt-2.5 border-t border-slate-100">
                <span class="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">Academic Git Pipeline:</span>
                <div class="flex flex-wrap gap-1">
                  <span class="rounded-md bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-700">📦 materi-kuliah</span>
                  <span class="rounded-md bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-700">📝 manuscripts</span>
                  <span class="rounded-md bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-700">🧪 experiments</span>
                </div>
              </div>
            </div>

            <button
              type="button"
              @click="activeTab = 'agentops'"
              class="mt-3.5 w-full rounded-xl bg-slate-900 py-2 text-xs font-bold text-white hover:bg-slate-800 transition-colors text-center cursor-pointer shadow-2xs flex items-center justify-center gap-1.5"
            >
              <span>⚡</span>
              <span>Buka Agent Ops &amp; Audit Logs</span>
              <span>➔</span>
            </button>
          </div>
        </div>

        <!-- AI Engineer Portfolio Showcase Grid (Fase 1 s.d. 5) -->
        <div class="rounded-3xl border border-slate-200/90 bg-white p-5 shadow-xs space-y-3">
          <div class="flex items-center justify-between pb-2 border-b border-slate-100">
            <div class="flex items-center gap-2">
              <span class="text-base">🚀</span>
              <h3 class="text-xs font-bold uppercase tracking-wider text-slate-800">
                Core AI Engineering Showcase (Fase 1 s.d. 5)
              </h3>
            </div>
            <span class="rounded-md bg-purple-50 border border-purple-200 text-purple-800 text-[10px] font-bold px-2 py-0.5">
              Production AI Stack
            </span>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 pt-1">
            <!-- 1. MCP -->
            <button
              type="button"
              @click="activeTab = 'agentops'"
              class="text-left rounded-2xl border border-indigo-100 bg-gradient-to-br from-indigo-50/60 to-white p-3.5 hover:border-indigo-300 hover:shadow-xs transition-all cursor-pointer group"
            >
              <div class="flex items-center justify-between">
                <span class="text-base group-hover:scale-110 transition-transform">🔌</span>
                <span class="rounded bg-indigo-100 text-indigo-900 text-[9px] font-bold px-1.5 py-0.2">FASE 1</span>
              </div>
              <h4 class="mt-2 text-xs font-bold text-slate-900">Model Context Protocol</h4>
              <p class="mt-1 text-[11px] text-slate-500 line-clamp-2">Anthropic standard SSE /mcp/sse &amp; 8 tool schemas untuk Claude Desktop/Cursor.</p>
              <span class="mt-2.5 inline-block text-[10px] font-bold text-indigo-600 group-hover:underline">Buka MCP Ops ➔</span>
            </button>

            <!-- 2. CRAG + RAPTOR -->
            <button
              type="button"
              @click="activeTab = 'rag'"
              class="text-left rounded-2xl border border-purple-100 bg-gradient-to-br from-purple-50/60 to-white p-3.5 hover:border-purple-300 hover:shadow-xs transition-all cursor-pointer group"
            >
              <div class="flex items-center justify-between">
                <span class="text-base group-hover:scale-110 transition-transform">🧠</span>
                <span class="rounded bg-purple-100 text-purple-900 text-[9px] font-bold px-1.5 py-0.2">FASE 2</span>
              </div>
              <h4 class="mt-2 text-xs font-bold text-slate-900">Next-Gen CRAG &amp; RAPTOR</h4>
              <p class="mt-1 text-[11px] text-slate-500 line-clamp-2">GMM Hierarchical Clustering, HyDE Query Expansion &amp; Cross-Encoder Reranker.</p>
              <span class="mt-2.5 inline-block text-[10px] font-bold text-purple-600 group-hover:underline">Uji CRAG ➔</span>
            </button>

            <!-- 3. VLM -->
            <button
              type="button"
              @click="activeTab = 'vlm'"
              class="text-left rounded-2xl border border-blue-100 bg-gradient-to-br from-blue-50/60 to-white p-3.5 hover:border-blue-300 hover:shadow-xs transition-all cursor-pointer group"
            >
              <div class="flex items-center justify-between">
                <span class="text-base group-hover:scale-110 transition-transform">📸</span>
                <span class="rounded bg-blue-100 text-blue-900 text-[9px] font-bold px-1.5 py-0.2">FASE 3</span>
              </div>
              <h4 class="mt-2 text-xs font-bold text-slate-900">Multimodal VLM Intelligence</h4>
              <p class="mt-1 text-[11px] text-slate-500 line-clamp-2">Gemini 2.0 Flash VLM: Kurva konvergensi CatBoost &amp; OCR catatan tulisan tangan.</p>
              <span class="mt-2.5 inline-block text-[10px] font-bold text-blue-600 group-hover:underline">Analisis Visual ➔</span>
            </button>

            <!-- 4. ML Radar -->
            <button
              type="button"
              @click="activeTab = 'mlradar'"
              class="text-left rounded-2xl border border-cyan-100 bg-gradient-to-br from-cyan-50/60 to-white p-3.5 hover:border-cyan-300 hover:shadow-xs transition-all cursor-pointer group"
            >
              <div class="flex items-center justify-between">
                <span class="text-base group-hover:scale-110 transition-transform">📊</span>
                <span class="rounded bg-cyan-100 text-cyan-900 text-[9px] font-bold px-1.5 py-0.2">FASE 4</span>
              </div>
              <h4 class="mt-2 text-xs font-bold text-slate-900">Classical ML Anomaly Radar</h4>
              <p class="mt-1 text-[11px] text-slate-500 line-clamp-2">Isolation Forest &lt; 2ms deterministik + intervensi empatik otonom LLM bersyarat.</p>
              <span class="mt-2.5 inline-block text-[10px] font-bold text-cyan-700 group-hover:underline">Simulasi Radar ➔</span>
            </button>

            <!-- 5. Evals -->
            <button
              type="button"
              @click="activeTab = 'evals'"
              class="text-left rounded-2xl border border-emerald-100 bg-gradient-to-br from-emerald-50/60 to-white p-3.5 hover:border-emerald-300 hover:shadow-xs transition-all cursor-pointer group"
            >
              <div class="flex items-center justify-between">
                <span class="text-base group-hover:scale-110 transition-transform">🏆</span>
                <span class="rounded bg-emerald-100 text-emerald-900 text-[9px] font-bold px-1.5 py-0.2">FASE 5</span>
              </div>
              <h4 class="mt-2 text-xs font-bold text-slate-900">AI Quality Flywheel (Evals)</h4>
              <p class="mt-1 text-[11px] text-slate-500 line-clamp-2">81.8/100 Composite Score, 20 Golden Dataset, dan CI/CD regression testing.</p>
              <span class="mt-2.5 inline-block text-[10px] font-bold text-emerald-700 group-hover:underline">Inspeksi Evals ➔</span>
            </button>
          </div>
        </div>

        <!-- Focus Session Bar: Seamless Deep Work Controller -->
        <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div class="flex items-center gap-2.5">
            <div class="h-9 w-9 rounded-xl flex items-center justify-center shrink-0 text-base" :class="activeTimer ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-700'">
              {{ activeTimer ? '⚡' : '⏱️' }}
            </div>
            <div>
              <div class="flex items-center gap-2">
                <h4 class="text-xs font-bold text-slate-900">
                  {{ activeTimer ? `Fokus Aktif: ${activeTimer.project_name}` : 'Mulai Sesi Deep Work' }}
                </h4>
                <span v-if="activeTimer" class="rounded-full bg-emerald-100 px-2 py-0.2 text-[10px] font-bold text-emerald-800 animate-pulse">
                  Berjalan
                </span>
              </div>
              <p class="text-[11px] text-slate-500 mt-0.5">
                {{ activeTimer ? `Dimulai ${formatDateTime(activeTimer.started_at)} • Auto habit streak aktif` : `Total fokus hari ini: ${totalFocusMinutesToday} menit • Catatan tersimpan: ${notes.length} ide` }}
              </p>
            </div>
          </div>

          <div v-if="activeTimer">
            <button
              type="button"
              @click="handleStopTimer(activeTimer.id)"
              :disabled="stoppingTimer"
              class="rounded-xl bg-rose-600 px-4 py-2 text-xs font-bold text-white hover:bg-rose-700 disabled:opacity-50 transition-colors shadow-2xs cursor-pointer"
            >
              {{ stoppingTimer ? 'Menyimpan...' : '⏹️ Selesai Sesi Fokus' }}
            </button>
          </div>
          <div v-else class="flex items-center gap-2 w-full sm:w-auto">
            <input
              v-model="newTimerProject"
              type="text"
              placeholder="Contoh: Riset IDCS / Tugas Matkul..."
              class="rounded-xl border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs text-slate-900 placeholder-slate-400 focus:bg-white focus:border-slate-800 focus:outline-none w-full sm:w-64"
              @keyup.enter="handleStartTimer"
            />
            <button
              type="button"
              @click="handleStartTimer"
              :disabled="startingTimer || !newTimerProject.trim()"
              class="rounded-xl bg-slate-900 px-3.5 py-1.5 text-xs font-bold text-white hover:bg-slate-800 disabled:opacity-50 transition-colors shrink-0 shadow-2xs cursor-pointer"
            >
              {{ startingTimer ? '...' : '▶️ Mulai' }}
            </button>
          </div>
        </div>

      <!-- Konten Utama 2 Kolom -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <!-- Kolom Kiri (7 Kolom): Tugas & Habit Tracker -->
        <div class="lg:col-span-7 space-y-6">
          <!-- Section 1: Daftar Tugas -->
          <section class="rounded-xl border border-gray-200 bg-white p-5 shadow-xs">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 mb-4 border-b border-gray-100 pb-3">
              <div>
                <h2 class="text-base font-bold text-gray-900">Daftar Tugas</h2>
                <p class="text-xs text-gray-500">Diurutkan berdasarkan area & deadline</p>
              </div>

              <!-- Filter Tab -->
              <div class="flex rounded-lg bg-gray-100 p-0.5 text-xs font-medium">
                <button
                  @click="taskFilter = 'pending'"
                  :class="[
                    'px-2.5 py-1 rounded-md transition-all',
                    taskFilter === 'pending' ? 'bg-white text-gray-900 shadow-xs' : 'text-gray-600 hover:text-gray-900'
                  ]"
                >
                  Pending ({{ pendingTasks.length }})
                </button>
                <button
                  @click="taskFilter = 'completed'"
                  :class="[
                    'px-2.5 py-1 rounded-md transition-all',
                    taskFilter === 'completed' ? 'bg-white text-gray-900 shadow-xs' : 'text-gray-600 hover:text-gray-900'
                  ]"
                >
                  Selesai ({{ completedTasks.length }})
                </button>
                <button
                  @click="taskFilter = 'urgent'"
                  :class="[
                    'px-2.5 py-1 rounded-md transition-all',
                    taskFilter === 'urgent' ? 'bg-rose-100 text-rose-800 font-bold shadow-xs' : 'text-rose-600 hover:text-rose-800'
                  ]"
                >
                  🔥 Mendesak ({{ urgentCount }})
                </button>
                <button
                  @click="taskFilter = 'all'"
                  :class="[
                    'px-2.5 py-1 rounded-md transition-all',
                    taskFilter === 'all' ? 'bg-white text-gray-900 shadow-xs' : 'text-gray-600 hover:text-gray-900'
                  ]"
                >
                  Semua
                </button>
              </div>
            </div>

            <!-- Tasks List -->
            <div v-if="filteredTasks.length === 0" class="py-8 text-center text-xs text-gray-500">
              Tidak ada tugas dalam kategori ini.
            </div>

            <ul v-else class="divide-y divide-gray-100">
              <li
                v-for="task in filteredTasks"
                :key="task.id"
                class="py-3 first:pt-0 last:pb-0 flex items-start justify-between gap-3 group"
              >
                <!-- Quick Checkbox Toggle -->
                <button
                  type="button"
                  @click="handleToggleTask(task.id)"
                  class="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-lg border transition-all cursor-pointer"
                  :class="task.status === 'completed' ? 'border-emerald-600 bg-emerald-600 text-white' : 'border-gray-300 hover:border-gray-500 bg-white'"
                  :title="task.status === 'completed' ? 'Tandai belum selesai' : 'Tandai selesai'"
                >
                  <span v-if="task.status === 'completed'" class="text-xs font-bold leading-none">✓</span>
                </button>

                <div class="min-w-0 flex-1">
                  <div class="flex flex-wrap items-center gap-1.5">
                    <span
                      v-if="task.area_id && areaMap[task.area_id]"
                      class="rounded bg-blue-50 px-1.5 py-0.5 text-[11px] font-semibold text-blue-800 border border-blue-100"
                    >
                      [{{ areaMap[task.area_id] }}]
                    </span>
                    <span
                      v-if="task.is_urgent && task.status === 'pending'"
                      class="rounded bg-rose-50 px-1.5 py-0.5 text-[11px] font-bold text-rose-700 border border-rose-200"
                    >
                      ⚠️ Mendesak
                    </span>
                    <span
                      :class="[
                        'text-sm font-medium text-gray-900',
                        task.status === 'completed' ? 'line-through text-gray-400' : ''
                      ]"
                    >
                      {{ task.title }}
                    </span>
                  </div>

                  <div class="mt-1 flex items-center gap-2 text-xs">
                    <span class="text-gray-400">#{{ task.id }}</span>
                    <span class="text-gray-300">•</span>
                    <!-- Deadline Badge -->
                    <span
                      v-if="task.status === 'pending'"
                      :class="[
                        'rounded px-1.5 py-0.5 text-[11px] border',
                        formatDeadline(task.deadline).badgeClass
                      ]"
                    >
                      {{ formatDeadline(task.deadline).text }}
                    </span>
                    <span v-else class="text-[11px] text-emerald-700 font-medium">
                      ✓ Selesai {{ formatDateTime(task.completed_at) }}
                    </span>
                  </div>
                </div>

                <!-- Status Pill -->
                <span
                  v-if="task.status === 'completed'"
                  class="shrink-0 rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-semibold text-emerald-700 border border-emerald-200"
                >
                  Selesai
                </span>
                <span
                  v-else
                  class="shrink-0 rounded-full bg-gray-100 px-2 py-0.5 text-[11px] font-medium text-gray-600"
                >
                  Pending
                </span>
              </li>
            </ul>
          </section>

          <!-- Section 2: Habit Tracker -->
          <section class="rounded-xl border border-gray-200 bg-white p-5 shadow-xs">
            <div class="flex items-center justify-between mb-3 border-b border-gray-100 pb-3">
              <div>
                <h2 class="text-base font-bold text-gray-900">Kebiasaan Harian</h2>
                <p class="text-xs text-gray-500">Status pencapaian hari ini ({{ todayHuman }})</p>
              </div>
              <span class="text-xs font-semibold text-gray-700 bg-gray-50 border border-gray-200 rounded-md px-2 py-1">
                {{ completedHabitsTodayCount }}/{{ habits.length }} Selesai
              </span>
            </div>

            <div v-if="habits.length === 0" class="py-6 text-center text-xs text-gray-500">
              Belum ada habit yang didaftarkan.<br />
              Pantau rutinitas belajarmu di sini setiap hari.
            </div>

            <ul v-else class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              <li
                v-for="h in habitsWithStatus"
                :key="h.id"
                @click="handleToggleHabit(h.id)"
                :class="[
                  'rounded-xl border p-3 flex items-center justify-between transition-all cursor-pointer hover:shadow-xs',
                  h.isCompletedToday ? 'border-emerald-200 bg-emerald-50/60' : 'border-gray-200 bg-gray-50/50 hover:bg-white'
                ]"
                :title="h.isCompletedToday ? 'Klik untuk batal centang' : 'Klik untuk menyelesaikan habit hari ini'"
              >
                <div>
                  <div class="flex items-center gap-2">
                    <button
                      type="button"
                      class="flex h-5 w-5 shrink-0 items-center justify-center rounded-lg border transition-all text-xs font-bold leading-none cursor-pointer"
                      :class="h.isCompletedToday ? 'border-emerald-600 bg-emerald-600 text-white' : 'border-gray-300 bg-white text-transparent'"
                    >
                      ✓
                    </button>
                    <span class="text-sm font-semibold text-gray-900">{{ h.name }}</span>
                  </div>
                  <span class="text-[11px] text-gray-500 mt-1 ml-7 block">
                    {{ h.isCompletedToday ? '✓ Selesai hari ini' : 'Ketuk untuk ceklis' }}
                  </span>
                </div>
                <div class="text-right">
                  <span
                    v-if="h.streak > 0"
                    class="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-[11px] font-bold text-amber-900"
                  >
                    🔥 {{ h.streak }} hari
                  </span>
                  <span v-else class="text-[11px] text-gray-400">Belum ada streak</span>
                </div>
              </li>
            </ul>
          </section>
        </div>

        <!-- Kolom Kanan (5 Kolom): Deep Work Logs & Catatan Ide -->
        <div class="lg:col-span-5 space-y-6">
          <!-- Sesi Fokus (Time Logs) -->
          <section class="rounded-xl border border-gray-200 bg-white p-5 shadow-xs">
            <div class="flex items-center justify-between mb-3 border-b border-gray-100 pb-3">
              <div>
                <h2 class="text-base font-bold text-gray-900">Riwayat Sesi Fokus</h2>
                <p class="text-xs text-gray-500">Sesi deep work terbaru</p>
              </div>
              <span class="text-xs text-gray-400">30 sesi terakhir</span>
            </div>

            <!-- Quick Start Timer Input In-App -->
            <div class="mb-3.5 flex items-center gap-2">
              <input
                v-model="newTimerProject"
                type="text"
                placeholder="Nama tugas atau materi kuliah..."
                class="block w-full rounded-xl border border-gray-200 bg-gray-50 px-3.5 py-2 text-xs text-gray-900 placeholder-gray-400 focus:bg-white focus:border-gray-900 focus:outline-none min-h-[40px]"
                @keyup.enter="handleStartTimer"
              />
              <button
                type="button"
                @click="handleStartTimer"
                :disabled="startingTimer || !newTimerProject.trim()"
                class="rounded-xl bg-gray-900 px-3.5 py-2 text-xs font-bold text-white hover:bg-gray-800 disabled:opacity-50 transition-colors shrink-0 min-h-[40px] cursor-pointer shadow-2xs"
              >
                {{ startingTimer ? '...' : '▶️ Mulai' }}
              </button>
            </div>

            <div v-if="timeLogs.length === 0" class="py-6 text-center text-xs text-gray-500">
              Belum ada riwayat fokus. Masukkan nama tugas di atas lalu klik Mulai.
            </div>

            <ul v-else class="divide-y divide-gray-100 max-h-96 overflow-y-auto pr-1">
              <li
                v-for="item in timeLogs"
                :key="item.id"
                class="py-2.5 first:pt-0 last:pb-0 flex items-center justify-between"
              >
                <div class="min-w-0 pr-2">
                  <div class="flex items-center gap-1.5">
                    <span class="font-medium text-sm text-gray-900 truncate">{{ item.project_name }}</span>
                    <span
                      v-if="item.ended_at === null"
                      class="rounded bg-emerald-100 px-1.5 py-0.2 text-[10px] font-bold text-emerald-800 shrink-0"
                    >
                      Aktif
                    </span>
                  </div>
                  <span class="text-[11px] text-gray-400 block mt-0.5">
                    {{ formatDateTime(item.started_at) }}
                  </span>
                </div>
                <div class="shrink-0 text-right">
                  <span
                    v-if="item.duration_minutes !== null"
                    class="font-mono text-xs font-bold text-gray-800 bg-gray-100 px-2 py-0.5 rounded"
                  >
                    {{ item.duration_minutes }}m
                  </span>
                  <span v-else class="text-xs text-emerald-600 font-semibold">berjalan</span>
                </div>
              </li>
            </ul>
          </section>

          <!-- Catatan & Ide -->
          <section class="rounded-xl border border-gray-200 bg-white p-5 shadow-xs">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 mb-3 border-b border-gray-100 pb-3">
              <div>
                <h2 class="text-base font-bold text-gray-900">Catatan & Ide</h2>
                <p class="text-xs text-gray-500">Tersimpan otomatis dari chat</p>
              </div>

              <!-- Tab Navigasi: Daftar vs Graf -->
              <div class="flex items-center bg-gray-100 p-0.5 rounded-lg text-xs font-medium self-start sm:self-auto">
                <button
                  type="button"
                  @click="switchNotesTab('list')"
                  :class="[
                    'px-2.5 py-1 rounded-md transition-all',
                    notesTab === 'list'
                      ? 'bg-white text-gray-900 shadow-xs font-semibold'
                      : 'text-gray-500 hover:text-gray-700'
                  ]"
                >
                  📋 Daftar
                </button>
                <button
                  type="button"
                  @click="switchNotesTab('graph')"
                  :class="[
                    'px-2.5 py-1 rounded-md transition-all',
                    notesTab === 'graph'
                      ? 'bg-white text-indigo-900 shadow-xs font-semibold'
                      : 'text-gray-500 hover:text-gray-700'
                  ]"
                >
                  🕸️ Jejaring Ide
                </button>
              </div>
            </div>

            <!-- Tab 1: Daftar Catatan -->
            <div v-if="notesTab === 'list'">
              <div v-if="notes.length === 0" class="py-6 text-center text-xs text-gray-500">
                Belum ada catatan yang tersimpan.
              </div>

              <ul v-else class="divide-y divide-gray-100 max-h-96 overflow-y-auto pr-1">
                <li
                  v-for="note in notes"
                  :key="note.id"
                  class="py-3 first:pt-0 last:pb-0"
                >
                  <p class="whitespace-pre-wrap text-xs sm:text-sm leading-relaxed text-gray-800">
                    {{ note.content }}
                  </p>
                  <div class="mt-2 flex flex-wrap items-center justify-between gap-1.5">
                    <div class="flex flex-wrap gap-1">
                      <span
                        v-for="tag in note.tags ?? []"
                        :key="tag"
                        class="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] font-medium text-gray-600"
                      >
                        #{{ tag }}
                      </span>
                    </div>
                    <span class="text-[10px] text-gray-400">
                      {{ formatDateTime(note.created_at) }}
                    </span>
                  </div>
                </li>
              </ul>
            </div>

            <!-- Tab 2: Visualisasi Hubungan Antar Catatan (Knowledge Graph) -->
            <div v-else>
              <div v-if="notes.length === 0" class="py-6 text-center text-xs text-gray-500">
                Belum ada catatan untuk divisualisasikan.
              </div>
              <div v-else class="space-y-3">
                <div class="flex items-center justify-between text-[11px] text-gray-500">
                  <div class="flex items-center gap-1.5">
                    <span class="inline-block w-2 h-2 rounded-full bg-emerald-500"></span>
                    <span><strong>{{ graphNodes.length }}</strong> simpul • <strong>{{ graphEdges.length }}</strong> relasi</span>
                  </div>
                  <span class="text-gray-400">Tarik simpul untuk menata • Klik untuk detail</span>
                </div>

                <div class="relative overflow-hidden rounded-xl bg-slate-950 shadow-inner border border-slate-800">
                  <canvas
                    ref="graphCanvas"
                    @mousedown="handleCanvasMouseDown"
                    @mousemove="handleCanvasMouseMove"
                    @mouseup="handleCanvasMouseUp"
                    @mouseleave="handleCanvasMouseLeave"
                    class="w-full h-80 cursor-grab active:cursor-grabbing block"
                  ></canvas>
                </div>

                <!-- Detail Catatan Terpilih -->
                <div
                  v-if="selectedNode"
                  class="rounded-lg border border-indigo-100 bg-indigo-50/50 p-3 text-xs transition-all shadow-xs"
                >
                  <div class="flex items-center justify-between">
                    <span class="font-bold text-indigo-950 flex items-center gap-1.5">
                      <span class="w-2.5 h-2.5 rounded-full inline-block" :style="{ backgroundColor: selectedNode.color }"></span>
                      Catatan #{{ selectedNode.id }}
                    </span>
                    <button
                      type="button"
                      @click="selectedNode = null"
                      class="text-gray-400 hover:text-gray-600 font-bold px-1"
                    >
                      ✕
                    </button>
                  </div>
                  <p class="mt-1.5 text-xs leading-relaxed text-gray-800 whitespace-pre-wrap">
                    {{ selectedNode.fullContent }}
                  </p>
                  <div class="mt-2 flex flex-wrap items-center justify-between gap-1.5">
                    <div class="flex flex-wrap gap-1">
                      <span
                        v-for="tag in selectedNode.tags"
                        :key="tag"
                        class="rounded bg-indigo-100 text-indigo-800 px-1.5 py-0.5 text-[10px] font-semibold"
                      >
                        #{{ tag }}
                      </span>
                    </div>
                    <span class="text-[10px] text-gray-400">
                      {{ formatDateTime(selectedNode.created_at) }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </section>
        </div>
      </div>
      </div>
    </main>

    <!-- Raycast-Style Command Palette & Quick Capture (Ctrl+K) -->
    <QuickCaptureModal
      ref="quickCaptureRef"
      v-if="currentUserId"
      :user-id="currentUserId"
      :areas="areas"
      @created="handleQuickCreated"
      @navigate-tab="handleTabNavigate"
      @open-rag="(q) => handleOpenBrainRag(q)"
      @open-tech-specs="handleOpenTechSpecs"
      @open-privacy="() => handleOpenPrivacy('governance')"
    />

    <!-- Privacy & Data Sovereignty Center Modal -->
    <PrivacyModal
      ref="privacyModalRef"
      :user-id="currentUserId"
      :user-email="userEmail"
    />

    <!-- Tech Specs & Architecture Inspector Modal -->
    <TechSpecsModal ref="techSpecsModalRef" />

    <!-- Brain RAG & Semantic Search Modal -->
    <BrainRagModal
      ref="brainRagModalRef"
      v-if="currentUserId"
      :user-id="currentUserId"
      :user-email="userEmail"
      :notes="notes"
    />

    <!-- Interactive Recruiter & Tech Lead Tour Modal -->
    <RecruiterTourModal
      ref="recruiterTourRef"
      @navigate-tab="handleTabNavigate"
      @open-rag="(q) => handleOpenBrainRag(q)"
      @open-tech-specs="handleOpenTechSpecs"
    />

    <!-- Sticky Recruiter Quick Cockpit (Desktop-only 1-Click Interactive Showcase) -->
    <div class="hidden lg:flex fixed bottom-4 left-1/2 -translate-x-1/2 z-20 bg-slate-950/90 backdrop-blur-md text-white border border-slate-700/80 rounded-2xl px-3.5 py-2 shadow-2xl items-center gap-2.5 text-xs max-w-[95vw] overflow-x-auto scrollbar-none animate-in fade-in slide-in-from-bottom-4 duration-200">
      <div class="flex items-center gap-1.5 shrink-0">
        <span class="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
        <span class="font-black text-purple-300 text-[11px] uppercase tracking-wider hidden sm:inline">⚡ Recruiter Cockpit:</span>
      </div>
      <div class="flex items-center gap-1.5 shrink-0">
        <button
          type="button"
          @click="handleTabNavigate('evals')"
          class="rounded-xl px-2.5 py-1 text-[11px] font-bold transition-all cursor-pointer"
          :class="activeTab === 'evals' ? 'bg-purple-600 text-white shadow-xs' : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white'"
        >
          🛡️ OOD Guardrail
        </button>
        <button
          v-if="userRole === 'owner'"
          type="button"
          @click="handleTabNavigate('research')"
          class="rounded-xl px-2.5 py-1 text-[11px] font-bold transition-all cursor-pointer"
          :class="activeTab === 'research' ? 'bg-purple-600 text-white shadow-xs' : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white'"
        >
          🔬 Tesis S2 (IDCS)
        </button>
        <button
          v-else
          type="button"
          @click="handleTabNavigate('rag')"
          class="rounded-xl px-2.5 py-1 text-[11px] font-bold transition-all cursor-pointer"
          :class="activeTab === 'rag' ? 'bg-purple-600 text-white shadow-xs' : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white'"
        >
          🧠 Next-Gen CRAG
        </button>
        <button
          type="button"
          @click="handleTabNavigate('mlradar')"
          class="rounded-xl px-2.5 py-1 text-[11px] font-bold transition-all cursor-pointer"
          :class="activeTab === 'mlradar' ? 'bg-purple-600 text-white shadow-xs' : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white'"
        >
          📊 Radar &lt;2ms
        </button>
        <button
          type="button"
          @click="handleTabNavigate('vlm')"
          class="rounded-xl px-2.5 py-1 text-[11px] font-bold transition-all cursor-pointer"
          :class="activeTab === 'vlm' ? 'bg-purple-600 text-white shadow-xs' : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white'"
        >
          📸 VLM Gemini 2.0
        </button>
        <button
          type="button"
          @click="handleTabNavigate('agentops')"
          class="rounded-xl px-2.5 py-1 text-[11px] font-bold transition-all cursor-pointer"
          :class="activeTab === 'agentops' ? 'bg-purple-600 text-white shadow-xs' : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white'"
        >
          🔌 MCP SSE
        </button>
      </div>
      <button
        type="button"
        @click="showCommandPalette = true"
        class="ml-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-white px-2 py-1 text-[10px] font-mono shrink-0 cursor-pointer border border-slate-700"
        title="Buka Command Palette (Ctrl+K)"
      >
        Ctrl+K
      </button>
    </div>

    <!-- Global Command Palette Modal (Raycast / Linear style) -->
    <CommandPaletteModal
      :is-open="showCommandPalette"
      :user-role="userRole"
      @close="showCommandPalette = false"
      @navigate-tab="handleTabNavigate"
      @open-tech-specs="handleOpenTechSpecs"
      @open-brain-rag="() => handleOpenBrainRag()"
      @open-quick-capture="handleOpenQuickCapture"
    />
  </div>
</template>
