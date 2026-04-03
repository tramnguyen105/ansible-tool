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
          ? 'border-rose-500/30 bg-rose-50'
          : primaryState.tone === 'active'
            ? 'border-amber-500/30 bg-amber-50'
            : 'border-emerald-500/30 bg-emerald-50'"
      >
        <p class="text-[0.8rem] font-medium uppercase tracking-[0.12em]" :class="primaryState.tone === 'critical' ? 'text-rose-500' : primaryState.tone === 'active' ? 'text-amber-600' : 'text-emerald-600'">
          {{ primaryState.eyebrow }}
        </p>
        <h3 class="mt-2 text-[1.8rem] font-semibold text-slate-900">{{ primaryState.title }}</h3>
        <p class="mt-2 text-[0.98rem] leading-7 text-slate-800/90">{{ primaryState.description }}</p>
      </section>

      <section class="rounded-2xl border border-slate-200 bg-white p-5">
        <p class="text-[0.8rem] font-medium uppercase tracking-[0.12em] text-slate-500">Result set</p>
        <div class="mt-4 grid gap-4 sm:grid-cols-3">
          <div>
            <p class="text-[0.78rem] uppercase tracking-[0.1em] text-slate-500">Latest job</p>
            <p class="mt-2 text-[0.98rem] font-medium text-slate-900">{{ latestJobSummary }}</p>
          </div>
          <div>
            <p class="text-[0.78rem] uppercase tracking-[0.1em] text-slate-500">Latest failure</p>
            <p class="mt-2 text-[0.98rem] font-medium text-slate-900">{{ latestFailureSummary }}</p>
          </div>
          <div>
            <p class="text-[0.78rem] uppercase tracking-[0.1em] text-slate-500">Visible jobs</p>
            <p class="mt-2 text-[0.98rem] font-medium text-slate-900">{{ totalJobs }}</p>
          </div>
        </div>
      </section>
    </div>

    <div class="mt-6 grid gap-4 xl:grid-cols-4">
      <CardStat label="Failed jobs" :value="summary.failed" tone="tracked" helper="Matching failed jobs requiring review." />
      <CardStat label="Running jobs" :value="summary.running" tone="managed" helper="Matching jobs currently in progress." />
      <CardStat label="Queued jobs" :value="summary.queued" tone="validated" helper="Matching jobs waiting for worker capacity." />
      <CardStat label="Check mode" :value="summary.checkMode" tone="secured" helper="Validation runs in the current result set." />
    </div>

    <section class="mt-6 rounded-2xl border border-slate-200 bg-white p-5">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p class="text-[0.8rem] font-medium uppercase tracking-[0.12em] text-slate-500">Filters</p>
          <h3 class="mt-2 text-[1.15rem] font-semibold text-slate-900">Execution history</h3>
          <p class="mt-2 text-[0.96rem] text-slate-600">Filter by status, mode, or name to isolate the jobs that matter now.</p>
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
        :rows="rows"
        :loading="isLoading"
        :error="Boolean(queryError)"
        :sort-by="sortBy"
        :sort-order="sortOrder as 'asc' | 'desc'"
        loading-title="Loading jobs"
        loading-description="Fetching execution history from the API."
        error-title="Job history is unavailable"
        error-description="The job query failed. Retry the request or adjust the active filters."
        empty-title="No jobs match your current filters"
        empty-description="Launch a job manually or broaden the filters to review older activity."
        @retry="load"
        @sort="handleSort"
      >
        <template #name="{ row }">
          <div>
            <p class="font-medium text-slate-900">{{ row.name }}</p>
            <p class="mt-1 text-xs text-slate-500">{{ row.target_value || 'All managed hosts' }}</p>
          </div>
        </template>
        <template #status="{ row }">
          <StatusBadge :value="row.status" />
        </template>
        <template #target_type="{ row }">
          <div>
            <p class="font-medium text-slate-900">{{ row.target_type }}</p>
            <p class="mt-1 text-xs text-slate-500">{{ row.modeLabel }}</p>
          </div>
        </template>
        <template #created_at="{ row }">
          <div>
            <p class="font-medium text-slate-900">{{ formatDateTime(row.created_at) }}</p>
            <p class="mt-1 text-xs text-slate-500">{{ row.relativeCreated }}</p>
          </div>
        </template>
        <template #actions="{ row }">
          <RouterLink class="text-[0.96rem] font-medium text-sky-600 transition hover:text-slate-900" :to="`/jobs/${row.id}`">Details</RouterLink>
        </template>
        <template #footer>
          <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p class="text-sm text-slate-600">
              Showing {{ rows.length ? offset + 1 : 0 }}-{{ offset + rows.length }} of {{ totalJobs }} jobs
            </p>
            <div class="flex items-center gap-2">
              <button class="btn-secondary" :disabled="isLoading || page <= 1" @click="goToPreviousPage">Previous</button>
              <span class="text-sm text-slate-500">Page {{ page }}</span>
              <button class="btn-secondary" :disabled="isLoading || !hasMore" @click="goToNextPage">Next</button>
            </div>
          </div>
        </template>
      </DataTable>
    </div>

    <JobRunWizard :open="showWizard" @close="showWizard = false" @saved="refreshFromStart" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import { jobsApi, type JobListItem, type JobListSummary } from '../../api/jobs'
