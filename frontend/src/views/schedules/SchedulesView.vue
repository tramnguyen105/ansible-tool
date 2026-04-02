<template>
  <div>
    <PageHeader
      title="Schedules"
      eyebrow="Recurring Automation"
      description="Trigger approved jobs on predictable schedules and keep the next dispatch visible before unattended changes occur."
    >
      <button class="btn-secondary" :disabled="isLoading || isSaving || isLoadingLookups" @click="load">{{ isLoading ? 'Refreshing...' : 'Refresh' }}</button>
      <button class="btn-primary" :disabled="isLoadingLookups" @click="openCreate">New schedule</button>
    </PageHeader>

    <div class="grid gap-4 xl:grid-cols-4">
      <CardStat label="Schedules" :value="rows.length" tone="cataloged" :helper="rows.length ? 'Recurring automation entries are configured.' : 'No schedules have been created.'" />
      <CardStat label="Enabled" :value="enabledCount" tone="enabled" :helper="enabledCount ? 'These schedules can dispatch work automatically.' : 'No schedules are currently active.'" />
      <CardStat label="Check mode" :value="checkModeCount" tone="review" :helper="checkModeCount ? 'Some schedules are limited to validation runs.' : 'No schedules currently use check mode.'" />
      <CardStat label="Next due" :value="nextDueLabel" tone="timed" helper="The earliest enabled schedule due to run from the current list." />
    </div>

    <section class="mt-6 rounded-2xl border border-slate-200 bg-white p-5">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p class="text-[0.8rem] font-medium uppercase tracking-[0.12em] text-slate-500">Filters</p>
          <h3 class="mt-2 text-[1.15rem] font-semibold text-slate-900">Schedule library</h3>
          <p class="mt-2 text-[0.96rem] text-slate-600">Filter by name, state, or execution mode to isolate schedules quickly.</p>
        </div>
        <div class="grid gap-3 sm:grid-cols-2 lg:min-w-[460px] xl:grid-cols-3">
          <input v-model="search" :disabled="isLoading" placeholder="Search by schedule name" />
          <select v-model="enabledFilter" :disabled="isLoading">
            <option value="all">All states</option>
            <option value="enabled">Enabled</option>
            <option value="disabled">Disabled</option>
          </select>
          <select v-model="modeFilter" :disabled="isLoading">
            <option value="all">All modes</option>
            <option value="check">Check mode</option>
            <option value="live">Live execution</option>
          </select>
        </div>
      </div>
    </section>

    <div class="mt-6">
      <DataTable
        title="Schedule library"
        description="Review cron cadence, execution mode, and next run timing before allowing automation to continue unattended."
        :columns="columns"
        :rows="filteredRows"
        :loading="isLoading"
        loading-title="Loading schedules"
        loading-description="Collecting recurring automation records and calculating the next visible dispatch windows."
        :empty-title="hasActiveFilters ? 'No schedules match your current filters' : 'No schedules saved'"
        :empty-description="hasActiveFilters
          ? 'Adjust or clear filters to review additional recurring automation entries.'
          : 'Create a schedule after the same playbook has been validated manually with the intended inventory and credentials.'"
      >
        <template #name="{ row }">
          <div>
            <p class="font-medium text-slate-900">{{ row.name }}</p>
            <p class="mt-1 text-xs text-console-muted">{{ row.description || 'No description provided' }}</p>
          </div>
        </template>
        <template #cron_expression="{ row }">
          <div>
            <p class="text-slate-900">{{ row.cron_expression }}</p>
            <p class="mt-1 text-xs text-console-muted">{{ row.check_mode ? 'Check mode schedule' : 'Live execution schedule' }}</p>
          </div>
        </template>
        <template #enabled="{ row }">
          <StatusBadge :value="row.enabled ? 'enabled' : 'disabled'" />
        </template>
        <template #next_run_at="{ row }">
          <div>
            <p class="text-slate-900">{{ formatDateTime(row.next_run_at) }}</p>
            <p class="mt-1 text-xs text-console-muted">{{ row.timezone }}</p>
          </div>
        </template>
        <template #actions="{ row }">
          <div class="flex justify-end gap-3 text-sm">
            <button class="text-console-glow transition hover:text-slate-900" :disabled="isSaving" @click="openEdit(row)">Edit</button>
            <button class="text-rose-300 transition hover:text-rose-200 disabled:opacity-50" :disabled="isSaving" @click="removeSchedule(row)">Delete</button>
          </div>
        </template>
      </DataTable>
    </div>

    <DrawerPanel :open="showDrawer" :title="selectedId ? 'Edit schedule' : 'Create schedule'" @close="closeDrawer">
      <div class="space-y-4">
        <div v-if="isLoadingLookups" class="rounded-2xl border border-console-edge bg-console-deep/50 p-4 text-sm text-console-muted">
          Loading inventories, credentials, and playbooks for schedule targeting.
        </div>

        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <label class="field-label">Name</label>
            <input v-model="form.name" :disabled="isSaving || isLoadingLookups" placeholder="nightly-validation" />
          </div>
          <div>
            <label class="field-label">Cron Expression</label>
            <input v-model="form.cron_expression" :disabled="isSaving || isLoadingLookups" placeholder="0 2 * * *" />
          </div>
          <div class="md:col-span-2">
            <label class="field-label">Description</label>
            <textarea
              v-model="form.description"
              :disabled="isSaving || isLoadingLookups"
              rows="3"
              placeholder="Purpose, risk level, and operator notes for this recurring run."
            />
          </div>
          <div>
            <label class="field-label">Timezone</label>
            <input v-model="form.timezone" :disabled="isSaving || isLoadingLookups" />
          </div>
          <div>
            <label class="field-label">Inventory</label>
            <select v-model="form.inventory_id" :disabled="isSaving || isLoadingLookups">
              <option v-for="item in inventories" :key="item.id" :value="item.id">{{ item.name }}</option>
            </select>
          </div>
          <div>
            <label class="field-label">Credential</label>
            <select v-model="form.credential_id" :disabled="isSaving || isLoadingLookups">
              <option v-for="item in credentials" :key="item.id" :value="item.id">{{ item.name }}</option>
            </select>
          </div>
          <div>
            <label class="field-label">Playbook</label>
            <select v-model="form.playbook_id" :disabled="isSaving || isLoadingLookups">
              <option v-for="item in playbooks" :key="item.id" :value="item.id">{{ item.name }}</option>
            </select>
          </div>
        </div>

        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <label class="field-label">Target Type</label>
            <select v-model="form.target_type" :disabled="isSaving || isLoadingLookups">
              <option value="all">All managed hosts</option>
              <option value="hosts">Specific hosts</option>
              <option value="groups">Specific groups</option>
            </select>
          </div>
          <div>
            <label class="field-label">Target Value</label>
            <input
              v-model="form.target_value"
              :disabled="isSaving || isLoadingLookups"
              :placeholder="form.target_type === 'all' ? 'Optional host or group selector' : 'Required when targeting hosts or groups'"
            />
          </div>
        </div>

        <BannerNotice
          v-if="formError"
          title="Fix schedule form errors"
          tone="warn"
          :text="formError"
        />

        <div class="flex flex-wrap items-center gap-5 text-sm text-console-muted">
          <label class="flex items-center gap-2">
            <input v-model="form.enabled" :disabled="isSaving || isLoadingLookups" type="checkbox" class="w-auto" />
            Enabled
          </label>
          <label class="flex items-center gap-2">
            <input v-model="form.check_mode" :disabled="isSaving || isLoadingLookups" type="checkbox" class="w-auto" />
            Check mode only
          </label>
        </div>

        <BannerNotice
          title="Scheduling safety"
          tone="warn"
          text="Only schedule jobs that have already been reviewed manually. Unattended live execution should be limited to well-understood, low-risk tasks."
        />

        <div class="flex justify-end gap-2">
          <button class="btn-secondary" :disabled="isSaving" @click="closeDrawer">Cancel</button>
          <button class="btn-primary" :disabled="isSaving || isLoadingLookups" @click="save">{{ isSaving ? 'Saving...' : selectedId ? 'Save changes' : 'Save schedule' }}</button>
        </div>
      </div>
    </DrawerPanel>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'

