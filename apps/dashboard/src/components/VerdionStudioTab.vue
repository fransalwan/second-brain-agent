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

interface DirectDeal {
  id: number
  client_name: string
  founder_handle: string
  project_title: string
  package_type: string
  deal_amount_usd: number
  stage: 'lead' | 'loom_sent' | 'call_booked' | 'deposit_paid' | 'in_progress' | 'delivered' | 'testimonial_secured'
  notes: string | null
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

const activeSubTab = ref<'case_study' | 'bip_engine' | 'cold_loom' | 'deals' | 'retainers'>('case_study')
const loading = ref(true)
const saving = ref(false)
const errorMsg = ref<string | null>(null)
const successMsg = ref<string | null>(null)

// Data state
const careerGoal = ref<CareerGoal | null>(null)
const directDeals = ref<DirectDeal[]>([
  {
    id: 1,
    client_name: 'HyperScale AI',
    founder_handle: '@alex_founder (X)',
    project_title: 'Multi-Agent RAG Orchestration Engine',
    package_type: 'AI Agent Workflow',
    deal_amount_usd: 3500,
    stage: 'deposit_paid',
    notes: '50% deposit received via Wise ($1,750). Delivering in 10 days.',
    created_at: new Date().toISOString(),
  },
  {
    id: 2,
    client_name: 'Nexus Billing SaaS',
    founder_handle: 'linkedin.com/in/sarah-cto',
    project_title: 'FastAPI Stripe Webhook & Sub-100ms API Refactor',
    package_type: '14-Day MVP Sprint',
    deal_amount_usd: 2800,
    stage: 'call_booked',
    notes: 'Sent 90s Loom audit showing 3s webhook latency drop to 80ms.',
    created_at: new Date().toISOString(),
  },
])

const retainers = ref<VerdionRetainer[]>([])

// Currency exchange rate default
const usdRate = computed(() => careerGoal.value?.usd_to_idr_rate || 16200)

// -------------------------------------------------------------
// 1. FLAGSHIP CASE STUDY SHOWCASE STATE
// -------------------------------------------------------------
const caseStudyCopied = ref(false)

const caseStudyMarkdown = computed(() => {
  return `# Case Study #01: Second Brain — Enterprise-Grade Autonomous Workspace Architecture

**Studio:** Verdion (Boutique Software Engineering & Autonomous AI Systems)  
**Lead Engineer:** Frans Alwan (Principal Engineer)  
**Status:** In Production • 100% Automated Test Suite Passing  
**Live Application:** https://second-brain-agent.netlify.app  

---

### 1. Executive Summary & Problem
Modern knowledge workers and engineering founders suffer from context fragmentation across note apps, health tracking, and task management. Off-the-shelf tools either hallucinate without verified context or introduce unacceptable UI latency (>1.5s).

Verdion engineered **Second Brain**: a full-stack, type-safe, multi-tenant autonomous workspace that bridges async agent task execution with deterministic database reliability.

---

### 2. System Architecture
\`\`\`
[ Vue 3 + Tailwind Client ]  <--->  [ Supabase PostgreSQL + Row-Level Security ]
          |                                            |
          v                                            v
[ FastAPI Async Engine ]   <--->  [ Autonomous LLM Agent & Background Workers ]
\`\`\`

- **Frontend:** Vue 3 Composition API, Vite, TypeScript, zero CSS framework bloat.
- **API Engine:** Python FastAPI with async non-blocking worker concurrency.
- **Database & Security:** Supabase PostgreSQL with granular multi-tenant Row-Level Security (RLS) policies.
- **Agent Intelligence:** Multi-turn tool execution, background task polling, and zero-hallucination context injection.

---

### 3. Engineering Benchmarks & Proof of Work
- **Automated Test Coverage:** 100% passing across frontend unit/integration suite (55 tests) and backend pytest suite (77 tests).
- **Query Latency:** Sub-100ms API responses through optimized foreign-key indexing and compound RLS filters.
- **Cost Efficiency:** Engineered to run 100% within serverless free-tier constraints while supporting production concurrency.
- **Code Standards:** Type-safe, linted, strict CI/CD automated pipeline on git push.

---
*Built with precision by Verdion Studio. Inquiries: fransalwan55@gmail.com*`
})

function copyCaseStudy() {
  navigator.clipboard.writeText(caseStudyMarkdown.value)
  caseStudyCopied.value = true
  setTimeout(() => {
    caseStudyCopied.value = false
  }, 2500)
}

// -------------------------------------------------------------
// 2. BUILD-IN-PUBLIC (BiP) CONTENT ENGINE STATE
// -------------------------------------------------------------
const bipPostType = ref<'teardown' | 'performance' | 'devlog'>('teardown')
const bipTopic = ref('Supabase Row-Level Security (RLS)')
const bipMetric = ref('Dropped query latency from 1,420ms to 78ms')
const bipInsight = ref('Composite indexing on (user_id, created_at) prevents sequential table scans during RLS policy checks.')
const bipCopied = ref(false)

const bipTwitterContent = computed(() => {
  if (bipPostType.value === 'teardown') {
    return `Most multi-tenant apps leak data or crash under scale.

How we built enterprise RLS @VerdionStudio:
• Filtered at DB level, not app
• ${bipInsight.value}
• Result: ${bipMetric.value}

Proof of work > talk. 🧵👇`
  } else if (bipPostType.value === 'performance') {
    return `⚡ Perf Win @VerdionStudio:

We just ${bipMetric.value} on our core API engine.

Fix: ${bipInsight.value}

Clean code + async wins. 🛠️`
  } else {
    return `🚢 Shipped @VerdionStudio:
Refactored ${bipTopic.value}.
Result: ${bipMetric.value}.
${bipInsight.value}`
  }
})

const bipLinkedInContent = computed(() => {
  return `Why most software rewrites fail (and how we approach performance engineering at Verdion):

When scaling web applications and autonomous AI systems, founders often think they need a massive microservice rewrite. 

In reality, 90% of latency bottlenecks stem from database indexing and synchronous blocking loops.

Here is what we implemented this week:
• Focus Area: ${bipTopic.value}
• Measured Impact: ${bipMetric.value}
• Engineering Insight: ${bipInsight.value}

At Verdion, we believe in radical transparency and high-signal engineering: 100% automated test coverage, sub-100ms response times, and zero bloat.

What is the biggest performance bottleneck in your current stack?

#SoftwareEngineering #BuildInPublic #SystemDesign #FastAPI #VueJS #PostgreSQL`
})

const bipTwitterLength = computed(() => bipTwitterContent.value.length)

function copyBipText(text: string) {
  navigator.clipboard.writeText(text)
  bipCopied.value = true
  setTimeout(() => {
    bipCopied.value = false
  }, 2000)
}

// -------------------------------------------------------------
// 3. COLD LOOM AUDIT & FOUNDER DM DRAFTER STATE
// -------------------------------------------------------------
const coldTargetStartup = ref('FinTech Alpha')
const coldFounderName = ref('Alex')
const coldObservedBottleneck = ref('dashboard metrics take 4.2 seconds to load due to unindexed relation queries')
const coldVerdionFix = ref('Redis async caching layer + compound Supabase index')
const coldLoomUrl = ref('loom.com/share/verdion-audit-demo')
const coldDmCopied = ref(false)
const coldScriptCopied = ref(false)

const coldFounderDm = computed(() => {
  return `Hi ${coldFounderName.value}, saw your recent launch for ${coldTargetStartup.value}—really slick product concept!

I was testing the platform and noticed that ${coldObservedBottleneck.value}.

To save your team debugging time, I spun up a 90-second video demo showing how to resolve this with ${coldVerdionFix.value} (drops latency under 150ms):
${coldLoomUrl.value}

No sales pitch attached—just thought it might be useful as you scale. If you'd like me to deploy and test this into your repo this week, happy to hop on a quick 10-min chat.

Best,
Frans Alwan
Lead Engineer @ Verdion Studio`
})

const cold90sScript = computed(() => {
  return `[00:00 - 00:20 | Hook & Diagnosis]
"Hi ${coldFounderName.value}! Congratulations on ${coldTargetStartup.value}. I was checking out your product and noticed a critical bottleneck: ${coldObservedBottleneck.value}."

[00:20 - 00:55 | The Working Sandbox Proof]
"Instead of just sending an email, I cloned a sandbox environment reproducing your architecture. Here is the fix using ${coldVerdionFix.value}. Notice in the network tab how the query time dropped immediately to sub-150ms with zero data mutation."

[00:55 - 01:30 | Call to Action]
"At Verdion Studio, we specialize in high-performance backends and AI workflows. If your engineering team is swamped and you want this merged and tested today, reply to my message and we can roll this out. Cheers!"`
})

function copyColdDm() {
  navigator.clipboard.writeText(coldFounderDm.value)
  coldDmCopied.value = true
  setTimeout(() => (coldDmCopied.value = false), 2000)
}

function copyColdScript() {
  navigator.clipboard.writeText(cold90sScript.value)
  coldScriptCopied.value = true
  setTimeout(() => (coldScriptCopied.value = false), 2000)
}

// -------------------------------------------------------------
// 4. DIRECT DEALS PIPELINE & FINANCIAL COMPUTATIONS
// -------------------------------------------------------------
const showNewDirectDealModal = ref(false)
const newDeal = ref({
  client_name: '',
  founder_handle: '',
  project_title: '',
  package_type: '14-Day MVP Sprint',
  deal_amount_usd: 2500,
  stage: 'lead' as DirectDeal['stage'],
  notes: '',
})

const showNewRetainerModal = ref(false)
const newRetainer = ref({
  client_name: '',
  monthly_rate_usd: 800,
  billing_day: 1,
  notes: '',
})

// Metrics
const totalDirectPipelineUsd = computed(() => {
  return directDeals.value.reduce((acc, d) => acc + (d.deal_amount_usd || 0), 0)
})

const closedRevenueUsd = computed(() => {
  return directDeals.value
    .filter((d) => ['deposit_paid', 'in_progress', 'delivered', 'testimonial_secured'].includes(d.stage))
    .reduce((acc, d) => acc + (d.deal_amount_usd || 0), 0)
})

const closedRevenueIdr = computed(() => {
  // 100% Retained (0% platform cut!)
  return closedRevenueUsd.value * usdRate.value
})

const totalRetainerMrrUsd = computed(() => {
  return retainers.value
    .filter((r) => r.status === 'active')
    .reduce((acc, r) => acc + (r.monthly_rate_usd || 0), 0)
})

const totalRetainerMrrIdr = computed(() => {
  return totalRetainerMrrUsd.value * usdRate.value
})

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
    maximumFractionDigits: 0,
  }).format(amount)
}

