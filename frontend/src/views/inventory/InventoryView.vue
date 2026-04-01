<template>
  <div>
    <PageHeader
      title="Inventory"
      eyebrow="Managed Targets"
      description="Keep device scope clean, searchable, and ready for controlled automation runs. Import existing inventories or build smaller execution sets manually."
    >
      <button class="btn-secondary" :disabled="isSaving" @click="openCreate">New inventory</button>
      <button class="btn-primary" :disabled="isSaving" @click="showImport = true">Import inventory</button>
    </PageHeader>

    <div class="grid gap-4 xl:grid-cols-4">
      <CardStat label="Inventories" :value="rows.length" tone="cataloged" :helper="rows.length ? 'Workspace inventory objects available.' : 'No inventories created yet.'" />
      <CardStat label="Hosts" :value="hostTotal" tone="reachable" :helper="hostTotal ? `${enabledHostTotal} enabled for targeting.` : 'Add hosts manually or import a file.'" />
      <CardStat label="Groups" :value="groupTotal" tone="organized" :helper="groupTotal ? 'Host grouping is available for scoped jobs.' : 'Create groups to target jobs safely.'" />
      <CardStat label="Variables" :value="variableBearingInventories" tone="templated" :helper="variableBearingInventories ? 'Inventories include scoped variables.' : 'No inventory variables defined yet.'" />
    </div>

    <section class="mt-6 rounded-3xl border border-console-edge bg-console-panel/80 p-5 shadow-xl shadow-slate-950/20">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p class="text-xs uppercase tracking-[0.22em] text-console-glow">Inventory Control</p>
          <h3 class="mt-2 text-xl font-semibold text-white">Target management workspace</h3>
          <p class="mt-2 max-w-3xl text-sm leading-6 text-console-muted">
            Search inventories quickly, review host and group counts, and keep imports normalized before they are used by operators.
          </p>
        </div>
        <div class="grid gap-3 sm:grid-cols-2 lg:min-w-[420px]">
          <input v-model="search" :disabled="isLoading" placeholder="Search by inventory name" />
          <select v-model="sourceFilter" :disabled="isLoading">
            <option value="all">All sources</option>
            <option value="manual">Manual</option>
            <option value="import">Import</option>
          </select>
        </div>
      </div>
    </section>

    <div class="mt-6">
      <DataTable
        title="Inventory catalog"
        description="Review source, host counts, and variable coverage before operators select an inventory for job execution."
        :columns="columns"
        :rows="filteredRows"
        :loading="isLoading"
        loading-title="Loading inventory"
        loading-description="Collecting manual and imported inventory objects, host counts, and readiness metadata."
        empty-title="No inventory matches your filters"
        empty-description="Create a new inventory manually or import a source file to seed the workspace."
      >
        <template #name="{ row }">
          <div>
            <p class="font-medium text-white">{{ row.name }}</p>
            <p class="mt-1 text-xs text-console-muted">{{ row.description || 'No description provided' }}</p>
          </div>
        </template>
        <template #source_type="{ row }">
          <StatusBadge :value="row.source_type" />
        </template>
        <template #hosts="{ row }">
          <div>
            <p class="text-white">{{ row.host_count }} hosts</p>
            <p class="mt-1 text-xs text-console-muted">{{ row.enabled_host_count }} enabled</p>
          </div>
        </template>
        <template #groups="{ row }">
          <div>
            <p class="text-white">{{ row.group_count }} groups</p>
            <p class="mt-1 text-xs text-console-muted">{{ row.variable_count }} variable scopes</p>
          </div>
        </template>
        <template #readiness="{ row }">
          <div>
            <StatusBadge :value="row.readiness" />
            <p class="mt-2 text-xs text-console-muted">{{ row.readiness_note }}</p>
          </div>
        </template>
        <template #actions="{ row }">
          <div class="flex justify-end gap-3 text-sm">
            <button class="text-console-glow transition hover:text-white" :disabled="isSaving" @click="openEdit(row)">Edit</button>
            <button class="text-rose-300 transition hover:text-rose-200 disabled:opacity-50" :disabled="isSaving" @click="promptDelete(row)">Delete</button>
          </div>
        </template>
      </DataTable>
    </div>

    <InventoryImportWizard :open="showImport" @close="showImport = false" @saved="load" />

    <DrawerPanel :open="showDeleteConfirm" title="Delete inventory" @close="closeDeleteConfirm">
      <div class="space-y-4">
        <p class="text-sm text-console-muted">
          Deleting <span class="font-medium text-white">{{ deleteCandidate?.name }}</span> is permanent.
          This inventory is referenced by {{ deleteUsage.schedules_total }} schedules ({{ deleteUsage.schedules_enabled }} enabled) and {{ deleteUsage.jobs_total }} jobs ({{ deleteUsage.jobs_active }} active).
        </p>
        <div>
          <label class="field-label">Type inventory name to confirm</label>
          <input v-model="deleteConfirmText" :disabled="isSaving" placeholder="Inventory name" />
        </div>
        <div class="flex justify-end gap-2">
          <button class="btn-secondary" :disabled="isSaving" @click="closeDeleteConfirm">Cancel</button>
          <button class="btn-primary" :disabled="isSaving || deleteConfirmText !== (deleteCandidate?.name || '')" @click="removeInventory">
            {{ isSaving ? 'Deleting...' : 'Delete inventory' }}
          </button>
        </div>
      </div>
    </DrawerPanel>

    <DrawerPanel :open="showCreate" :title="selectedId ? 'Edit inventory' : 'Create inventory'" @close="closeDrawer">
      <div class="space-y-4">
        <div>
          <label class="field-label">Name</label>
          <input v-model="form.name" :disabled="isSaving" placeholder="Core WAN routers" />
        </div>
        <div>
          <label class="field-label">Description</label>
          <input v-model="form.description" :disabled="isSaving" placeholder="Optional operator context" />
        </div>
        <div>
          <label class="field-label">Inventory Vars JSON</label>
          <textarea v-model="varsText" :disabled="isSaving" placeholder='{"ansible_network_os": "cisco.ios.ios"}'></textarea>
        </div>
        <div>
          <div class="flex items-center justify-between">
            <label class="field-label">Inventory Members</label>
            <div class="flex gap-2 text-xs">
              <button class="btn-secondary" :disabled="isSaving" @click="editorMode = 'guided'">Guided</button>
              <button class="btn-secondary" :disabled="isSaving" @click="editorMode = 'json'">Advanced JSON</button>
            </div>
          </div>
        </div>
        <div v-if="editorMode === 'guided'" class="grid gap-4 lg:grid-cols-2">
          <div class="space-y-3 rounded-2xl border border-console-edge bg-console-deep/40 p-4">
            <div class="flex items-center justify-between">
              <p class="text-sm font-medium text-white">Hosts</p>
              <button class="btn-secondary" :disabled="isSaving" @click="addHost">Add host</button>
            </div>
            <div v-for="(host, index) in formHosts" :key="`host-${index}`" class="space-y-2 rounded-xl border border-console-edge/70 p-3">
              <input v-model="host.name" :disabled="isSaving" placeholder="Host name" />
              <input v-model="host.address" :disabled="isSaving" placeholder="Address (optional)" />
              <input v-model="host.groupsText" :disabled="isSaving" placeholder="Groups (comma separated)" />
              <textarea v-model="host.variablesText" :disabled="isSaving" placeholder='{"role":"edge"}'></textarea>
              <label class="flex items-center gap-2 text-sm text-console-muted">
                <input v-model="host.enabled" :disabled="isSaving" type="checkbox" class="w-auto" />
                Enabled
              </label>
              <button class="text-rose-300 transition hover:text-rose-200" :disabled="isSaving" @click="removeHost(index)">Remove</button>
            </div>
          </div>
          <div class="space-y-3 rounded-2xl border border-console-edge bg-console-deep/40 p-4">
            <div class="flex items-center justify-between">
              <p class="text-sm font-medium text-white">Groups</p>
              <button class="btn-secondary" :disabled="isSaving" @click="addGroup">Add group</button>
            </div>
            <div v-for="(group, index) in formGroups" :key="`group-${index}`" class="space-y-2 rounded-xl border border-console-edge/70 p-3">
              <input v-model="group.name" :disabled="isSaving" placeholder="Group name" />
              <input v-model="group.childrenText" :disabled="isSaving" placeholder="Child groups (comma separated)" />
              <textarea v-model="group.variablesText" :disabled="isSaving" placeholder='{"site":"dc1"}'></textarea>
              <button class="text-rose-300 transition hover:text-rose-200" :disabled="isSaving" @click="removeGroup(index)">Remove</button>
            </div>
          </div>
        </div>
        <div v-else class="space-y-3">
          <div>
            <label class="field-label">Hosts JSON Array</label>
            <textarea v-model="hostsText" :disabled="isSaving" placeholder='[{"name":"edge-rtr-01","address":"10.0.0.10","groups":["wan"]}]'></textarea>
          </div>
          <div>
            <label class="field-label">Groups JSON Array</label>
            <textarea v-model="groupsText" :disabled="isSaving" placeholder='[{"name":"wan","children":[]}]'></textarea>
          </div>
        </div>
        <BannerNotice
          title="Validation"
          tone="info"
          text="Use valid JSON for variables, hosts, and groups. Hosts and groups are normalized into structured inventory records after save."
        />
        <div class="flex justify-end gap-2">
          <button class="btn-secondary" :disabled="isSaving" @click="closeDrawer">Cancel</button>
          <button class="btn-primary" :disabled="isSaving" @click="saveInventory">{{ isSaving ? 'Saving...' : selectedId ? 'Save changes' : 'Create inventory' }}</button>
        </div>
      </div>
    </DrawerPanel>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import api from '../../api/client'
