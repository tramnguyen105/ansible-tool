<template>
  <div>
    <div v-if="isLoading" class="rounded-2xl border border-slate-800 bg-slate-900 p-6">
      <div class="h-4 w-40 rounded-full bg-slate-800" />
      <div class="mt-5 grid gap-4 xl:grid-cols-4">
        <div class="h-24 rounded-2xl bg-slate-800/80" />
        <div class="h-24 rounded-2xl bg-slate-800/70" />
        <div class="h-24 rounded-2xl bg-slate-800/60" />
        <div class="h-24 rounded-2xl bg-slate-800/50" />
      </div>
      <p class="mt-5 text-sm text-slate-400">Loading job metadata and runner output…</p>
    </div>

    <div v-else-if="job">
      <PageHeader
        :title="job.name"
        eyebrow="Job detail"
        description="Review status, timing, scope, and captured output before deciding whether to repeat the run."
      >
        <RouterLink class="btn-secondary" to="/jobs">Back to jobs</RouterLink>
      </PageHeader>

      <div class="mt-6 grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
        <section
          class="rounded-2xl border p-5"
          :class="statusTone === 'critical'
            ? 'border-rose-500/30 bg-rose-500/10'
            : statusTone === 'active'
              ? 'border-amber-500/30 bg-amber-500/10'
              : 'border-emerald-500/30 bg-emerald-500/10'"
        >
          <p class="text-[0.8rem] font-medium uppercase tracking-[0.12em]" :class="statusTone === 'critical' ? 'text-rose-200' : statusTone === 'active' ? 'text-amber-200' : 'text-emerald-200'">
            {{ statusEyebrow }}
          </p>
          <div class="mt-2 flex items-center gap-3">
            <h3 class="text-[1.8rem] font-semibold text-white">{{ statusTitle }}</h3>
            <StatusBadge :value="job.status" />
          </div>
          <p class="mt-2 text-[0.98rem] leading-7 text-slate-200/90">{{ statusDescription }}</p>
        </section>

        <section class="rounded-2xl border border-slate-800 bg-slate-900 p-5">
          <p class="text-[0.8rem] font-medium uppercase tracking-[0.12em] text-slate-500">Execution window</p>
          <div class="mt-4 grid gap-4 sm:grid-cols-3">
            <div>
              <p class="text-[0.78rem] uppercase tracking-[0.1em] text-slate-500">Submitted</p>
              <p class="mt-2 text-[0.98rem] font-medium text-white">{{ formatDateTime(job.created_at) }}</p>
            </div>
            <div>
              <p class="text-[0.78rem] uppercase tracking-[0.1em] text-slate-500">Started</p>
              <p class="mt-2 text-[0.98rem] font-medium text-white">{{ formatDateTime(job.started_at) }}</p>
            </div>
            <div>
              <p class="text-[0.78rem] uppercase tracking-[0.1em] text-slate-500">Finished</p>
              <p class="mt-2 text-[0.98rem] font-medium text-white">{{ formatDateTime(job.finished_at) }}</p>
            </div>
          </div>
        </section>
      </div>

      <div class="mt-6 grid gap-4 xl:grid-cols-4">
        <CardStat label="Status" :value="job.status" tone="tracked" :helper="job.finished_at ? `Finished ${formatDateTime(job.finished_at)}` : 'Execution is still in progress or waiting to run.'" />
        <CardStat label="Mode" :value="job.check_mode ? 'Check' : 'Live'" tone="managed" :helper="job.check_mode ? 'Validation-only execution.' : 'Live execution against managed targets.'" />
        <CardStat label="Return code" :value="job.result?.return_code ?? 'n/a'" tone="validated" :helper="job.result?.return_code === 0 ? 'Runner reported a successful exit code.' : 'Review non-zero return codes before repeating the run.'" />
        <CardStat label="Target" :value="targetLabel" tone="secured" :helper="job.target_value || 'All managed hosts in the selected inventory.'" />
      </div>

      <div class="mt-6 grid gap-6 xl:grid-cols-[0.72fr_1.28fr]">
        <section class="space-y-4 rounded-2xl border border-slate-800 bg-slate-900 p-5">
          <div>
            <p class="text-[0.8rem] font-medium uppercase tracking-[0.12em] text-slate-500">Run context</p>
            <h3 class="mt-2 text-[1.15rem] font-semibold text-white">Execution metadata</h3>
          </div>

          <div class="space-y-3 rounded-2xl border border-slate-800 bg-slate-950/70 p-4 text-[0.97rem]">
            <div class="flex items-start justify-between gap-4">
              <span class="text-slate-400">Target type</span>
              <span class="text-right text-white">{{ job.target_type }}</span>
            </div>
            <div class="flex items-start justify-between gap-4">
              <span class="text-slate-400">Target value</span>
              <span class="text-right text-white">{{ job.target_value || 'All managed hosts' }}</span>
            </div>
            <div class="flex items-start justify-between gap-4">
              <span class="text-slate-400">Celery task</span>
              <span class="max-w-[220px] break-all text-right text-white">{{ job.celery_task_id || 'Not queued' }}</span>
            </div>
          </div>

          <div class="rounded-2xl border border-slate-800 bg-slate-950/70 p-4 text-[0.97rem]">
            <p class="text-[0.78rem] uppercase tracking-[0.1em] text-slate-500">Result summary</p>
            <pre class="mt-3 max-h-[220px] overflow-auto whitespace-pre-wrap break-words rounded-xl bg-slate-950 p-3 text-xs text-slate-300">{{ summaryText }}</pre>
          </div>
        </section>

        <div class="space-y-6">
          <section class="rounded-2xl border border-slate-800 bg-slate-900 p-5">
            <div class="flex items-center justify-between gap-3">
              <h3 class="text-[1.15rem] font-semibold text-white">Execution output</h3>
              <StatusBadge :value="job.status" />
            </div>
            <pre class="mt-4 max-h-[420px] overflow-auto rounded-2xl bg-slate-950 p-4 text-xs text-slate-200">{{ job.result?.stdout || 'No stdout captured yet.' }}</pre>
          </section>

          <section class="rounded-2xl border border-slate-800 bg-slate-900 p-5">
            <h3 class="text-[1.15rem] font-semibold text-white">Error output</h3>
            <pre class="mt-4 max-h-[260px] overflow-auto rounded-2xl bg-slate-950 p-4 text-xs text-rose-100">{{ job.result?.stderr || 'No stderr captured.' }}</pre>
          </section>
        </div>
      </div>
    </div>

    <div v-else class="rounded-2xl border border-slate-800 bg-slate-900 p-6">
      <PageHeader title="Job detail" eyebrow="Execution review" description="The requested job could not be loaded." />
      <p class="mt-4 text-[0.97rem] text-slate-400">Verify the job still exists and that the current session has permission to review it.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import api from '../../api/client'
