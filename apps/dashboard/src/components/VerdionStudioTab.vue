<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

const props = defineProps<{
  userId: string
}>()

interface LocalLead {
  id: number
  business_name: string
  category: 'restaurant_cafe' | 'villa_hospitality' | 'rental_tour' | 'spa_salon' | 'other'
  maps_url: string
  rating: number
  review_count: number
  location_area: string
  contact_wa: string
  pain_point: string
  deal_value_idr: number
  status: 'lead' | 'wa_sent' | 'replied' | 'meeting_demo' | 'dp_paid' | 'completed' | 'retainer_active'
  notes: string | null
  created_at: string
}

interface LocalRetainer {
  id: number
  client_name: string
  monthly_rate_idr: number
  billing_day: number
  status: 'active' | 'paused'
  notes: string | null
}

const activeSubTab = ref<'pipeline' | 'sandbox' | 'outreach' | 'pricing'>('pipeline')
const loading = ref(true)
const errorMsg = ref<string | null>(null)
const successMsg = ref<string | null>(null)

// -------------------------------------------------------------
// LOCAL LEADS & PIPELINE DATA
// -------------------------------------------------------------
const leads = ref<LocalLead[]>([
  {
    id: 1,
    business_name: 'Canggu Breeze Cafe & Bakery',
    category: 'restaurant_cafe',
    maps_url: 'https://maps.google.com/?q=Canggu+Breeze+Cafe',
    rating: 4.8,
    review_count: 245,
    location_area: 'Jl. Pantai Batu Bolong, Canggu',
    contact_wa: '081234567890',
    pain_point: 'Invoice manual kertas sering hilang saat pesanan ramai, owner tidak bisa pantau omset harian dari jauh.',
    deal_value_idr: 15000000,
    status: 'dp_paid',
    notes: 'DP 50% (Rp 7.500.000) sudah masuk BCA. Target deployment kasir web dalam 5 hari.',
    created_at: new Date().toISOString(),
  },
  {
    id: 2,
    business_name: 'Uluwatu Sunset Villa Sanctuary',
    category: 'villa_hospitality',
    maps_url: 'https://maps.google.com/?q=Uluwatu+Sunset+Villa',
    rating: 4.9,
    review_count: 180,
    location_area: 'Pecatu, Uluwatu',
    contact_wa: '081987654321',
    pain_point: 'Booking dan invoice tamu masih manual via WhatsApp, rekap pengeluaran staf villa berantakan di Excel.',
    deal_value_idr: 22000000,
    status: 'meeting_demo',
    notes: 'Jadwal demo Zoom/temu offline besok jam 14:00 WITA dengan Owner (Bule expat).',
    created_at: new Date().toISOString(),
  },
  {
    id: 3,
    business_name: 'Seminyak MotoRent & Surf Camp',
    category: 'rental_tour',
    maps_url: 'https://maps.google.com/?q=Seminyak+MotoRent',
    rating: 4.6,
    review_count: 310,
    location_area: 'Jl. Kayu Aya, Seminyak',
    contact_wa: '082111223344',
    pain_point: 'Tidak ada tracking ketersediaan unit motor dan deposit paspor tamu sering tidak tercatat rapi.',
    deal_value_idr: 18000000,
    status: 'wa_sent',
    notes: 'Sudah dikirimkan video demo Loom 45 detik via WhatsApp manajer operasional.',
    created_at: new Date().toISOString(),
  },
])

const retainers = ref<LocalRetainer[]>([
  {
    id: 1,
    client_name: 'Canggu Breeze Cafe & Bakery',
    monthly_rate_idr: 750000,
    billing_day: 1,
    status: 'active',
    notes: 'Maintenance cloud hosting Supabase + backup database mingguan.',
  },
])

// -------------------------------------------------------------
// FINANCIAL & CASHFLOW METRICS (IDR FOCUS)
// -------------------------------------------------------------
const totalPipelineIdr = computed(() => {
  return leads.value.reduce((sum, l) => sum + (l.deal_value_idr || 0), 0)
})

const totalCashInIdr = computed(() => {
  return leads.value.reduce((sum, l) => {
    if (l.status === 'completed' || l.status === 'retainer_active') {
      return sum + l.deal_value_idr
    } else if (l.status === 'dp_paid') {
      return sum + l.deal_value_idr * 0.5 // 50% DP
    }
    return sum
  }, 0)
})

const activeRetainerMrrIdr = computed(() => {
  return retainers.value
    .filter((r) => r.status === 'active')
    .reduce((sum, r) => sum + (r.monthly_rate_idr || 0), 0)
})

const averageDealSizeIdr = computed(() => {
  if (leads.value.length === 0) return 0
  return Math.round(totalPipelineIdr.value / leads.value.length)
})

function formatRupiah(amount: number): string {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0,
  }).format(amount)
}

// -------------------------------------------------------------
// MODUL 1: ADD NEW GOOGLE MAPS LEAD STATE
// -------------------------------------------------------------
const showNewLeadModal = ref(false)
const newLead = ref({
  business_name: '',
  category: 'restaurant_cafe' as LocalLead['category'],
  maps_url: '',
  rating: 4.8,
  review_count: 150,
  location_area: 'Canggu, Bali',
  contact_wa: '',
  pain_point: '',
  deal_value_idr: 15000000,
  status: 'lead' as LocalLead['status'],
  notes: '',
})

function handleAddLead() {
  if (!newLead.value.business_name) return
  const created: LocalLead = {
    id: Date.now(),
    business_name: newLead.value.business_name,
    category: newLead.value.category,
    maps_url: newLead.value.maps_url || 'https://maps.google.com',
    rating: Number(newLead.value.rating) || 4.5,
    review_count: Number(newLead.value.review_count) || 50,
    location_area: newLead.value.location_area || 'Bali',
    contact_wa: newLead.value.contact_wa,
    pain_point: newLead.value.pain_point || 'Pencatatan nota dan laporan kasir masih manual.',
    deal_value_idr: Number(newLead.value.deal_value_idr) || 15000000,
    status: newLead.value.status,
    notes: newLead.value.notes,
    created_at: new Date().toISOString(),
  }
  leads.value.unshift(created)
  showNewLeadModal.value = false
  successMsg.value = `Prospek "${created.business_name}" berhasil ditambahkan ke Radar Verdion!`
  setTimeout(() => (successMsg.value = null), 3500)
}

