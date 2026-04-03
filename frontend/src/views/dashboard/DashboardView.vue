<template>
  <div>
    <PageHeader
      title="Dashboard"
      eyebrow="Overview"
      description="Current automation state, recent activity, and upcoming scheduled work."
    >
      <RouterLink class="btn-secondary" to="/inventory">Manage inventory</RouterLink>
      <RouterLink class="btn-primary" to="/jobs">Run job</RouterLink>
    </PageHeader>

    <div v-if="isLoading" class="mt-6 rounded-3xl border border-console-edge bg-white/80 p-6 shadow-sm">
      <div class="h-4 w-40 rounded-full bg-slate-100" />
      <div class="mt-5 grid gap-4 lg:grid-cols-3">
        <div class="h-28 rounded-3xl bg-slate-200/80" />
        <div class="h-28 rounded-3xl bg-slate-200/70" />
        <div class="h-28 rounded-3xl bg-slate-200/60" />
      </div>
      <p class="mt-5 text-[0.96rem] text-slate-600">Loading dashboard data…</p>
    </div>

    <template v-else>
      <section class="mt-6 grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
        <div class="rounded-[28px] border border-console-edge bg-white/85 p-6 shadow-sm">
          <p class="text-[0.76rem] font-semibold uppercase tracking-[0.24em] text-console-glow">{{ primaryState.eyebrow }}</p>
          <div class="mt-4 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h3 class="text-[2rem] font-semibold leading-tight text-slate-900">{{ primaryState.title }}</h3>
              <p class="mt-3 max-w-2xl text-[1rem] leading-7 text-console-muted">{{ primaryState.description }}</p>
            </div>
            <div class="rounded-3xl border border-console-edge/80 bg-console-surface/70 px-4 py-4">
              <p class="text-[0.72rem] uppercase tracking-[0.18em] text-console-muted">Operator focus</p>
              <p class="mt-2 text-sm font-medium text-slate-900">{{ attentionSummary }}</p>
            </div>
          </div>
        </div>

        <div class="rounded-[28px] border border-console-edge bg-white/85 p-6 shadow-sm">
          <p class="text-[0.76rem] font-semibold uppercase tracking-[0.24em] text-console-warm">Activity window</p>
          <div class="mt-4 grid gap-4 sm:grid-cols-3">
            <div>
              <p class="text-[0.72rem] uppercase tracking-[0.16em] text-console-muted">Latest job</p>
              <p class="mt-2 text-sm font-medium text-slate-900">{{ latestJobSummary }}</p>
            </div>
            <div>
              <p class="text-[0.72rem] uppercase tracking-[0.16em] text-console-muted">Next run</p>
              <p class="mt-2 text-sm font-medium text-slate-900">{{ nextRunSummary }}</p>
            </div>
            <div>
              <p class="text-[0.72rem] uppercase tracking-[0.16em] text-console-muted">Enabled schedules</p>
              <p class="mt-2 text-sm font-medium text-slate-900">{{ enabledSchedulesLabel }}</p>
            </div>
          </div>
        </div>
      </section>

      <div class="mt-6 grid gap-4 xl:grid-cols-4">
        <CardStat label="Failed jobs" :value="jobSummary.failed" tone="tracked" helper="Execution failures requiring review." />
        <CardStat label="Running jobs" :value="jobSummary.running" tone="managed" helper="Jobs currently queued or in progress." />
        <CardStat label="Enabled schedules" :value="enabledSchedulesCount" tone="validated" helper="Recurring runs currently active." />
        <CardStat label="Inventories" :value="inventoryStats.inventories" tone="secured" helper="Managed target sets available for jobs." />
      </div>

      <div class="mt-6 grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <section class="rounded-3xl border border-console-edge bg-white/85 p-5 shadow-sm">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-xs uppercase tracking-[0.2em] text-console-muted">Operational state</p>
              <h3 class="mt-2 text-xl font-semibold text-slate-900">Readiness summary</h3>
            </div>
            <RouterLink class="text-sm font-medium text-console-glow transition hover:text-slate-900" to="/jobs">View jobs</RouterLink>
          </div>

          <div class="mt-5 grid gap-4 md:grid-cols-3">
            <div class="rounded-2xl border border-console-edge bg-console-surface/70 p-4">
              <p class="text-[0.74rem] uppercase tracking-[0.14em] text-console-muted">Readiness</p>
              <p class="mt-3 text-[0.97rem] text-slate-700">{{ readinessSummary }}</p>
            </div>
            <div class="rounded-2xl border border-console-edge bg-console-surface/70 p-4">
              <p class="text-[0.74rem] uppercase tracking-[0.14em] text-console-muted">Next schedule</p>
              <p class="mt-3 text-[0.97rem] text-slate-700">{{ nextScheduleSummary }}</p>
            </div>
            <div class="rounded-2xl border border-console-edge bg-console-surface/70 p-4">
              <p class="text-[0.74rem] uppercase tracking-[0.14em] text-console-muted">Coverage</p>
              <p class="mt-3 text-[0.97rem] text-slate-700">{{ coverageSummary }}</p>
            </div>
          </div>
        </section>

        <section class="rounded-3xl border border-console-edge bg-white/85 p-5 shadow-sm">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-xs uppercase tracking-[0.2em] text-console-muted">Quick actions</p>
              <h3 class="mt-2 text-xl font-semibold text-slate-900">Common tasks</h3>
            </div>
          </div>

          <div class="mt-5 space-y-3">
            <RouterLink
              v-for="action in quickActions"
              :key="action.to"
              :to="action.to"
              class="block rounded-2xl border border-console-edge bg-console-surface/60 px-4 py-4 transition hover:border-console-glow/30 hover:bg-white"
            >
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="font-medium text-slate-900">{{ action.title }}</p>
                  <p class="mt-1 text-[0.96rem] text-console-muted">{{ action.description }}</p>
                </div>
                <span class="text-[0.9rem] font-medium text-console-glow">Open</span>
              </div>
            </RouterLink>
          </div>
        </section>
      </div>

      <div class="mt-6 grid gap-6 xl:grid-cols-[1.25fr_0.95fr]">
        <DataTable
          title="Recent Jobs"
          description="Latest execution activity."
          :columns="jobColumns"
          :rows="recentJobs"
          empty-title="No jobs found"
          empty-description="Run a playbook to create job history."
          compact
        >
          <template #status="{ row }">
            <StatusBadge :value="row.status" />
          </template>
          <template #created_at="{ row }">
            <div>
              <p class="font-medium text-slate-900">{{ formatDateTime(row.created_at) }}</p>
              <p class="mt-1 text-xs text-slate-500">{{ row.check_mode ? 'Check mode' : 'Live execution' }}</p>
            </div>
          </template>
          <template #target_type="{ row }">
            <div>
              <p class="font-medium text-slate-900">{{ row.target_type }}</p>
              <p class="mt-1 text-xs text-slate-500">{{ row.target_value || 'All managed hosts' }}</p>
            </div>
          </template>
          <template #actions="{ row }">
            <RouterLink class="text-[0.96rem] font-medium text-sky-600 transition hover:text-slate-900" :to="`/jobs/${row.id}`">Details</RouterLink>
          </template>
        </DataTable>

        <DataTable
          title="Upcoming Schedules"
          description="Planned recurring automation."
          :columns="scheduleColumns"
          :rows="upcomingSchedules"
          empty-title="No active schedules"
          empty-description="Create a schedule after validating a manual run."
          compact
        >
          <template #enabled="{ row }">
            <StatusBadge :value="row.enabled ? 'enabled' : 'disabled'" />
          </template>
          <template #next_run_at="{ row }">
            <div>
              <p class="font-medium text-slate-900">{{ formatDateTime(row.next_run_at) }}</p>
              <p class="mt-1 text-xs text-slate-500">{{ row.cron_expression }}</p>
            </div>
          </template>
        </DataTable>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import api from '../../api/client'
