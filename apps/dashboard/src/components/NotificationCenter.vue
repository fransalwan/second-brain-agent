<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import {
  type AppNotification,
  getReadNotificationIds,
  markAllNotificationsAsRead,
  markNotificationAsRead,
  playNotificationSound,
  requestBrowserNotificationPermission,
  sendBrowserPush,
} from '../lib/notifications'

const props = defineProps<{
  userId: string
  tasks: any[]
  habits: any[]
  habitLogs: any[]
  profile: any
  activeTimer: any
}>()

const emit = defineEmits<{
  (e: 'navigate-tab', tab: 'overview' | 'health' | 'coursework' | 'research' | 'hobby'): void
  (e: 'action', payload: { type: string; data?: any }): void
}>()

const isOpen = ref(false)
const activeFilter = ref<'all' | 'tasks' | 'health'>('all')
const permissionStatus = ref<NotificationPermission>(
  typeof window !== 'undefined' && 'Notification' in window
    ? Notification.permission
    : 'default'
)

const readIds = ref<Set<string>>(new Set())

onMounted(() => {
  readIds.value = getReadNotificationIds()
})

const notifications = computed<AppNotification[]>(() => {
  const list: AppNotification[] = []
  const today = new Date()
  const todayStr = today.toISOString().split('T')[0]
  const currentHour = today.getHours()

  // 1. Morning Brief Notification (Pagi 05:00 - 12:00)
  if (currentHour >= 5 && currentHour < 12) {
    const pendingCount = props.tasks.filter((t) => t.status === 'pending').length
    list.push({
      id: `brief-${todayStr}`,
      title: '☀️ Briefing Pagi Hari Ini',
      message: `Selamat pagi! Kamu memiliki ${pendingCount} tugas pending di Second Brain. Siapkan target fokus utamamu hari ini!`,
      type: 'brief',
      category: 'general',
      timestamp: 'Pagi ini',
      read: readIds.value.has(`brief-${todayStr}`),
      actionTab: 'overview',
      actionLabel: 'Lihat Ringkasan',
    })
  }

  // 2. Night Cutoff / Wind Down (Malam 21:00 - 04:00)
  const cutoffStr = props.profile?.night_cutoff_time?.slice(0, 5) || '23:00'
  const cutoffHour = parseInt(cutoffStr.split(':')[0], 10) || 23
  if (currentHour >= cutoffHour || currentHour < 4) {
    list.push({
      id: `night-${todayStr}`,
      title: '🌙 Waktu Istirahat & Recharge',
      message: `Sudah lewat jam ${cutoffStr}. Waktunya istirahat agar otak kembali segar besok. Hindari tugas berat larut malam ya!`,
      type: 'health',
      category: 'health',
      timestamp: 'Malam ini',
      read: readIds.value.has(`night-${todayStr}`),
      actionTab: 'health',
      actionLabel: 'Log Jam Tidur',
    })
  }

  // 3. Urgent & Overdue Tasks
  for (const task of props.tasks) {
    if (task.status !== 'pending') continue
    if (task.is_urgent) {
      list.push({
        id: `urgent-task-${task.id}`,
        title: `🚨 Tugas Mendesak: ${task.title}`,
        message: task.deadline
          ? `Deadline: ${task.deadline}. Selesaikan tugas ini lebih dulu!`
          : 'Tugas ini ditandai sangat penting & mendesak.',
        type: 'urgent',
        category: 'coursework',
        timestamp: task.deadline ? `Deadline: ${task.deadline}` : 'Mendesak',
        read: readIds.value.has(`urgent-task-${task.id}`),
        actionTab: 'overview',
        actionLabel: 'Tinjau Tugas',
      })
    } else if (task.deadline) {
      const dDate = new Date(task.deadline)
      const diffDays = Math.ceil((dDate.getTime() - today.getTime()) / (1000 * 3600 * 24))
      if (diffDays <= 0) {
        list.push({
          id: `overdue-task-${task.id}`,
          title: `⏰ Deadline Hari Ini / Terlewat: ${task.title}`,
          message: `Batas waktu pengerjaan: ${task.deadline}. Jangan tunda lagi!`,
          type: 'urgent',
          category: 'coursework',
          timestamp: 'Hari ini',
          read: readIds.value.has(`overdue-task-${task.id}`),
          actionTab: 'overview',
          actionLabel: 'Cek Tugas',
        })
      } else if (diffDays <= 2) {
        list.push({
          id: `approaching-task-${task.id}`,
          title: `⏳ Deadline Dekat: ${task.title}`,
          message: `Sisa waktu ${diffDays} hari lagi (${task.deadline}). Cicil sekarang yuk!`,
          type: 'info',
          category: 'coursework',
          timestamp: `${diffDays} hari lagi`,
          read: readIds.value.has(`approaching-task-${task.id}`),
          actionTab: 'overview',
          actionLabel: 'Mulai Cicil',
        })
      }
    }
  }

  // 4. Habit Reminders (Belum selesai hari ini)
  const completedHabitIds = new Set(
    props.habitLogs
      .filter((l) => l.completed_date === todayStr)
      .map((l) => l.habit_id)
  )
  const pendingHabits = props.habits.filter((h) => h.is_active && !completedHabitIds.has(h.id))
  if (pendingHabits.length > 0 && currentHour >= 12) {
    list.push({
      id: `habit-pending-${todayStr}`,
      title: `🧘 ${pendingHabits.length} Habit Belum Selesai Hari Ini`,
      message: `Jaga streakmu! Habit yang menanti: ${pendingHabits.map((h) => h.name).slice(0, 3).join(', ')}${pendingHabits.length > 3 ? '...' : ''}.`,
      type: 'habit',
      category: 'health',
      timestamp: 'Hari ini',
      read: readIds.value.has(`habit-pending-${todayStr}`),
      actionTab: 'overview',
      actionLabel: 'Centang Habit',
    })
  }

  // 5. Pomodoro Focus Timer Active
  if (props.activeTimer) {
    list.push({
      id: `timer-active-${props.activeTimer.id}`,
      title: `⏱️ Sesi Fokus Sedang Berjalan: ${props.activeTimer.project_name}`,
      message: 'Kamu sedang dalam mode deep work. Pertahankan konsentrasi dan hindari distraksi!',
      type: 'info',
      category: 'general',
      timestamp: 'Sedang berjalan',
      read: false,
      actionTab: 'overview',
      actionLabel: 'Lihat Timer',
    })
  }

  return list
})