import CardStat from '../../components/common/CardStat.vue'
import PageHeader from '../../components/common/PageHeader.vue'
import StatusBadge from '../../components/common/StatusBadge.vue'
import { useAppStore } from '../../stores/app'
import { formatDateTime } from '../../utils/format'

const route = useRoute()
const app = useAppStore()
const job = ref<any>(null)
const isLoading = ref(true)

const targetLabel = computed(() => {
  if (!job.value) return 'n/a'
  return job.value.target_type === 'all' ? 'All hosts' : job.value.target_type
})

const summaryText = computed(() => {
  const summary = job.value?.result?.summary_json
  if (!summary || Object.keys(summary).length === 0) {
    return 'No structured result summary was captured.'
  }
  return JSON.stringify(summary, null, 2)
})

const statusTone = computed(() => {
  if (!job.value) return 'neutral'
  if (['failed', 'error', 'cancelled'].includes(job.value.status)) return 'critical'
  if (['running', 'queued', 'pending'].includes(job.value.status)) return 'active'
  return 'healthy'
})

const statusEyebrow = computed(() => {
  if (statusTone.value === 'critical') return 'Needs review'
  if (statusTone.value === 'active') return 'Execution in progress'
  return 'Completed state'
})

const statusTitle = computed(() => {
  if (!job.value) return 'Job status'
  return `${job.value.status.charAt(0).toUpperCase()}${job.value.status.slice(1)} execution`
})

const statusDescription = computed(() => {
  if (!job.value) return ''
  if (statusTone.value === 'critical') {
    return 'This job did not complete cleanly. Review stderr, summary output, and target scope before running it again.'
  }
  if (statusTone.value === 'active') {
    return 'This job is still queued or running. Avoid overlapping changes against the same systems until it finishes.'
  }
  return 'This job completed without an active failure state. Review captured output before repeating it if the target scope is sensitive.'
})

onMounted(async () => {
  isLoading.value = true
  try {
    const response = await api.get(`/jobs/${route.params.id}`)
    job.value = response.data.data
  } catch {
    app.pushToast('Job detail could not be loaded', 'error', 'Check the job identifier and refresh the page.')
  } finally {
    isLoading.value = false
  }
})
</script>
