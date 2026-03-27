<template>
  <div>
    <PageHeader
      title="Jobs"
      eyebrow="Execution Queue"
      description="Launch jobs with the right guardrails, then watch queue state, live execution, and result detail without leaving the operations console."
    >
      <button class="btn-secondary" :disabled="isLoading" @click="load">{{ isLoading ? 'Refreshing...' : 'Refresh' }}</button>
      <button class="btn-primary" @click="showWizard = true">Run job</button>
    </PageHeader>

    <BannerNotice
      title="Production Warning"
      tone="warn"
      text="Live jobs can reach production devices immediately. Prefer check mode for unreviewed playbooks, large target scopes, or newly imported inventory."
    />

    <div class="mt-5 grid gap-4 xl:grid-cols-4">
      <CardStat label="Queued" :value="summary.queued" tone="queued" :helper="summary.queued ? 'Waiting for worker capacity or schedule dispatch.' : 'No queued jobs.'" />
      <CardStat label="Running" :value="summary.running" tone="running" :helper="summary.running ? 'Active jobs are currently modifying or validating targets.' : 'No active execution.'" />
      <CardStat label="Succeeded" :value="summary.success" tone="success" :helper="summary.success ? 'Recent execution completed successfully.' : 'No completed success records yet.'" />
      <CardStat label="Failed" :value="summary.failed" tone="failed" :helper="summary.failed ? 'Review failed jobs before re-running.' : 'No recent failures.'" />
    </div>

    <section class="mt-6 rounded-3xl border border-console-edge bg-console-panel/80 p-5 shadow-xl shadow-slate-950/20">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p class="text-xs uppercase tracking-[0.22em] text-console-glow">Execution Control</p>
          <h3 class="mt-2 text-xl font-semibold text-white">Filter active and historical jobs</h3>
          <p class="mt-2 max-w-3xl text-sm leading-6 text-console-muted">
            Keep visibility on risky target scopes and distinguish check-mode validation from live production runs.
          </p>
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
        description="Review target scope, submission time, and execution mode before opening job detail."
        :columns="columns"
        :rows="filteredRows"
        :loading="isLoading"
        loading-title="Loading job history"
        loading-description="Collecting execution history, queue state, and mode metadata from the backend."
        empty-title="No jobs match your current filters"
        empty-description="Launch a job manually or broaden the filters to review older activity."
      >
        <template #name="{ row }">
          <div>
            <p class="font-medium text-white">{{ row.name }}</p>
            <p class="mt-1 text-xs text-console-muted">{{ row.target_value || 'All managed hosts' }}</p>
          </div>
        </template>
        <template #status="{ row }">
          <StatusBadge :value="row.status" />
        </template>
        <template #target_type="{ row }">
          <div>
            <p class="text-white">{{ row.target_type }}</p>
            <p class="mt-1 text-xs text-console-muted">{{ row.modeLabel }}</p>
          </div>
        </template>
        <template #created_at="{ row }">
          <div>
            <p class="text-white">{{ formatDateTime(row.created_at) }}</p>
            <p class="mt-1 text-xs text-console-muted">{{ row.relativeCreated }}</p>
          </div>
        </template>
        <template #actions="{ row }">
          <RouterLink class="text-console-glow transition hover:text-white" :to="`/jobs/${row.id}`">Open</RouterLink>
        </template>
      </DataTable>
    </div>

    <JobRunWizard :open="showWizard" @close="showWizard = false" @saved="load" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import api from '../../api/client'
import BannerNotice from '../../components/common/BannerNotice.vue'
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

function normalizeRow(row: any) {
  return {
    ...row,
    modeLabel: row.check_mode ? 'Check mode validation' : 'Live production run',
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
