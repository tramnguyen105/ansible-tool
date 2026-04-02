<template>
  <div>
    <PageHeader
      title="Audit Logs"
      eyebrow="Immutable Activity"
      description="Review authentication, credential usage, playbook edits, and job execution events from one filtered activity stream."
    >
      <button class="btn-secondary" :disabled="isLoading" @click="resetFilters">Reset filters</button>
      <button class="btn-secondary" :disabled="isLoading" @click="saveFilterPreset">Save filters</button>
      <button class="btn-secondary" :disabled="isLoading" @click="loadSavedPreset">Load saved</button>
      <button class="btn-primary" :disabled="isLoading" @click="load(false)">{{ isLoading ? 'Loading...' : 'Apply filters' }}</button>
    </PageHeader>

    <div class="grid gap-4 xl:grid-cols-4">
      <CardStat label="Total events" :value="total" tone="logged" :helper="total ? 'Audit records matching the current filters.' : 'No events match the current filter set.'" />
      <CardStat label="Success" :value="successCount" tone="success" :helper="successCount ? 'Successful operator actions on this page.' : 'No successful events in view.'" />
      <CardStat label="Errors" :value="errorCount" tone="failed" :helper="errorCount ? 'Failures need review.' : 'No failed events in view.'" />
      <CardStat label="Latest" :value="latestEvent" tone="recent" helper="Most recent event returned from the current query." />
    </div>

    <section class="mt-6 rounded-3xl border border-console-edge bg-console-panel/80 p-5 shadow-xl shadow-slate-300/25">
      <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <input v-model="filters.action" placeholder="Action contains, e.g. login" :disabled="isLoading" />
        <select v-model="filters.resource_type" :disabled="isLoading">
          <option value="">All resource types</option>
          <option v-for="item in resourceTypeOptions" :key="item" :value="item">{{ item }}</option>
        </select>
        <select v-model="filters.status" :disabled="isLoading">
          <option value="">All statuses</option>
          <option value="success">success</option>
          <option value="failure">failure</option>
        </select>
        <input v-model="filters.message" placeholder="Message contains" :disabled="isLoading" />
        <input v-model="filters.user_id" placeholder="User ID (UUID)" :disabled="isLoading" />
        <input v-model="filters.resource_id" placeholder="Resource ID contains" :disabled="isLoading" />
        <input v-model="filters.created_from" type="datetime-local" :disabled="isLoading" />
        <input v-model="filters.created_to" type="datetime-local" :disabled="isLoading" />
      </div>
      <div class="mt-4 flex flex-wrap items-center gap-2 text-sm">
        <button class="btn-secondary" :disabled="isLoading" @click="applyPreset('failed')">Failed only</button>
        <button class="btn-secondary" :disabled="isLoading" @click="applyPreset('auth')">Auth events</button>
        <button class="btn-secondary" :disabled="isLoading" @click="applyPreset('playbook')">Playbook changes</button>
        <button class="btn-secondary" :disabled="isLoading" @click="applyPreset('last24h')">Last 24h</button>
        <label class="ml-2 inline-flex items-center gap-2 text-console-muted">
          <input v-model="autoRefresh" type="checkbox" :disabled="isLoading" />
          Auto refresh (10s)
        </label>
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
            <p class="text-slate-900">{{ formatDateTime(row.created_at) }}</p>
            <p class="mt-1 text-xs text-console-muted">{{ formatRelativeTime(row.created_at) }}</p>
          </div>
        </template>
        <template #status="{ row }">
          <StatusBadge :value="row.status" />
        </template>
        <template #actor="{ row }">
          <div>
            <p class="text-slate-900">{{ row.actor_display_name || row.actor_username || 'System' }}</p>
            <p class="mt-1 text-xs text-console-muted">{{ row.actor_username || row.user_id || 'No user id' }}</p>
          </div>
        </template>
        <template #resource_type="{ row }">
          <div>
            <p class="text-slate-900">{{ row.resource_type }}</p>
            <p class="mt-1 text-xs text-console-muted">{{ row.resource_id || 'No resource id' }}</p>
          </div>
        </template>
        <template #message="{ row }">
          <div>
            <p class="text-slate-900">{{ row.message }}</p>
            <p class="mt-1 text-xs text-console-muted">{{ row.ip_address || 'No IP recorded' }}</p>
          </div>
        </template>
        <template #actions="{ row }">
          <button class="text-console-glow transition hover:text-slate-900" @click="openDetails(row)">Details</button>
        </template>
      </DataTable>
    </div>

    <div class="mt-4 flex items-center justify-between rounded-2xl border border-console-edge bg-console-panel/60 px-4 py-3 text-sm text-console-muted">
      <p>Showing {{ offset + 1 }}-{{ Math.min(offset + rows.length, total) }} of {{ total }}</p>
      <div class="flex items-center gap-2">
        <button class="btn-secondary" :disabled="isLoading || !total" @click="exportLogs('csv')">Export CSV</button>
        <button class="btn-secondary" :disabled="isLoading || !total" @click="exportLogs('json')">Export JSON</button>
        <select v-model.number="limit" :disabled="isLoading" @change="changePageSize">
          <option :value="25">25</option>
          <option :value="50">50</option>
          <option :value="100">100</option>
          <option :value="200">200</option>
        </select>
        <button class="btn-secondary" :disabled="isLoading || offset === 0" @click="prevPage">Previous</button>
        <button class="btn-secondary" :disabled="isLoading || !hasMore" @click="nextPage">Next</button>
      </div>
    </div>

    <DrawerPanel :open="showDetailDrawer" title="Audit event details" @close="closeDetails">
      <div v-if="selectedRow" class="space-y-4">
        <div class="grid gap-3 md:grid-cols-2">
          <div>
            <p class="field-label">Time</p>
            <p>{{ formatDateTime(selectedRow.created_at) }}</p>
          </div>
          <div>
            <p class="field-label">Status</p>
            <StatusBadge :value="selectedRow.status" />
          </div>
          <div>
            <p class="field-label">Actor</p>
            <p>{{ selectedRow.actor_display_name || selectedRow.actor_username || 'System' }}</p>
          </div>
          <div>
            <p class="field-label">User ID</p>
            <p class="break-all">{{ selectedRow.user_id || 'None' }}</p>
          </div>
          <div>
            <p class="field-label">Action</p>
            <p>{{ selectedRow.action }}</p>
          </div>
          <div>
            <p class="field-label">Resource</p>
            <p>{{ selectedRow.resource_type }} / {{ selectedRow.resource_id || 'None' }}</p>
          </div>
        </div>
        <div>
          <p class="field-label">Message</p>
          <p>{{ selectedRow.message }}</p>
        </div>
        <div>
          <p class="field-label">Details JSON</p>
          <pre class="overflow-auto rounded-xl border border-console-edge bg-console-deep/40 p-3 text-xs">{{ prettyDetails }}</pre>
        </div>
      </div>
    </DrawerPanel>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'

