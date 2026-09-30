<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { supabase } from '../lib/supabase'

const props = defineProps<{
  userId: string
}>()

interface CareerGoal {
  id?: number
  user_id: string
  month: string
  target_revenue_usd: number
  target_proposals_count: number
  current_badge: string
  usd_to_idr_rate: number
  company_name: string
  min_project_budget_usd: number
  monthly_profit_target_idr: number
}

interface UpworkProposal {
  id: number
  job_title: string
  bid_amount_usd: number | null
  connects_spent: number
  client_country: string | null
  job_url: string | null
  status: string
  notes: string | null
  client_spend_usd: number
  client_hire_rate: number
  client_rating: number
  hook_text: string | null
  proposal_score: number
  submitted_at: string
}

interface UpworkContract {
  id: number
  proposal_id: number | null
  client_name: string
  project_title: string
  contract_type: string
  rate_or_budget_usd: number
  total_earned_usd: number
  status: string
  rating: number | null
  feedback: string | null
  deadline: string | null
  created_at: string
}

interface UpworkMilestone {
  id: number
  contract_id: number
  title: string
  amount_usd: number
  escrow_funded: boolean
  status: string
  submitted_at: string | null
  auto_release_deadline: string | null
  deliverables_notes: string | null
  created_at: string
}

interface VerdionChangeRequest {
  id: number
  contract_id: number
  request_title: string
  estimated_hours: number
  additional_price_usd: number
  status: string
  notes: string | null
  created_at: string
}

interface VerdionSubcontractorLog {
  id: number
  contract_id: number
  subdev_name: string
  task_scope: string
  payout_idr: number
  status: string
  created_at: string
}

interface VerdionRetainer {
  id: number
  client_name: string
  monthly_rate_usd: number
  start_date: string
  billing_day: number
  status: string
  notes: string | null
  created_at: string
}

const activeSubTab = ref<'deals' | 'milestones' | 'arbitrage' | 'retainers'>('deals')
const loading = ref(true)
const saving = ref(false)
const errorMsg = ref<string | null>(null)
const successMsg = ref<string | null>(null)

// Data state
const careerGoal = ref<CareerGoal | null>(null)
const proposals = ref<UpworkProposal[]>([])
const contracts = ref<UpworkContract[]>([])
const milestones = ref<UpworkMilestone[]>([])
const changeRequests = ref<VerdionChangeRequest[]>([])
const subdevLogs = ref<VerdionSubcontractorLog[]>([])
const retainers = ref<VerdionRetainer[]>([])

// Exchange rate default
const usdRate = computed(() => careerGoal.value?.usd_to_idr_rate || 16200)

// Whale Vetting Form
const vettingPaymentVerified = ref(true)
const vettingTotalSpend = ref(25000)
const vettingHireRate = ref(70)
const vettingAvgRate = ref(35)

const computedVettingScore = computed(() => {
  let score = 0
  if (vettingPaymentVerified.value) score += 25
  if (vettingTotalSpend.value >= 10000) score += 35
  else if (vettingTotalSpend.value >= 2000) score += 20
  else if (vettingTotalSpend.value >= 500) score += 10

  if (vettingHireRate.value >= 60) score += 20
  else if (vettingHireRate.value >= 40) score += 10

  if (vettingAvgRate.value >= 30) score += 20
  else if (vettingAvgRate.value >= 20) score += 10

  return Math.min(100, score)
})

// 2-Second Hook Generator Workbench
const hookClientProblem = ref('Supabase query latency under load')
const hookVerdionSolution = ref('pre-tested async pgBouncer pooling')
const hookDemoLink = ref('loom.com/share/verdion')
const hookClarifyingQuestion = ref('Have you configured pool limits?')

const generatedHook = computed(() => {
  return `Saw your bottleneck with ${hookClientProblem.value}. Verdion has resolved this exact issue using ${hookVerdionSolution.value}. Live demo: ${hookDemoLink.value}. ${hookClarifyingQuestion.value}`
})

const hookCharCount = computed(() => generatedHook.value.length)
const copiedHook = ref(false)

function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text)
  copiedHook.value = true
  setTimeout(() => {
    copiedHook.value = false
  }, 2000)
}

// Modal States
const showNewProposalModal = ref(false)
const newProposal = ref({
  job_title: '',
  bid_amount_usd: 1000,
  connects_spent: 16,
  client_country: 'United States',
  client_spend_usd: 20000,
  client_hire_rate: 70,
  client_rating: 5.0,
  job_url: '',
  hook_text: '',
  notes: '',
})

const showNewMilestoneModal = ref(false)
const newMilestone = ref({
  contract_id: 0,
  title: '',
  amount_usd: 300,
  escrow_funded: true,
  deliverables_notes: '',
})

const showNewCrModal = ref(false)
const newCr = ref({
  contract_id: 0,
  request_title: '',
  estimated_hours: 4,
  additional_price_usd: 250,
  notes: '',
})

const showNewSubdevModal = ref(false)
const newSubdev = ref({
  contract_id: 0,
  subdev_name: '',
  task_scope: '',
  payout_idr: 1000000,
})

const showNewRetainerModal = ref(false)
const newRetainer = ref({
  client_name: '',
  monthly_rate_usd: 800,
  billing_day: 1,
  notes: '',
})

// Metrics & Financial Computations
const totalEarnedUsd = computed(() => {
  return contracts.value.reduce((acc, c) => acc + (c.total_earned_usd || 0), 0)
})

const netEarnedUsd = computed(() => {
  // After Upwork 10% platform fee
  return totalEarnedUsd.value * 0.90
})

const netEarnedIdr = computed(() => {
  return netEarnedUsd.value * usdRate.value
})

const monthlyTargetUsd = computed(() => {
  return careerGoal.value?.target_revenue_usd || 2500
})

const targetProgressPercent = computed(() => {
  if (monthlyTargetUsd.value <= 0) return 0
  return Math.min(100, Math.round((totalEarnedUsd.value / monthlyTargetUsd.value) * 100))
})

const totalSubdevCostIdr = computed(() => {
  return subdevLogs.value.reduce((acc, s) => acc + (s.payout_idr || 0), 0)
})

const verdionNetProfitIdr = computed(() => {
  return netEarnedIdr.value - totalSubdevCostIdr.value
})

const verdionMarginPercent = computed(() => {
  if (netEarnedIdr.value <= 0) return 0
  return Math.max(0, Math.round((verdionNetProfitIdr.value / netEarnedIdr.value) * 100))
})

const totalRetainerMrrUsd = computed(() => {
  return retainers.value
    .filter((r) => r.status === 'active')
    .reduce((acc, r) => acc + (r.monthly_rate_usd || 0), 0)
})

const totalRetainerMrrIdr = computed(() => {
  return totalRetainerMrrUsd.value * usdRate.value
})

const totalConnectsSpent = computed(() => {
  return proposals.value.reduce((acc, p) => acc + (p.connects_spent || 0), 0)
})

const interviewProposals = computed(() => {
  return proposals.value.filter((p) => p.status === 'interviewing' || p.status === 'hired')
})