import CardStat from '../../components/common/CardStat.vue'
import DataTable from '../../components/common/DataTable.vue'
import PageHeader from '../../components/common/PageHeader.vue'
import StatusBadge from '../../components/common/StatusBadge.vue'
import { useAppStore } from '../../stores/app'
import { formatDateTime } from '../../utils/format'

const app = useAppStore()
const isLoading = ref(true)
const jobs = ref<any[]>([])
const schedules = ref<any[]>([])
const inventoryStats = ref({ inventories: 0, hosts: 0, enabled_hosts: 0, groups: 0, variable_bearing: 0 })
const jobSummary = ref({ queued: 0, running: 0, success: 0, failed: 0, check_mode: 0 })
const supportStats = ref({ credentials: 0, playbooks: 0 })

const quickActions = [
  { title: 'Run job', description: 'Launch automation against a selected target set.', to: '/jobs' },
  { title: 'Manage inventory', description: 'Add, review, or update managed hosts.', to: '/inventory' },
  { title: 'Convert CLI', description: 'Turn pasted IOS configuration into reusable artifacts.', to: '/converter' },
]

const jobColumns = [
  { key: 'name', label: 'Job' },
  { key: 'status', label: 'Status' },
  { key: 'target_type', label: 'Target' },
  { key: 'created_at', label: 'Submitted' },
]

