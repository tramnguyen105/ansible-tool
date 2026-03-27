<template>
  <div>
    <div v-if="isLoading" class="rounded-3xl border border-console-edge bg-console-panel/80 p-6 shadow-xl shadow-slate-950/20">
      <div class="h-4 w-40 rounded-full bg-console-edge/80" />
      <div class="mt-5 grid gap-4 xl:grid-cols-4">
        <div class="h-24 rounded-2xl bg-console-deep/80" />
        <div class="h-24 rounded-2xl bg-console-deep/70" />
        <div class="h-24 rounded-2xl bg-console-deep/60" />
        <div class="h-24 rounded-2xl bg-console-deep/50" />
      </div>
      <p class="mt-5 text-sm text-console-muted">Loading job metadata, result summary, and captured runner output.</p>
    </div>

    <div v-else-if="job">
      <PageHeader
        :title="job.name"
        eyebrow="Job Detail"
        description="Inspect execution status, timing, target scope, and captured ansible-runner output before deciding whether the job is safe to repeat."
      />

      <div class="grid gap-4 xl:grid-cols-4">
        <CardStat label="Status" :value="job.status" tone="execution" :helper="job.finished_at ? `Finished ${formatDateTime(job.finished_at)}` : 'Execution is still in progress or waiting to run.'" />
        <CardStat label="Mode" :value="job.check_mode ? 'Check' : 'Live'" tone="guardrail" :helper="job.check_mode ? 'Validation-only execution.' : 'Live production-impacting run.'" />
        <CardStat label="Return Code" :value="job.result?.return_code ?? 'n/a'" tone="result" :helper="job.result?.return_code === 0 ? 'Runner reported a successful exit code.' : 'Non-zero codes should be reviewed carefully.'" />
        <CardStat label="Target" :value="targetLabel" tone="scope" :helper="job.target_value || 'All managed hosts in the selected inventory.'" />
      </div>

      <div class="mt-6 grid gap-6 xl:grid-cols-[0.75fr_1.25fr]">
        <section class="space-y-4 rounded-3xl border border-console-edge bg-console-panel/80 p-5 shadow-xl shadow-slate-950/20">
          <div>
            <p class="text-xs uppercase tracking-[0.22em] text-console-glow">Execution metadata</p>
            <h3 class="mt-2 text-xl font-semibold text-white">Run context</h3>
          </div>

          <div class="space-y-3 rounded-2xl border border-console-edge/70 bg-console-deep/60 p-4 text-sm">
            <div class="flex items-start justify-between gap-4">
              <span class="text-console-muted">Created</span>
              <span class="text-right text-white">{{ formatDateTime(job.created_at) }}</span>
            </div>
            <div class="flex items-start justify-between gap-4">
              <span class="text-console-muted">Started</span>
              <span class="text-right text-white">{{ formatDateTime(job.started_at) }}</span>
            </div>
            <div class="flex items-start justify-between gap-4">
              <span class="text-console-muted">Finished</span>
              <span class="text-right text-white">{{ formatDateTime(job.finished_at) }}</span>
            </div>
            <div class="flex items-start justify-between gap-4">
              <span class="text-console-muted">Target type</span>
              <span class="text-right text-white">{{ job.target_type }}</span>
            </div>
            <div class="flex items-start justify-between gap-4">
              <span class="text-console-muted">Target value</span>
              <span class="text-right text-white">{{ job.target_value || 'All managed hosts' }}</span>
            </div>
            <div class="flex items-start justify-between gap-4">
              <span class="text-console-muted">Celery task</span>
              <span class="max-w-[220px] break-all text-right text-white">{{ job.celery_task_id || 'Not queued' }}</span>
            </div>
          </div>

          <div class="rounded-2xl border border-console-edge/70 bg-console-deep/60 p-4 text-sm">
            <p class="text-xs uppercase tracking-[0.18em] text-console-muted">Result summary</p>
            <pre class="mt-3 max-h-[220px] overflow-auto whitespace-pre-wrap break-words rounded-xl bg-slate-950/40 p-3 text-xs text-console-ink">{{ summaryText }}</pre>
          </div>
        </section>

        <div class="space-y-6">
          <section class="rounded-3xl border border-console-edge bg-console-panel/80 p-5 shadow-xl shadow-slate-950/20">
            <div class="flex items-center justify-between gap-3">
              <h3 class="text-lg font-semibold text-white">Execution Output</h3>
              <StatusBadge :value="job.status" />
            </div>
            <pre class="mt-4 max-h-[420px] overflow-auto rounded-2xl bg-console-deep/80 p-4 text-xs text-console-ink">{{ job.result?.stdout || 'No stdout captured yet.' }}</pre>
          </section>

          <section class="rounded-3xl border border-console-edge bg-console-panel/80 p-5 shadow-xl shadow-slate-950/20">
            <h3 class="text-lg font-semibold text-white">Error Output</h3>
            <pre class="mt-4 max-h-[260px] overflow-auto rounded-2xl bg-slate-950/70 p-4 text-xs text-rose-100">{{ job.result?.stderr || 'No stderr captured.' }}</pre>
          </section>
        </div>
      </div>
    </div>

    <div v-else class="rounded-3xl border border-console-edge bg-console-panel/80 p-6 shadow-xl shadow-slate-950/20">
      <PageHeader title="Job Detail" eyebrow="Execution Review" description="The requested job could not be loaded." />
      <p class="mt-4 text-sm text-console-muted">Verify the job still exists and that the current session has permission to review it.</p>
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
