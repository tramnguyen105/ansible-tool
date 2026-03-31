<template>
  <div>
    <PageHeader
      title="Jobs"
      eyebrow="Execution"
      description="Launch jobs, monitor active execution, and review recent results from one place."
    >
      <button class="btn-secondary" :disabled="isLoading" @click="load">{{ isLoading ? 'Refreshing…' : 'Refresh' }}</button>
      <button class="btn-primary" @click="showWizard = true">Run job</button>
    </PageHeader>

    <div class="mt-6 grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
      <section
        class="rounded-2xl border p-5"
        :class="primaryState.tone === 'critical'
          ? 'border-rose-500/30 bg-rose-500/10'
          : primaryState.tone === 'active'
            ? 'border-amber-500/30 bg-amber-500/10'
            : 'border-emerald-500/30 bg-emerald-500/10'"
      >
        <p class="text-[0.8rem] font-medium uppercase tracking-[0.12em]" :class="primaryState.tone === 'critical' ? 'text-rose-200' : primaryState.tone === 'active' ? 'text-amber-200' : 'text-emerald-200'">
          {{ primaryState.eyebrow }}
        </p>
        <h3 class="mt-2 text-[1.8rem] font-semibold text-white">{{ primaryState.title }}</h3>
        <p class="mt-2 text-[0.98rem] leading-7 text-slate-200/90">{{ primaryState.description }}</p>
      </section>

      <section class="rounded-2xl border border-slate-800 bg-slate-900 p-5">
        <p class="text-[0.8rem] font-medium uppercase tracking-[0.12em] text-slate-500">Activity window</p>
        <div class="mt-4 grid gap-4 sm:grid-cols-3">
          <div>
            <p class="text-[0.78rem] uppercase tracking-[0.1em] text-slate-500">Latest job</p>
            <p class="mt-2 text-[0.98rem] font-medium text-white">{{ latestJobSummary }}</p>
          </div>
          <div>
            <p class="text-[0.78rem] uppercase tracking-[0.1em] text-slate-500">Latest failure</p>
            <p class="mt-2 text-[0.98rem] font-medium text-white">{{ latestFailureSummary }}</p>
          </div>
          <div>
            <p class="text-[0.78rem] uppercase tracking-[0.1em] text-slate-500">Live jobs</p>
            <p class="mt-2 text-[0.98rem] font-medium text-white">{{ liveRunSummary }}</p>
          </div>
        </div>
      </section>
    </div>

    <div class="mt-6 grid gap-4 xl:grid-cols-4">
      <CardStat label="Failed jobs" :value="summary.failed" tone="tracked" helper="Recent failures requiring review." />
      <CardStat label="Running jobs" :value="summary.running" tone="managed" helper="Jobs currently queued or in progress." />
      <CardStat label="Queued jobs" :value="summary.queued" tone="validated" helper="Waiting for worker capacity or dispatch." />
      <CardStat label="Check mode" :value="summary.checkMode" tone="secured" helper="Validation runs recorded in the current list." />
    </div>

    <section class="mt-6 rounded-2xl border border-slate-800 bg-slate-900 p-5">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p class="text-[0.8rem] font-medium uppercase tracking-[0.12em] text-slate-500">Filters</p>
          <h3 class="mt-2 text-[1.15rem] font-semibold text-white">Execution history</h3>
          <p class="mt-2 text-[0.96rem] text-slate-400">Filter by status, mode, or name to isolate the jobs that matter now.</p>
        </div>
        <div class="grid gap-3 sm:grid-cols-2 lg:min-w-[460px] xl:grid-cols-3">
          <input v-model="search" placeholder="Search by job name" :disabled="isLoading" />
          <select v-model="statusFilter" :disabled="isLoading">
            <option value="all">All statuses</option>
            <option value="queued">Queued</option>
            <option value="running">Running</option>
            <option value="success">Success</option>
            <option value="failed">Failed</option>
          </select>
          <select v-model="modeFilter" :disabled="isLoading">
            <option value="all">All modes</option>
            <option value="check">Check mode</option>
            <option value="live">Live runs</option>
          </select>
        </div>
      </div>
    </section>

    <div class="mt-6">
      <DataTable
        title="Job history"
        description="Recent execution records with target scope, mode, and status."
        :columns="columns"
        :rows="filteredRows"
        empty-title="No jobs match your current filters"
        empty-description="Launch a job manually or broaden the filters to review older activity."
      >
        <template #name="{ row }">
          <div>
            <p class="font-medium text-white">{{ row.name }}</p>
            <p class="mt-1 text-xs text-slate-500">{{ row.target_value || 'All managed hosts' }}</p>
          </div>
        </template>
        <template #status="{ row }">
          <StatusBadge :value="row.status" />
        </template>
        <template #target_type="{ row }">
          <div>
            <p class="font-medium text-white">{{ row.target_type }}</p>
            <p class="mt-1 text-xs text-slate-500">{{ row.modeLabel }}</p>
          </div>
        </template>
        <template #created_at="{ row }">
          <div>
            <p class="font-medium text-white">{{ formatDateTime(row.created_at) }}</p>
            <p class="mt-1 text-xs text-slate-500">{{ row.relativeCreated }}</p>
          </div>
        </template>
        <template #actions="{ row }">
          <RouterLink class="text-[0.96rem] font-medium text-sky-300 transition hover:text-white" :to="`/jobs/${row.id}`">Details</RouterLink>
        </template>
      </DataTable>
    </div>

    <JobRunWizard :open="showWizard" @close="showWizard = false" @saved="load" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import api from '../../api/client'
