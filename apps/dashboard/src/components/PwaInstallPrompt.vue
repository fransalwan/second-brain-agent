<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

const deferredPrompt = ref<any>(null)
const isInstalled = ref(false)
const isDismissed = ref(false)
const showIosTip = ref(false)

const isIos = computed(() => {
  if (typeof window === 'undefined') return false
  const userAgent = window.navigator.userAgent.toLowerCase()
  return /iphone|ipad|ipod/.test(userAgent)
})

const isStandalone = computed(() => {
  if (typeof window === 'undefined') return false
  return (
    window.matchMedia('(display-mode: standalone)').matches ||
    (window.navigator as any).standalone === true
  )
})

onMounted(() => {
  if (sessionStorage.getItem('sb_pwa_dismissed') === 'true' || isStandalone.value) {
    isDismissed.value = true
    return
  }

  // Tangkap event instalasi browser (Android, Chrome, Edge)
  window.addEventListener('beforeinstallprompt', (e: Event) => {
    e.preventDefault()
    deferredPrompt.value = e
  })

  // Deteksi ketika aplikasi berhasil di-install
  window.addEventListener('appinstalled', () => {
    isInstalled.value = true
    deferredPrompt.value = null
  })
})

async function triggerInstall() {
  if (deferredPrompt.value) {
    deferredPrompt.value.prompt()
    const { outcome } = await deferredPrompt.value.userChoice
    if (outcome === 'accepted') {
      isInstalled.value = true
    }
    deferredPrompt.value = null
  } else if (isIos.value) {
    showIosTip.value = !showIosTip.value
  }
}

function dismissPrompt() {
  isDismissed.value = true
  sessionStorage.setItem('sb_pwa_dismissed', 'true')
}
</script>

<template>
  <!-- Tampilkan banner jika belum di-install & belum di-dismiss (dan browser mendukung atau di iOS) -->
  <div
    v-if="!isStandalone && !isDismissed && (deferredPrompt || isIos)"
    class="fixed bottom-20 sm:bottom-6 right-4 sm:right-6 z-40 max-w-sm rounded-2xl border border-indigo-200 bg-white/95 p-4 shadow-xl backdrop-blur-md transition-all animate-bounce-short"
  >
    <div class="flex items-start gap-3">
      <div class="text-2xl p-2 rounded-xl bg-indigo-50 border border-indigo-100 select-none">
        📲
      </div>
      <div class="flex-1 space-y-1">
        <div class="flex items-center justify-between">
          <h4 class="text-xs font-bold text-gray-900">Pasang di Layar Utama HP</h4>
          <button
            type="button"
            @click="dismissPrompt"
            class="text-gray-400 hover:text-gray-600 text-xs p-1 cursor-pointer"
          >
            ✕
          </button>
        </div>
        <p class="text-[11px] text-gray-600 leading-relaxed">
          Gunakan Second Brain seperti aplikasi native tanpa bilah URL browser, lebih hemat kuota, dan akses 1-tap.
        </p>

        <!-- iOS Step-by-Step Tip Popover -->
        <div
          v-if="showIosTip"
          class="mt-2 rounded-xl bg-indigo-50 p-2.5 text-[11px] text-indigo-900 border border-indigo-100 space-y-1"
        >
          <p class="font-bold">Cara Pasang di Safari iOS:</p>
          <ol class="list-decimal pl-4 space-y-0.5 text-[10px] text-indigo-800">
            <li>Tap ikon <strong>Bagikan (Share)</strong> di bilah bawah Safari.</li>
            <li>Scroll ke bawah dan pilih <strong>"Tambahkan ke Layar Utama" (Add to Home Screen)</strong>.</li>
            <li>Tap <strong>Tambah (Add)</strong> di pojok kanan atas.</li>
          </ol>
        </div>

        <div class="pt-2 flex items-center gap-2">
          <button
            type="button"
            @click="triggerInstall"
            class="rounded-xl bg-indigo-600 px-3.5 py-1.5 text-xs font-bold text-white shadow-xs hover:bg-indigo-700 active:scale-95 transition-all cursor-pointer flex items-center gap-1.5"
          >
            <span>✨</span>
            <span>{{ isIos ? (showIosTip ? 'Tutup Petunjuk' : 'Lihat Cara Pasang') : 'Pasang Aplikasi' }}</span>
          </button>
          <button
            type="button"
            @click="dismissPrompt"
            class="text-[11px] font-semibold text-gray-500 hover:text-gray-800 cursor-pointer"
          >
            Nanti Saja
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@keyframes bounceShort {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-6px);
  }
}
.animate-bounce-short {
  animation: bounceShort 3s ease-in-out infinite;
}
</style>
