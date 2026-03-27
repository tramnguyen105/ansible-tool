<template>
  <div>
    <PageHeader
      title="Dashboard"
      eyebrow="Operations Summary"
      description="Monitor automation readiness, recent execution activity, and the next scheduled changes from one workspace."
    >
      <RouterLink class="btn-secondary" to="/inventory">Review Inventory</RouterLink>
      <RouterLink class="btn-primary" to="/jobs">Run Automation</RouterLink>
    </PageHeader>

    <div class="grid gap-4 xl:grid-cols-4">
      <CardStat label="Inventories" :value="stats.inventories" tone="managed" :helper="inventoryHelper" />
      <CardStat label="Credentials" :value="stats.credentials" tone="secured" :helper="credentialHelper" />
      <CardStat label="Playbooks" :value="stats.playbooks" tone="validated" :helper="playbookHelper" />
      <CardStat label="Jobs" :value="stats.jobs" tone="tracked" :helper="jobHelper" />
    </div>

    <div v-if="isLoading" class="mt-6 rounded-3xl border border-console-edge bg-console-panel/80 p-6 shadow-xl shadow-slate-950/20">
      <div class="h-4 w-36 rounded-full bg-console-edge/80" />
      <div class="mt-5 grid gap-4 lg:grid-cols-3">
        <div class="h-28 rounded-2xl bg-console-deep/80" />
        <div class="h-28 rounded-2xl bg-console-deep/70" />
        <div class="h-28 rounded-2xl bg-console-deep/60" />
      </div>
      <p class="mt-5 text-sm text-console-muted">Collecting inventory, credential, playbook, job, and schedule posture for the operator dashboard.</p>
    </div>

    <template v-else>
      <div class="mt-6 grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <section class="rounded-3xl border border-console-edge bg-console-panel/80 p-5 shadow-xl shadow-slate-950/20">
          <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <p class="text-xs uppercase tracking-[0.22em] text-console-glow">Automation Health</p>
              <h3 class="mt-2 text-xl font-semibold text-white">Current operator posture</h3>
              <p class="mt-2 max-w-2xl text-sm leading-6 text-console-muted">
                Keep risky changes visible. Use check mode for uncertain playbooks, review failed jobs quickly, and confirm the next scheduled tasks are expected.
              </p>
            </div>
            <div class="grid min-w-[240px] gap-3 sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
              <div class="rounded-2xl border border-console-edge/80 bg-console-deep/70 px-4 py-3">
                <p class="text-xs uppercase tracking-[0.18em] text-console-muted">Succeeded</p>
                <p class="mt-2 text-2xl font-semibold text-white">{{ statusCounts.success }}</p>
              </div>
              <div class="rounded-2xl border border-console-edge/80 bg-console-deep/70 px-4 py-3">
                <p class="text-xs uppercase tracking-[0.18em] text-console-muted">Running</p>
                <p class="mt-2 text-2xl font-semibold text-white">{{ statusCounts.running }}</p>
              </div>
              <div class="rounded-2xl border border-console-edge/80 bg-console-deep/70 px-4 py-3">
                <p class="text-xs uppercase tracking-[0.18em] text-console-muted">Failed</p>
                <p class="mt-2 text-2xl font-semibold text-white">{{ statusCounts.failed }}</p>
              </div>
            </div>
          </div>

          <div class="mt-5 grid gap-4 lg:grid-cols-3">
            <div class="rounded-2xl border border-console-edge/70 bg-console-deep/60 p-4">
              <p class="text-xs uppercase tracking-[0.18em] text-console-muted">Manual readiness</p>
              <p class="mt-3 text-sm text-console-ink/90">{{ manualReadiness }}</p>
            </div>
            <div class="rounded-2xl border border-console-edge/70 bg-console-deep/60 p-4">
              <p class="text-xs uppercase tracking-[0.18em] text-console-muted">Schedule pressure</p>
              <p class="mt-3 text-sm text-console-ink/90">{{ schedulePressure }}</p>
            </div>
            <div class="rounded-2xl border border-console-edge/70 bg-console-deep/60 p-4">
              <p class="text-xs uppercase tracking-[0.18em] text-console-muted">Operational note</p>
              <p class="mt-3 text-sm text-console-ink/90">{{ operatorNote }}</p>
            </div>
          </div>
        </section>

        <section class="rounded-3xl border border-console-edge bg-console-panel/80 p-5 shadow-xl shadow-slate-950/20">
          <p class="text-xs uppercase tracking-[0.22em] text-console-glow">Quick Actions</p>
          <h3 class="mt-2 text-xl font-semibold text-white">Common operator tasks</h3>
          <div class="mt-5 space-y-3">
            <RouterLink
              v-for="action in quickActions"
              :key="action.to"
              :to="action.to"
              class="block rounded-2xl border border-console-edge/80 bg-console-deep/70 px-4 py-4 transition hover:border-cyan-400/30 hover:bg-console-surface/80"
            >
              <div class="flex items-center justify-between gap-3">
                <div>
                  <p class="font-medium text-white">{{ action.title }}</p>
                  <p class="mt-1 text-sm text-console-muted">{{ action.description }}</p>
                </div>
                <span class="text-console-glow">Open</span>
              </div>
            </RouterLink>
          </div>
        </section>
      </div>

      <div class="mt-6 grid gap-6 xl:grid-cols-[1.25fr_0.95fr]">
        <DataTable
          title="Recent Jobs"
          description="Watch the most recent executions first, especially failed and running tasks."
          :columns="jobColumns"
          :rows="recentJobs"
          empty-title="No jobs have been launched"
          empty-description="Use the run flow to launch a playbook manually, or create schedules for repeatable operations."
          compact
        >
          <template #status="{ row }">
            <StatusBadge :value="row.status" />
          </template>
          <template #created_at="{ row }">
            <div>
              <p class="text-white">{{ formatDateTime(row.created_at) }}</p>
              <p class="mt-1 text-xs text-console-muted">{{ row.check_mode ? 'Check mode' : 'Live execution' }}</p>
            </div>
          </template>
          <template #target_type="{ row }">
            <div>
              <p class="text-white">{{ row.target_type }}</p>
              <p class="mt-1 text-xs text-console-muted">{{ row.target_value || 'All managed hosts' }}</p>
            </div>
          </template>
          <template #actions="{ row }">
            <RouterLink class="text-console-glow transition hover:text-white" :to="`/jobs/${row.id}`">View details</RouterLink>
          </template>
        </DataTable>

        <DataTable
          title="Scheduled Runs"
          description="Confirm the next planned executions and disable anything that should not run unattended."
          :columns="scheduleColumns"
          :rows="upcomingSchedules"
          empty-title="No active schedules"
          empty-description="Create a scheduled run once the inventory, credential, and playbook flow has been validated manually."
          compact
        >
          <template #enabled="{ row }">
            <StatusBadge :value="row.enabled ? 'enabled' : 'disabled'" />
          </template>
          <template #next_run_at="{ row }">
            <div>
              <p class="text-white">{{ formatDateTime(row.next_run_at) }}</p>
              <p class="mt-1 text-xs text-console-muted">{{ row.cron_expression }}</p>
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
import { formatDateTime, pluralize } from '../../utils/format'