import CardStat from '../../components/common/CardStat.vue'
import DataTable from '../../components/common/DataTable.vue'
import PageHeader from '../../components/common/PageHeader.vue'
import StatusBadge from '../../components/common/StatusBadge.vue'
import JobRunWizard from '../../components/wizards/JobRunWizard.vue'
import { useAppStore } from '../../stores/app'
import { formatDateTime, formatRelativeTime } from '../../utils/format'

const app = useAppStore()
const rows = ref<any[]>([])
const showWizard = ref(false)
const search = ref('')
const statusFilter = ref('all')
const modeFilter = ref('all')
const isLoading = ref(true)

const columns = [
  { key: 'name', label: 'Job' },
  { key: 'status', label: 'Status' },
  { key: 'target_type', label: 'Target scope' },
  { key: 'created_at', label: 'Submitted' },
]

const summary = computed(() => ({
  queued: rows.value.filter((row) => ['queued', 'pending'].includes(row.status)).length,
  running: rows.value.filter((row) => row.status === 'running').length,
  success: rows.value.filter((row) => ['success', 'completed'].includes(row.status)).length,
  failed: rows.value.filter((row) => ['failed', 'error'].includes(row.status)).length,
  checkMode: rows.value.filter((row) => row.check_mode).length,
}))

const filteredRows = computed(() => {
  return rows.value.filter((row) => {
    const matchesSearch = row.name.toLowerCase().includes(search.value.toLowerCase())
    const matchesStatus =
      statusFilter.value === 'all' ||
      (statusFilter.value === 'success' && ['success', 'completed'].includes(row.status)) ||
      (statusFilter.value === 'failed' && ['failed', 'error'].includes(row.status)) ||
      (statusFilter.value === 'queued' && ['queued', 'pending'].includes(row.status)) ||
      row.status === statusFilter.value
    const matchesMode =
      modeFilter.value === 'all' ||
      (modeFilter.value === 'check' && row.check_mode) ||
      (modeFilter.value === 'live' && !row.check_mode)

    return matchesSearch && matchesStatus && matchesMode
  })
})

const latestJob = computed(() => rows.value[0] || null)
const latestFailure = computed(() => rows.value.find((row) => ['failed', 'error'].includes(row.status)) || null)

const latestJobSummary = computed(() => {
  if (!latestJob.value) return 'No jobs recorded yet.'
  return `${latestJob.value.name} · ${latestJob.value.relativeCreated}`
})

const latestFailureSummary = computed(() => {
  if (!latestFailure.value) return 'No recent failures.'
  return `${latestFailure.value.name} · ${latestFailure.value.relativeCreated}`
})

const liveRunSummary = computed(() => {
  const live = rows.value.filter((row) => !row.check_mode)
  if (!live.length) return 'No live runs recorded.'
  return `${live.length} live run${live.length === 1 ? '' : 's'} in history`
})

const primaryState = computed(() => {
  if (summary.value.failed > 0) {
    return {
      tone: 'critical',
      eyebrow: 'Needs attention',
      title: `${summary.value.failed} failed job${summary.value.failed === 1 ? '' : 's'}`,
      description: 'Review recent failures before queuing more runs against the same systems.',
    }
  }
  if (summary.value.running > 0 || summary.value.queued > 0) {
    return {
      tone: 'active',
      eyebrow: 'Execution in progress',
      title: `${summary.value.running + summary.value.queued} active or queued job${summary.value.running + summary.value.queued === 1 ? '' : 's'}`,
      description: 'Automation is currently running or waiting for worker capacity. Avoid overlapping changes without a reason.',
    }
  }
  return {
    tone: 'healthy',
    eyebrow: 'Stable state',
    title: 'No active execution issues',
    description: 'No failed, running, or queued jobs are currently competing for attention.',
  }
})

function normalizeRow(row: any) {
  return {
    ...row,
    modeLabel: row.check_mode ? 'Check mode validation' : 'Live run',
    relativeCreated: formatRelativeTime(row.created_at),
  }
}

async function load() {
  isLoading.value = true
  try {
    const response = await api.get('/jobs')
    rows.value = response.data.data.map(normalizeRow)
  } catch {
    app.pushToast('Job history could not be loaded', 'error', 'Check the API connection and retry the request.')
  } finally {
    isLoading.value = false
  }
}

onMounted(load)
</script>