const filteredNotifications = computed(() => {
  if (activeFilter.value === 'tasks') {
    return notifications.value.filter((n) => n.category === 'coursework')
  }
  if (activeFilter.value === 'health') {
    return notifications.value.filter((n) => n.category === 'health')
  }
  return notifications.value
})

const unreadCount = computed(() => {
  return notifications.value.filter((n) => !n.read).length
})

const hasUrgent = computed(() => {
  return notifications.value.some((n) => n.type === 'urgent' && !n.read)
})

// Trigger gentle push when new urgent notification arrives
watch(
  () => hasUrgent.value,
  (val) => {
    if (val && permissionStatus.value === 'granted') {
      const urgentItem = notifications.value.find((n) => n.type === 'urgent' && !n.read)
      if (urgentItem) {
        sendBrowserPush(urgentItem.title, urgentItem.message)
        playNotificationSound('alert')
      }
    }
  }
)

function toggleOpen() {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    playNotificationSound('gentle')
  }
}

function handleMarkAsRead(item: AppNotification) {
  markNotificationAsRead(item.id)
  readIds.value.add(item.id)
  readIds.value = new Set(readIds.value)
}

function handleMarkAllRead() {
  const ids = notifications.value.map((n) => n.id)
  markAllNotificationsAsRead(ids)
  readIds.value = new Set(ids)
}

function handleAction(item: AppNotification) {
  handleMarkAsRead(item)
  if (item.actionTab) {
    emit('navigate-tab', item.actionTab)
  }
  isOpen.value = false
}