// Data Fetching
async function fetchVerdionData() {
  loading.value = true
  errorMsg.value = null

  try {
    const currentMonth = new Date().toISOString().slice(0, 7)
    const { data: goalData } = await supabase
      .from('career_goals')
      .select('*')
      .eq('user_id', props.userId)
      .eq('month', currentMonth)
      .maybeSingle()

    if (goalData) {
      careerGoal.value = goalData
    } else {
      careerGoal.value = {
        user_id: props.userId,
        month: currentMonth,
        target_revenue_usd: 5000,
        target_proposals_count: 15,
        current_badge: 'Boutique Founder',
        usd_to_idr_rate: 16200,
        company_name: 'Verdion Studio',
        min_project_budget_usd: 1500,
        monthly_profit_target_idr: 75000000,
      }
    }

    const { data: retData } = await supabase
      .from('verdion_retainers')
      .select('*')
      .eq('user_id', props.userId)
      .order('created_at', { ascending: false })

    if (retData && retData.length > 0) {
      retainers.value = retData
    } else {
      retainers.value = [
        {
          id: 101,
          client_name: 'HyperScale AI (Ongoing Architecture SLA)',
          monthly_rate_usd: 1200,
          start_date: '2026-10-01',
          billing_day: 1,
          status: 'active',
          notes: '15 hrs/month retainer for agent monitoring & database tuning',
          created_at: new Date().toISOString(),
        },
      ]
    }
  } catch (err: any) {
    errorMsg.value = err.message || 'Gagal memuat data Verdion Studio.'
  } finally {
    loading.value = false
  }
}

