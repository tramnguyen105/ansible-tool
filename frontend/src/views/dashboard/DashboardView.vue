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

    <div class="mt-6 grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
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
            <p class="text-[0.78rem] uppercase tracking-[0.1em] text-slate-500">Next run</p>
            <p class="mt-2 text-[0.98rem] font-medium text-white">{{ nextRunSummary }}</p>
          </div>
          <div>
            <p class="text-[0.78rem] uppercase tracking-[0.1em] text-slate-500">Enabled schedules</p>
            <p class="mt-2 text-[0.98rem] font-medium text-white">{{ enabledSchedulesLabel }}</p>
          </div>
        </div>
      </section>
    </div>

    <div class="mt-6 grid gap-4 xl:grid-cols-4">
      <CardStat label="Failed jobs" :value="statusCounts.failed" tone="tracked" helper="Execution failures requiring review." />
      <CardStat label="Running jobs" :value="statusCounts.running" tone="managed" helper="Jobs currently queued or in progress." />
      <CardStat label="Enabled schedules" :value="enabledSchedulesCount" tone="validated" helper="Recurring runs currently active." />
      <CardStat label="Inventories" :value="stats.inventories" tone="secured" helper="Managed target sets available for jobs." />
    </div>

    <div v-if="isLoading" class="mt-6 rounded-2xl border border-slate-800 bg-slate-900 p-6">
      <div class="h-4 w-36 rounded-full bg-slate-800" />
      <div class="mt-5 grid gap-4 lg:grid-cols-3">
        <div class="h-24 rounded-2xl bg-slate-800/80" />
        <div class="h-24 rounded-2xl bg-slate-800/70" />
        <div class="h-24 rounded-2xl bg-slate-800/60" />
      </div>
      <p class="mt-5 text-[0.96rem] text-slate-400">Loading dashboard data…</p>
    </div>

    <template v-else>
      <div class="mt-6 grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <section class="rounded-2xl border border-slate-800 bg-slate-900 p-5">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-xs uppercase tracking-[0.16em] text-slate-500">Operational state</p>
              <h3 class="mt-2 text-xl font-semibold text-white">Readiness summary</h3>
            </div>
            <RouterLink class="text-sm text-console-glow transition hover:text-white" to="/jobs">View jobs</RouterLink>
          </div>

          <div class="mt-5 grid gap-4 md:grid-cols-3">
            <div class="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
              <p class="text-[0.78rem] uppercase tracking-[0.1em] text-slate-500">Readiness</p>
              <p class="mt-3 text-[0.97rem] text-slate-300">{{ readinessSummary }}</p>
            </div>
            <div class="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
              <p class="text-[0.78rem] uppercase tracking-[0.1em] text-slate-500">Next schedule</p>
              <p class="mt-3 text-[0.97rem] text-slate-300">{{ nextScheduleSummary }}</p>
            </div>
            <div class="rounded-2xl border border-slate-800 bg-slate-950/70 p-4">
              <p class="text-[0.78rem] uppercase tracking-[0.1em] text-slate-500">Attention</p>
              <p class="mt-3 text-[0.97rem] text-slate-300">{{ attentionSummary }}</p>
            </div>
          </div>
        </section>

        <section class="rounded-2xl border border-slate-800 bg-slate-900 p-5">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-xs uppercase tracking-[0.16em] text-slate-500">Quick actions</p>
              <h3 class="mt-2 text-xl font-semibold text-white">Common tasks</h3>
            </div>
          </div>

          <div class="mt-5 space-y-3">
            <RouterLink
              v-for="action in quickActions"
              :key="action.to"
              :to="action.to"
              class="block rounded-2xl border border-slate-800 bg-slate-950/70 px-4 py-4 transition hover:border-slate-700 hover:bg-slate-950"
            >
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="font-medium text-white">{{ action.title }}</p>
                  <p class="mt-1 text-[0.96rem] text-slate-400">{{ action.description }}</p>
                </div>
                <span class="text-[0.95rem] text-slate-500">Open</span>
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
              <p class="font-medium text-white">{{ formatDateTime(row.created_at) }}</p>
              <p class="mt-1 text-xs text-slate-500">{{ row.check_mode ? 'Check mode' : 'Live execution' }}</p>
            </div>
          </template>
          <template #target_type="{ row }">
            <div>
              <p class="font-medium text-white">{{ row.target_type }}</p>
              <p class="mt-1 text-xs text-slate-500">{{ row.target_value || 'All managed hosts' }}</p>
            </div>
          </template>
          <template #actions="{ row }">
            <RouterLink class="text-[0.96rem] font-medium text-sky-300 transition hover:text-white" :to="`/jobs/${row.id}`">Details</RouterLink>
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
              <p class="font-medium text-white">{{ formatDateTime(row.next_run_at) }}</p>
              <p class="mt-1 text-xs text-slate-500">{{ row.cron_expression }}</p>
            </div>
          </template>
        </DataTable>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import api from '../../api/client'
