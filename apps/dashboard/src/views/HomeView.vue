<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { supabase } from '../lib/supabase'

interface ProfileItem {
  full_name: string | null
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
const profile = ref<ProfileItem | null>(null)
const profileLoaded = ref(false)

const areas = ref<AreaItem[]>([])
const tasks = ref<TaskItem[]>([])
const habits = ref<HabitItem[]>([])
const habitLogs = ref<HabitLogItem[]>([])
const notes = ref<NoteItem[]>([])
const timeLogs = ref<TimeLogItem[]>([])

const loading = ref(true)
const errorMsg = ref<string | null>(null)
const loggingOut = ref(false)
const taskFilter = ref<'all' | 'pending' | 'completed'>('pending')
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

  const {
    data: { session },
  } = await supabase.auth.getSession()

  if (!session) {
    loading.value = false
    return
  }
  userEmail.value = session.user?.email ?? null

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
      supabase.from('profiles').select('full_name, brief_time, night_cutoff_time').maybeSingle(),
      supabase.from('areas').select('id, name, position').order('position', { ascending: true }),
      supabase.from('tasks').select('*').order('created_at', { ascending: false }),
      supabase.from('habits').select('*').eq('is_active', true).order('position', { ascending: true }),
      supabase.from('habit_logs').select('*').order('completed_date', { ascending: false }),
      supabase.from('time_logs').select('*').order('started_at', { ascending: false }).limit(30),
      supabase.from('notes').select('*').order('created_at', { ascending: false }).limit(20),
    ])

    profileLoaded.value = true
    profile.value = profileRes.data ?? null
    areas.value = areasRes.data ?? []
    tasks.value = tasksRes.data ?? []
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
    await supabase.auth.signOut()
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

