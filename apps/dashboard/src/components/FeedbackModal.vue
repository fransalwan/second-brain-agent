<script setup lang="ts">
import { ref } from 'vue'
import { supabase } from '../lib/supabase'
import { playNotificationSound } from '../lib/notifications'

const props = defineProps<{
  userId: string
  userEmail?: string | null
}>()

const isOpen = ref(false)
const category = ref<'fitur' | 'bug' | 'review'>('fitur')
const rating = ref<number>(5)
const feedbackText = ref('')
const isSubmitting = ref(false)
const isSubmitted = ref(false)

function toggleModal() {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    isSubmitted.value = false
  }
}

async function submitFeedback() {
  if (!feedbackText.value.trim() || isSubmitting.value) return
  isSubmitting.value = true

  try {
    const formattedContent = `[USER FEEDBACK] Kategori: ${category.value.toUpperCase()} | Rating: ${rating.value}/5 | Pesan: ${feedbackText.value.trim()}`
    
    // Save to notes with #feedback tag
    await supabase.from('notes').insert({
      user_id: props.userId,
      content: formattedContent,
      tags: ['feedback', category.value],
    })

    playNotificationSound('chime')
    isSubmitted.value = true
    feedbackText.value = ''
  } catch (err) {
    console.error('Failed to submit feedback:', err)
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div>
    <!-- Floating Trigger Button -->
    <button
      type="button"
      @click="toggleModal"
      class="fixed bottom-24 left-5 sm:bottom-7 sm:left-7 z-30 inline-flex items-center gap-2 rounded-2xl bg-white/95 px-3.5 py-2 text-xs font-bold text-gray-800 shadow-lg border border-gray-200/90 hover:bg-gray-50 hover:scale-105 active:scale-95 transition-all cursor-pointer backdrop-blur-xs"
      title="Beri Masukan / Request Fitur"
    >
      <span class="text-base select-none">💬</span>
      <span class="hidden sm:inline">Curhat / Request Fitur</span>
      <span class="sm:hidden">Feedback</span>
    </button>

    <!-- Feedback Modal -->
    <div
      v-if="isOpen"
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
    >
      <!-- Backdrop -->
      <div
        class="fixed inset-0 bg-black/40 backdrop-blur-sm transition-opacity"
        @click="isOpen = false"
      ></div>

      <!-- Modal Card -->
      <div
        class="relative w-full max-w-md rounded-3xl border border-gray-200 bg-white p-5 sm:p-6 shadow-2xl transition-all space-y-4"
      >
        <!-- Header -->
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-2.5">
            <span class="text-2xl select-none">💬</span>
            <div>
              <h3 class="text-sm font-bold text-gray-900">Curhat & Masukan Mahasiswa</h3>
              <p class="text-[11px] text-gray-500">Kritik, saran, & request fitur langsung dibaca developer</p>
            </div>
          </div>
          <button
            type="button"
            @click="isOpen = false"
            class="text-gray-400 hover:text-gray-600 p-1 text-sm cursor-pointer"
          >
            ✕
          </button>
        </div>

        <!-- Success State -->
        <div
          v-if="isSubmitted"
          class="py-6 text-center space-y-2"
        >
          <div class="text-3xl select-none">🎉</div>
          <h4 class="text-sm font-bold text-gray-900">Masukanmu Berhasil Terkirim!</h4>
          <p class="text-xs text-gray-600 max-w-xs mx-auto">
            Terima kasih banyak atas feedback jujurnya. Masukanmu akan menjadi prioritas pengembangan di update berikutnya.
          </p>
          <button
            type="button"
            @click="isOpen = false"
            class="mt-3 rounded-xl bg-gray-900 px-4 py-2 text-xs font-bold text-white hover:bg-black transition-colors cursor-pointer"
          >
            Tutup
          </button>
        </div>

        <!-- Form State -->
        <form
          v-else
          @submit.prevent="submitFeedback"
          class="space-y-3.5"
        >
          <!-- Category Chips -->
          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1.5">Topik Masukan:</label>
            <div class="grid grid-cols-3 gap-1.5 text-xs">
              <button
                type="button"
                @click="category = 'fitur'"
                class="rounded-xl py-2 px-2.5 font-bold transition-all text-center border cursor-pointer"
                :class="category === 'fitur' ? 'border-indigo-600 bg-indigo-50 text-indigo-900 shadow-2xs' : 'border-gray-200 text-gray-600 hover:bg-gray-50'"
              >
                🚀 Request Fitur
              </button>
              <button
                type="button"
                @click="category = 'bug'"
                class="rounded-xl py-2 px-2.5 font-bold transition-all text-center border cursor-pointer"
                :class="category === 'bug' ? 'border-rose-600 bg-rose-50 text-rose-900 shadow-2xs' : 'border-gray-200 text-gray-600 hover:bg-gray-50'"
              >
                🐛 Lapor Bug
              </button>
              <button
                type="button"
                @click="category = 'review'"
                class="rounded-xl py-2 px-2.5 font-bold transition-all text-center border cursor-pointer"
                :class="category === 'review' ? 'border-amber-600 bg-amber-50 text-amber-900 shadow-2xs' : 'border-gray-200 text-gray-600 hover:bg-gray-50'"
              >
                💡 Pengalaman
              </button>
            </div>
          </div>

          <!-- Star Rating -->
          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="text-xs font-semibold text-gray-700">Penilaian Kamu:</label>
              <span class="text-xs font-bold text-amber-600">{{ rating }} dari 5 Bintang</span>
            </div>
            <div class="flex items-center gap-1.5">
              <button
                v-for="star in [1, 2, 3, 4, 5]"
                :key="star"
                type="button"
                @click="rating = star"
                class="text-xl p-1 transition-transform hover:scale-110 cursor-pointer select-none"
              >
                {{ star <= rating ? '⭐' : '☆' }}
              </button>
            </div>
          </div>

          <!-- Message Textarea -->
          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">Pesan / Curhat Detail:</label>
            <textarea
              v-model="feedbackText"
              rows="3"
              required
              placeholder="Tulis apa saja: fitur yang kamu harapkan, kendala saat pakai di HP, atau kritik jujurmu..."
              class="w-full rounded-2xl border border-gray-300 bg-gray-50/70 p-3 text-xs text-gray-900 placeholder-gray-400 focus:bg-white focus:border-gray-900 focus:outline-none transition-colors"
            ></textarea>
          </div>

          <!-- Action Buttons -->
          <div class="flex items-center justify-between gap-3 pt-1">
            <button
              type="button"
              @click="isOpen = false"
              class="text-xs text-gray-500 hover:text-gray-800 cursor-pointer"
            >
              Batal
            </button>
            <button
              type="submit"
              :disabled="!feedbackText.trim() || isSubmitting"
              class="rounded-xl bg-gray-900 px-4 py-2 text-xs font-bold text-white hover:bg-black disabled:opacity-50 transition-colors shadow-xs cursor-pointer min-h-[36px]"
            >
              {{ isSubmitting ? 'Mengirim...' : 'Kirim Masukan' }}
            </button>
          </div>
        </form>

        <!-- Footer Alternative Link -->
        <div class="border-t border-gray-100 pt-2.5 text-center">
          <p class="text-[11px] text-gray-500">
            Ingin evaluasi lebih lengkap?
            <a
              href="https://docs.google.com/forms"
              target="_blank"
              class="font-semibold text-indigo-600 hover:underline"
            >
              Buka Google Form (2 Menit) ↗
            </a>
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
