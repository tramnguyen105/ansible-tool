<template>
  <div>
    <PageHeader title="Jobs" eyebrow="Execution Queue" description="Launch jobs, monitor queue state, and drill into execution output and result summaries.">
      <button class="btn-primary" @click="showWizard = true">Run Job</button>
    </PageHeader>
    <BannerNotice title="Warning" tone="warn" text="Live jobs can reach production devices immediately. Prefer check mode for risky or unreviewed changes." />
    <div class="mt-5">
      <DataTable :columns="columns" :rows="rows" row-key="id">
        <template #status="{ row }">
          <StatusBadge :value="row.status" />
        </template>
        <template #actions="{ row }">
          <RouterLink class="text-console-glow" :to="`/jobs/${row.id}`">View</RouterLink>
        </template>
      </DataTable>
    </div>
    <JobRunWizard :open="showWizard" @close="showWizard = false" @saved="load" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import api from '../../api/client'
import BannerNotice from '../../components/common/BannerNotice.vue'
import DataTable from '../../components/common/DataTable.vue'
import PageHeader from '../../components/common/PageHeader.vue'
import StatusBadge from '../../components/common/StatusBadge.vue'
import JobRunWizard from '../../components/wizards/JobRunWizard.vue'

const rows = ref<any[]>([])
const showWizard = ref(false)
const columns = [
  { key: 'name', label: 'Name' },
  { key: 'status', label: 'Status' },
  { key: 'target_type', label: 'Target Type' },
  { key: 'created_at', label: 'Created' },
]

async function load() {
  const response = await api.get('/jobs')
  rows.value = response.data.data
}

onMounted(load)
</script>