onUnmounted(() => {
  stopSimulation()
})

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="min-h-screen bg-gray-50 text-gray-900 pb-16">
    <!-- Header Navbar -->
    <header class="border-b border-gray-200 bg-white sticky top-0 z-10 shadow-xs">
      <div class="mx-auto flex max-w-6xl items-center justify-between px-4 py-3.5 sm:px-6">
        <div class="flex items-center gap-3">
          <div class="h-9 w-9 rounded-xl bg-gray-900 flex items-center justify-center text-white text-lg font-bold shadow-xs">
            🧠
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h1 class="text-base font-bold tracking-tight text-gray-900 sm:text-lg">Second Brain</h1>
              <span class="rounded-full bg-gray-100 px-2 py-0.5 text-[11px] font-medium text-gray-600">Dashboard</span>
            </div>
            <p class="text-xs text-gray-500 flex items-center gap-1.5 mt-0.5">
              <span v-if="profile?.full_name" class="font-semibold text-gray-800">{{ profile.full_name }}</span>
              <span v-if="profile?.full_name" class="text-gray-300">•</span>
              <span>{{ userEmail }}</span>
            </p>
          </div>
        </div>

        <div class="flex items-center gap-2.5">
          <!-- Indikator Jadwal -->
          <div v-if="profile" class="hidden sm:flex items-center gap-2 text-xs text-gray-500 bg-gray-50 border border-gray-200 rounded-lg px-2.5 py-1.5">
            <span>☀️ Brief: <strong class="text-gray-800">{{ profile.brief_time?.slice(0, 5) || '07:00' }}</strong></span>
            <span class="text-gray-300">|</span>
            <span>🌙 Malam: <strong class="text-gray-800">{{ profile.night_cutoff_time?.slice(0, 5) || '23:00' }}</strong></span>
          </div>

          <button
            @click="handleLogout"
            :disabled="loggingOut"
            class="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:ring-offset-2 disabled:opacity-50 transition-colors"
          >
            {{ loggingOut ? 'Keluar...' : 'Logout' }}
          </button>
        </div>
      </div>
    </header>

    <main class="mx-auto max-w-6xl px-4 pt-6 sm:px-6 space-y-6">
      <!-- Banner jika akun belum connect Telegram -->
      <div
        v-if="profileLoaded && !profile"
        class="rounded-xl border border-amber-200 bg-amber-50 p-4 text-amber-900 shadow-sm"
      >
        <div class="flex items-start gap-3">
          <span class="text-xl">⚠️</span>
          <div>
            <h2 class="text-sm font-semibold">Akun Belum Ditautkan ke Bot Telegram</h2>
            <p class="mt-1 text-xs leading-relaxed text-amber-800">
              Akun Supabase ini belum memiliki profil terhubung. Kirim perintah
              <code class="rounded bg-amber-100 px-1.5 py-0.5 font-mono text-xs font-semibold text-amber-900">/connect KODE</code>
              di Telegram agar aktivitas sinkron secara real-time.
            </p>
          </div>
        </div>
      </div>

      <!-- Banner Active Timer Berjalan -->
      <div
        v-if="activeTimer"
        class="rounded-xl border border-emerald-200 bg-emerald-50/80 p-4 sm:p-5 shadow-sm transition-all"
      >
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div class="flex items-start sm:items-center gap-3">
            <span class="relative flex h-3.5 w-3.5 mt-1 sm:mt-0">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-3.5 w-3.5 bg-emerald-600"></span>
            </span>
            <div>
              <div class="flex items-center gap-2">
                <span class="text-xs font-bold uppercase tracking-wider text-emerald-800">Sesi Fokus Aktif</span>
                <span class="text-xs text-emerald-700">Dimulai {{ formatDateTime(activeTimer.started_at) }}</span>
              </div>
              <h2 class="text-lg sm:text-xl font-bold text-emerald-950 mt-0.5">
                {{ activeTimer.project_name }}
              </h2>
            </div>
          </div>
          <div class="text-xs text-emerald-800 bg-emerald-100/70 border border-emerald-200 rounded-lg px-3 py-1.5 self-start sm:self-auto">
            Ketik <strong>/stop</strong> di Telegram untuk menghentikan sesi ini
          </div>
        </div>
      </div>

      <!-- Ringkasan Statistik Utama (4 Card Metrics) -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-3.5 sm:gap-4">
        <!-- Metric 1: Waktu Fokus Hari Ini -->
        <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-xs">
          <div class="flex items-center justify-between">
            <span class="text-xs font-medium text-gray-500">Fokus Hari Ini</span>
            <span class="text-base">⏱️</span>
          </div>
          <p class="text-xl sm:text-2xl font-extrabold text-gray-900 mt-1">
            <span v-if="totalFocusMinutesToday >= 60">
              {{ Math.floor(totalFocusMinutesToday / 60) }}j {{ totalFocusMinutesToday % 60 }}m
            </span>
            <span v-else>
              {{ totalFocusMinutesToday }} menit
            </span>
          </p>
          <span class="text-[11px] text-gray-400 mt-0.5 block">Dari sesi deep work</span>
        </div>

        <!-- Metric 2: Tugas Pending & Mendesak -->
        <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-xs">
          <div class="flex items-center justify-between">
            <span class="text-xs font-medium text-gray-500">Tugas Pending</span>
            <span class="text-base">🎯</span>
          </div>
          <div class="flex items-baseline gap-2 mt-1">
            <p class="text-xl sm:text-2xl font-extrabold text-gray-900">{{ pendingTasks.length }}</p>
            <span v-if="urgentCount > 0" class="rounded bg-rose-100 px-1.5 py-0.5 text-[11px] font-bold text-rose-700">
              {{ urgentCount }} mendesak
            </span>
          </div>
          <span class="text-[11px] text-gray-400 mt-0.5 block">{{ completedTasks.length }} tugas selesai</span>
        </div>

        <!-- Metric 3: Habit Hari Ini -->
        <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-xs">
          <div class="flex items-center justify-between">
            <span class="text-xs font-medium text-gray-500">Habit Hari Ini</span>
            <span class="text-base">🔥</span>
          </div>
          <p class="text-xl sm:text-2xl font-extrabold text-gray-900 mt-1">
            {{ completedHabitsTodayCount }}/{{ habits.length }}
          </p>
          <span class="text-[11px] text-gray-400 mt-0.5 block">Centang via /check di Telegram</span>
        </div>

        <!-- Metric 4: Catatan & Ide -->
        <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-xs">
          <div class="flex items-center justify-between">
            <span class="text-xs font-medium text-gray-500">Catatan & Ide</span>
            <span class="text-base">📝</span>
          </div>
          <p class="text-xl sm:text-2xl font-extrabold text-gray-900 mt-1">
            {{ notes.length }}
          </p>
          <span class="text-[11px] text-gray-400 mt-0.5 block">Tersimpan dari chat</span>
        </div>
      </div>

      <!-- Area Hidup Chips (Prinsip Urutan Prioritas) -->
      <div v-if="areas.length > 0" class="rounded-xl border border-gray-200 bg-white p-4 shadow-xs">
        <div class="flex items-center justify-between mb-2.5">
          <div class="flex items-center gap-1.5">
            <span class="text-xs font-bold uppercase tracking-wider text-gray-500">Urutan Prioritas Area Hidup</span>
            <span class="text-xs text-gray-400">(Bobot tugas ditentukan urutan ini)</span>
          </div>
          <span class="text-[11px] text-gray-400">Atur lewat bot: <code>ubah urutan area: ...</code></span>
        </div>
        <div class="flex flex-wrap gap-2">
          <div
            v-for="area in areas"
            :key="area.id"
            class="flex items-center gap-1.5 rounded-lg border border-gray-200 bg-gray-50/80 px-2.5 py-1 text-xs font-medium text-gray-800"
          >
            <span class="h-4 w-4 rounded-full bg-gray-900 text-[10px] text-white flex items-center justify-center font-bold">
              {{ area.position }}
            </span>
            <span>{{ area.name }}</span>
          </div>
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
              Kirim <code>tambah habit [nama]</code> di Telegram.
            </div>

            <ul v-else class="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              <li
                v-for="h in habitsWithStatus"
                :key="h.id"
                :class="[
                  'rounded-lg border p-3 flex items-center justify-between transition-all',
                  h.isCompletedToday ? 'border-emerald-200 bg-emerald-50/50' : 'border-gray-200 bg-gray-50/40'
                ]"
              >
                <div>
                  <div class="flex items-center gap-1.5">
                    <span class="text-sm">{{ h.isCompletedToday ? '✅' : '⏳' }}</span>
                    <span class="text-sm font-semibold text-gray-900">{{ h.name }}</span>
                  </div>
                  <span class="text-[11px] text-gray-500 mt-0.5 block">ID #{{ h.id }}</span>
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

            <div v-if="timeLogs.length === 0" class="py-6 text-center text-xs text-gray-500">
              Belum ada riwayat fokus. Mulai dengan mengirim <code>mulai [project]</code> di Telegram.
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
    </main>
  </div>
</template>