function calculateLeadScore(lead: LocalLead): number {
  let score = 30
  if (lead.review_count >= 200) score += 30
  else if (lead.review_count >= 100) score += 20
  else if (lead.review_count >= 30) score += 10

  if (lead.rating >= 4.5) score += 20
  if (lead.contact_wa && lead.contact_wa.length >= 10) score += 20
  return Math.min(100, score)
}

// -------------------------------------------------------------
// MODUL 2: INSTANT MOCKUP SANDBOX (SENJATA DEMO KILAT 45 DETIK)
// -------------------------------------------------------------
const mockBusinessName = ref('Sunset Haven Resto & Bar')
const mockBusinessType = ref<'resto' | 'villa' | 'rental'>('resto')
const mockItems = ref([
  { id: 1, name: 'Truffle Fries Bowl', price: 55000, qty: 1 },
  { id: 2, name: 'Crispy Pork Belly / Ayam Bakar', price: 95000, qty: 2 },
  { id: 3, name: 'Dragonfruit Coconut Smoothie', price: 45000, qty: 1 },
])

const sandboxCart = ref<Array<{ name: string; price: number; qty: number }>>([
  { name: 'Crispy Pork Belly / Ayam Bakar', price: 95000, qty: 2 },
  { name: 'Dragonfruit Coconut Smoothie', price: 45000, qty: 1 },
])

const sandboxSubtotal = computed(() => {
  return sandboxCart.value.reduce((sum, item) => sum + item.price * item.qty, 0)
})
const sandboxTax = computed(() => Math.round(sandboxSubtotal.value * 0.10)) // 10% PB1
const sandboxTotal = computed(() => sandboxSubtotal.value + sandboxTax.value)

function addItemToSandbox(item: { name: string; price: number }) {
  const existing = sandboxCart.value.find((c) => c.name === item.name)
  if (existing) {
    existing.qty++
  } else {
    sandboxCart.value.push({ name: item.name, price: item.price, qty: 1 })
  }
}

function removeSandboxItem(index: number) {
  sandboxCart.value.splice(index, 1)
}

const loomScriptText = computed(() => {
  return `[Detik 00 - 15 | Sapaan Ramah & Masalah]
"Halo Bli/Kak [Nama Owner] & tim ${mockBusinessName.value}! Salam kenal, saya Frans dari Verdion Studio. Saya perhatikan ulasan di Google Maps kalian ramai sekali, tapi biasanya resto/bisnis yang ramai sering kewalahan rekap nota bon manual tiap malam..."

[Detik 15 - 35 | Tunjukkan Demo Nyata Berlogo Bisnis Mereka]
"Supaya staf gak pusing dan owner bisa pantau omset real-time, saya iseng buatkan prototype mini-sistem kasir & invoice khusus untuk ${mockBusinessName.value}. Lihat di layar ini: staf tinggal klik menu seperti ${mockItems.value[0]?.name || 'menu'}, klik terbitkan, invoice QRIS otomatis terbuat dalam 2 detik dan bisa langsung dikirim ke WhatsApp tamu..."

[Detik 35 - 45 | Ajakan Santai Tanpa Paksaan]
"Kalau kalian ingin sistem sederhana seperti ini dipasang langsung untuk kasir kalian minggu ini, kabari saya ya. Free uji coba dan tanpa komitmen apa pun. Sukses terus untuk ${mockBusinessName.value}!"`
})

const copiedScript = ref(false)
function copyLoomScript() {
  navigator.clipboard.writeText(loomScriptText.value)
  copiedScript.value = true
  setTimeout(() => (copiedScript.value = false), 2000)
}

// -------------------------------------------------------------
// MODUL 3: WHATSAPP OUTREACH & OBJECTION DESTROYER
// -------------------------------------------------------------
const selectedLeadForWa = ref<LocalLead>(leads.value[0])
const waVideoLink = ref('loom.com/share/verdion-canggu-demo')

const generatedWaPitch = computed(() => {
  const lead = selectedLeadForWa.value
  const cleanPhone = (lead.contact_wa || '').replace(/[^0-9]/g, '')
  const normalPhone = cleanPhone.startsWith('0') ? '62' + cleanPhone.slice(1) : cleanPhone

  const message = `Halo Bli/Kak dan tim ${lead.business_name}! 👋

Salam kenal, saya Frans dari Verdion Studio. 

Saya perhatikan ulasan ${lead.business_name} di Google Maps ramai sekali (rating ${lead.rating} ⭐ dari ${lead.review_count}+ ulasan, mantap banget!).

Biasanya tempat yang ramai seperti ini mulai mengalami kendala di ${lead.pain_point.toLowerCase()}.

Untuk membantu operasional staf dan memudahkan owner memantau omset dari HP, saya sempat membuatkan video demo singkat (45 detik) bagaimana sistem invoice & kasir digital otomatis khusus untuk ${lead.business_name}:
${waVideoLink.value}

Sistem ini bisa langsung dipakai staf via tablet/HP tanpa perlu ganti perangkat. Kalau berkenan dicoba atau mau tanya-tanya santai, silakan balas chat ini ya Kak. (Free, tanpa komitmen).

Terima kasih dan sukses terus untuk ${lead.business_name}! 🙏`

  return { message, normalPhone }
})

const copiedWa = ref(false)
function copyWaPitch() {
  navigator.clipboard.writeText(generatedWaPitch.value.message)
  copiedWa.value = true
  setTimeout(() => (copiedWa.value = false), 2000)
}