const proposalWinRate = computed(() => {
  if (proposals.value.length === 0) return 0
  return Math.round((interviewProposals.value.length / proposals.value.length) * 100)
})

// Currency Formatter
function formatIdr(amount: number): string {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0,
  }).format(amount)
}

function formatUsd(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  }).format(amount)
}

// Fetch all Verdion data
async function fetchVerdionData() {
  loading.value = true
  errorMsg.value = null

  try {
    // 1. Career Goal
    const currentMonth = new Date().toISOString().slice(0, 7)
    const { data: goalData, error: goalErr } = await supabase
      .from('career_goals')
      .select('*')
      .eq('user_id', props.userId)
      .eq('month', currentMonth)
      .maybeSingle()

    if (!goalErr && goalData) {
      careerGoal.value = goalData
    } else {
      careerGoal.value = {
        user_id: props.userId,
        month: currentMonth,
        target_revenue_usd: 2500,
        target_proposals_count: 20,
        current_badge: 'Top Rated',
        usd_to_idr_rate: 16200,
        company_name: 'Verdion',
        min_project_budget_usd: 800,
        monthly_profit_target_idr: 40000000,
      }
    }

    // 2. Proposals
    const { data: propData, error: propErr } = await supabase
      .from('upwork_proposals')
      .select('*')
      .eq('user_id', props.userId)
      .order('submitted_at', { ascending: false })

    if (!propErr && propData) {
      proposals.value = propData
    }

    // 3. Contracts
    const { data: contractData, error: contractErr } = await supabase
      .from('upwork_contracts')
      .select('*')
      .eq('user_id', props.userId)
      .order('created_at', { ascending: false })

    if (!contractErr && contractData) {
      contracts.value = contractData

      const contractIds = contractData.map((c) => c.id)

      if (contractIds.length > 0) {
        // 4. Milestones
        const { data: mData } = await supabase
          .from('upwork_milestones')
          .select('*')
          .in('contract_id', contractIds)
          .order('created_at', { ascending: true })

        if (mData) milestones.value = mData

        // 5. Change Requests
        const { data: crData } = await supabase
          .from('verdion_change_requests')
          .select('*')
          .in('contract_id', contractIds)
          .order('created_at', { ascending: false })

        if (crData) changeRequests.value = crData

        // 6. Subcontractor Logs
        const { data: subData } = await supabase
          .from('verdion_subcontractor_logs')
          .select('*')
          .in('contract_id', contractIds)
          .order('created_at', { ascending: false })

        if (subData) subdevLogs.value = subData
      }
    }

    // 7. Retainers
    const { data: retData, error: retErr } = await supabase
      .from('verdion_retainers')
      .select('*')
      .eq('user_id', props.userId)
      .order('created_at', { ascending: false })

    if (!retErr && retData) {
      retainers.value = retData
    }
  } catch (err: any) {
    errorMsg.value = err.message || 'Gagal memuat data Verdion Studio.'
  } finally {
    loading.value = false
  }
}

// Handlers
async function handleCreateProposal() {
  if (!newProposal.value.job_title) return
  saving.value = true

  try {
    const payload = {
      user_id: props.userId,
      job_title: newProposal.value.job_title,
      bid_amount_usd: newProposal.value.bid_amount_usd,
      connects_spent: newProposal.value.connects_spent,
      client_country: newProposal.value.client_country,
      client_spend_usd: newProposal.value.client_spend_usd,
      client_hire_rate: newProposal.value.client_hire_rate,
      client_rating: newProposal.value.client_rating,
      job_url: newProposal.value.job_url,
      hook_text: newProposal.value.hook_text || generatedHook.value,
      proposal_score: computedVettingScore.value,
      status: 'submitted',
      notes: newProposal.value.notes,
      submitted_at: new Date().toISOString(),
    }

    const { data, error } = await supabase
      .from('upwork_proposals')
      .insert([payload])
      .select()
      .single()

    if (error) throw error
    if (data) {
      proposals.value.unshift(data)
      showNewProposalModal.value = false
      successMsg.value = 'Proposal Whale berhasil dicatat!'
      setTimeout(() => (successMsg.value = null), 3000)
    }
  } catch (err: any) {
    errorMsg.value = err.message || 'Gagal menyimpan proposal.'
  } finally {
    saving.value = false
  }
}

async function handleToggleMilestoneEscrow(milestone: UpworkMilestone) {
  const newStatus = !milestone.escrow_funded
  milestone.escrow_funded = newStatus
  try {
    await supabase
      .from('upwork_milestones')
      .update({ escrow_funded: newStatus })
      .eq('id', milestone.id)
  } catch (err: any) {
    milestone.escrow_funded = !newStatus
  }
}

async function handleCreateMilestone() {
  if (!newMilestone.value.title || !newMilestone.value.contract_id) return
  saving.value = true

  try {
    const payload = {
      contract_id: newMilestone.value.contract_id,
      title: newMilestone.value.title,
      amount_usd: newMilestone.value.amount_usd,
      escrow_funded: newMilestone.value.escrow_funded,
      status: 'in_progress',
      deliverables_notes: newMilestone.value.deliverables_notes,
    }

    const { data, error } = await supabase
      .from('upwork_milestones')
      .insert([payload])
      .select()
      .single()

    if (error) throw error
    if (data) {
      milestones.value.push(data)
      showNewMilestoneModal.value = false
      successMsg.value = 'Milestone baru berhasil ditambahkan!'
      setTimeout(() => (successMsg.value = null), 3000)
    }
  } catch (err: any) {
    errorMsg.value = err.message || 'Gagal menambahkan milestone.'
  } finally {
    saving.value = false
  }
}

async function handleCreateChangeRequest() {
  if (!newCr.value.request_title || !newCr.value.contract_id) return
  saving.value = true

  try {
    const payload = {
      contract_id: newCr.value.contract_id,
      request_title: newCr.value.request_title,
      estimated_hours: newCr.value.estimated_hours,
      additional_price_usd: newCr.value.additional_price_usd,
      status: 'quoted',
      notes: newCr.value.notes,
    }

    const { data, error } = await supabase
      .from('verdion_change_requests')
      .insert([payload])
      .select()
      .single()

    if (error) throw error
    if (data) {
      changeRequests.value.unshift(data)
      showNewCrModal.value = false
      successMsg.value = 'Change Request berhasil dibuat sebagai peluang omset baru!'
      setTimeout(() => (successMsg.value = null), 3000)
    }
  } catch (err: any) {
    errorMsg.value = err.message || 'Gagal membuat change request.'
  } finally {
    saving.value = false
  }
}

async function handleCreateSubdev() {
  if (!newSubdev.value.subdev_name || !newSubdev.value.contract_id) return
  saving.value = true

  try {
    const payload = {
      contract_id: newSubdev.value.contract_id,
      subdev_name: newSubdev.value.subdev_name,
      task_scope: newSubdev.value.task_scope,
      payout_idr: newSubdev.value.payout_idr,
      status: 'pending',
    }

    const { data, error } = await supabase
      .from('verdion_subcontractor_logs')
      .insert([payload])
      .select()
      .single()

    if (error) throw error
    if (data) {
      subdevLogs.value.unshift(data)
      showNewSubdevModal.value = false
      successMsg.value = 'Log Subdev & Margin Arbitrase berhasil disimpan!'
      setTimeout(() => (successMsg.value = null), 3000)
    }
  } catch (err: any) {
    errorMsg.value = err.message || 'Gagal menyimpan data subkontraktor.'
  } finally {
    saving.value = false
  }
}

