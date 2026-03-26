<template>
  <div v-if="job">
    <PageHeader :title="job.name" eyebrow="Job Detail" description="Inspect execution status, result summary, and stdout captured from ansible-runner." />
    <div class="grid gap-6 xl:grid-cols-[0.8fr_1.2fr]">
      <div class="space-y-4 rounded-3xl border border-console-edge bg-console-panel/70 p-5">
        <div class="flex items-center justify-between">
          <span class="text-console-muted">Status</span>
          <StatusBadge :value="job.status" />
        </div>
        <div class="flex items-center justify-between">
          <span class="text-console-muted">Target</span>
          <span>{{ job.target_type }} {{ job.target_value || '' }}</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-console-muted">Check Mode</span>
          <span>{{ job.check_mode ? 'Yes' : 'No' }}</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-console-muted">Return Code</span>
          <span>{{ job.result?.return_code ?? 'n/a' }}</span>
        </div>
      </div>
      <div class="rounded-3xl border border-console-edge bg-console-panel/70 p-5">
        <h3 class="text-lg font-semibold">Execution Output</h3>
        <pre class="mt-4 max-h-[620px] overflow-auto rounded-2xl bg-console-deep/80 p-4 text-xs text-console-ink">{{ job.result?.stdout || 'No stdout captured yet.' }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import api from '../../api/client'
import PageHeader from '../../components/common/PageHeader.vue'
import StatusBadge from '../../components/common/StatusBadge.vue'

const route = useRoute()
const job = ref<any>(null)

onMounted(async () => {
  const response = await api.get(`/jobs/${route.params.id}`)
  job.value = response.data.data
})
</script>