function openDirectWhatsApp() {
  const { normalPhone, message } = generatedWaPitch.value
  const url = `https://wa.me/${normalPhone}?text=${encodeURIComponent(message)}`
  window.open(url, '_blank')
}

// Local Objections Data
const objectionList = ref([
  {
    objection: 'Kami sudah pakai nota kertas / Excel bertahun-tahun dan masih jalan.',
    answer: 'Nota kertas sering tercecer, rawan basah/hilang, dan owner harus menunggu staf rekap berjam-jam tiap malam. Dengan sistem Verdion, omset terhitung otomatis per detik, struk langsung masuk ke WhatsApp pelanggan, dan owner bisa cek laporan laba bersih kapan pun dari pantai atau rumah.',
  },
  {
    objection: 'Kenapa gak langganan aplikasi POS kasir umum saja kayak Moka atau Pawoon?',
    answer: 'Aplikasi umum sifatnya kaku dan mewajibkan langganan bulanan mahal terus-menerus. Mereka tidak punya fitur kustom seperti invoice khusus villa, sistem deposit rental, atau format menu spesifik Anda. Di Verdion, sistem dibuat kustom 100% mengikuti SOP Anda, sekali bayar menjadi aset milik Anda selamanya tanpa biaya sewa software mahal.',
  },
  {
    objection: 'Staf kami gaptek, takut malah bikin antrean makin lambat.',
    answer: 'Sistem Verdion kami rancang seringkas chat WhatsApp. Tombol menu besar, jelas, dan hanya butuh 2 sentuhan untuk cetak nota. Kami berikan garansi pelatihan staf 15 menit langsung mahir, lengkap dengan nomor CS WhatsApp jika staf butuh bantuan.',
  },
  {
    objection: 'Berapa biayanya? Takut kemahalan buat tempat kami.',
    answer: 'Paket starter kami mulai dari Rp 8jt – Rp 15jt (bisa dicicil 2x: DP 50% dan pelunasan setelah sistem live dan staf lancar memakai). Investasi ini tertutup dalam 1–2 bulan hanya dari penghematan jam kerja staf dan pencegahan kebocoran kasir.',
  },
])

const copiedObjectionIdx = ref<number | null>(null)
function copyObjectionAnswer(text: string, idx: number) {
  navigator.clipboard.writeText(text)
  copiedObjectionIdx.value = idx
  setTimeout(() => (copiedObjectionIdx.value = null), 2000)
}

onMounted(() => {
  loading.value = false
})
</script>

