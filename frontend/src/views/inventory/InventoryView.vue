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
            <button class="text-rose-300 transition hover:text-rose-200 disabled:opacity-50" :disabled="isSaving" @click="removeInventory(row)">Delete</button>
          </div>
        </template>
      </DataTable>
    </div>

    <InventoryImportWizard :open="showImport" @close="showImport = false" @saved="load" />

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
          <label class="field-label">Hosts JSON Array</label>
          <textarea v-model="hostsText" :disabled="isSaving" placeholder='[{"name":"edge-rtr-01","address":"10.0.0.10","groups":["wan"]}]'></textarea>
        </div>
        <div>
          <label class="field-label">Groups JSON Array</label>
          <textarea v-model="groupsText" :disabled="isSaving" placeholder='[{"name":"wan","children":[]}]'></textarea>
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
const selectedId = ref<string | null>(null)
const varsText = ref('{}')
const hostsText = ref('[]')
const groupsText = ref('[]')
const isLoading = ref(true)
const isSaving = ref(false)
const form = reactive({ name: '', description: '' })

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

function normalizeRow(item: any) {
  const enabledHosts = item.hosts.filter((host: any) => host.enabled)
  const variableCount = Object.keys(item.variables_json || {}).length + item.groups.reduce((total: number, group: any) => {
    return total + Object.keys(group.variables_json || {}).length
  }, 0)

  let readiness = 'review'
  let readinessNote = 'Inventory exists but needs more context.'

  if (item.hosts.length && enabledHosts.length) {
    readiness = 'ready'
    readinessNote = 'Usable for operator targeting.'
  }
  if (!item.hosts.length) {
    readiness = 'incomplete'
    readinessNote = 'No hosts are assigned yet.'
  }
  if (item.hosts.length && !enabledHosts.length) {
    readiness = 'disabled'
    readinessNote = 'All hosts are currently disabled.'
  }

  return {
    ...item,
    host_count: item.hosts.length,
    enabled_host_count: enabledHosts.length,
    group_count: item.groups.length,
    variable_count: variableCount,
    readiness,
    readiness_note: readinessNote,
  }
}

async function load() {
  isLoading.value = true
  try {
    const response = await api.get('/inventories')
    rows.value = response.data.data.map(normalizeRow)
  } catch {
    app.pushToast('Inventory data could not be loaded', 'error', 'Check API reachability and refresh the inventory workspace.')
  } finally {
    isLoading.value = false
  }
}

function resetForm() {
  selectedId.value = null
  form.name = ''
  form.description = ''
  varsText.value = '{}'
  hostsText.value = '[]'
  groupsText.value = '[]'
}

function openCreate() {
  resetForm()
  showCreate.value = true
}

function openEdit(row: any) {
  selectedId.value = row.id
  form.name = row.name
  form.description = row.description || ''
  varsText.value = JSON.stringify(row.variables_json || {}, null, 2)
  hostsText.value = JSON.stringify(
    row.hosts.map((host: any) => ({
      name: host.name,
      address: host.address,
      description: host.description,
      variables: host.variables_json,
      enabled: host.enabled,
      groups: host.groups,
    })),
    null,
    2,
  )
  groupsText.value = JSON.stringify(
    row.groups.map((group: any) => ({
      name: group.name,
      description: group.description,
      variables: group.variables_json,
      children: group.children,
    })),
    null,
    2,
  )
  showCreate.value = true
}

function closeDrawer() {
  if (isSaving.value) return
  showCreate.value = false
  resetForm()
}

async function saveInventory() {
  isSaving.value = true
  try {
    const payload = {
      name: form.name,
      description: form.description,
      variables: JSON.parse(varsText.value || '{}'),
      hosts: JSON.parse(hostsText.value || '[]'),
      groups: JSON.parse(groupsText.value || '[]'),
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

async function removeInventory(row: any) {
  if (!window.confirm(`Delete inventory "${row.name}"?`)) return
  try {
    await api.delete(`/inventories/${row.id}`)
    app.pushToast('Inventory deleted', 'success')
    await load()
  } catch (error: any) {
    app.pushToast(error?.response?.data?.message || 'Inventory could not be deleted', 'error')
  }
}

onMounted(load)
</script>