import api from '../../api/client'
import BannerNotice from '../../components/common/BannerNotice.vue'
import CardStat from '../../components/common/CardStat.vue'
import DataTable from '../../components/common/DataTable.vue'
import DrawerPanel from '../../components/common/DrawerPanel.vue'
import PageHeader from '../../components/common/PageHeader.vue'
import StatusBadge from '../../components/common/StatusBadge.vue'
import { useAppStore } from '../../stores/app'
import { formatDateTime } from '../../utils/format'

const app = useAppStore()
const rows = ref<any[]>([])
const showDrawer = ref(false)
const selectedId = ref<string | null>(null)
const inventories = ref<any[]>([])
const credentials = ref<any[]>([])
const playbooks = ref<any[]>([])
const isLoading = ref(true)
const isLoadingLookups = ref(false)
const isSaving = ref(false)
const hasLoadedLookups = ref(false)
const search = ref('')
const enabledFilter = ref('all')
const modeFilter = ref('all')
const formError = ref('')
const form = reactive<any>({
  name: 'nightly-run',
  description: '',
  cron_expression: '0 2 * * *',
  timezone: 'UTC',
  enabled: true,
  inventory_id: '',
  credential_id: '',
  playbook_id: '',
  target_type: 'all',
  target_value: '',
  extra_vars: {},
  check_mode: false,
})
const columns = [
  { key: 'name', label: 'Schedule' },
  { key: 'cron_expression', label: 'Cadence' },
  { key: 'enabled', label: 'State' },
  { key: 'next_run_at', label: 'Next run' },
]