import CardStat from '../../components/common/CardStat.vue'
import DataTable from '../../components/common/DataTable.vue'
import PageHeader from '../../components/common/PageHeader.vue'
import StatusBadge from '../../components/common/StatusBadge.vue'
import JobRunWizard from '../../components/wizards/JobRunWizard.vue'
import { useListQueryState } from '../../composables/useListQueryState'
import { usePagedCollection } from '../../composables/usePagedCollection'
import { useAppStore } from '../../stores/app'
import { formatDateTime, formatRelativeTime } from '../../utils/format'

const app = useAppStore()
const showWizard = ref(false)
const queryError = ref<unknown>(null)

const {
  search,
  sortBy,
  sortOrder,
  page,
  offset: routeOffset,
  filters,
  setSort,
  setPage,
} = useListQueryState({
  pageSize: 10,
  search: { key: 'search', defaultValue: '' },
  filters: [
    { key: 'status', defaultValue: 'all' },
    { key: 'mode', defaultValue: 'all' },
  ],
  sortBy: { key: 'sortBy', defaultValue: 'created_at' },
  sortOrder: { key: 'sortOrder', defaultValue: 'desc' },
})

const statusFilter = filters.status
const modeFilter = filters.mode

const columns = [
  { key: 'name', label: 'Job', sortable: true },
  { key: 'status', label: 'Status', sortable: true },
  { key: 'target_type', label: 'Target scope', sortable: true },
  { key: 'created_at', label: 'Submitted', sortable: true },
]

type JobRow = JobListItem & { modeLabel: string; relativeCreated: string }
type JobsMeta = { summary: JobListSummary }

const {
  items: rows,
  isLoading,
  total: totalJobs,
  hasMore,
  offset,
  meta,
  load: baseLoad,
  refreshFromStart,
} = usePagedCollection<JobRow, JobsMeta>({
  pageSize: 10,
  watchSources: [search, statusFilter, modeFilter, sortBy, sortOrder],
  onError: (error) => {
    queryError.value = error
    app.pushToast('Job history could not be loaded', 'error', 'Check the API connection and retry the request.')
  },
  query: async ({ limit, offset }) => {
    const params: Record<string, string | number | string[]> = {
      limit,
      offset,
      sort_by: sortBy.value,
      sort_order: sortOrder.value,
    }
    if (search.value.trim()) params.search = search.value.trim()
    if (statusFilter.value !== 'all') params.statuses = [statusFilter.value]
    if (modeFilter.value !== 'all') params.mode = modeFilter.value

    const response = await jobsApi.query(params)
    return {
      ...response.data.data,
      items: response.data.data.items.map(normalizeRow),
    }
  },
})

const summary = computed(() => ({
  queued: meta.value.summary?.queued || 0,
  running: meta.value.summary?.running || 0,
  success: meta.value.summary?.success || 0,
  failed: meta.value.summary?.failed || 0,
  checkMode: meta.value.summary?.check_mode || 0,
}))

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
  queryError.value = null
  await baseLoad().catch(() => undefined)
}

function handleSort(key: string) {
  setSort(key)
}

function goToNextPage() {
  if (!hasMore.value) return
  setPage(page.value + 1)
  return load()
}

function goToPreviousPage() {
  if (page.value <= 1) return
  setPage(page.value - 1)
  return load()
}

watch(routeOffset, (nextOffset) => {
  offset.value = nextOffset
}, { immediate: true })

onMounted(load)
</script>