async function enableWebPush() {
  const res = await requestBrowserNotificationPermission()
  permissionStatus.value = res
  if (res === 'granted') {
    playNotificationSound('chime')
    sendBrowserPush('🎉 Notifikasi Second Brain Aktif!', 'Kamu akan menerima pengingat deadline dan briefing langsung di perangkat ini.')
  }
}
</script>

<template>
  <div class="relative">
    <!-- Notification Bell Button -->
    <button
      type="button"
      @click="toggleOpen"
      class="relative flex h-9 w-9 items-center justify-center rounded-xl border border-gray-200 bg-white text-gray-700 shadow-2xs hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-900 transition-all cursor-pointer"
      :class="hasUrgent ? 'border-rose-300 bg-rose-50/50' : ''"
      title="Pusat Notifikasi"
      aria-label="Pusat Notifikasi"
    >
      <span class="text-base select-none">🔔</span>

      <!-- Unread Badge Counter -->
      <span
        v-if="unreadCount > 0"
        class="absolute -top-1 -right-1 flex h-4 min-w-[16px] items-center justify-center rounded-full px-1 text-[10px] font-extrabold text-white shadow-xs"
        :class="hasUrgent ? 'bg-rose-600 animate-pulse' : 'bg-gray-900'"
      >
        {{ unreadCount > 9 ? '9+' : unreadCount }}
      </span>
    </button>

    <!-- Backdrop on mobile -->
    <div
      v-if="isOpen"
      @click="isOpen = false"
      class="fixed inset-0 z-40 bg-black/20 backdrop-blur-2xs sm:hidden"
    ></div>

    <!-- Notification Drawer / Dropdown Popover -->
    <transition
      enter-active-class="transition duration-150 ease-out"
      enter-from-class="transform scale-95 opacity-0"
      enter-to-class="transform scale-100 opacity-100"
      leave-active-class="transition duration-100 ease-in"
      leave-from-class="transform scale-100 opacity-100"
      leave-to-class="transform scale-95 opacity-0"
    >
      <div
        v-if="isOpen"
        class="fixed inset-x-3 top-16 z-50 sm:absolute sm:inset-auto sm:right-0 sm:top-11 sm:w-96 rounded-2xl border border-gray-200 bg-white shadow-xl overflow-hidden flex flex-col max-h-[82vh]"
      >
        <!-- Header Popover -->
        <div class="border-b border-gray-100 p-4 bg-gray-50/70 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="text-lg">🔔</span>
            <div>
              <h2 class="text-sm font-bold text-gray-900">Notifikasi App</h2>
              <p class="text-[11px] text-gray-500">Pengingat langsung di perangkatmu</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button
              v-if="unreadCount > 0"
              @click="handleMarkAllRead"
              class="text-[11px] font-semibold text-gray-600 hover:text-gray-900 hover:underline cursor-pointer"
            >
              Tandai Dibaca
            </button>
            <button
              @click="isOpen = false"
              class="text-gray-400 hover:text-gray-600 p-1 text-xs cursor-pointer"
            >
              ✕
            </button>
          </div>
        </div>

        <!-- Web Push Permission Banner (jika belum diizinkan) -->
        <div
          v-if="permissionStatus !== 'granted'"
          class="border-b border-amber-100 bg-amber-50/80 px-4 py-2.5 flex items-center justify-between gap-3 text-xs text-amber-900"
        >
          <div class="flex items-center gap-2">
            <span>✨</span>
            <span class="text-[11px] leading-tight font-medium">
              Aktifkan Browser Push agar pengingat muncul di HP & laptop!
            </span>
          </div>
          <button
            @click="enableWebPush"
            class="rounded-lg bg-amber-600 px-2.5 py-1 text-[11px] font-bold text-white shadow-2xs hover:bg-amber-700 shrink-0 cursor-pointer"
          >
            Aktifkan 🔔
          </button>
        </div>

        <!-- Filter Bar -->
        <div class="flex items-center border-b border-gray-100 px-3 bg-white text-xs font-medium text-gray-500">
          <button
            @click="activeFilter = 'all'"
            class="border-b-2 py-2 px-2.5 transition-colors cursor-pointer"
            :class="activeFilter === 'all' ? 'border-gray-900 text-gray-900 font-bold' : 'border-transparent hover:text-gray-800'"
          >
            Semua ({{ notifications.length }})
          </button>
          <button
            @click="activeFilter = 'tasks'"
            class="border-b-2 py-2 px-2.5 transition-colors cursor-pointer"
            :class="activeFilter === 'tasks' ? 'border-gray-900 text-gray-900 font-bold' : 'border-transparent hover:text-gray-800'"
          >
            Tugas & Kuliah
          </button>
          <button
            @click="activeFilter = 'health'"
            class="border-b-2 py-2 px-2.5 transition-colors cursor-pointer"
            :class="activeFilter === 'health' ? 'border-gray-900 text-gray-900 font-bold' : 'border-transparent hover:text-gray-800'"
          >
            Kesehatan
          </button>
        </div>

        <!-- Notification List -->
        <div class="overflow-y-auto divide-y divide-gray-100 flex-1 overscroll-contain">
          <div
            v-if="filteredNotifications.length === 0"
            class="py-10 px-4 text-center space-y-2"
          >
            <div class="text-3xl">✨</div>
            <p class="text-xs font-semibold text-gray-800">Semua Beres!</p>
            <p class="text-[11px] text-gray-500 max-w-xs mx-auto">
              Tidak ada notifikasi tertunda saat ini. Waktu yang tepat untuk fokus dan berkarya.
            </p>
          </div>

          <div
            v-for="item in filteredNotifications"
            :key="item.id"
            class="p-3.5 transition-colors flex items-start gap-3 hover:bg-gray-50/70"
            :class="item.read ? 'opacity-70 bg-white' : 'bg-gray-50/40'"
          >
            <!-- Badge Icon -->
            <div
              class="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl text-sm font-bold shadow-2xs"
              :class="{
                'bg-rose-100 text-rose-800': item.type === 'urgent',
                'bg-amber-100 text-amber-800': item.type === 'brief',
                'bg-indigo-100 text-indigo-800': item.type === 'exam' || item.type === 'info',
                'bg-purple-100 text-purple-800': item.type === 'health',
                'bg-emerald-100 text-emerald-800': item.type === 'habit',
              }"
            >
              <span v-if="item.type === 'urgent'">🚨</span>
              <span v-else-if="item.type === 'brief'">☀️</span>
              <span v-else-if="item.type === 'health'">🌙</span>
              <span v-else-if="item.type === 'habit'">🧘</span>
              <span v-else>💡</span>
            </div>

            <!-- Content -->
            <div class="flex-1 min-w-0 space-y-1">
              <div class="flex items-center justify-between gap-2">
                <h3 class="text-xs font-bold text-gray-900 truncate">
                  {{ item.title }}
                </h3>
                <span class="text-[10px] text-gray-400 shrink-0 font-medium">
                  {{ item.timestamp }}
                </span>
              </div>
              <p class="text-[11px] text-gray-600 line-clamp-2 leading-relaxed">
                {{ item.message }}
              </p>

              <!-- Actions -->
              <div class="flex items-center gap-2 pt-1">
                <button
                  v-if="item.actionLabel"
                  type="button"
                  @click="handleAction(item)"
                  class="rounded-lg bg-gray-900 px-2.5 py-1 text-[10px] font-bold text-white shadow-2xs hover:bg-gray-800 transition-colors cursor-pointer"
                >
                  {{ item.actionLabel }} ↗
                </button>
                <button
                  v-if="!item.read"
                  type="button"
                  @click="handleMarkAsRead(item)"
                  class="text-[10px] text-gray-500 hover:text-gray-800 hover:underline cursor-pointer"
                >
                  Tandai selesai
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="border-t border-gray-100 p-2.5 bg-gray-50/60 text-center">
          <p class="text-[10px] text-gray-500">
            Semua notifikasi dikelola secara mandiri oleh dashboard Second Brain.
          </p>
        </div>
      </div>
    </transition>
  </div>
</template>