const enabledCount = computed(() => rows.value.filter((item) => item.enabled).length)
const checkModeCount = computed(() => rows.value.filter((item) => item.check_mode).length)
const nextDueLabel = computed(() => {
  const nextRun = rows.value
    .filter((item) => item.enabled && item.next_run_at)
    .map((item) => item.next_run_at)
    .sort()[0]
  return nextRun ? formatDateTime(nextRun) : 'None'
})
const hasActiveFilters = computed(() => {
  return search.value.trim().length > 0 || enabledFilter.value !== 'all' || modeFilter.value !== 'all'
})
const filteredRows = computed(() => {
  return rows.value.filter((row) => {
    const matchesSearch = row.name.toLowerCase().includes(search.value.trim().toLowerCase())
    const matchesEnabled =
      enabledFilter.value === 'all' ||
      (enabledFilter.value === 'enabled' && row.enabled) ||
      (enabledFilter.value === 'disabled' && !row.enabled)
    const matchesMode =
      modeFilter.value === 'all' ||
      (modeFilter.value === 'check' && row.check_mode) ||
      (modeFilter.value === 'live' && !row.check_mode)
    return matchesSearch && matchesEnabled && matchesMode
  })
})

function resetForm() {
  selectedId.value = null
  form.name = 'nightly-run'
  form.description = ''
  form.cron_expression = '0 2 * * *'
  form.timezone = 'UTC'
  form.enabled = true
  form.inventory_id = inventories.value[0]?.id || ''
  form.credential_id = credentials.value[0]?.id || ''
  form.playbook_id = playbooks.value[0]?.id || ''
  form.target_type = 'all'
  form.target_value = ''
  form.extra_vars = {}
  form.check_mode = false
}

