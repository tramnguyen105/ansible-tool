<template>
  <div>
    <PageHeader
      title="Audit Logs"
      eyebrow="Immutable Activity"
      description="Review authentication, credential usage, playbook edits, and job execution events from one filtered activity stream."
    >
      <button class="btn-secondary" :disabled="isLoading" @click="resetFilters">Reset filters</button>
      <button class="btn-primary" :disabled="isLoading" @click="load">{{ isLoading ? 'Loading...' : 'Apply filters' }}</button>
    </PageHeader>

    <div class="grid gap-4 xl:grid-cols-4">
      <CardStat label="Events" :value="rows.length" tone="logged" :helper="rows.length ? 'Audit records returned by the current filters.' : 'No events match the current filter set.'" />
      <CardStat label="Success" :value="successCount" tone="success" :helper="successCount ? 'Successful operator actions recorded.' : 'No successful events in view.'" />
      <CardStat label="Errors" :value="errorCount" tone="failed" :helper="errorCount ? 'Failures need review.' : 'No failed audit events in view.'" />
      <CardStat label="Latest" :value="latestEvent" tone="recent" helper="Most recent event returned from the current query." />
    </div>

    <section class="mt-6 rounded-3xl border border-console-edge bg-console-panel/80 p-5 shadow-xl shadow-slate-950/20">
      <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <input v-model="filters.action" placeholder="Action, e.g. login" :disabled="isLoading" />
        <input v-model="filters.resource_type" placeholder="Resource type, e.g. job" :disabled="isLoading" />
        <input v-model="filters.status" placeholder="Status, e.g. success" :disabled="isLoading" />
        <input v-model="filters.limit" placeholder="Result limit" type="number" min="1" max="500" :disabled="isLoading" />
      </div>
    </section>

    <div class="mt-6">
      <DataTable
        title="Audit activity stream"
        description="Use the audit stream to confirm who changed what, when, and whether the operation completed successfully."
        :columns="columns"
        :rows="rows"
        :loading="isLoading"
        loading-title="Loading audit activity"
        loading-description="Collecting filtered authentication, credential, playbook, and job events from the audit service."
        empty-title="No audit events returned"
        empty-description="Adjust the filters or generate activity by signing in, editing playbooks, or running jobs."
      >
        <template #created_at="{ row }">
          <div>
            <p class="text-white">{{ formatDateTime(row.created_at) }}</p>
            <p class="mt-1 text-xs text-console-muted">{{ formatRelativeTime(row.created_at) }}</p>
          </div>
        </template>
        <template #status="{ row }">
          <StatusBadge :value="row.status" />
        </template>
        <template #message="{ row }">
          <div>
            <p class="text-white">{{ row.message }}</p>
            <p class="mt-1 text-xs text-console-muted">{{ row.ip_address || 'No IP recorded' }}</p>
          </div>
        </template>
      </DataTable>
    </div>
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
import { formatDateTime, formatRelativeTime } from '../../utils/format'

const app = useAppStore()
const rows = ref<any[]>([])
const isLoading = ref(true)
const filters = reactive({ action: '', resource_type: '', status: '', limit: 100 })
const columns = [
  { key: 'created_at', label: 'Time' },
  { key: 'action', label: 'Action' },
  { key: 'resource_type', label: 'Resource' },
  { key: 'status', label: 'Status' },
  { key: 'message', label: 'Message' },
]

const successCount = computed(() => rows.value.filter((item) => item.status === 'success').length)
const errorCount = computed(() => rows.value.filter((item) => item.status !== 'success').length)
const latestEvent = computed(() => (rows.value[0]?.action ? rows.value[0].action : 'None'))

function resetFilters() {
  filters.action = ''
  filters.resource_type = ''
  filters.status = ''
  filters.limit = 100
  load()
}

async function load() {
  isLoading.value = true
  try {
    const response = await api.get('/audit-logs', { params: { ...filters } })
    rows.value = response.data.data
  } catch {
    app.pushToast('Audit logs could not be loaded', 'error', 'Check filter values and API reachability, then retry.')
  } finally {
    isLoading.value = false
  }
}

onMounted(load)
</script>