import BannerNotice from '../../components/common/BannerNotice.vue'
import CardStat from '../../components/common/CardStat.vue'
import DataTable from '../../components/common/DataTable.vue'
import DrawerPanel from '../../components/common/DrawerPanel.vue'
import PageHeader from '../../components/common/PageHeader.vue'
import StatusBadge from '../../components/common/StatusBadge.vue'
import InventoryImportWizard from '../../components/wizards/InventoryImportWizard.vue'
import { useAppStore } from '../../stores/app'

const app = useAppStore()
const rows = ref<any[]>([])
const search = ref('')
const sourceFilter = ref('all')
const showImport = ref(false)
const showCreate = ref(false)
const showDeleteConfirm = ref(false)
const selectedId = ref<string | null>(null)
const editorMode = ref<'guided' | 'json'>('guided')
const varsText = ref('{}')
const hostsText = ref('[]')
const groupsText = ref('[]')
const isLoading = ref(true)
const isSaving = ref(false)
const deleteConfirmText = ref('')
const deleteCandidate = ref<any | null>(null)
const deleteUsage = reactive({ schedules_total: 0, schedules_enabled: 0, jobs_total: 0, jobs_active: 0 })
const form = reactive({ name: '', description: '' })
const formHosts = ref<any[]>([])
const formGroups = ref<any[]>([])