function handleAddDirectDeal() {
  if (!newDeal.value.client_name) return
  const created: DirectDeal = {
    id: Date.now(),
    client_name: newDeal.value.client_name,
    founder_handle: newDeal.value.founder_handle || '@founder',
    project_title: newDeal.value.project_title || 'Custom Engineering Sprint',
    package_type: newDeal.value.package_type,
    deal_amount_usd: Number(newDeal.value.deal_amount_usd) || 2500,
    stage: newDeal.value.stage,
    notes: newDeal.value.notes,
    created_at: new Date().toISOString(),
  }
  directDeals.value.unshift(created)
  showNewDirectDealModal.value = false
  successMsg.value = 'Direct Client Deal berhasil dicatat!'
  setTimeout(() => (successMsg.value = null), 3000)
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
    const { data, error } = await supabase.from('verdion_retainers').insert([payload]).select().single()
    if (error) throw error
    if (data) {
      retainers.value.unshift(data)
    } else {
      retainers.value.unshift({ ...payload, id: Date.now(), start_date: '2026-10-01', created_at: new Date().toISOString() })
    }
    showNewRetainerModal.value = false
    successMsg.value = 'Klien Retainer Recurring berhasil ditambahkan!'
    setTimeout(() => (successMsg.value = null), 3000)
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
    <div class="rounded-2xl border border-amber-300/80 bg-gradient-to-br from-amber-500/10 via-yellow-500/5 to-white p-5 shadow-xs">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-amber-100 pb-4">
        <div class="flex items-center gap-3">
          <div class="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-tr from-amber-500 to-yellow-400 text-white font-black text-xl shadow-xs">
            ⚡
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h2 class="text-lg font-black tracking-tight text-gray-950 uppercase">VERDION STUDIO</h2>
              <span class="rounded-md bg-amber-500/20 px-2 py-0.5 text-[11px] font-bold text-amber-900 border border-amber-400/30">
                BUILD-IN-PUBLIC & PUBLIC CREDIBILITY ENGINE
              </span>
            </div>
            <p class="text-xs text-gray-600 mt-0.5 font-medium">
              Boutique Software Engineering • Flagship Proof of Work • 0% Platform Fee • Global Direct Inbound
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
        <!-- Metric 1: Closed Revenue USD -->
        <div class="rounded-xl border border-amber-100 bg-white p-3.5 shadow-2xs">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-gray-500">Revenue Closing (Direct)</span>
            <span class="rounded-full bg-emerald-100 px-1.5 py-0.2 text-[10px] font-bold text-emerald-800">
              0% Fee
            </span>
          </div>
          <div class="mt-2">
            <span class="text-lg sm:text-xl font-extrabold text-gray-900">{{ formatUsd(closedRevenueUsd) }}</span>
            <span class="text-xs text-gray-400 font-medium"> USD</span>
            <p class="text-[11px] text-emerald-700 font-bold mt-0.5">
              {{ formatIdr(closedRevenueIdr) }}
            </p>
          </div>
        </div>

        <!-- Metric 2: Direct Deal Pipeline -->
        <div class="rounded-xl border border-amber-100 bg-white p-3.5 shadow-2xs">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-gray-500">Pipeline Deal Aktif</span>
            <span class="rounded-full bg-blue-100 px-1.5 py-0.2 text-[10px] font-bold text-blue-800">
              {{ directDeals.length }} Deals
            </span>
          </div>
          <div class="mt-2">
            <div class="text-base sm:text-lg font-black text-gray-900">
              {{ formatUsd(totalDirectPipelineUsd) }}
            </div>
            <p class="text-[11px] text-gray-500 font-medium mt-0.5">
              Potensi Bersih: <strong class="text-gray-800">{{ formatIdr(totalDirectPipelineUsd * usdRate) }}</strong>
            </p>
          </div>
        </div>

        <!-- Metric 3: Recurring Retainer MRR -->
        <div class="rounded-xl border border-amber-100 bg-white p-3.5 shadow-2xs">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-gray-500">Recurring MRR</span>
            <span class="rounded-full bg-indigo-100 px-1.5 py-0.2 text-[10px] font-bold text-indigo-800">
              Retainer
            </span>
          </div>
          <div class="mt-2">
            <span class="text-lg sm:text-xl font-black text-indigo-950">{{ formatUsd(totalRetainerMrrUsd) }}</span>
            <span class="text-xs text-gray-400">/bln</span>
            <p class="text-[11px] text-gray-500 font-medium mt-0.5">
              {{ formatIdr(totalRetainerMrrIdr) }}/bulan
            </p>
          </div>
        </div>

        <!-- Metric 4: Platform Fee Saved -->
        <div class="rounded-xl border border-amber-100 bg-white p-3.5 shadow-2xs">
          <div class="flex items-center justify-between">
            <span class="text-xs font-semibold text-gray-500">Penghematan Fee Platform</span>
            <span class="rounded-full bg-emerald-100 px-1.5 py-0.2 text-[10px] font-bold text-emerald-900">
              Hemat 10%
            </span>
          </div>
          <div class="mt-2">
            <span class="text-lg sm:text-xl font-black text-emerald-700">{{ formatUsd(closedRevenueUsd * 0.10) }}</span>
            <p class="text-[11px] text-gray-500 font-medium mt-0.5">
              Disimpan untuk kas Verdion (Bebas komisi)
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

    <!-- Sub-Tabs Navigation for Verdion Build-in-Public Command Center -->
    <div class="flex items-center gap-2 border-b border-gray-200 overflow-x-auto no-scrollbar pb-1">
      <button
        @click="activeSubTab = 'case_study'"
        class="flex items-center gap-1.5 px-3 py-2 text-xs font-bold rounded-lg transition-all cursor-pointer whitespace-nowrap"
        :class="activeSubTab === 'case_study' ? 'bg-gray-900 text-white shadow-xs' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
      >
        <span>🏛️</span>
        <span>Case Study #01 (Flagship Proof)</span>
      </button>

      <button
        @click="activeSubTab = 'bip_engine'"
        class="flex items-center gap-1.5 px-3 py-2 text-xs font-bold rounded-lg transition-all cursor-pointer whitespace-nowrap"
        :class="activeSubTab === 'bip_engine' ? 'bg-gray-900 text-white shadow-xs' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
      >
        <span>✍️</span>
        <span>Build-in-Public (X & LinkedIn)</span>
      </button>

      <button
        @click="activeSubTab = 'cold_loom'"
        class="flex items-center gap-1.5 px-3 py-2 text-xs font-bold rounded-lg transition-all cursor-pointer whitespace-nowrap"
        :class="activeSubTab === 'cold_loom' ? 'bg-gray-900 text-white shadow-xs' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
      >
        <span>🎯</span>
        <span>Cold Loom Audit Drafter</span>
      </button>

      <button
        @click="activeSubTab = 'deals'"
        class="flex items-center gap-1.5 px-3 py-2 text-xs font-bold rounded-lg transition-all cursor-pointer whitespace-nowrap"
        :class="activeSubTab === 'deals' ? 'bg-gray-900 text-white shadow-xs' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
      >
        <span>💼</span>
        <span>Productized Deals (0% Fee)</span>
        <span class="rounded-full bg-emerald-500 text-white px-1.5 py-0.2 text-[10px] font-bold">
          {{ directDeals.length }}
        </span>
      </button>

      <button
        @click="activeSubTab = 'retainers'"
        class="flex items-center gap-1.5 px-3 py-2 text-xs font-bold rounded-lg transition-all cursor-pointer whitespace-nowrap"
        :class="activeSubTab === 'retainers' ? 'bg-gray-900 text-white shadow-xs' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
      >
        <span>🔄</span>
        <span>Retainers & MRR</span>
        <span class="rounded-full bg-indigo-500 text-white px-1.5 py-0.2 text-[10px] font-bold">
          {{ retainers.length }}
        </span>
      </button>
    </div>

    <!-- ============================================================== -->
    <!-- SUB-TAB 1: CASE STUDY #01 (FLAGSHIP PROOF OF WORK)             -->
    <!-- ============================================================== -->
    <div v-if="activeSubTab === 'case_study'" class="space-y-6">
      <div class="rounded-xl border border-gray-200 bg-white p-5 shadow-2xs space-y-5">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-gray-100 pb-4">
          <div>
            <div class="flex items-center gap-2">
              <span class="rounded-md bg-amber-100 text-amber-900 font-extrabold text-[10px] px-2 py-0.5 uppercase tracking-wide">
                Flagship Showcase
              </span>
              <h3 class="text-base font-black text-gray-950">
                Case Study #01: Second Brain Autonomous Workspace
              </h3>
            </div>
            <p class="text-xs text-gray-500 mt-1">
              Gunakan studi kasus ini sebagai bukti nyata kredibilitas teknis (*Proof of Work*) Verdion kepada klien global.
            </p>
          </div>
          <div class="flex items-center gap-2">
            <a
              href="https://second-brain-agent.netlify.app"
              target="_blank"
              class="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-bold text-gray-700 hover:bg-gray-50 transition-colors shadow-2xs inline-flex items-center gap-1"
            >
              <span>🌐</span>
              <span>Live Application ↗</span>
            </a>
            <button
              @click="copyCaseStudy"
              class="rounded-lg bg-gray-900 text-white px-3.5 py-1.5 text-xs font-bold hover:bg-gray-800 transition-colors shadow-2xs cursor-pointer inline-flex items-center gap-1.5"
            >
              <span>{{ caseStudyCopied ? '✅ Disalin!' : '📋 Salin Markdown Studi Kasus' }}</span>
            </button>
          </div>
        </div>

        <!-- 4-Pillar Proof Benchmarks -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div class="rounded-lg border border-emerald-200 bg-emerald-50/50 p-3">
            <span class="text-[10px] font-bold text-emerald-800 uppercase block">Automated Test Pass</span>
            <span class="text-lg font-black text-emerald-950 block mt-0.5">100% Passing</span>
            <span class="text-[11px] text-emerald-700">55 FE + 77 BE tests</span>
          </div>
          <div class="rounded-lg border border-blue-200 bg-blue-50/50 p-3">
            <span class="text-[10px] font-bold text-blue-800 uppercase block">API Response Latency</span>
            <span class="text-lg font-black text-blue-950 block mt-0.5">&lt; 100ms</span>
            <span class="text-[11px] text-blue-700">Async non-blocking FastAPI</span>
          </div>
          <div class="rounded-lg border border-purple-200 bg-purple-50/50 p-3">
            <span class="text-[10px] font-bold text-purple-800 uppercase block">Data Security</span>
            <span class="text-lg font-black text-purple-950 block mt-0.5">PostgreSQL RLS</span>
            <span class="text-[11px] text-purple-700">Isolated multi-tenant policies</span>
          </div>
          <div class="rounded-lg border border-amber-200 bg-amber-50/50 p-3">
            <span class="text-[10px] font-bold text-amber-800 uppercase block">Cloud Infrastructure</span>
            <span class="text-lg font-black text-amber-950 block mt-0.5">Zero Bloat</span>
            <span class="text-[11px] text-amber-700">100% Free-tier serverless ready</span>
          </div>
        </div>

        <!-- Architecture Breakdown Diagram -->
        <div class="rounded-xl border border-gray-200 bg-gray-900 text-gray-100 p-4 font-mono text-xs overflow-x-auto shadow-2xs">
          <div class="flex items-center justify-between text-gray-400 text-[10px] uppercase font-bold border-b border-gray-800 pb-2 mb-3">
            <span>Verified System Architecture (Verdion Production Blueprint)</span>
            <span class="text-emerald-400">● Production Verified</span>
          </div>
          <pre class="leading-relaxed">
┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│       Vue 3 + Tailwind CSS      │ <---> │   Supabase PostgreSQL Engine    │
│  (Type-safe, Reactive Client)   │       │ (Row-Level Security, Sub-100ms) │
└────────────────┬────────────────┘       └────────────────┬────────────────┘
                 │                                         │
                 ▼                                         ▼
┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│     FastAPI Async Engine Core   │ <---> │  Autonomous AI Agent Pipelines  │
│  (Non-blocking background sync) │       │ (Multi-turn tool call & models) │
└─────────────────────────────────┘       └─────────────────────────────────┘
          </pre>
        </div>

        <!-- Case Study Preview Box -->
        <div class="rounded-xl border border-gray-200 bg-gray-50 p-4 text-xs text-gray-800 space-y-3">
          <span class="text-[11px] font-bold text-gray-700 uppercase tracking-wider block">
            Studi Kasus Lengkap (Siap Share ke Founder / Substack / LinkedIn):
          </span>
          <pre class="bg-white p-3 rounded-lg border border-gray-200 text-[11px] font-mono whitespace-pre-wrap select-all leading-relaxed text-gray-800">{{ caseStudyMarkdown }}</pre>
        </div>
      </div>
    </div>

    <!-- ============================================================== -->
    <!-- SUB-TAB 2: BUILD-IN-PUBLIC SOCIAL POST ENGINE                  -->
    <!-- ============================================================== -->
    <div v-else-if="activeSubTab === 'bip_engine'" class="space-y-6">
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <!-- Left: Configuration Form -->
        <div class="lg:col-span-5 space-y-4">
          <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-2xs space-y-4">
            <div class="border-b border-gray-100 pb-3">
              <h3 class="text-sm font-bold text-gray-900 flex items-center gap-2">
                <span>✍️</span>
                <span>BiP Social Post Drafter</span>
              </h3>
              <p class="text-[11px] text-gray-500 mt-0.5">
                Ubah kodingan harianmu menjadi konten teknis bernilai tinggi untuk X & LinkedIn.
              </p>
            </div>

            <!-- Post Type Selector -->
            <div>
              <label class="block text-[11px] font-semibold text-gray-700 mb-1.5">Tipe Konten:</label>
              <div class="grid grid-cols-3 gap-1.5">
                <button
                  type="button"
                  @click="bipPostType = 'teardown'"
                  class="rounded-lg px-2.5 py-1.5 text-xs font-bold cursor-pointer transition-colors text-center"
                  :class="bipPostType === 'teardown' ? 'bg-gray-900 text-white shadow-2xs' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
                >
                  Teardown
                </button>
                <button
                  type="button"
                  @click="bipPostType = 'performance'"
                  class="rounded-lg px-2.5 py-1.5 text-xs font-bold cursor-pointer transition-colors text-center"
                  :class="bipPostType === 'performance' ? 'bg-gray-900 text-white shadow-2xs' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
                >
                  Perf Win
                </button>
                <button
                  type="button"
                  @click="bipPostType = 'devlog'"
                  class="rounded-lg px-2.5 py-1.5 text-xs font-bold cursor-pointer transition-colors text-center"
                  :class="bipPostType === 'devlog' ? 'bg-gray-900 text-white shadow-2xs' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
                >
                  Devlog
                </button>
              </div>
            </div>

            <!-- Dynamic Input Fields -->
            <div class="space-y-3">
              <div>
                <label class="block text-[11px] font-semibold text-gray-700 mb-1">Topik Komponen / Fitur:</label>
                <input
                  type="text"
                  v-model="bipTopic"
                  class="w-full rounded-lg border border-gray-300 px-3 py-1.5 text-xs text-gray-800 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
                  placeholder="e.g. Supabase Row-Level Security"
                />
              </div>

              <div>
                <label class="block text-[11px] font-semibold text-gray-700 mb-1">Metrik / Perubahan Terukur:</label>
                <input
                  type="text"
                  v-model="bipMetric"
                  class="w-full rounded-lg border border-gray-300 px-3 py-1.5 text-xs text-gray-800 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
                  placeholder="e.g. Dropped query latency from 1,420ms to 78ms"
                />
              </div>

              <div>
                <label class="block text-[11px] font-semibold text-gray-700 mb-1">Insight Teknis Utama (Root Cause):</label>
                <textarea
                  v-model="bipInsight"
                  rows="3"
                  class="w-full rounded-lg border border-gray-300 px-3 py-1.5 text-xs text-gray-800 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
                  placeholder="e.g. Composite indexing on (user_id, created_at) prevents sequential table scans during RLS checks."
                ></textarea>
              </div>
            </div>
          </div>
        </div>

        <!-- Right: Generated Post Formats (X & LinkedIn) -->
        <div class="lg:col-span-7 space-y-4">
          <!-- Twitter / X Preview -->
          <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-2xs space-y-3">
            <div class="flex items-center justify-between border-b border-gray-100 pb-2.5">
              <div class="flex items-center gap-2">
                <span class="text-base">𝕏</span>
                <h4 class="text-xs font-bold text-gray-900">Format X (Twitter Thread Hook)</h4>
              </div>
              <div class="flex items-center gap-2">
                <span
                  class="rounded-full px-2 py-0.5 text-[10px] font-bold"
                  :class="bipTwitterLength <= 280 ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'"
                >
                  {{ bipTwitterLength }} / 280 Karakter
                </span>
                <button
                  @click="copyBipText(bipTwitterContent)"
                  class="rounded-lg bg-gray-900 text-white px-2.5 py-1 text-xs font-bold hover:bg-gray-800 transition-colors cursor-pointer"
                >
                  {{ bipCopied ? '✅ Disalin' : '📋 Salin X' }}
                </button>
              </div>
            </div>
            <pre class="bg-gray-50 p-3 rounded-lg border border-gray-200 text-xs font-sans whitespace-pre-wrap select-all text-gray-800 leading-relaxed">{{ bipTwitterContent }}</pre>
          </div>

          <!-- LinkedIn Preview -->
          <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-2xs space-y-3">
            <div class="flex items-center justify-between border-b border-gray-100 pb-2.5">
              <div class="flex items-center gap-2">
                <span class="text-base">💼</span>
                <h4 class="text-xs font-bold text-gray-900">Format LinkedIn (Founder & Engineering Feed)</h4>
              </div>
              <button
                @click="copyBipText(bipLinkedInContent)"
                class="rounded-lg bg-blue-700 text-white px-2.5 py-1 text-xs font-bold hover:bg-blue-800 transition-colors cursor-pointer"
              >
                📋 Salin LinkedIn
              </button>
            </div>
            <pre class="bg-gray-50 p-3 rounded-lg border border-gray-200 text-xs font-sans whitespace-pre-wrap select-all text-gray-800 leading-relaxed">{{ bipLinkedInContent }}</pre>
          </div>
        </div>
      </div>
    </div>

    <!-- ============================================================== -->
    <!-- SUB-TAB 3: COLD LOOM AUDIT & FOUNDER DM DRAFTER                -->
    <!-- ============================================================== -->
    <div v-else-if="activeSubTab === 'cold_loom'" class="space-y-6">
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <!-- Left: Target Input Form -->
        <div class="lg:col-span-5 space-y-4">
          <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-2xs space-y-3.5">
            <div class="border-b border-gray-100 pb-3">
              <h3 class="text-sm font-bold text-gray-900 flex items-center gap-2">
                <span>🎯</span>
                <span>The 90-Second Loom Founder Audit</span>
              </h3>
              <p class="text-[11px] text-gray-500 mt-0.5">
                Dapatkan klien US/EU tanpa platform dengan mengirimkan video audit masalah produk mereka.
              </p>
            </div>

            <div>
              <label class="block text-[11px] font-semibold text-gray-700 mb-1">Nama Startup Target:</label>
              <input
                type="text"
                v-model="coldTargetStartup"
                class="w-full rounded-lg border border-gray-300 px-3 py-1.5 text-xs text-gray-800 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
                placeholder="e.g. FinTech Alpha"
              />
            </div>

            <div>
              <label class="block text-[11px] font-semibold text-gray-700 mb-1">Nama Founder / CTO:</label>
              <input
                type="text"
                v-model="coldFounderName"
                class="w-full rounded-lg border border-gray-300 px-3 py-1.5 text-xs text-gray-800 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
                placeholder="e.g. Alex"
              />
            </div>

            <div>
              <label class="block text-[11px] font-semibold text-gray-700 mb-1">Masalah / Bottleneck yang Ditemukan:</label>
              <textarea
                v-model="coldObservedBottleneck"
                rows="2"
                class="w-full rounded-lg border border-gray-300 px-3 py-1.5 text-xs text-gray-800 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
                placeholder="e.g. dashboard takes 4.2 seconds to load due to unindexed queries"
              ></textarea>
            </div>

            <div>
              <label class="block text-[11px] font-semibold text-gray-700 mb-1">Solusi Rekayasa Verdion:</label>
              <input
                type="text"
                v-model="coldVerdionFix"
                class="w-full rounded-lg border border-gray-300 px-3 py-1.5 text-xs text-gray-800 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
                placeholder="e.g. Redis caching + compound Supabase index"
              />
            </div>

            <div>
              <label class="block text-[11px] font-semibold text-gray-700 mb-1">Link Loom Video (90 Detik):</label>
              <input
                type="text"
                v-model="coldLoomUrl"
                class="w-full rounded-lg border border-gray-300 px-3 py-1.5 text-xs text-gray-800 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
                placeholder="loom.com/share/verdion-audit-demo"
              />
            </div>
          </div>
        </div>

        <!-- Right: Generated Scripts & Outreach DMs -->
        <div class="lg:col-span-7 space-y-4">
          <!-- 90s Video Script -->
          <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-2xs space-y-3">
            <div class="flex items-center justify-between border-b border-gray-100 pb-2.5">
              <div>
                <h4 class="text-xs font-bold text-gray-900 flex items-center gap-1.5">
                  <span>🎥</span>
                  <span>Naskah Rekaman Video Loom 90-Detik</span>
                </h4>
                <p class="text-[10px] text-gray-500">Tunjukkan kodingan solusimu langsung di layar.</p>
              </div>
              <button
                @click="copyColdScript"
                class="rounded-lg bg-gray-900 text-white px-2.5 py-1 text-xs font-bold hover:bg-gray-800 transition-colors cursor-pointer"
              >
                {{ coldScriptCopied ? '✅ Disalin' : '📋 Salin Script Loom' }}
              </button>
            </div>
            <pre class="bg-gray-50 p-3 rounded-lg border border-gray-200 text-xs font-sans whitespace-pre-wrap select-all text-gray-800 leading-relaxed">{{ cold90sScript }}</pre>
          </div>

          <!-- Direct Message Script -->
          <div class="rounded-xl border border-amber-200 bg-amber-50/40 p-4 shadow-2xs space-y-3">
            <div class="flex items-center justify-between border-b border-amber-100 pb-2.5">
              <div>
                <h4 class="text-xs font-bold text-amber-950 flex items-center gap-1.5">
                  <span>📩</span>
                  <span>Draf DM LinkedIn / X ke Founder</span>
                </h4>
                <p class="text-[10px] text-amber-800">100% Value-first, tanpa bahasa sales murahan.</p>
              </div>
              <button
                @click="copyColdDm"
                class="rounded-lg bg-amber-600 text-white px-2.5 py-1 text-xs font-bold hover:bg-amber-700 transition-colors cursor-pointer"
              >
                {{ coldDmCopied ? '✅ Disalin' : '📋 Salin DM Founder' }}
              </button>
            </div>
            <pre class="bg-white p-3 rounded-lg border border-amber-200 text-xs font-mono whitespace-pre-wrap select-all text-gray-900 leading-relaxed">{{ coldFounderDm }}</pre>
          </div>
        </div>
      </div>
    </div>

    <!-- ============================================================== -->
    <!-- SUB-TAB 4: PRODUCTIZED DEALS & DIRECT PIPELINE                 -->
    <!-- ============================================================== -->
    <div v-else-if="activeSubTab === 'deals'" class="space-y-6">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h3 class="text-base font-black text-gray-900 flex items-center gap-2">
            <span>💼</span>
            <span>Productized Services & Direct Client Pipeline</span>
          </h3>
          <p class="text-xs text-gray-500 mt-0.5">
            Tarif studio tetap (fixed-scope), 0% potongan fee platform, dan pembayaran 50% deposit via Wise/Stripe.
          </p>
        </div>
        <button
          @click="showNewDirectDealModal = true"
          class="rounded-lg bg-emerald-600 text-white px-3.5 py-1.5 text-xs font-bold hover:bg-emerald-700 transition-colors shadow-2xs cursor-pointer flex items-center gap-1"
        >
          <span>+</span>
          <span>Catat Direct Deal Baru</span>
        </button>
      </div>

      <!-- 3 Productized Service Menus -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-2xs space-y-2">
          <div class="flex items-center justify-between">
            <span class="rounded bg-gray-100 text-gray-800 text-[10px] font-extrabold px-2 py-0.5 uppercase">Tier 1</span>
            <span class="text-sm font-black text-gray-900">$500</span>
          </div>
          <h4 class="text-sm font-bold text-gray-950">48-Hour Technical & Architecture Audit</h4>
          <p class="text-xs text-gray-500 leading-relaxed">
            Audit keamanan, query database bottleneck, dan blueprint refactor sebelum klien scaling.
          </p>
          <span class="text-[11px] text-emerald-700 font-bold block pt-1">Turnaround: 48 Jam</span>
        </div>

        <div class="rounded-xl border border-amber-300 bg-gradient-to-br from-amber-50 to-white p-4 shadow-2xs space-y-2 relative overflow-hidden">
          <div class="flex items-center justify-between">
            <span class="rounded bg-amber-500 text-white text-[10px] font-extrabold px-2 py-0.5 uppercase">Most Demanded</span>
            <span class="text-sm font-black text-amber-950">$2,500 – $4,000</span>
          </div>
          <h4 class="text-sm font-bold text-gray-950">14-Day Production MVP Sprint</h4>
          <p class="text-xs text-gray-600 leading-relaxed">
            Full-stack prototype siap launch (FastAPI + Vue/React + Supabase RLS) dengan 100% test coverage.
          </p>
          <span class="text-[11px] text-amber-800 font-bold block pt-1">Turnaround: 14 Hari</span>
        </div>

        <div class="rounded-xl border border-purple-200 bg-white p-4 shadow-2xs space-y-2">
          <div class="flex items-center justify-between">
            <span class="rounded bg-purple-100 text-purple-900 text-[10px] font-extrabold px-2 py-0.5 uppercase">Enterprise</span>
            <span class="text-sm font-black text-purple-950">$3,000 – $5,000</span>
          </div>
          <h4 class="text-sm font-bold text-gray-950">Autonomous AI Agent Workflow Pipeline</h4>
          <p class="text-xs text-gray-500 leading-relaxed">
            Sistem multi-agent otomatis, function-calling, state persistence, dan background workers.
          </p>
          <span class="text-[11px] text-purple-700 font-bold block pt-1">Turnaround: 21 Hari</span>
        </div>
      </div>

      <!-- Deals Pipeline Table -->
      <div class="rounded-xl border border-gray-200 bg-white p-4 shadow-2xs space-y-3">
        <h4 class="text-sm font-bold text-gray-900">Daftar Deal Klien Langsung (Direct Pipeline):</h4>
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="bg-gray-50 text-gray-500 uppercase text-[10px] font-bold border-b border-gray-200">
              <tr>
                <th class="py-2.5 px-3">Klien / Startup</th>
                <th class="py-2.5 px-3">Founder Handle</th>
                <th class="py-2.5 px-3">Paket Layanan</th>
                <th class="py-2.5 px-3">Nilai Deal ($ USD)</th>
                <th class="py-2.5 px-3">Tahap Pipeline</th>
                <th class="py-2.5 px-3">Catatan</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              <tr v-for="deal in directDeals" :key="deal.id" class="hover:bg-gray-50/70 transition-colors">
                <td class="py-3 px-3">
                  <div class="font-bold text-gray-900">{{ deal.client_name }}</div>
                  <div class="text-[11px] text-gray-500">{{ deal.project_title }}</div>
                </td>
                <td class="py-3 px-3 font-mono text-[11px] text-gray-700">{{ deal.founder_handle }}</td>
                <td class="py-3 px-3 font-semibold text-gray-800">{{ deal.package_type }}</td>
                <td class="py-3 px-3">
                  <span class="font-black text-gray-950">{{ formatUsd(deal.deal_amount_usd) }}</span>
                  <span class="text-[10px] text-emerald-700 block font-bold">100% Net IDR</span>
                </td>
                <td class="py-3 px-3">
                  <span
                    class="rounded-full px-2 py-0.5 text-[10px] font-bold uppercase"
                    :class="{
                      'bg-emerald-100 text-emerald-800': ['deposit_paid', 'delivered'].includes(deal.stage),
                      'bg-indigo-100 text-indigo-800': deal.stage === 'call_booked',
                      'bg-blue-100 text-blue-800': deal.stage === 'in_progress',
                      'bg-gray-100 text-gray-800': deal.stage === 'lead' || deal.stage === 'loom_sent',
                    }"
                  >
                    {{ deal.stage.replace('_', ' ') }}
                  </span>
                </td>
                <td class="py-3 px-3 text-gray-600 text-[11px] max-w-xs truncate" :title="deal.notes || ''">
                  {{ deal.notes || '-' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ============================================================== -->
    <!-- SUB-TAB 5: RETAINERS & RECURRING MRR                           -->
    <!-- ============================================================== -->
    <div v-else-if="activeSubTab === 'retainers'" class="space-y-6">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-base font-black text-gray-900 flex items-center gap-2">
            <span>🔄</span>
            <span>Retainer & Client Recurring MRR</span>
          </h3>
          <p class="text-xs text-gray-500 mt-0.5">
            Ubah kontrak sekali bayar menjadi pemasukan rutin bulanan ($800 - $1,500/bln) via invoice Wise/Stripe.
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

    <!-- MODAL 1: NEW DIRECT DEAL -->
    <div v-if="showNewDirectDealModal" class="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/50 p-4 backdrop-blur-xs">
      <div class="w-full max-w-lg rounded-2xl bg-white p-5 shadow-xl space-y-4">
        <h3 class="text-base font-bold text-gray-900">Catat Direct Client Deal Baru</h3>
        <div class="space-y-3 text-xs">
          <div>
            <label class="block font-semibold text-gray-700 mb-1">Nama Startup / Klien:</label>
            <input type="text" v-model="newDeal.client_name" class="w-full rounded-lg border border-gray-300 p-2" placeholder="e.g. Acme AI" />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block font-semibold text-gray-700 mb-1">Founder Handle / Kontak:</label>
              <input type="text" v-model="newDeal.founder_handle" class="w-full rounded-lg border border-gray-300 p-2" placeholder="@founder_x" />
            </div>
            <div>
              <label class="block font-semibold text-gray-700 mb-1">Nilai Kontrak ($ USD):</label>
              <input type="number" v-model.number="newDeal.deal_amount_usd" class="w-full rounded-lg border border-gray-300 p-2" />
            </div>
          </div>
          <div>
            <label class="block font-semibold text-gray-700 mb-1">Paket Layanan:</label>
            <select v-model="newDeal.package_type" class="w-full rounded-lg border border-gray-300 p-2">
              <option value="48-Hour Technical Audit">48-Hour Technical Audit ($500)</option>
              <option value="14-Day MVP Sprint">14-Day Production MVP Sprint ($2,500 – $4,000)</option>
              <option value="AI Agent Workflow">Autonomous AI Agent Workflow ($3,000 – $5,000)</option>
              <option value="Custom Engineering">Custom Engineering Sprint</option>
            </select>
          </div>
          <div>
            <label class="block font-semibold text-gray-700 mb-1">Tahap Pipeline:</label>
            <select v-model="newDeal.stage" class="w-full rounded-lg border border-gray-300 p-2">
              <option value="lead">Lead Identified</option>
              <option value="loom_sent">Loom Audit Sent</option>
              <option value="call_booked">Discovery Call Booked</option>
              <option value="deposit_paid">50% Deposit Paid</option>
              <option value="in_progress">In Progress</option>
              <option value="delivered">Delivered & Fully Paid</option>
              <option value="testimonial_secured">Testimonial Secured</option>
            </select>
          </div>
          <div>
            <label class="block font-semibold text-gray-700 mb-1">Catatan Tambahan:</label>
            <textarea v-model="newDeal.notes" rows="2" class="w-full rounded-lg border border-gray-300 p-2" placeholder="e.g. Deposit via Wise, deadline Oct 15"></textarea>
          </div>
        </div>
        <div class="flex justify-end gap-2 pt-2 border-t">
          <button @click="showNewDirectDealModal = false" class="px-3 py-1.5 text-xs font-semibold text-gray-600 cursor-pointer">Batal</button>
          <button @click="handleAddDirectDeal" class="px-4 py-1.5 text-xs font-bold text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 cursor-pointer">
            Simpan Deal
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL 2: NEW RETAINER -->
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
            <textarea v-model="newRetainer.notes" rows="2" class="w-full rounded-lg border border-gray-300 p-2" placeholder="e.g. 15 jam/bulan architecture tuning & bug fixing"></textarea>
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