import CardStat from '../../components/common/CardStat.vue'
import DataTable from '../../components/common/DataTable.vue'
import PageHeader from '../../components/common/PageHeader.vue'
import StatusBadge from '../../components/common/StatusBadge.vue'
import { useAppStore } from '../../stores/app'
import { formatDateTime } from '../../utils/format'

const app = useAppStore()
const isLoading = ref(true)
const stats = reactive({ inventories: 0, credentials: 0, playbooks: 0, jobs: 0 })
const jobs = ref<any[]>([])
const schedules = ref<any[]>([])

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

const statusCounts = computed(() => ({
  success: jobs.value.filter((job) => ['success', 'completed'].includes(job.status)).length,
  running: jobs.value.filter((job) => ['running', 'queued', 'pending'].includes(job.status)).length,
  failed: jobs.value.filter((job) => ['failed', 'error'].includes(job.status)).length,
}))

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
  if (!stats.inventories || !stats.credentials || !stats.playbooks) {
    return 'Inventory, credentials, or playbooks are still missing.'
  }
  return 'Core inputs are present for manual validation runs.'
})

const nextScheduleSummary = computed(() => {
  if (!nextSchedule.value) return 'No enabled schedules.'
  return `${nextSchedule.value.name} at ${formatDateTime(nextSchedule.value.next_run_at)}`
})

const attentionSummary = computed(() => {
  if (statusCounts.value.failed > 0) return `${statusCounts.value.failed} failed job(s) need review.`
  if (statusCounts.value.running > 0) return `${statusCounts.value.running} job(s) currently running.`
  return 'No immediate execution issues.'
})

const primaryState = computed(() => {
  if (statusCounts.value.failed > 0) {
    return {
      tone: 'critical',
      eyebrow: 'Needs attention',
      title: `${statusCounts.value.failed} failed job${statusCounts.value.failed === 1 ? '' : 's'}`,
      description: 'Review recent failures before running additional automation against the same target scope.',
    }
  }

  if (statusCounts.value.running > 0) {
    return {
      tone: 'active',
      eyebrow: 'Automation in progress',
      title: `${statusCounts.value.running} active job${statusCounts.value.running === 1 ? '' : 's'}`,
      description: 'Automation is currently running. Avoid overlapping changes until these executions complete.',
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
    const [inventories, credentials, playbooks, jobsResp, scheduleResp] = await Promise.all([
      api.get('/inventories'),
      api.get('/credentials'),
      api.get('/playbooks'),
      api.get('/jobs'),
      api.get('/schedules'),
    ])

    stats.inventories = inventories.data.data.length
    stats.credentials = credentials.data.data.length
    stats.playbooks = playbooks.data.data.length
    stats.jobs = jobsResp.data.data.length
    jobs.value = jobsResp.data.data
    schedules.value = scheduleResp.data.data
  } catch {
    app.pushToast('Dashboard data could not be loaded', 'error', 'Check API reachability and reload the page.')
  } finally {
    isLoading.value = false
  }
}

onMounted(load)
</script>