import api from '../../api/client'
import CardStat from '../../components/common/CardStat.vue'
import DataTable from '../../components/common/DataTable.vue'
import DrawerPanel from '../../components/common/DrawerPanel.vue'
import PageHeader from '../../components/common/PageHeader.vue'
import StatusBadge from '../../components/common/StatusBadge.vue'
import { useAppStore } from '../../stores/app'
import { formatDateTime, formatRelativeTime } from '../../utils/format'

const app = useAppStore()
const rows = ref<any[]>([])
const total = ref(0)
const limit = ref(100)
const offset = ref(0)
const hasMore = ref(false)
const isLoading = ref(true)
const autoRefresh = ref(false)
const refreshTimer = ref<number | null>(null)
const showDetailDrawer = ref(false)
const selectedRow = ref<any | null>(null)
const localStorageKey = 'audit-log-filters-v1'

const filters = reactive({
  action: '',
  resource_type: '',
  status: '',
  message: '',
  user_id: '',
  resource_id: '',
  created_from: '',
  created_to: '',
})

const resourceTypeOptions = ['auth', 'credential', 'inventory', 'playbook', 'template', 'job', 'schedule', 'system']
const columns = [
  { key: 'created_at', label: 'Time' },
  { key: 'status', label: 'Status' },
  { key: 'action', label: 'Action' },
  { key: 'actor', label: 'Actor' },
  { key: 'resource_type', label: 'Resource' },
  { key: 'message', label: 'Message' },
]

const successCount = computed(() => rows.value.filter((item) => item.status === 'success').length)
const errorCount = computed(() => rows.value.filter((item) => item.status !== 'success').length)
const latestEvent = computed(() => (rows.value[0]?.action ? rows.value[0].action : 'None'))
const prettyDetails = computed(() => JSON.stringify(selectedRow.value?.details_json || {}, null, 2))