const columns = [
  { key: 'name', label: 'Inventory' },
  { key: 'source_type', label: 'Source' },
  { key: 'hosts', label: 'Hosts' },
  { key: 'groups', label: 'Groups' },
  { key: 'readiness', label: 'Readiness' },
]

const filteredRows = computed(() => {
  return rows.value.filter((item) => {
    const matchesSearch = item.name.toLowerCase().includes(search.value.toLowerCase())
    const matchesSource = sourceFilter.value === 'all' || item.source_type === sourceFilter.value
    return matchesSearch && matchesSource
  })
})

const hostTotal = computed(() => rows.value.reduce((total, item) => total + item.host_count, 0))
const enabledHostTotal = computed(() => rows.value.reduce((total, item) => total + item.enabled_host_count, 0))
const groupTotal = computed(() => rows.value.reduce((total, item) => total + item.group_count, 0))
const variableBearingInventories = computed(() => rows.value.filter((item) => item.variable_count > 0).length)

function normalizeSummaryRow(item: any) {
  return {
    ...item,
    variable_count: item.variable_scope_count || 0,
  }
}

async function load() {
  isLoading.value = true
  try {
    const response = await api.get('/inventories/summary')
    rows.value = response.data.data.map(normalizeSummaryRow)
  } catch {
    app.pushToast('Inventory data could not be loaded', 'error', 'Check API reachability and refresh the inventory workspace.')
  } finally {
    isLoading.value = false
  }
}

function resetForm() {
  selectedId.value = null
  editorMode.value = 'guided'
  form.name = ''
  form.description = ''
  varsText.value = '{}'
  hostsText.value = '[]'
  groupsText.value = '[]'
  formHosts.value = []
  formGroups.value = []
}

function openCreate() {
  resetForm()
  showCreate.value = true
}

async function openEdit(row: any) {
  isLoading.value = true
  try {
    const response = await api.get(`/inventories/${row.id}`)
    const detail = response.data.data
    selectedId.value = detail.id
    form.name = detail.name
    form.description = detail.description || ''
    varsText.value = JSON.stringify(detail.variables_json || {}, null, 2)
    const hostPayload = detail.hosts.map((host: any) => ({
      name: host.name,
      address: host.address,
      description: host.description,
      variables: host.variables_json || {},
      enabled: host.enabled,
      groups: host.groups || [],
    }))
    const groupPayload = detail.groups.map((group: any) => ({
      name: group.name,
      description: group.description,
      variables: group.variables_json || {},
      children: group.children || [],
    }))
    hostsText.value = JSON.stringify(hostPayload, null, 2)
    groupsText.value = JSON.stringify(groupPayload, null, 2)
    formHosts.value = hostPayload.map((host: any) => ({
      name: host.name || '',
      address: host.address || '',
      enabled: host.enabled !== false,
      groupsText: (host.groups || []).join(', '),
      variablesText: JSON.stringify(host.variables || {}, null, 2),
    }))
    formGroups.value = groupPayload.map((group: any) => ({
      name: group.name || '',
      childrenText: (group.children || []).join(', '),
      variablesText: JSON.stringify(group.variables || {}, null, 2),
    }))
    showCreate.value = true
  } catch (error: any) {
    app.pushToast(error?.response?.data?.message || 'Inventory details could not be loaded', 'error')
  } finally {
    isLoading.value = false
  }
}