async function loadLookups(force = false) {
  if (hasLoadedLookups.value && !force) return
  isLoadingLookups.value = true
  try {
    const [inventoryResp, credentialResp, playbookResp] = await Promise.all([
      api.get('/inventories'),
      api.get('/credentials?active_only=true'),
      api.get('/playbooks'),
    ])
    inventories.value = inventoryResp.data.data
    credentials.value = credentialResp.data.data
    playbooks.value = playbookResp.data.data
    hasLoadedLookups.value = true
    if (!selectedId.value) resetForm()
  } catch {
    hasLoadedLookups.value = false
    app.pushToast('Schedule dependencies could not be loaded', 'error', 'Inventories, credentials, and playbooks must be available before a schedule can be saved.')
  } finally {
    isLoadingLookups.value = false
  }
}

function openCreate() {
  formError.value = ''
  resetForm()
  showDrawer.value = true
}

function openEdit(row: any) {
  formError.value = ''
  selectedId.value = row.id
  form.name = row.name
  form.description = row.description || ''
  form.cron_expression = row.cron_expression
  form.timezone = row.timezone
  form.enabled = row.enabled
  form.inventory_id = row.inventory_id
  form.credential_id = row.credential_id
  form.playbook_id = row.playbook_id
  form.target_type = row.target_type
  form.target_value = row.target_value || ''
  form.extra_vars = row.extra_vars_json || {}
  form.check_mode = row.check_mode
  showDrawer.value = true
}

function closeDrawer() {
  if (isSaving.value) return
  formError.value = ''
  showDrawer.value = false
  resetForm()
}

async function load() {
  isLoading.value = true
  try {
    const response = await api.get('/schedules')
    rows.value = response.data.data
  } catch {
    app.pushToast('Schedules could not be loaded', 'error', 'Check API reachability and refresh the schedule library.')
  } finally {
    isLoading.value = false
  }
}

watch(
  () => showDrawer.value,
  (open) => {
    if (open) loadLookups()
  },
)

function validateForm() {
  const cronPattern = /^(\S+\s+){4}\S+$/
  const cron = form.cron_expression.trim()
  const timezone = form.timezone.trim()
  const targetValue = form.target_value.trim()
  if (!form.name.trim()) return 'Schedule name is required.'
  if (!cronPattern.test(cron)) return 'Cron expression must contain exactly five fields (for example: 0 2 * * *).'
  if (!timezone) return 'Timezone is required.'
  if (!form.inventory_id) return 'Inventory is required.'
  if (!form.credential_id) return 'Credential is required.'
  if (!form.playbook_id) return 'Playbook is required.'
  if (form.target_type !== 'all' && !targetValue) return 'Target value is required when target type is hosts or groups.'
  return ''
}

async function save() {
  formError.value = validateForm()
  if (formError.value) {
    app.pushToast(formError.value, 'error')
    return
  }
  isSaving.value = true
  try {
    const payload = {
      ...form,
      name: form.name.trim(),
      description: form.description.trim(),
      cron_expression: form.cron_expression.trim(),
      timezone: form.timezone.trim(),
      target_value: form.target_value.trim(),
      extra_vars: form.extra_vars || {},
    }
    if (selectedId.value) {
      await api.put(`/schedules/${selectedId.value}`, payload)
      app.pushToast('Schedule updated', 'success', 'The recurring run definition has been updated.')
    } else {
      await api.post('/schedules', payload)
      app.pushToast('Schedule saved', 'success', 'The schedule is now available for automatic dispatch.')
    }
    closeDrawer()
    await load()
  } catch (error: any) {
    app.pushToast(error?.response?.data?.message || 'Schedule could not be saved', 'error')
  } finally {
    isSaving.value = false
  }
}

async function removeSchedule(row: any) {
  if (!window.confirm(`Delete schedule "${row.name}"?`)) return
  try {
    await api.delete(`/schedules/${row.id}`)
    app.pushToast('Schedule deleted', 'success')
    await load()
  } catch (error: any) {
    app.pushToast(error?.response?.data?.message || 'Schedule could not be deleted', 'error')
  }
}

onMounted(async () => {
  await load()
  await loadLookups()
})
</script>