function buildParams() {
  return {
    action: filters.action.trim() || undefined,
    resource_types: filters.resource_type ? [filters.resource_type] : undefined,
    statuses: filters.status ? [filters.status] : undefined,
    user_id: filters.user_id.trim() || undefined,
    resource_id: filters.resource_id.trim() || undefined,
    message: filters.message.trim() || undefined,
    created_from: filters.created_from ? new Date(filters.created_from).toISOString() : undefined,
    created_to: filters.created_to ? new Date(filters.created_to).toISOString() : undefined,
    limit: limit.value,
    offset: offset.value,
  }
}

function resetFilters() {
  filters.action = ''
  filters.resource_type = ''
  filters.status = ''
  filters.message = ''
  filters.user_id = ''
  filters.resource_id = ''
  filters.created_from = ''
  filters.created_to = ''
  offset.value = 0
  load(false)
}

function applyPreset(name: 'failed' | 'auth' | 'playbook' | 'last24h') {
  if (name === 'failed') {
    filters.status = 'failure'
    filters.resource_type = ''
  } else if (name === 'auth') {
    filters.resource_type = 'auth'
    filters.status = ''
  } else if (name === 'playbook') {
    filters.resource_type = 'playbook'
    filters.status = ''
  } else {
    const since = new Date(Date.now() - 24 * 60 * 60 * 1000)
    filters.created_from = toDatetimeLocal(since)
  }
  offset.value = 0
  load(false)
}

function saveFilterPreset() {
  const payload = { filters: { ...filters }, limit: limit.value }
  localStorage.setItem(localStorageKey, JSON.stringify(payload))
  app.pushToast('Filters saved', 'success')
}

function loadSavedPreset() {
  const raw = localStorage.getItem(localStorageKey)
  if (!raw) {
    app.pushToast('No saved filters found', 'error')
    return
  }
  try {
    const parsed = JSON.parse(raw)
    Object.assign(filters, parsed.filters || {})
    limit.value = Number(parsed.limit || 100)
    offset.value = 0
    load(false)
    app.pushToast('Saved filters applied', 'success')
  } catch {
    app.pushToast('Saved filters are invalid', 'error')
  }
}

async function exportLogs(format: 'csv' | 'json') {
  try {
    const response = await api.get('/audit-logs/export', {
      params: { ...buildParams(), format, offset: undefined },
      responseType: 'blob',
    })
    const url = window.URL.createObjectURL(response.data)
    const link = document.createElement('a')
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
    link.href = url
    link.download = `audit-logs-${timestamp}.${format}`
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
    app.pushToast(`Audit export ready (${format.toUpperCase()})`, 'success')
  } catch {
    app.pushToast('Audit export failed', 'error', 'Retry export after confirming API reachability and current filters.')
  }
}

async function load(resetOffset = false) {
  if (resetOffset) offset.value = 0
  isLoading.value = true
  try {
    const response = await api.get('/audit-logs', { params: buildParams() })
    rows.value = response.data.data.items
    total.value = response.data.data.total
    hasMore.value = response.data.data.has_more
  } catch {
    app.pushToast('Audit logs could not be loaded', 'error', 'Check filter values and API reachability, then retry.')
  } finally {
    isLoading.value = false
  }
}

function prevPage() {
  if (offset.value === 0) return
  offset.value = Math.max(0, offset.value - limit.value)
  load(false)
}

function nextPage() {
  if (!hasMore.value) return
  offset.value += limit.value
  load(false)
}

function changePageSize() {
  offset.value = 0
  load(false)
}

function openDetails(row: any) {
  selectedRow.value = row
  showDetailDrawer.value = true
}

function closeDetails() {
  showDetailDrawer.value = false
  selectedRow.value = null
}

function toDatetimeLocal(input: Date) {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${input.getFullYear()}-${pad(input.getMonth() + 1)}-${pad(input.getDate())}T${pad(input.getHours())}:${pad(input.getMinutes())}`
}

watch(
  autoRefresh,
  (enabled) => {
    if (refreshTimer.value) {
      window.clearInterval(refreshTimer.value)
      refreshTimer.value = null
    }
    if (enabled) {
      refreshTimer.value = window.setInterval(() => load(false), 10_000)
    }
  },
  { immediate: false },
)

onMounted(() => load(false))

onBeforeUnmount(() => {
  if (refreshTimer.value) window.clearInterval(refreshTimer.value)
})
</script>
