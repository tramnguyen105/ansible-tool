<template>
  <div>
    <PageHeader title="Dashboard" eyebrow="Operations Summary" description="Track core automation objects and recent activity from a single workspace." />
    <div class="grid gap-4 lg:grid-cols-4">
      <CardStat label="Inventories" :value="stats.inventories" tone="managed" />
      <CardStat label="Credentials" :value="stats.credentials" tone="secured" />
      <CardStat label="Playbooks" :value="stats.playbooks" tone="validated" />
      <CardStat label="Jobs" :value="stats.jobs" tone="tracked" />
    </div>
    <div class="mt-6 grid gap-6 xl:grid-cols-[1.4fr_1fr]">
      <div class="rounded-3xl border border-console-edge bg-console-panel/70 p-5">
        <h3 class="text-lg font-semibold">Recent Jobs</h3>
        <div class="mt-4 space-y-3 text-sm">
          <RouterLink v-for="job in recentJobs" :key="job.id" :to="`/jobs/${job.id}`" class="flex items-center justify-between rounded-2xl border border-console-edge/80 bg-console-deep/70 px-4 py-3 hover:bg-console-surface/80">
            <span>{{ job.name }}</span>
            <StatusBadge :value="job.status" />
          </RouterLink>
        </div>
      </div>
      <div class="rounded-3xl border border-console-edge bg-console-panel/70 p-5">
        <h3 class="text-lg font-semibold">Scheduled Runs</h3>
        <div class="mt-4 space-y-3 text-sm">
          <div v-for="schedule in schedules" :key="schedule.id" class="rounded-2xl border border-console-edge/80 bg-console-deep/70 px-4 py-3">
            <div class="flex items-center justify-between">
              <span>{{ schedule.name }}</span>
              <StatusBadge :value="schedule.enabled ? 'enabled' : 'disabled'" />
            </div>
            <p class="mt-2 text-console-muted">Next run: {{ schedule.next_run_at || 'n/a' }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'

import api from '../../api/client'
import CardStat from '../../components/common/CardStat.vue'
import PageHeader from '../../components/common/PageHeader.vue'
import StatusBadge from '../../components/common/StatusBadge.vue'

const stats = reactive({ inventories: 0, credentials: 0, playbooks: 0, jobs: 0 })
const recentJobs = ref<any[]>([])
const schedules = ref<any[]>([])

onMounted(async () => {
  const [inventories, credentials, playbooks, jobs, scheduleResp] = await Promise.all([
    api.get('/inventories'),
    api.get('/credentials'),
    api.get('/playbooks'),
    api.get('/jobs'),
    api.get('/schedules'),
  ])
  stats.inventories = inventories.data.data.length
  stats.credentials = credentials.data.data.length
  stats.playbooks = playbooks.data.data.length
  stats.jobs = jobs.data.data.length
  recentJobs.value = jobs.data.data.slice(0, 5)
  schedules.value = scheduleResp.data.data.slice(0, 5)
})
</script>