const scheduleColumns = [
  { key: 'name', label: 'Schedule' },
  { key: 'enabled', label: 'State' },
  { key: 'next_run_at', label: 'Next run' },
]

const recentJobs = computed(() => jobs.value.slice(0, 6))
const upcomingSchedules = computed(() => schedules.value.filter((row) => row.enabled).slice(0, 5))
const enabledSchedulesCount = computed(() => schedules.value.filter((row) => row.enabled).length)

const latestJob = computed(() => jobs.value[0] || null)
const nextSchedule = computed(() => upcomingSchedules.value[0] || null)
const enabledSchedulesLabel = computed(() => enabledSchedulesCount.value === 1 ? '1 active schedule' : `${enabledSchedulesCount.value} active schedules`)

const latestJobSummary = computed(() => {
  if (!latestJob.value) return 'No jobs recorded yet.'
  return `${latestJob.value.name} · ${latestJob.value.status}`
})

const nextRunSummary = computed(() => {
  if (!nextSchedule.value) return 'No enabled schedules.'
  return formatDateTime(nextSchedule.value.next_run_at)
})

const readinessSummary = computed(() => {
  if (!inventoryStats.value.inventories || !supportStats.value.credentials || !supportStats.value.playbooks) {
    return 'Inventory, credentials, or playbooks are still missing.'
  }
  return 'Core inputs are present for manual validation runs.'
})

const nextScheduleSummary = computed(() => {
  if (!nextSchedule.value) return 'No enabled schedules.'
  return `${nextSchedule.value.name} at ${formatDateTime(nextSchedule.value.next_run_at)}`
})

const attentionSummary = computed(() => {
  if (jobSummary.value.failed > 0) return `${jobSummary.value.failed} failed job(s) need review.`
  if (jobSummary.value.running > 0) return `${jobSummary.value.running} job(s) currently running.`
  if (jobSummary.value.queued > 0) return `${jobSummary.value.queued} job(s) waiting to execute.`
  return 'No immediate execution issues.'
})

const coverageSummary = computed(() => {
  return `${inventoryStats.value.enabled_hosts} enabled hosts across ${inventoryStats.value.groups} groups.`
})

const primaryState = computed(() => {
  if (jobSummary.value.failed > 0) {
    return {
      tone: 'critical',
      eyebrow: 'Needs attention',
      title: `${jobSummary.value.failed} failed job${jobSummary.value.failed === 1 ? '' : 's'}`,
      description: 'Review recent failures before running additional automation against the same target scope.',
    }
  }

  if (jobSummary.value.running > 0 || jobSummary.value.queued > 0) {
    return {
      tone: 'active',
      eyebrow: 'Automation in progress',
      title: `${jobSummary.value.running + jobSummary.value.queued} active job${jobSummary.value.running + jobSummary.value.queued === 1 ? '' : 's'}`,
      description: 'Automation is currently running or waiting for worker capacity. Keep overlapping changes deliberate.',
    }
  }

  return {
    tone: 'healthy',
    eyebrow: 'Stable state',
    title: 'No active execution issues',
    description: 'No running or failed jobs are currently competing for operator attention.',
  }
})

async function load() {
  isLoading.value = true
  try {
    const [inventoryResp, credentials, playbooks, jobsResp, scheduleResp] = await Promise.all([
      api.get('/inventories/summary/query', { params: { limit: 1, offset: 0 } }),
      api.get('/credentials'),
      api.get('/playbooks'),
      api.get('/jobs/query', { params: { limit: 6, offset: 0, sort_by: 'created_at', sort_order: 'desc' } }),
      api.get('/schedules'),
    ])

    inventoryStats.value = inventoryResp.data.data.stats
    supportStats.value.credentials = credentials.data.data.length
    supportStats.value.playbooks = playbooks.data.data.length
    jobs.value = jobsResp.data.data.items
    jobSummary.value = jobsResp.data.data.summary
    schedules.value = scheduleResp.data.data
  } catch {
    app.pushToast('Dashboard data could not be loaded', 'error', 'Check API reachability and reload the page.')
  } finally {
    isLoading.value = false
  }
}

onMounted(load)
</script>