async function handleCreateRetainer() {
  if (!newRetainer.value.client_name) return
  saving.value = true

  try {
    const payload = {
      user_id: props.userId,
      client_name: newRetainer.value.client_name,
      monthly_rate_usd: newRetainer.value.monthly_rate_usd,
      billing_day: newRetainer.value.billing_day,
      status: 'active',
      notes: newRetainer.value.notes,
    }

    const { data, error } = await supabase
      .from('verdion_retainers')
      .insert([payload])
      .select()
      .single()

    if (error) throw error
    if (data) {
      retainers.value.unshift(data)
      showNewRetainerModal.value = false
      successMsg.value = 'Klien Retainer Recurring berhasil ditambahkan!'
      setTimeout(() => (successMsg.value = null), 3000)
    }
  } catch (err: any) {
    errorMsg.value = err.message || 'Gagal menyimpan retainer.'
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  fetchVerdionData()
})
</script>

<template>
  <div class="space-y-6">
    <!-- Top Executive Revenue Bar -->
    <div class="rounded-2xl border border-amber-200/80 bg-gradient-to-br from-amber-500/10 via-yellow-500/5 to-white p-5 shadow-xs">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-amber-100 pb-4">
        <div class="flex items-center gap-3">
          <div class="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-tr from-amber-500 to-yellow-400 text-white font-black text-xl shadow-xs">
            ⚡
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h2 class="text-lg font-black tracking-tight text-gray-950 uppercase">VERDION STUDIO</h2>
              <span class="rounded-md bg-amber-500/20 px-2 py-0.5 text-[11px] font-bold text-amber-900 border border-amber-400/30">
                PROFIT LEVERAGE ENGINE
              </span>
            </div>
            <p class="text-xs text-gray-600 mt-0.5 font-medium">
              High-Ticket Deals • Global Arbitrage (USD In, IDR Out) • Zero Burnout • Retainer Scaling
            </p>
          </div>
        </div>

        <!-- Exchange Rate & Controls -->
        <div class="flex items-center gap-3 self-end md:self-auto">
          <div class="flex items-center gap-2 rounded-lg bg-white/80 border border-amber-200 px-3 py-1.5 text-xs shadow-2xs">
            <span class="text-gray-500 font-medium">Kurs Valuta:</span>
            <span class="font-bold text-gray-900">1 USD = Rp {{ usdRate.toLocaleString('id-ID') }}</span>
          </div>
          <button
            @click="fetchVerdionData"
            class="rounded-lg border border-gray-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-gray-700 hover:bg-gray-50 transition-colors shadow-2xs cursor-pointer"
            title="Refresh Data"
          >
            🔄 Sync
          </button>
        </div>
      </div>

      <!-- Key Financial Metrics 4-Col Grid -->
      <div class="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
        <!-- Metric 1: Monthly Target Progress -->
        <div class="rounded-xl border border-amber-100 bg-white p-3.5 shadow-2xs">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-gray-500">Omset Bulan Ini</span>
            <span class="rounded-full bg-emerald-100 px-1.5 py-0.2 text-[10px] font-bold text-emerald-800">
              {{ targetProgressPercent }}%
            </span>
          </div>
          <div class="mt-2">
            <span class="text-lg sm:text-xl font-extrabold text-gray-900">{{ formatUsd(totalEarnedUsd) }}</span>
            <span class="text-xs text-gray-400 font-medium"> / {{ formatUsd(monthlyTargetUsd) }}</span>
          </div>
          <div class="mt-2 w-full bg-gray-100 rounded-full h-2 overflow-hidden">
            <div
              class="bg-gradient-to-r from-amber-500 to-emerald-500 h-2 rounded-full transition-all duration-500"
              :style="{ width: `${targetProgressPercent}%` }"
            ></div>
          </div>
        </div>

        <!-- Metric 2: Net Payout IDR -->
        <div class="rounded-xl border border-amber-100 bg-white p-3.5 shadow-2xs">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-gray-500">Pendapatan Bersih (Net)</span>
            <span class="text-[10px] text-gray-400 font-medium">After 10% Fee</span>
          </div>
          <div class="mt-2">
            <div class="text-base sm:text-lg font-black text-emerald-700">
              {{ formatIdr(netEarnedIdr) }}
            </div>
            <p class="text-[11px] text-gray-500 font-medium mt-0.5">
              Net USD: <strong class="text-gray-800">{{ formatUsd(netEarnedUsd) }}</strong>
            </p>
          </div>
        </div>

        <!-- Metric 3: Net Profit Margin -->
        <div class="rounded-xl border border-amber-100 bg-white p-3.5 shadow-2xs">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-gray-500">Margin Laba Verdion</span>
            <span class="rounded-full bg-amber-100 px-1.5 py-0.2 text-[10px] font-bold text-amber-900">
              Arbitrase
            </span>
          </div>
          <div class="mt-2">
            <span class="text-lg sm:text-xl font-black text-amber-900">{{ verdionMarginPercent }}%</span>
            <p class="text-[11px] text-gray-500 font-medium mt-0.5">
              Laba Bersih: <strong class="text-gray-800">{{ formatIdr(verdionNetProfitIdr) }}</strong>
            </p>
          </div>
        </div>

        <!-- Metric 4: Retainer MRR -->
        <div class="rounded-xl border border-amber-100 bg-white p-3.5 shadow-2xs">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-gray-500">Recurring MRR</span>
            <span class="rounded-full bg-indigo-100 px-1.5 py-0.2 text-[10px] font-bold text-indigo-800">
              Passive
            </span>
          </div>
          <div class="mt-2">
            <span class="text-lg sm:text-xl font-black text-indigo-900">{{ formatUsd(totalRetainerMrrUsd) }}</span>
            <span class="text-xs text-gray-400">/bln</span>
            <p class="text-[11px] text-gray-500 font-medium mt-0.5">
              {{ formatIdr(totalRetainerMrrIdr) }}/bulan
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

    <!-- Sub-Tabs Navigation for Verdion Leverage Engine -->
    <div class="flex items-center gap-2 border-b border-gray-200 overflow-x-auto no-scrollbar pb-1">
      <button
        @click="activeSubTab = 'deals'"
        class="flex items-center gap-1.5 px-3 py-2 text-xs font-bold rounded-lg transition-all cursor-pointer whitespace-nowrap"
        :class="activeSubTab === 'deals' ? 'bg-gray-900 text-white shadow-xs' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
      >
        <span>🎯</span>
        <span>Whale Radar & 2-Sec Hook</span>
      </button>

      <button
        @click="activeSubTab = 'milestones'"
        class="flex items-center gap-1.5 px-3 py-2 text-xs font-bold rounded-lg transition-all cursor-pointer whitespace-nowrap"
        :class="activeSubTab === 'milestones' ? 'bg-gray-900 text-white shadow-xs' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
      >
        <span>📦</span>
        <span>Milestone & Escrow Sentinel</span>
        <span class="rounded-full bg-amber-400 text-gray-950 px-1.5 py-0.2 text-[10px] font-black">
          {{ milestones.length }}
        </span>
      </button>

      <button
        @click="activeSubTab = 'arbitrage'"
        class="flex items-center gap-1.5 px-3 py-2 text-xs font-bold rounded-lg transition-all cursor-pointer whitespace-nowrap"
        :class="activeSubTab === 'arbitrage' ? 'bg-gray-900 text-white shadow-xs' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
      >
        <span>👥</span>
        <span>Labor & Margin Arbitrage</span>
      </button>

      <button
        @click="activeSubTab = 'retainers'"
        class="flex items-center gap-1.5 px-3 py-2 text-xs font-bold rounded-lg transition-all cursor-pointer whitespace-nowrap"
        :class="activeSubTab === 'retainers' ? 'bg-gray-900 text-white shadow-xs' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
      >
        <span>🔄</span>
        <span>Retainer & Client LTV</span>
        <span class="rounded-full bg-indigo-500 text-white px-1.5 py-0.2 text-[10px] font-bold">
          {{ retainers.length }}
        </span>
      </button>
    </div>

    <!-- ============================================================== -->
    <!-- SUB-TAB 1: WHALE DEAL RADAR & 2-SECOND HOOK STUDIO             -->
    <!-- ============================================================== -->
    <div v-if="activeSubTab === 'deals'" class="space-y-6">
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <!-- Left: Whale Vetting Calculator -->
        <div class="lg:col-span-5 space-y-4">
          <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-2xs">
            <div class="flex items-center justify-between border-b border-gray-100 pb-3">
              <h3 class="text-sm font-bold text-gray-900 flex items-center gap-2">
                <span>🛡️</span>
                <span>Whale Client Vetting Scorecard</span>
              </h3>
              <div
                class="rounded-full px-2.5 py-0.5 text-xs font-black shadow-2xs"
                :class="
                  computedVettingScore >= 80
                    ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                    : computedVettingScore >= 50
                    ? 'bg-amber-100 text-amber-800 border border-amber-300'
                    : 'bg-rose-100 text-rose-800 border border-rose-300'
                "
              >
                {{ computedVettingScore }} / 100
              </div>
            </div>

            <!-- Recommendation Alert -->
            <div class="mt-3 p-2.5 rounded-lg text-xs font-medium"
              :class="
                computedVettingScore >= 80
                  ? 'bg-emerald-50 text-emerald-900 border border-emerald-200'
                  : computedVettingScore >= 50
                  ? 'bg-amber-50 text-amber-900 border border-amber-200'
                  : 'bg-rose-50 text-rose-900 border border-rose-200'
              "
            >
              <div v-if="computedVettingScore >= 80" class="flex items-center gap-1.5">
                <span class="text-base">💎</span>
                <span><strong>VERDION WHALE TARGET:</strong> Kirim custom proposal + demo Loom segera! Klien berdaya beli tinggi.</span>
              </div>
              <div v-else-if="computedVettingScore >= 50" class="flex items-center gap-1.5">
                <span class="text-base">⚠️</span>
                <span><strong>PROCEED WITH CAUTION:</strong> Bid dengan template efisien. Jangan habiskan waktu bikin aset baru.</span>
              </div>
              <div v-else class="flex items-center gap-1.5">
                <span class="text-base">⛔</span>
                <span><strong>CONNECTS TRAP (SKIP):</strong> Hindari buang connects. Klien riwayat bayar rendah atau hire rate buruk.</span>
              </div>
            </div>

            <!-- Sliders & Checkboxes -->
            <div class="mt-4 space-y-3.5">
              <label class="flex items-center gap-2.5 text-xs font-semibold text-gray-800 cursor-pointer">
                <input
                  type="checkbox"
                  v-model="vettingPaymentVerified"
                  class="rounded text-amber-600 focus:ring-amber-500 h-4 w-4"
                />
                <span>Payment Method Verified (+25 Poin)</span>
              </label>

              <div>
                <div class="flex justify-between text-xs mb-1">
                  <span class="text-gray-600 font-medium">Total Pengeluaran Klien di Upwork:</span>
                  <span class="font-bold text-gray-900">{{ formatUsd(vettingTotalSpend) }}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="50000"
                  step="1000"
                  v-model.number="vettingTotalSpend"
                  class="w-full accent-amber-500 cursor-pointer"
                />
              </div>

              <div>
                <div class="flex justify-between text-xs mb-1">
                  <span class="text-gray-600 font-medium">Client Hire Rate (%):</span>
                  <span class="font-bold text-gray-900">{{ vettingHireRate }}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  step="5"
                  v-model.number="vettingHireRate"
                  class="w-full accent-amber-500 cursor-pointer"
                />
              </div>

              <div>
                <div class="flex justify-between text-xs mb-1">
                  <span class="text-gray-600 font-medium">Rata-rata Tarif Klien ($/jam):</span>
                  <span class="font-bold text-gray-900">{{ formatUsd(vettingAvgRate) }}/hr</span>
                </div>
                <input
                  type="range"
                  min="10"
                  max="100"
                  step="5"
                  v-model.number="vettingAvgRate"
                  class="w-full accent-amber-500 cursor-pointer"
                />
              </div>
            </div>
          </div>
        </div>

        <!-- Right: 2-Second Hook Generator Workbench -->
        <div class="lg:col-span-7 space-y-4">
          <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-2xs">
            <div class="flex items-center justify-between border-b border-gray-100 pb-3">
              <div>
                <h3 class="text-sm font-bold text-gray-900 flex items-center gap-2">
                  <span>⚡</span>
                  <span>The "2-Second Hook" Workbench</span>
                </h3>
                <p class="text-[11px] text-gray-500 mt-0.5">
                  Optimasi 150–200 karakter pertama agar lolos preview dashboard klien Upwork.
                </p>
              </div>
              <div
                class="rounded-full px-2 py-0.5 text-[11px] font-bold"
                :class="hookCharCount <= 200 ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'"
              >
                {{ hookCharCount }} / 200 Karakter
              </div>
            </div>

            <!-- Generator Fields -->
            <div class="mt-3.5 space-y-3">
              <div>
                <label class="block text-[11px] font-semibold text-gray-600 mb-1">Masalah Utama Klien (Diagnosis):</label>
                <input
                  type="text"
                  v-model="hookClientProblem"
                  class="w-full rounded-lg border border-gray-300 px-3 py-1.5 text-xs text-gray-800 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
                  placeholder="e.g. Bottleneck parallel LLM agent orchestration"
                />
              </div>

              <div>
                <label class="block text-[11px] font-semibold text-gray-600 mb-1">Solusi & Bukti Reusable Asset Verdion:</label>
                <input
                  type="text"
                  v-model="hookVerdionSolution"
                  class="w-full rounded-lg border border-gray-300 px-3 py-1.5 text-xs text-gray-800 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
                  placeholder="e.g. Pre-tested async worker queue cutting latency 65%"
                />
              </div>

              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-[11px] font-semibold text-gray-600 mb-1">Link Demo / Loom Video:</label>
                  <input
                    type="text"
                    v-model="hookDemoLink"
                    class="w-full rounded-lg border border-gray-300 px-3 py-1.5 text-xs text-gray-800 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
                    placeholder="loom.com/share/verdion-agent"
                  />
                </div>
                <div>
                  <label class="block text-[11px] font-semibold text-gray-600 mb-1">1 Pertanyaan Arsitektur Tajam:</label>
                  <input
                    type="text"
                    v-model="hookClarifyingQuestion"
                    class="w-full rounded-lg border border-gray-300 px-3 py-1.5 text-xs text-gray-800 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
                    placeholder="e.g. Do you require pgBouncer pooling?"
                  />
                </div>
              </div>

              <!-- Output Box -->
              <div class="rounded-xl border border-amber-300/80 bg-amber-50/50 p-3 mt-3 relative">
                <span class="text-[10px] font-bold text-amber-900 uppercase tracking-wider block mb-1">
                  Generated Preview Hook:
                </span>
                <p class="text-xs font-mono text-gray-900 leading-relaxed select-all">
                  {{ generatedHook }}
                </p>
                <div class="mt-2.5 flex items-center justify-between">
                  <span class="text-[10px] text-gray-500">
                    💡 Klien membaca ini sebelum klik tombol "View Proposal"
                  </span>
                  <button
                    @click="copyToClipboard(generatedHook)"
                    class="rounded-lg bg-gray-900 text-white px-3 py-1.5 text-xs font-bold hover:bg-gray-800 transition-colors shadow-2xs flex items-center gap-1.5 cursor-pointer"
                  >
                    <span>{{ copiedHook ? '✅ Disalin!' : '📋 Salin Hook' }}</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Proposal Pipeline List -->
      <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-2xs">
        <div class="flex items-center justify-between border-b border-gray-100 pb-3">
          <div>
            <h3 class="text-sm font-bold text-gray-900 flex items-center gap-2">
              <span>📋</span>
              <span>Daftar Proposal Whale & Efisiensi Connects</span>
            </h3>
            <p class="text-[11px] text-gray-500 mt-0.5">
              Total Connects: <strong>{{ totalConnectsSpent }}</strong> • Win Rate: <strong>{{ proposalWinRate }}%</strong> (Interview/Hired)
            </p>
          </div>
          <button
            @click="showNewProposalModal = true"
            class="rounded-lg bg-amber-500 text-white px-3 py-1.5 text-xs font-bold hover:bg-amber-600 transition-colors shadow-2xs cursor-pointer flex items-center gap-1"
          >
            <span>+</span>
            <span>Catat Proposal Whale</span>
          </button>
        </div>

        <!-- Table Proposals -->
        <div class="mt-3 overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="bg-gray-50 text-gray-500 uppercase text-[10px] font-bold border-b border-gray-200">
              <tr>
                <th class="py-2.5 px-3">Judul Lowongan</th>
                <th class="py-2.5 px-3">Negara / Klien</th>
                <th class="py-2.5 px-3">Nilai Bid</th>
                <th class="py-2.5 px-3">Skor Vetting</th>
                <th class="py-2.5 px-3">Status</th>
                <th class="py-2.5 px-3">Hook Terkirim</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr v-for="prop in proposals" :key="prop.id" class="hover:bg-gray-50/70 transition-colors">
                <td class="py-3 px-3">
                  <div class="font-bold text-gray-900">{{ prop.job_title }}</div>
                  <a
                    v-if="prop.job_url"
                    :href="prop.job_url"
                    target="_blank"
                    class="text-[11px] text-amber-600 hover:underline"
                  >
                    Buka Lowongan ↗
                  </a>
                </td>
                <td class="py-3 px-3">
                  <div class="font-semibold text-gray-800">{{ prop.client_country || 'Global' }}</div>
                  <div class="text-[10px] text-gray-500">
                    Spent: {{ formatUsd(prop.client_spend_usd) }} • Hire: {{ prop.client_hire_rate }}%
                  </div>
                </td>
                <td class="py-3 px-3">
                  <span class="font-extrabold text-gray-900">{{ formatUsd(prop.bid_amount_usd || 0) }}</span>
                  <span class="text-[10px] text-gray-400 block">{{ prop.connects_spent }} Connects</span>
                </td>
                <td class="py-3 px-3">
                  <span
                    class="rounded-full px-2 py-0.5 text-[10px] font-extrabold"
                    :class="
                      prop.proposal_score >= 80
                        ? 'bg-emerald-100 text-emerald-800'
                        : prop.proposal_score >= 50
                        ? 'bg-amber-100 text-amber-800'
                        : 'bg-rose-100 text-rose-800'
                    "
                  >
                    {{ prop.proposal_score }} / 100
                  </span>
                </td>
                <td class="py-3 px-3">
                  <span
                    class="rounded-md px-2 py-0.5 text-[10px] font-bold uppercase"
                    :class="{
                      'bg-emerald-100 text-emerald-800': prop.status === 'hired',
                      'bg-indigo-100 text-indigo-800': prop.status === 'interviewing',
                      'bg-gray-100 text-gray-800': prop.status === 'submitted',
                      'bg-rose-100 text-rose-800': prop.status === 'rejected',
                    }"
                  >
                    {{ prop.status }}
                  </span>
                </td>
                <td class="py-3 px-3 max-w-xs">
                  <p class="truncate text-gray-600 font-mono text-[11px]" :title="prop.hook_text || '-'">
                    {{ prop.hook_text || '-' }}
                  </p>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ============================================================== -->
    <!-- SUB-TAB 2: MILESTONES & ESCROW SENTINEL (SCOPE FORTRESS)      -->
    <!-- ============================================================== -->
    <div v-else-if="activeSubTab === 'milestones'" class="space-y-6">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-base font-black text-gray-900 flex items-center gap-2">
            <span>📦</span>
            <span>Milestone Fortress & 100% Escrow Rule</span>
          </h3>
          <p class="text-xs text-gray-500 mt-0.5">
            Dilarang menulis 1 baris kode pun sebelum dana klien berstatus <strong>Escrow Funded</strong>.
          </p>
        </div>
        <div class="flex items-center gap-2">
          <button
            @click="showNewCrModal = true"
            class="rounded-lg border border-purple-300 bg-purple-50 text-purple-900 px-3 py-1.5 text-xs font-bold hover:bg-purple-100 transition-colors shadow-2xs cursor-pointer flex items-center gap-1"
          >
            <span>⚡</span>
            <span>+ Change Request (Monetizer)</span>
          </button>
          <button
            @click="showNewMilestoneModal = true"
            class="rounded-lg bg-gray-900 text-white px-3 py-1.5 text-xs font-bold hover:bg-gray-800 transition-colors shadow-2xs cursor-pointer flex items-center gap-1"
          >
            <span>+</span>
            <span>Tambah Milestone</span>
          </button>
        </div>
      </div>

      <!-- Contracts & Milestones Grid -->
      <div class="space-y-4">
        <div
          v-for="contract in contracts"
          :key="contract.id"
          class="rounded-xl border border-gray-200 bg-white p-4 shadow-2xs space-y-3"
        >
          <!-- Contract Header -->
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-gray-100 pb-3">
            <div>
              <div class="flex items-center gap-2">
                <h4 class="text-sm font-black text-gray-900">{{ contract.project_title }}</h4>
                <span
                  class="rounded-md px-2 py-0.5 text-[10px] font-bold uppercase"
                  :class="contract.status === 'active' ? 'bg-emerald-100 text-emerald-800' : 'bg-gray-100 text-gray-700'"
                >
                  {{ contract.status }}
                </span>
              </div>
              <p class="text-xs text-gray-500 mt-0.5">
                Klien: <strong class="text-gray-800">{{ contract.client_name }}</strong> • Tipe: {{ contract.contract_type }}
              </p>
            </div>
            <div class="text-right">
              <span class="text-sm font-black text-gray-900">{{ formatUsd(contract.total_earned_usd) }}</span>
              <span class="text-xs text-gray-400"> / {{ formatUsd(contract.rate_or_budget_usd) }}</span>
            </div>
          </div>

          <!-- Milestones for this Contract -->
          <div class="space-y-2">
            <span class="text-[11px] font-bold text-gray-500 uppercase tracking-wider">Milestones Terdaftar:</span>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div
                v-for="ms in milestones.filter((m) => m.contract_id === contract.id)"
                :key="ms.id"
                class="rounded-lg border p-3 text-xs space-y-2 transition-all"
                :class="
                  ms.escrow_funded
                    ? 'border-emerald-200 bg-emerald-50/40'
                    : 'border-rose-200 bg-rose-50/40'
                "
              >
                <div class="flex items-start justify-between gap-2">
                  <div>
                    <h5 class="font-bold text-gray-900">{{ ms.title }}</h5>
                    <span class="text-sm font-black text-gray-900 block mt-0.5">{{ formatUsd(ms.amount_usd) }}</span>
                  </div>
                  <!-- Escrow Status Badge & Toggle -->
                  <button
                    @click="handleToggleMilestoneEscrow(ms)"
                    class="rounded-full px-2 py-0.5 text-[10px] font-extrabold cursor-pointer transition-all shadow-2xs"
                    :class="
                      ms.escrow_funded
                        ? 'bg-emerald-600 text-white hover:bg-emerald-700'
                        : 'bg-rose-600 text-white hover:bg-rose-700'
                    "
                    title="Klik untuk toggle status Escrow"
                  >
                    {{ ms.escrow_funded ? '🛡️ ESCROW FUNDED' : '⚠️ NOT FUNDED (FREEZE)' }}
                  </button>
                </div>

                <p v-if="ms.deliverables_notes" class="text-[11px] text-gray-600 bg-white/70 p-2 rounded border border-gray-200/50">
                  {{ ms.deliverables_notes }}
                </p>

                <!-- 14-day release timer if submitted -->
                <div v-if="ms.auto_release_deadline" class="text-[10px] text-gray-500 flex items-center justify-between border-t border-gray-200/40 pt-1.5">
                  <span>⏱️ 14-Day Auto Release:</span>
                  <span class="font-bold text-gray-800">Aktif (Upwork Escrow Protection)</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Change Requests / Scope Creep for this Contract -->
          <div
            v-if="changeRequests.filter((cr) => cr.contract_id === contract.id).length > 0"
            class="rounded-lg border border-purple-200 bg-purple-50/50 p-3 text-xs space-y-2"
          >
            <div class="flex items-center justify-between">
              <span class="font-bold text-purple-900 flex items-center gap-1.5">
                <span>⚡</span>
                <span>Change Requests Terdeteksi (Peluang Omset Tambahan):</span>
              </span>
            </div>
            <div class="space-y-1.5">
              <div
                v-for="cr in changeRequests.filter((cr) => cr.contract_id === contract.id)"
                :key="cr.id"
                class="rounded bg-white p-2 border border-purple-100 flex items-center justify-between"
              >
                <div>
                  <span class="font-semibold text-gray-900">{{ cr.request_title }}</span>
                  <span class="text-[11px] text-gray-500 block">{{ cr.notes }}</span>
                </div>
                <div class="text-right">
                  <span class="font-black text-purple-700">+{{ formatUsd(cr.additional_price_usd) }}</span>
                  <span class="text-[10px] text-gray-400 block">({{ cr.estimated_hours }} jam)</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ============================================================== -->
    <!-- SUB-TAB 3: LABOR & MARGIN ARBITRAGE (AGENCY SCALING)           -->
    <!-- ============================================================== -->
    <div v-else-if="activeSubTab === 'arbitrage'" class="space-y-6">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-base font-black text-gray-900 flex items-center gap-2">
            <span>👥</span>
            <span>Labor & Margin Arbitrage Engine</span>
          </h3>
          <p class="text-xs text-gray-500 mt-0.5">
            Dapatkan kontrak dalam USD dari pasar global, delegasikan task repetitif ke subdev IDR lokal.
          </p>
        </div>
        <button
          @click="showNewSubdevModal = true"
          class="rounded-lg bg-gray-900 text-white px-3 py-1.5 text-xs font-bold hover:bg-gray-800 transition-colors shadow-2xs cursor-pointer flex items-center gap-1"
        >
          <span>+</span>
          <span>Catat Pembagian Subdev</span>
        </button>
      </div>

      <!-- Financial Arbitrage Summary Card -->
      <div class="rounded-xl border border-emerald-200 bg-emerald-50/60 p-4 shadow-2xs">
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 text-center">
          <div>
            <span class="text-xs text-gray-500 font-semibold block">Total Revenue Klien (Net IDR)</span>
            <span class="text-lg font-black text-emerald-800">{{ formatIdr(netEarnedIdr) }}</span>
          </div>
          <div>
            <span class="text-xs text-gray-500 font-semibold block">Total Biaya Subkontraktor</span>
            <span class="text-lg font-black text-rose-700">-{{ formatIdr(totalSubdevCostIdr) }}</span>
          </div>
          <div>
            <span class="text-xs text-gray-500 font-semibold block">Laba Bersih Kas Verdion</span>
            <span class="text-xl font-black text-amber-900">{{ formatIdr(verdionNetProfitIdr) }} ({{ verdionMarginPercent }}%)</span>
          </div>
        </div>
      </div>

      <!-- Subcontractor Task Logs Table -->
      <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-2xs">
        <h4 class="text-sm font-bold text-gray-900 mb-3">Daftar Pendelegasian Task Subdev:</h4>
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="bg-gray-50 text-gray-500 uppercase text-[10px] font-bold border-b border-gray-200">
              <tr>
                <th class="py-2.5 px-3">Nama Subdev</th>
                <th class="py-2.5 px-3">Cakupan Task</th>
                <th class="py-2.5 px-3">Honor (IDR)</th>
                <th class="py-2.5 px-3">Status</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr v-for="sub in subdevLogs" :key="sub.id" class="hover:bg-gray-50/70 transition-colors">
                <td class="py-3 px-3 font-bold text-gray-900">{{ sub.subdev_name }}</td>
                <td class="py-3 px-3 text-gray-700">{{ sub.task_scope }}</td>
                <td class="py-3 px-3 font-extrabold text-rose-700">{{ formatIdr(sub.payout_idr) }}</td>
                <td class="py-3 px-3">
                  <span
                    class="rounded-full px-2 py-0.5 text-[10px] font-bold uppercase"
                    :class="sub.status === 'paid' ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'"
                  >
                    {{ sub.status }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ============================================================== -->
    <!-- SUB-TAB 4: RETAINERS & CLIENT LTV (RECURRING MRR)              -->
    <!-- ============================================================== -->
    <div v-else-if="activeSubTab === 'retainers'" class="space-y-6">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-base font-black text-gray-900 flex items-center gap-2">
            <span>🔄</span>
            <span>Retainer & Client LTV Multiplier</span>
          </h3>
          <p class="text-xs text-gray-500 mt-0.5">
            Ubah kontrak sekali bayar menjadi pemasukan rutin bulanan ($500 - $1,200/bln) tanpa beli connects lagi.
          </p>
        </div>
        <button
          @click="showNewRetainerModal = true"
          class="rounded-lg bg-indigo-600 text-white px-3 py-1.5 text-xs font-bold hover:bg-indigo-700 transition-colors shadow-2xs cursor-pointer flex items-center gap-1"
        >
          <span>+</span>
          <span>Tambah Klien Retainer</span>
        </button>
      </div>

      <!-- Retainer Cards Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div
          v-for="ret in retainers"
          :key="ret.id"
          class="rounded-xl border border-indigo-200 bg-gradient-to-br from-indigo-50/50 to-white p-4 shadow-2xs space-y-3"
        >
          <div class="flex items-center justify-between border-b border-indigo-100 pb-2.5">
            <div>
              <h4 class="text-sm font-black text-gray-900">{{ ret.client_name }}</h4>
              <span class="text-[11px] text-gray-500">Mulai: {{ ret.start_date }}</span>
            </div>
            <span class="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-800 uppercase">
              {{ ret.status }}
            </span>
          </div>

          <div class="flex items-center justify-between">
            <div>
              <span class="text-xs text-gray-500 font-semibold block">Paket Retainer Bulanan:</span>
              <span class="text-lg font-black text-indigo-950">{{ formatUsd(ret.monthly_rate_usd) }}/bln</span>
              <span class="text-xs text-gray-500 block">({{ formatIdr(ret.monthly_rate_usd * usdRate) }}/bln)</span>
            </div>
            <div class="rounded-lg bg-white border border-indigo-100 p-2 text-right">
              <span class="text-[10px] text-gray-400 font-bold block uppercase">Invoice Cycle</span>
              <span class="text-xs font-extrabold text-gray-800">Tgl {{ ret.billing_day }} tiap bulan</span>
            </div>
          </div>

          <p v-if="ret.notes" class="text-[11px] text-gray-600 bg-white/70 p-2 rounded border border-indigo-100">
            {{ ret.notes }}
          </p>
        </div>
      </div>
    </div>

    <!-- MODAL 1: NEW PROPOSAL -->
    <div v-if="showNewProposalModal" class="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/50 p-4 backdrop-blur-xs">
      <div class="w-full max-w-lg rounded-2xl bg-white p-5 shadow-xl space-y-4">
        <h3 class="text-base font-bold text-gray-900">Catat Proposal Whale Baru</h3>
        <div class="space-y-3 text-xs">
          <div>
            <label class="block font-semibold text-gray-700 mb-1">Judul Lowongan:</label>
            <input type="text" v-model="newProposal.job_title" class="w-full rounded-lg border border-gray-300 p-2" placeholder="e.g. AI Agent Orchestrator" />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-semibold text-gray-700 mb-1">Nilai Bid ($ USD):</label>
              <input type="number" v-model.number="newProposal.bid_amount_usd" class="w-full rounded-lg border border-gray-300 p-2" />
            </div>
            <div>
              <label class="block font-semibold text-gray-700 mb-1">Connects Terpakai:</label>
              <input type="number" v-model.number="newProposal.connects_spent" class="w-full rounded-lg border border-gray-300 p-2" />
            </div>
          </div>
          <div>
            <label class="block font-semibold text-gray-700 mb-1">Link Lowongan Upwork:</label>
            <input type="text" v-model="newProposal.job_url" class="w-full rounded-lg border border-gray-300 p-2" placeholder="https://upwork.com/jobs/..." />
          </div>
          <div>
            <label class="block font-semibold text-gray-700 mb-1">Hook Kalimat Pembuka:</label>
            <textarea v-model="newProposal.hook_text" rows="2" class="w-full rounded-lg border border-gray-300 p-2" placeholder="Kosongkan untuk memakai Hook Generator otomatis"></textarea>
          </div>
        </div>
        <div class="flex justify-end gap-2 pt-2 border-t">
          <button @click="showNewProposalModal = false" class="px-3 py-1.5 text-xs font-semibold text-gray-600 cursor-pointer">Batal</button>
          <button @click="handleCreateProposal" :disabled="saving" class="px-4 py-1.5 text-xs font-bold text-white bg-amber-500 rounded-lg hover:bg-amber-600 cursor-pointer">
            {{ saving ? 'Menyimpan...' : 'Simpan Proposal' }}
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL 2: NEW MILESTONE -->
    <div v-if="showNewMilestoneModal" class="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/50 p-4 backdrop-blur-xs">
      <div class="w-full max-w-md rounded-2xl bg-white p-5 shadow-xl space-y-4">
        <h3 class="text-base font-bold text-gray-900">Tambah Milestone Kontrak</h3>
        <div class="space-y-3 text-xs">
          <div>
            <label class="block font-semibold text-gray-700 mb-1">Pilih Kontrak:</label>
            <select v-model.number="newMilestone.contract_id" class="w-full rounded-lg border border-gray-300 p-2">
              <option :value="0" disabled>-- Pilih Kontrak --</option>
              <option v-for="c in contracts" :key="c.id" :value="c.id">{{ c.project_title }} ({{ c.client_name }})</option>
            </select>
          </div>
          <div>
            <label class="block font-semibold text-gray-700 mb-1">Nama Milestone:</label>
            <input type="text" v-model="newMilestone.title" class="w-full rounded-lg border border-gray-300 p-2" placeholder="e.g. Milestone 2: API Queue & Testing" />
          </div>
          <div>
            <label class="block font-semibold text-gray-700 mb-1">Nilai Milestone ($ USD):</label>
            <input type="number" v-model.number="newMilestone.amount_usd" class="w-full rounded-lg border border-gray-300 p-2" />
          </div>
          <label class="flex items-center gap-2 font-semibold text-gray-700 cursor-pointer">
            <input type="checkbox" v-model="newMilestone.escrow_funded" class="rounded text-amber-600 h-4 w-4" />
            <span>Escrow Sudah Didanai Klien?</span>
          </label>
        </div>
        <div class="flex justify-end gap-2 pt-2 border-t">
          <button @click="showNewMilestoneModal = false" class="px-3 py-1.5 text-xs font-semibold text-gray-600 cursor-pointer">Batal</button>
          <button @click="handleCreateMilestone" :disabled="saving" class="px-4 py-1.5 text-xs font-bold text-white bg-gray-900 rounded-lg hover:bg-gray-800 cursor-pointer">
            {{ saving ? 'Menyimpan...' : 'Tambah Milestone' }}
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL 3: NEW CHANGE REQUEST -->
    <div v-if="showNewCrModal" class="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/50 p-4 backdrop-blur-xs">
      <div class="w-full max-w-md rounded-2xl bg-white p-5 shadow-xl space-y-4">
        <h3 class="text-base font-bold text-purple-900 flex items-center gap-2">
          <span>⚡</span>
          <span>Catat Change Request (Scope Creep Monetizer)</span>
        </h3>
        <p class="text-[11px] text-gray-500">
          Ubah permintaan revisi atau fitur tambahan dari klien menjadi omset milestone baru.
        </p>
        <div class="space-y-3 text-xs">
          <div>
            <label class="block font-semibold text-gray-700 mb-1">Pilih Kontrak:</label>
            <select v-model.number="newCr.contract_id" class="w-full rounded-lg border border-gray-300 p-2">
              <option :value="0" disabled>-- Pilih Kontrak --</option>
              <option v-for="c in contracts" :key="c.id" :value="c.id">{{ c.project_title }} ({{ c.client_name }})</option>
            </select>
          </div>
          <div>
            <label class="block font-semibold text-gray-700 mb-1">Permintaan Tambahan Klien:</label>
            <input type="text" v-model="newCr.request_title" class="w-full rounded-lg border border-gray-300 p-2" placeholder="e.g. Export data to Google Sheets & Slack" />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-semibold text-gray-700 mb-1">Estimasi Jam Pengerjaan:</label>
              <input type="number" v-model.number="newCr.estimated_hours" class="w-full rounded-lg border border-gray-300 p-2" />
            </div>
            <div>
              <label class="block font-semibold text-gray-700 mb-1">Tambahan Biaya ($ USD):</label>
              <input type="number" v-model.number="newCr.additional_price_usd" class="w-full rounded-lg border border-gray-300 p-2" />
            </div>
          </div>
        </div>
        <div class="flex justify-end gap-2 pt-2 border-t">
          <button @click="showNewCrModal = false" class="px-3 py-1.5 text-xs font-semibold text-gray-600 cursor-pointer">Batal</button>
          <button @click="handleCreateChangeRequest" :disabled="saving" class="px-4 py-1.5 text-xs font-bold text-white bg-purple-700 rounded-lg hover:bg-purple-800 cursor-pointer">
            {{ saving ? 'Menyimpan...' : 'Simpan Peluang CR' }}
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL 4: NEW SUBDEV -->
    <div v-if="showNewSubdevModal" class="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/50 p-4 backdrop-blur-xs">
      <div class="w-full max-w-md rounded-2xl bg-white p-5 shadow-xl space-y-4">
        <h3 class="text-base font-bold text-gray-900">Catat Subkontraktor (Arbitrase Dev)</h3>
        <div class="space-y-3 text-xs">
          <div>
            <label class="block font-semibold text-gray-700 mb-1">Pilih Kontrak:</label>
            <select v-model.number="newSubdev.contract_id" class="w-full rounded-lg border border-gray-300 p-2">
              <option :value="0" disabled>-- Pilih Kontrak --</option>
              <option v-for="c in contracts" :key="c.id" :value="c.id">{{ c.project_title }} ({{ c.client_name }})</option>
            </select>
          </div>
          <div>
            <label class="block font-semibold text-gray-700 mb-1">Nama Subdev:</label>
            <input type="text" v-model="newSubdev.subdev_name" class="w-full rounded-lg border border-gray-300 p-2" placeholder="e.g. Rian (Junior Python Dev)" />
          </div>
          <div>
            <label class="block font-semibold text-gray-700 mb-1">Cakupan Task Yang Didelegasikan:</label>
            <input type="text" v-model="newSubdev.task_scope" class="w-full rounded-lg border border-gray-300 p-2" placeholder="e.g. Slicing UI, parser, data cleaning" />
          </div>
          <div>
            <label class="block font-semibold text-gray-700 mb-1">Biaya Bayar Subdev (Rp IDR):</label>
            <input type="number" v-model.number="newSubdev.payout_idr" step="50000" class="w-full rounded-lg border border-gray-300 p-2" />
          </div>
        </div>
        <div class="flex justify-end gap-2 pt-2 border-t">
          <button @click="showNewSubdevModal = false" class="px-3 py-1.5 text-xs font-semibold text-gray-600 cursor-pointer">Batal</button>
          <button @click="handleCreateSubdev" :disabled="saving" class="px-4 py-1.5 text-xs font-bold text-white bg-gray-900 rounded-lg hover:bg-gray-800 cursor-pointer">
            {{ saving ? 'Menyimpan...' : 'Simpan Subdev' }}
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL 5: NEW RETAINER -->
    <div v-if="showNewRetainerModal" class="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/50 p-4 backdrop-blur-xs">
      <div class="w-full max-w-md rounded-2xl bg-white p-5 shadow-xl space-y-4">
        <h3 class="text-base font-bold text-indigo-900">Tambah Klien Retainer Bulanan</h3>
        <div class="space-y-3 text-xs">
          <div>
            <label class="block font-semibold text-gray-700 mb-1">Nama Klien / Perusahaan:</label>
            <input type="text" v-model="newRetainer.client_name" class="w-full rounded-lg border border-gray-300 p-2" placeholder="e.g. FinTech Alpha (US)" />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-semibold text-gray-700 mb-1">Tarif Bulanan ($ USD):</label>
              <input type="number" v-model.number="newRetainer.monthly_rate_usd" class="w-full rounded-lg border border-gray-300 p-2" />
            </div>
            <div>
              <label class="block font-semibold text-gray-700 mb-1">Tanggal Tagihan (1-31):</label>
              <input type="number" min="1" max="31" v-model.number="newRetainer.billing_day" class="w-full rounded-lg border border-gray-300 p-2" />
            </div>
          </div>
          <div>
            <label class="block font-semibold text-gray-700 mb-1">Catatan Paket / SLA:</label>
            <textarea v-model="newRetainer.notes" rows="2" class="w-full rounded-lg border border-gray-300 p-2" placeholder="e.g. 10 jam/bulan SLA monitoring & bug fixing"></textarea>
          </div>
        </div>
        <div class="flex justify-end gap-2 pt-2 border-t">
          <button @click="showNewRetainerModal = false" class="px-3 py-1.5 text-xs font-semibold text-gray-600 cursor-pointer">Batal</button>
          <button @click="handleCreateRetainer" :disabled="saving" class="px-4 py-1.5 text-xs font-bold text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 cursor-pointer">
            {{ saving ? 'Menyimpan...' : 'Simpan Retainer' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