<template>
  <div class="space-y-6">
    <!-- Top Executive Revenue Bar (Rupiah Focus) -->
    <div class="rounded-2xl border border-emerald-300/80 bg-gradient-to-br from-emerald-500/10 via-teal-500/5 to-white p-5 shadow-xs">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-emerald-100 pb-4">
        <div class="flex items-center gap-3">
          <div class="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 text-white font-black text-xl shadow-xs">
            🗺️
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h2 class="text-lg font-black tracking-tight text-gray-950 uppercase">VERDION STUDIO</h2>
              <span class="rounded-md bg-emerald-500/20 px-2 py-0.5 text-[11px] font-bold text-emerald-950 border border-emerald-400/30">
                LOCAL B2B DIGITIZATION ENGINE
              </span>
            </div>
            <p class="text-xs text-gray-600 mt-0.5 font-medium">
              Google Maps Prospecting • Resto/Villa/Rental Mini-ERP & Invoicing • Cash DP 50% • Monthly Cloud Retainers
            </p>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <button
            @click="showNewLeadModal = true"
            class="rounded-lg bg-emerald-600 text-white px-3.5 py-1.5 text-xs font-bold hover:bg-emerald-700 transition-colors shadow-2xs cursor-pointer flex items-center gap-1.5"
          >
            <span>+</span>
            <span>Tambah Target Maps</span>
          </button>
        </div>
      </div>

      <!-- Key Financial Metrics 4-Col Grid in IDR -->
      <div class="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
        <!-- Metric 1: Cash In Diterima -->
        <div class="rounded-xl border border-emerald-100 bg-white p-3.5 shadow-2xs">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-gray-500">Uang Masuk Tunai (Cash In)</span>
            <span class="rounded-full bg-emerald-100 px-1.5 py-0.2 text-[10px] font-bold text-emerald-800">
              DP & Lunas
            </span>
          </div>
          <div class="mt-2">
            <span class="text-lg sm:text-xl font-black text-emerald-800">{{ formatRupiah(totalCashInIdr) }}</span>
            <p class="text-[11px] text-gray-500 mt-0.5">Uang kas bersih masuk rekening</p>
          </div>
        </div>

        <!-- Metric 2: Total Pipeline Deals -->
        <div class="rounded-xl border border-emerald-100 bg-white p-3.5 shadow-2xs">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-gray-500">Total Nilai Pipeline</span>
            <span class="rounded-full bg-blue-100 px-1.5 py-0.2 text-[10px] font-bold text-blue-800">
              {{ leads.length }} Prospek
            </span>
          </div>
          <div class="mt-2">
            <div class="text-lg sm:text-xl font-black text-gray-900">
              {{ formatRupiah(totalPipelineIdr) }}
            </div>
            <p class="text-[11px] text-gray-500 mt-0.5">
              Rata-rata: <strong>{{ formatRupiah(averageDealSizeIdr) }}</strong>/klien
            </p>
          </div>
        </div>

        <!-- Metric 3: Active Retainer MRR -->
        <div class="rounded-xl border border-emerald-100 bg-white p-3.5 shadow-2xs">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-gray-500">Passive Retainer MRR</span>
            <span class="rounded-full bg-indigo-100 px-1.5 py-0.2 text-[10px] font-bold text-indigo-800">
              Bulanan
            </span>
          </div>
          <div class="mt-2">
            <span class="text-lg sm:text-xl font-black text-indigo-900">{{ formatRupiah(activeRetainerMrrIdr) }}</span>
            <span class="text-xs text-gray-400">/bulan</span>
            <p class="text-[11px] text-gray-500 mt-0.5">
              Dari {{ retainers.length }} klien pemeliharaan server
            </p>
          </div>
        </div>

        <!-- Metric 4: Target Closing Bulan Ini -->
        <div class="rounded-xl border border-emerald-100 bg-white p-3.5 shadow-2xs">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-gray-500">Target Omset Verdion</span>
            <span class="rounded-full bg-amber-100 px-1.5 py-0.2 text-[10px] font-bold text-amber-900">
              Target
            </span>
          </div>
          <div class="mt-2">
            <span class="text-lg sm:text-xl font-black text-amber-900">Rp 40.000.000</span>
            <div class="mt-1 w-full bg-gray-100 rounded-full h-1.5 overflow-hidden">
              <div
                class="bg-emerald-500 h-1.5 rounded-full transition-all duration-500"
                :style="{ width: `${Math.min(100, Math.round((totalCashInIdr / 40000000) * 100))}%` }"
              ></div>
            </div>
            <p class="text-[10px] text-gray-500 mt-1">
              Progress: {{ Math.min(100, Math.round((totalCashInIdr / 40000000) * 100)) }}% dari target
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Alert Notifications -->
    <div v-if="successMsg" class="rounded-xl bg-emerald-50 border border-emerald-200 p-3 text-xs font-semibold text-emerald-800 flex items-center justify-between">
      <span>✅ {{ successMsg }}</span>
      <button @click="successMsg = null" class="text-emerald-600 hover:text-emerald-900 cursor-pointer">✕</button>
    </div>
    <div v-if="errorMsg" class="rounded-xl bg-rose-50 border border-rose-200 p-3 text-xs font-semibold text-rose-800 flex items-center justify-between">
      <span>⚠️ {{ errorMsg }}</span>
      <button @click="errorMsg = null" class="text-rose-600 hover:text-rose-900 cursor-pointer">✕</button>
    </div>

    <!-- Sub-Tabs Navigation for Local Digitization Command Center -->
    <div class="flex items-center gap-2 border-b border-gray-200 overflow-x-auto no-scrollbar pb-1">
      <button
        @click="activeSubTab = 'pipeline'"
        class="flex items-center gap-1.5 px-3 py-2 text-xs font-bold rounded-lg transition-all cursor-pointer whitespace-nowrap"
        :class="activeSubTab === 'pipeline' ? 'bg-gray-900 text-white shadow-xs' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
      >
        <span>📍</span>
        <span>Pipeline Prospek Maps ({{ leads.length }})</span>
      </button>

      <button
        @click="activeSubTab = 'sandbox'"
        class="flex items-center gap-1.5 px-3 py-2 text-xs font-bold rounded-lg transition-all cursor-pointer whitespace-nowrap"
        :class="activeSubTab === 'sandbox' ? 'bg-gray-900 text-white shadow-xs' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
      >
        <span>📱</span>
        <span>Instant Mockup & Loom Script</span>
      </button>

      <button
        @click="activeSubTab = 'outreach'"
        class="flex items-center gap-1.5 px-3 py-2 text-xs font-bold rounded-lg transition-all cursor-pointer whitespace-nowrap"
        :class="activeSubTab === 'outreach' ? 'bg-gray-900 text-white shadow-xs' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
      >
        <span>💬</span>
        <span>WhatsApp Pitch & Battlecards</span>
      </button>

      <button
        @click="activeSubTab = 'pricing'"
        class="flex items-center gap-1.5 px-3 py-2 text-xs font-bold rounded-lg transition-all cursor-pointer whitespace-nowrap"
        :class="activeSubTab === 'pricing' ? 'bg-gray-900 text-white shadow-xs' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
      >
        <span>🏷️</span>
        <span>Paket Harga & Retainer Bulanan</span>
      </button>
    </div>

    <!-- ============================================================== -->
    <!-- SUB-TAB 1: PIPELINE PROSPEK GOOGLE MAPS                        -->
    <!-- ============================================================== -->
    <div v-if="activeSubTab === 'pipeline'" class="space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-sm font-bold text-gray-900 flex items-center gap-1.5">
            <span>📍</span>
            <span>Target Bisnis Lokal (Resto, Cafe, Villa, Rental, Spa)</span>
          </h3>
          <p class="text-[11px] text-gray-500 mt-0.5">
            Data prospek yang ditemukan di Google Maps beserta diagnosis kendala operasional mereka.
          </p>
        </div>
      </div>

      <!-- Leads Table -->
      <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-2xs overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead class="bg-gray-50 text-gray-500 uppercase text-[10px] font-bold border-b border-gray-200">
            <tr>
              <th class="py-2.5 px-3">Nama Bisnis & Kategori</th>
              <th class="py-2.5 px-3">Maps & Rating</th>
              <th class="py-2.5 px-3">Kontak WhatsApp</th>
              <th class="py-2.5 px-3">Kendala Operasional (Pain Point)</th>
              <th class="py-2.5 px-3">Nilai Deal</th>
              <th class="py-2.5 px-3">Status</th>
              <th class="py-2.5 px-3">Aksi</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-for="lead in leads" :key="lead.id" class="hover:bg-gray-50/70 transition-colors">
              <td class="py-3 px-3">
                <div class="font-bold text-gray-900">{{ lead.business_name }}</div>
                <div class="text-[10px] text-gray-500 capitalize">{{ lead.category.replace('_', ' ') }} • {{ lead.location_area }}</div>
              </td>
              <td class="py-3 px-3">
                <div class="font-bold text-amber-600 flex items-center gap-1">
                  <span>⭐ {{ lead.rating }}</span>
                  <span class="text-[10px] text-gray-400">({{ lead.review_count }} ulasan)</span>
                </div>
                <div class="flex items-center gap-1.5 mt-0.5">
                  <span
                    class="rounded-full px-1.5 py-0.2 text-[9px] font-black"
                    :class="calculateLeadScore(lead) >= 90 ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'"
                  >
                    Skor: {{ calculateLeadScore(lead) }}/100
                  </span>
                  <a :href="lead.maps_url" target="_blank" class="text-[10px] text-blue-600 hover:underline">
                    Maps ↗
                  </a>
                </div>
              </td>
              <td class="py-3 px-3 font-mono text-[11px] text-gray-800">
                {{ lead.contact_wa || '-' }}
              </td>
              <td class="py-3 px-3 max-w-xs text-gray-600 text-[11px]">
                {{ lead.pain_point }}
              </td>
              <td class="py-3 px-3">
                <span class="font-black text-gray-900 block">{{ formatRupiah(lead.deal_value_idr) }}</span>
                <span v-if="lead.status === 'dp_paid'" class="text-[10px] text-emerald-700 font-bold block">DP 50% Masuk</span>
              </td>
              <td class="py-3 px-3">
                <span
                  class="rounded-full px-2 py-0.5 text-[10px] font-bold uppercase"
                  :class="{
                    'bg-emerald-100 text-emerald-800': ['dp_paid', 'completed', 'retainer_active'].includes(lead.status),
                    'bg-indigo-100 text-indigo-800': lead.status === 'meeting_demo',
                    'bg-amber-100 text-amber-800': lead.status === 'replied',
                    'bg-blue-100 text-blue-800': lead.status === 'wa_sent',
                    'bg-gray-100 text-gray-700': lead.status === 'lead',
                  }"
                >
                  {{ lead.status.replace('_', ' ') }}
                </span>
              </td>
              <td class="py-3 px-3">
                <button
                  @click="selectedLeadForWa = lead; activeSubTab = 'outreach'"
                  class="rounded bg-gray-900 text-white px-2 py-1 text-[11px] font-bold hover:bg-gray-800 cursor-pointer shadow-2xs"
                >
                  💬 Chat WA
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ============================================================== -->
    <!-- SUB-TAB 2: INSTANT MOCKUP SANDBOX (DEMO KILAT 45 DETIK)         -->
    <!-- ============================================================== -->
    <div v-else-if="activeSubTab === 'sandbox'" class="space-y-6">
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <!-- Left: Mockup Customizer -->
        <div class="lg:col-span-5 space-y-4">
          <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-2xs space-y-3.5">
            <div class="border-b border-gray-100 pb-2.5">
              <h3 class="text-sm font-bold text-gray-900 flex items-center gap-1.5">
                <span>📱</span>
                <span>Kustomisasi Demo Klien</span>
              </h3>
              <p class="text-[11px] text-gray-500 mt-0.5">
                Ketik nama resto/villa target untuk membuatkan demo kasir & invoice berlogo mereka.
              </p>
            </div>

            <div>
              <label class="block text-[11px] font-semibold text-gray-700 mb-1">Nama Tempat / Bisnis Target:</label>
              <input
                type="text"
                v-model="mockBusinessName"
                class="w-full rounded-lg border border-gray-300 px-3 py-1.5 text-xs text-gray-900 font-bold focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500"
              />
            </div>

            <div>
              <label class="block text-[11px] font-semibold text-gray-700 mb-1">Kategori Tempat:</label>
              <div class="grid grid-cols-3 gap-1.5">
                <button
                  type="button"
                  @click="mockBusinessType = 'resto'; mockBusinessName = 'Sunset Haven Resto & Bar'"
                  class="rounded px-2 py-1 text-[11px] font-bold cursor-pointer transition-colors"
                  :class="mockBusinessType === 'resto' ? 'bg-emerald-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
                >
                  Resto / Cafe
                </button>
                <button
                  type="button"
                  @click="mockBusinessType = 'villa'; mockBusinessName = 'Uluwatu Sunset Villa Sanctuary'"
                  class="rounded px-2 py-1 text-[11px] font-bold cursor-pointer transition-colors"
                  :class="mockBusinessType === 'villa' ? 'bg-emerald-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
                >
                  Villa / Hotel
                </button>
                <button
                  type="button"
                  @click="mockBusinessType = 'rental'; mockBusinessName = 'Seminyak MotoRent & Surf Camp'"
                  class="rounded px-2 py-1 text-[11px] font-bold cursor-pointer transition-colors"
                  :class="mockBusinessType === 'rental' ? 'bg-emerald-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
                >
                  Rental / Tour
                </button>
              </div>
            </div>

            <!-- Pre-loaded Menu Items -->
            <div>
              <label class="block text-[11px] font-semibold text-gray-700 mb-1.5">Contoh Menu / Layanan di Tempat Mereka:</label>
              <div class="space-y-2">
                <div v-for="item in mockItems" :key="item.id" class="flex items-center justify-between p-2 rounded-lg bg-gray-50 border border-gray-200 text-xs">
                  <div>
                    <span class="font-bold text-gray-800">{{ item.name }}</span>
                    <span class="text-gray-500 block text-[10px]">{{ formatRupiah(item.price) }}</span>
                  </div>
                  <button
                    @click="addItemToSandbox(item)"
                    class="rounded bg-emerald-600 text-white px-2 py-0.5 text-[10px] font-bold hover:bg-emerald-700 cursor-pointer"
                  >
                    + Tambah Pesanan
                  </button>
                </div>
              </div>
            </div>

            <!-- Naskah Video 45 Detik Loom -->
            <div class="rounded-xl border border-amber-200 bg-amber-50/50 p-3 space-y-2">
              <div class="flex items-center justify-between">
                <span class="text-[10px] font-bold text-amber-900 uppercase">Naskah Video Loom (45 Detik):</span>
                <button
                  @click="copyLoomScript"
                  class="rounded bg-amber-600 text-white px-2 py-0.5 text-[10px] font-bold hover:bg-amber-700 cursor-pointer"
                >
                  {{ copiedScript ? '✅ Disalin' : '📋 Salin Naskah' }}
                </button>
              </div>
              <pre class="text-[11px] font-sans text-gray-800 whitespace-pre-wrap leading-relaxed select-all">{{ loomScriptText }}</pre>
            </div>
          </div>
        </div>

        <!-- Right: Live Interactive Mini-POS & Invoice Sandbox -->
        <div class="lg:col-span-7 space-y-4">
          <div class="rounded-2xl border-2 border-gray-800 bg-gray-950 p-4 shadow-xl text-white space-y-4">
            <!-- Simulated Tablet Header -->
            <div class="flex items-center justify-between border-b border-gray-800 pb-3">
              <div class="flex items-center gap-2">
                <div class="h-3 w-3 rounded-full bg-emerald-500 animate-pulse"></div>
                <span class="font-black text-sm uppercase tracking-wide text-emerald-400">{{ mockBusinessName }}</span>
              </div>
              <span class="text-[10px] font-mono text-gray-400">Verdion Local Ops • Mode Kasir HP/Tablet</span>
            </div>

            <!-- POS Screen & Live Bill -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-gray-900">
              <!-- Left: Touch Items Grid -->
              <div class="space-y-2">
                <span class="text-[10px] font-bold text-gray-400 uppercase tracking-wider block">Menu / Item Sentuh:</span>
                <div class="space-y-1.5">
                  <button
                    v-for="item in mockItems"
                    :key="item.id"
                    @click="addItemToSandbox(item)"
                    class="w-full text-left p-2.5 rounded-lg bg-gray-800 text-white hover:bg-emerald-700 transition-colors border border-gray-700 cursor-pointer flex justify-between items-center text-xs"
                  >
                    <span class="font-medium truncate">{{ item.name }}</span>
                    <span class="font-bold text-emerald-300 text-[11px]">{{ formatRupiah(item.price) }}</span>
                  </button>
                </div>
              </div>

              <!-- Right: Live Bill & Invoice Simulator -->
              <div class="rounded-xl bg-white p-3.5 space-y-3 flex flex-col justify-between border border-gray-200">
                <div class="space-y-2">
                  <div class="text-center border-b border-gray-100 pb-2">
                    <span class="font-black text-xs block uppercase text-gray-900">{{ mockBusinessName }}</span>
                    <span class="text-[10px] text-gray-400 font-mono">Invoice #V-{{ Date.now().toString().slice(-4) }}</span>
                  </div>

                  <!-- Cart Items -->
                  <div class="space-y-1 text-xs max-h-36 overflow-y-auto">
                    <div v-for="(cartItem, idx) in sandboxCart" :key="idx" class="flex justify-between items-center text-[11px]">
                      <div class="flex items-center gap-1.5">
                        <button @click="removeSandboxItem(idx)" class="text-rose-500 hover:text-rose-700 cursor-pointer font-bold">×</button>
                        <span class="text-gray-800">{{ cartItem.qty }}x {{ cartItem.name }}</span>
                      </div>
                      <span class="font-bold text-gray-900">{{ formatRupiah(cartItem.price * cartItem.qty) }}</span>
                    </div>
                  </div>
                </div>

                <!-- Total & QRIS simulation -->
                <div class="border-t border-gray-200 pt-2 space-y-2">
                  <div class="flex justify-between text-xs font-black text-gray-950">
                    <span>TOTAL BAYAR:</span>
                    <span class="text-emerald-700 text-sm">{{ formatRupiah(sandboxTotal) }}</span>
                  </div>
                  <div class="rounded bg-emerald-50 p-2 text-center border border-emerald-200">
                    <span class="text-[10px] font-bold text-emerald-900 block">📱 QRIS OTOMATIS TERBIT</span>
                    <span class="text-[9px] text-gray-500">Staf klik kirim ➔ Struk masuk ke WhatsApp tamu</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Owner Insight Bar -->
            <div class="rounded-xl bg-gray-900 border border-gray-800 p-2.5 flex items-center justify-between text-xs">
              <span class="text-gray-400 text-[11px]">👀 Pantauan Owner (Real-time di HP):</span>
              <span class="text-emerald-400 font-bold">Omset Hari Ini: Rp 4.250.000 (34 Transaksi)</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ============================================================== -->
    <!-- SUB-TAB 3: WHATSAPP OUTREACH & OBJECTION DESTROYER             -->
    <!-- ============================================================== -->
    <div v-else-if="activeSubTab === 'outreach'" class="space-y-6">
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <!-- Left: WhatsApp Pitch Generator -->
        <div class="lg:col-span-6 space-y-4">
          <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-2xs space-y-3.5">
            <div class="border-b border-gray-100 pb-2.5 flex items-center justify-between">
              <div>
                <h3 class="text-sm font-bold text-gray-900 flex items-center gap-1.5">
                  <span>💬</span>
                  <span>WhatsApp Pitch ke Owner / Manajer</span>
                </h3>
                <p class="text-[11px] text-gray-500 mt-0.5">Pendekatan sopan, tanpa hard-selling, langsung memberi nilai.</p>
              </div>
              <button
                @click="openDirectWhatsApp"
                class="rounded-lg bg-emerald-600 text-white px-3 py-1.5 text-xs font-bold hover:bg-emerald-700 transition-colors shadow-2xs cursor-pointer flex items-center gap-1"
              >
                <span>📲</span>
                <span>Buka WhatsApp Web</span>
              </button>
            </div>

            <!-- Target Selector -->
            <div>
              <label class="block text-[11px] font-semibold text-gray-700 mb-1">Pilih Target Bisnis:</label>
              <select v-model="selectedLeadForWa" class="w-full rounded-lg border border-gray-300 p-2 text-xs">
                <option v-for="l in leads" :key="l.id" :value="l">
                  {{ l.business_name }} ({{ l.contact_wa }})
                </option>
              </select>
            </div>

            <div>
              <label class="block text-[11px] font-semibold text-gray-700 mb-1">Link Video Demo Loom (45 Detik):</label>
              <input
                type="text"
                v-model="waVideoLink"
                class="w-full rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-mono text-gray-800"
              />
            </div>

            <!-- Formatted WhatsApp Message -->
            <div>
              <div class="flex items-center justify-between mb-1">
                <label class="text-[11px] font-semibold text-gray-700">Draf Pesan WhatsApp Siap Kirim:</label>
                <button
                  @click="copyWaPitch"
                  class="rounded bg-gray-900 text-white px-2 py-0.5 text-[10px] font-bold hover:bg-gray-800 cursor-pointer"
                >
                  {{ copiedWa ? '✅ Disalin' : '📋 Salin Pesan' }}
                </button>
              </div>
              <pre class="bg-emerald-50/50 p-3 rounded-xl border border-emerald-200 text-xs font-sans whitespace-pre-wrap select-all text-gray-900 leading-relaxed">{{ generatedWaPitch.message }}</pre>
            </div>
          </div>
        </div>

        <!-- Right: Local Objection Destroyer -->
        <div class="lg:col-span-6 space-y-4">
          <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-2xs space-y-3.5">
            <div class="border-b border-gray-100 pb-2.5">
              <h3 class="text-sm font-bold text-gray-900 flex items-center gap-1.5">
                <span>🛡️</span>
                <span>Objection Destroyer (Jawaban Saat Klien Ragu)</span>
              </h3>
              <p class="text-[11px] text-gray-500 mt-0.5">1-Click Copy jawaban profesional saat owner resto/villa bertanya.</p>
            </div>

            <div class="space-y-3">
              <div
                v-for="(obj, idx) in objectionList"
                :key="idx"
                class="p-3 rounded-lg border border-gray-200 bg-gray-50/60 space-y-2 text-xs"
              >
                <div class="flex items-start justify-between gap-2">
                  <span class="font-bold text-gray-900 flex items-center gap-1">
                    <span class="text-rose-600">❓</span>
                    <span>"{{ obj.objection }}"</span>
                  </span>
                  <button
                    @click="copyObjectionAnswer(obj.answer, idx)"
                    class="rounded bg-white border border-gray-300 px-2 py-0.5 text-[10px] font-bold text-gray-700 hover:bg-gray-100 transition-colors shrink-0 cursor-pointer shadow-2xs"
                  >
                    {{ copiedObjectionIdx === idx ? '✅ Disalin' : '📋 Salin Jawaban' }}
                  </button>
                </div>
                <p class="text-[11px] text-gray-700 leading-relaxed bg-white p-2 rounded border border-gray-200/50">
                  {{ obj.answer }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ============================================================== -->
    <!-- SUB-TAB 4: PAKET HARGA & RETAINER BULANAN                      -->
    <!-- ============================================================== -->
    <div v-else-if="activeSubTab === 'pricing'" class="space-y-6">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-base font-black text-gray-900 flex items-center gap-2">
            <span>🏷️</span>
            <span>Paket Layanan Digitalisasi & Retainer Bulanan</span>
          </h3>
          <p class="text-xs text-gray-500 mt-0.5">
            Dua sumber pendapatan: Uang Muka (DP 50% di awal) + Biaya Pemeliharaan Server Rutin Bulanan.
          </p>
        </div>
      </div>

      <!-- 3 Tier Local Packages -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- Tier 1 -->
        <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-2xs space-y-3">
          <div class="flex items-center justify-between">
            <span class="rounded bg-gray-100 text-gray-800 text-[10px] font-extrabold px-2 py-0.5 uppercase">Tier 1 • Starter</span>
            <span class="text-sm font-black text-gray-900">Rp 10.000.000</span>
          </div>
          <h4 class="text-sm font-bold text-gray-950">Digital Kasir & Invoice QRIS</h4>
          <p class="text-xs text-gray-600 leading-relaxed">
            Cocok untuk Cafe / Toko / Rental kecil yang ingin mengganti nota kertas menjadi struk digital WhatsApp.
          </p>
          <ul class="text-[11px] text-gray-600 space-y-1 pt-1 border-t border-gray-100">
            <li>✓ Kasir Web HP/Tablet</li>
            <li>✓ Auto Invoice PDF & WhatsApp</li>
            <li>✓ QRIS Statis Otomatis</li>
            <li>✓ Pelatihan Staf 1 Hari</li>
          </ul>
        </div>

        <!-- Tier 2 -->
        <div class="rounded-xl border-2 border-emerald-500 bg-gradient-to-br from-emerald-50/50 to-white p-4 shadow-2xs space-y-3 relative">
          <div class="flex items-center justify-between">
            <span class="rounded bg-emerald-600 text-white text-[10px] font-extrabold px-2 py-0.5 uppercase">Paling Laris</span>
            <span class="text-sm font-black text-emerald-950">Rp 20.000.000</span>
          </div>
          <h4 class="text-sm font-bold text-gray-950">Mini-ERP Operasional Resto & Villa</h4>
          <p class="text-xs text-gray-600 leading-relaxed">
            Paket komplit untuk Restoran ramai atau Villa Management dengan pencatatan stok dan pengeluaran harian.
          </p>
          <ul class="text-[11px] text-gray-700 space-y-1 pt-1 border-t border-emerald-100">
            <li>✓ Semua Fitur Starter</li>
            <li>✓ Pencatatan Pengeluaran & Foto Nota</li>
            <li>✓ Multi-User: Akun Kasir vs Akun Owner</li>
            <li>✓ Dashboard Omset Real-time Jarak Jauh</li>
          </ul>
        </div>

        <!-- Tier 3 -->
        <div class="rounded-xl border border-indigo-200 bg-white p-4 shadow-2xs space-y-3">
          <div class="flex items-center justify-between">
            <span class="rounded bg-indigo-100 text-indigo-900 text-[10px] font-extrabold px-2 py-0.5 uppercase">Enterprise</span>
            <span class="text-sm font-black text-indigo-950">Rp 35.000.000</span>
          </div>
          <h4 class="text-sm font-bold text-gray-950">Multi-Cabang & Auto WhatsApp Report</h4>
          <p class="text-xs text-gray-600 leading-relaxed">
            Untuk pemilik beberapa resto/villa sekaligus yang ingin rekap omset otomatis masuk ke WhatsApp tiap jam 22:00.
          </p>
          <ul class="text-[11px] text-gray-600 space-y-1 pt-1 border-t border-gray-100">
            <li>✓ Semua Fitur Mini-ERP</li>
            <li>✓ Multi-Cabang / Multi-Outlet</li>
            <li>✓ Bot WhatsApp Otomatis ke HP Owner</li>
            <li>✓ Garansi SLA Support 24/7</li>
          </ul>
        </div>
      </div>

      <!-- Retainer Maintenance Box -->
      <div class="rounded-xl border border-indigo-200 bg-gradient-to-r from-indigo-50/70 via-white to-indigo-50/30 p-4 space-y-2">
        <div class="flex items-center justify-between">
          <h4 class="text-sm font-black text-indigo-950 flex items-center gap-1.5">
            <span>🔄</span>
            <span>Pendapatan Pasif Rutin: Retainer Maintenance Cloud</span>
          </h4>
          <span class="rounded bg-indigo-600 text-white text-[10px] font-bold px-2 py-0.5">
            Rp 750.000 – Rp 1.500.000 / bulan / klien
          </span>
        </div>
        <p class="text-xs text-gray-600 leading-relaxed">
          Setelah aplikasi live, klien dikenakan biaya operasional cloud & backup mingguan. 10 klien aktif = <strong>Rp 7.500.000 – Rp 15.000.000 per bulan pasif</strong> tanpa perlu mencari klien baru lagi!
        </p>
      </div>
    </div>

    <!-- MODAL: TAMBAH TARGET MAPS BARU -->
    <div v-if="showNewLeadModal" class="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/50 p-4 backdrop-blur-xs">
      <div class="w-full max-w-lg rounded-2xl bg-white p-5 shadow-xl space-y-4">
        <h3 class="text-base font-bold text-gray-900 flex items-center gap-1.5">
          <span>📍</span>
          <span>Tambah Target Bisnis dari Google Maps</span>
        </h3>
        <div class="space-y-3 text-xs">
          <div>
            <label class="block font-semibold text-gray-700 mb-1">Nama Tempat / Bisnis:</label>
            <input type="text" v-model="newLead.business_name" class="w-full rounded-lg border border-gray-300 p-2" placeholder="e.g. Canggu Surf Cafe" />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-semibold text-gray-700 mb-1">Kategori:</label>
              <select v-model="newLead.category" class="w-full rounded-lg border border-gray-300 p-2">
                <option value="restaurant_cafe">Restaurant / Cafe / Bar</option>
                <option value="villa_hospitality">Villa / Hotel / Homestay</option>
                <option value="rental_tour">Rental Motor/Mobil / Tour</option>
                <option value="spa_salon">Spa / Salon / Wellness</option>
                <option value="other">Bisnis Lainnya</option>
              </select>
            </div>
            <div>
              <label class="block font-semibold text-gray-700 mb-1">Area Lokasi:</label>
              <input type="text" v-model="newLead.location_area" class="w-full rounded-lg border border-gray-300 p-2" placeholder="e.g. Canggu, Bali" />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-semibold text-gray-700 mb-1">Rating Maps & Jumlah Review:</label>
              <div class="flex gap-2">
                <input type="number" step="0.1" v-model.number="newLead.rating" class="w-1/2 rounded-lg border border-gray-300 p-2" placeholder="4.8" />
                <input type="number" v-model.number="newLead.review_count" class="w-1/2 rounded-lg border border-gray-300 p-2" placeholder="150" />
              </div>
            </div>
            <div>
              <label class="block font-semibold text-gray-700 mb-1">Nomor WhatsApp Bisnis / Owner:</label>
              <input type="text" v-model="newLead.contact_wa" class="w-full rounded-lg border border-gray-300 p-2" placeholder="0812xxxx" />
            </div>
          </div>
          <div>
            <label class="block font-semibold text-gray-700 mb-1">Kendala Operasional yang Dideteksi:</label>
            <input type="text" v-model="newLead.pain_point" class="w-full rounded-lg border border-gray-300 p-2" placeholder="e.g. Nota masih kertas manual, sering salah hitung stok kasir" />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-semibold text-gray-700 mb-1">Estimasi Nilai Kontrak (Rp):</label>
              <input type="number" step="1000000" v-model.number="newLead.deal_value_idr" class="w-full rounded-lg border border-gray-300 p-2" />
            </div>
            <div>
              <label class="block font-semibold text-gray-700 mb-1">Tahap Status Prospek:</label>
              <select v-model="newLead.status" class="w-full rounded-lg border border-gray-300 p-2">
                <option value="lead">Lead Baru Terdata</option>
                <option value="wa_sent">Video Demo WA Terkirim</option>
                <option value="replied">Owner Membalas Chat</option>
                <option value="meeting_demo">Meeting / Demo Offline</option>
                <option value="dp_paid">DP 50% Sudah Diterima</option>
                <option value="completed">Aplikasi Live & Lunas</option>
              </select>
            </div>
          </div>
        </div>
        <div class="flex justify-end gap-2 pt-2 border-t">
          <button @click="showNewLeadModal = false" class="px-3 py-1.5 text-xs font-semibold text-gray-600 cursor-pointer">Batal</button>
          <button @click="handleAddLead" class="px-4 py-1.5 text-xs font-bold text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 cursor-pointer">
            Simpan Prospek
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