const app = useAppStore()
const isLoading = ref(true)
const stats = reactive({ inventories: 0, credentials: 0, playbooks: 0, jobs: 0 })
const jobs = ref<any[]>([])
const schedules = ref<any[]>([])

const quickActions = [
  { title: 'Import inventory', description: 'Normalize host data from CSV, Excel, YAML, or INI files.', to: '/inventory' },
  { title: 'Run a playbook', description: 'Launch a job with explicit inventory, credentials, and guardrails.', to: '/jobs' },
  { title: 'Convert Cisco CLI', description: 'Turn pasted IOS configuration into reusable Ansible artifacts.', to: '/converter' },
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
const upcomingSchedules = computed(() => schedules.value.slice(0, 5))

const statusCounts = computed(() => ({
  success: jobs.value.filter((job) => ['success', 'completed'].includes(job.status)).length,
  running: jobs.value.filter((job) => ['running', 'queued', 'pending'].includes(job.status)).length,
  failed: jobs.value.filter((job) => ['failed', 'error'].includes(job.status)).length,
}))

const inventoryHelper = computed(() =>
  stats.inventories ? `${pluralize(stats.inventories, 'inventory')} available for execution.` : 'Create or import an inventory to target devices.',
)
const credentialHelper = computed(() =>
  stats.credentials ? `${pluralize(stats.credentials, 'credential')} encrypted and ready for use.` : 'Store at least one credential before running jobs.',
)
const playbookHelper = computed(() =>
  stats.playbooks ? `${pluralize(stats.playbooks, 'playbook')} available for operator review.` : 'Author or generate a playbook to automate changes.',
)
const jobHelper = computed(() =>
  stats.jobs ? `${statusCounts.value.failed} failed, ${statusCounts.value.running} in progress.` : 'No execution history recorded yet.',
)

const manualReadiness = computed(() => {
  if (!stats.inventories || !stats.credentials || !stats.playbooks) {
    return 'The workspace is not ready for a safe run. Finish inventory, credential, and playbook setup first.'
  }
  return 'Core inputs are present. Prefer a manual check-mode run before enabling repeated execution.'
})

const schedulePressure = computed(() => {
  if (!schedules.value.length) {
    return 'No scheduled automation is active. Manual runs are the current control point.'
  }
  const enabledCount = schedules.value.filter((item) => item.enabled).length
  return `${pluralize(enabledCount, 'enabled schedule')} will continue to run unless operators disable them.`
})

const operatorNote = computed(() => {
  if (statusCounts.value.failed > 0) {
    return 'Recent failures exist. Review job output before pushing additional changes to production devices.'
  }
  if (statusCounts.value.running > 0) {
    return 'Active automation is in progress. Avoid overlapping changes against the same target scope.'
  }
  return 'The console is quiet. Use the next manual run to validate current playbooks against live inventory.'
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