function closeDrawer() {
  if (isSaving.value) return
  showCreate.value = false
  resetForm()
}

function addHost() {
  formHosts.value.push({
    name: '',
    address: '',
    enabled: true,
    groupsText: '',
    variablesText: '{}',
  })
}

function removeHost(index: number) {
  formHosts.value.splice(index, 1)
}

function addGroup() {
  formGroups.value.push({
    name: '',
    childrenText: '',
    variablesText: '{}',
  })
}

function removeGroup(index: number) {
  formGroups.value.splice(index, 1)
}

function buildPayloadFromGuided() {
  const hosts = formHosts.value
    .filter((host) => host.name.trim())
    .map((host) => ({
      name: host.name.trim(),
      address: host.address.trim() || null,
      variables: JSON.parse(host.variablesText || '{}'),
      enabled: Boolean(host.enabled),
      groups: host.groupsText
        .split(',')
        .map((item: string) => item.trim())
        .filter(Boolean),
    }))
  const groups = formGroups.value
    .filter((group) => group.name.trim())
    .map((group) => ({
      name: group.name.trim(),
      variables: JSON.parse(group.variablesText || '{}'),
      children: group.childrenText
        .split(',')
        .map((item: string) => item.trim())
        .filter(Boolean),
    }))
  hostsText.value = JSON.stringify(hosts, null, 2)
  groupsText.value = JSON.stringify(groups, null, 2)
  return { hosts, groups }
}

async function saveInventory() {
  isSaving.value = true
  try {
    const guidedPayload = editorMode.value === 'guided' ? buildPayloadFromGuided() : null
    const payload = {
      name: form.name.trim(),
      description: form.description.trim(),
      variables: JSON.parse(varsText.value || '{}'),
      hosts: guidedPayload ? guidedPayload.hosts : JSON.parse(hostsText.value || '[]'),
      groups: guidedPayload ? guidedPayload.groups : JSON.parse(groupsText.value || '[]'),
    }
    if (!payload.name) {
      app.pushToast('Inventory name is required', 'error')
      return
    }
    if (selectedId.value) {
      await api.put(`/inventories/${selectedId.value}`, payload)
      app.pushToast('Inventory updated', 'success', 'The inventory record has been updated.')
    } else {
      await api.post('/inventories', payload)
      app.pushToast('Inventory created', 'success', 'The inventory is now available for operator targeting.')
    }
    closeDrawer()
    await load()
  } catch (error: any) {
    if (error instanceof SyntaxError) {
      app.pushToast('Inventory JSON input is invalid', 'error', 'Correct variables, hosts, or groups JSON before saving.')
      return
    }
    app.pushToast(error?.response?.data?.message || 'Inventory could not be saved', 'error')
  } finally {
    isSaving.value = false
  }
}

async function promptDelete(row: any) {
  deleteCandidate.value = row
  deleteConfirmText.value = ''
  try {
    const response = await api.get(`/inventories/${row.id}/usage`)
    deleteUsage.schedules_total = response.data.data.schedules_total
    deleteUsage.schedules_enabled = response.data.data.schedules_enabled
    deleteUsage.jobs_total = response.data.data.jobs_total
    deleteUsage.jobs_active = response.data.data.jobs_active
    showDeleteConfirm.value = true
  } catch (error: any) {
    app.pushToast(error?.response?.data?.message || 'Inventory usage could not be loaded', 'error')
  }
}

function closeDeleteConfirm() {
  if (isSaving.value) return
  showDeleteConfirm.value = false
  deleteCandidate.value = null
  deleteConfirmText.value = ''
  deleteUsage.schedules_total = 0
  deleteUsage.schedules_enabled = 0
  deleteUsage.jobs_total = 0
  deleteUsage.jobs_active = 0
}

async function removeInventory() {
  if (!deleteCandidate.value) return
  isSaving.value = true
  try {
    await api.delete(`/inventories/${deleteCandidate.value.id}`)
    app.pushToast('Inventory deleted', 'success')
    closeDeleteConfirm()
    await load()
  } catch (error: any) {
    app.pushToast(error?.response?.data?.message || 'Inventory could not be deleted', 'error')
  } finally {
    isSaving.value = false
  }
}

onMounted(load)
</script>
