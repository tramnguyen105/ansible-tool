<template>
  <div>
    <PageHeader title="Inventory" eyebrow="Managed Targets" description="Shape clean execution targets, review readiness before operators run jobs, and keep imported data normalized.">
      <button class="btn-secondary" :disabled="isSaving" @click="openCreate">New inventory</button>
      <button class="btn-primary" :disabled="isSaving" @click="showImport = true">Import inventory</button>
    </PageHeader>

    <div class="grid gap-4 xl:grid-cols-4">
      <CardStat label="Inventories" :value="stats.inventories" tone="cataloged" :helper="stats.inventories ? 'Matching inventory objects available.' : 'No inventories match the current filters.'" />
      <CardStat label="Hosts" :value="stats.hosts" tone="reachable" :helper="stats.hosts ? `${stats.enabled_hosts} enabled for targeting.` : 'Add hosts manually or import a source file.'" />
      <CardStat label="Groups" :value="stats.groups" tone="organized" :helper="stats.groups ? 'Scoped host collections are available.' : 'Define groups to make job targeting safer.'" />
      <CardStat label="Variable scopes" :value="stats.variable_bearing" tone="templated" :helper="stats.variable_bearing ? 'Inventories include inventory or group variables.' : 'No scoped variables defined yet.'" />
    </div>

    <section class="mt-6 rounded-3xl border border-console-edge bg-console-panel/80 p-5 shadow-xl shadow-slate-300/25">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p class="text-xs uppercase tracking-[0.22em] text-console-glow">Inventory Workspace</p>
          <h3 class="mt-2 text-xl font-semibold text-slate-900">Catalog, validate, and prepare target sets</h3>
          <p class="mt-2 max-w-3xl text-sm leading-6 text-console-muted">Keep manual and imported inventories searchable, inspect readiness before operators use them, and edit membership with a guided workflow instead of raw payloads.</p>
        </div>
        <div class="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          <input v-model="search" :disabled="isLoading" placeholder="Search inventory name" />
          <select v-model="sourceFilter" :disabled="isLoading">
            <option value="all">All sources</option>
            <option value="manual">Manual</option>
            <option value="import">Import</option>
          </select>
          <select v-model="readinessFilter" :disabled="isLoading">
            <option value="all">All readiness</option>
            <option value="ready">Ready</option>
            <option value="incomplete">Incomplete</option>
            <option value="disabled">Disabled</option>
            <option value="review">Needs review</option>
          </select>
          <button class="btn-secondary" :disabled="isLoading" @click="load">{{ isLoading ? 'Refreshing...' : 'Refresh workspace' }}</button>
        </div>
      </div>
    </section>

    <div class="mt-6 grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
      <DataTable
        title="Inventory catalog"
        description="Sortable inventory list with source, readiness, and variable coverage."
        :columns="columns"
        :rows="rows"
        :loading="isLoading"
        :error="Boolean(queryError)"
        :sort-by="sortBy"
        :sort-order="sortOrder as 'asc' | 'desc'"
        loading-title="Loading inventory catalog"
        loading-description="Collecting inventory summaries, host counts, and readiness metadata."
        error-title="Inventory data is unavailable"
        error-description="The inventory query failed. Retry the request or adjust the current filters."
        empty-title="No inventory matches your filters"
        empty-description="Create a new inventory manually or import a source file to seed the workspace."
        @retry="load"
        @sort="handleSort"
      >
        <template #name="{ row }">
          <button class="text-left" @click="inspectInventory(row)">
            <p class="font-medium text-slate-900">{{ row.name }}</p>
            <p class="mt-1 text-xs text-console-muted">{{ row.description || 'No description provided' }}</p>
          </button>
        </template>
        <template #source_type="{ row }"><StatusBadge :value="row.source_type" /></template>
        <template #hosts="{ row }"><div><p class="text-slate-900">{{ row.host_count }} hosts</p><p class="mt-1 text-xs text-console-muted">{{ row.enabled_host_count }} enabled</p></div></template>
        <template #groups="{ row }"><div><p class="text-slate-900">{{ row.group_count }} groups</p><p class="mt-1 text-xs text-console-muted">{{ row.variable_count }} variable scopes</p></div></template>
        <template #readiness="{ row }"><div><StatusBadge :value="row.readiness" /><p class="mt-2 text-xs text-console-muted">{{ row.readiness_note }}</p></div></template>
        <template #actions="{ row }">
          <div class="flex justify-end gap-3 text-sm">
            <button class="text-console-glow transition hover:text-slate-900" :disabled="isSaving" @click="inspectInventory(row)">Review</button>
            <button class="text-console-glow transition hover:text-slate-900" :disabled="isSaving" @click="openEdit(row)">Edit</button>
            <button class="text-rose-500 transition hover:text-rose-700 disabled:opacity-50" :disabled="isSaving" @click="promptDelete(row)">Delete</button>
          </div>
        </template>
        <template #footer>
          <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p class="text-sm text-slate-600">Showing {{ rows.length ? offset + 1 : 0 }}-{{ offset + rows.length }} of {{ totalInventories }} inventories</p>
            <div class="flex items-center gap-2">
              <button class="btn-secondary" :disabled="isLoading || page <= 1" @click="goToPreviousPage">Previous</button>
              <span class="text-sm text-slate-500">Page {{ page }}</span>
              <button class="btn-secondary" :disabled="isLoading || !hasMore" @click="goToNextPage">Next</button>
            </div>
          </div>
        </template>
      </DataTable>

      <section class="rounded-3xl border border-console-edge bg-white p-5 shadow-lg shadow-slate-200/40">
        <div class="flex items-start justify-between gap-3">
          <div>
            <p class="text-xs uppercase tracking-[0.18em] text-console-glow">Review Panel</p>
            <h3 class="mt-2 text-xl font-semibold text-slate-900">{{ activeSummary?.name || 'Select an inventory' }}</h3>
            <p class="mt-2 text-sm leading-6 text-console-muted">{{ activeSummary?.description || 'Choose an inventory from the catalog to review source, members, variable coverage, and current usage.' }}</p>
          </div>
          <StatusBadge v-if="activeSummary" :value="activeSummary.readiness" />
        </div>

        <div v-if="activeSummary" class="mt-5 space-y-5">
          <div class="grid gap-3 sm:grid-cols-2">
            <div class="rounded-2xl border border-console-edge/80 bg-console-deep/40 p-4"><p class="text-xs uppercase tracking-[0.14em] text-console-muted">Source</p><p class="mt-2 text-lg font-semibold text-slate-900">{{ activeSummary.source_type }}</p></div>
            <div class="rounded-2xl border border-console-edge/80 bg-console-deep/40 p-4"><p class="text-xs uppercase tracking-[0.14em] text-console-muted">Readiness note</p><p class="mt-2 text-sm font-medium text-slate-900">{{ activeSummary.readiness_note }}</p></div>
          </div>
          <div class="grid gap-3 sm:grid-cols-3">
            <div class="rounded-2xl border border-console-edge/80 p-4"><p class="text-xs uppercase tracking-[0.14em] text-console-muted">Hosts</p><p class="mt-2 text-2xl font-semibold text-slate-900">{{ activeSummary.host_count }}</p><p class="mt-1 text-xs text-console-muted">{{ activeSummary.enabled_host_count }} enabled</p></div>
            <div class="rounded-2xl border border-console-edge/80 p-4"><p class="text-xs uppercase tracking-[0.14em] text-console-muted">Groups</p><p class="mt-2 text-2xl font-semibold text-slate-900">{{ activeSummary.group_count }}</p></div>
            <div class="rounded-2xl border border-console-edge/80 p-4"><p class="text-xs uppercase tracking-[0.14em] text-console-muted">Variable scopes</p><p class="mt-2 text-2xl font-semibold text-slate-900">{{ activeSummary.variable_count }}</p></div>
          </div>
          <div v-if="activeDetailLoading" class="rounded-2xl border border-dashed border-console-edge bg-console-deep/30 px-4 py-6 text-sm text-console-muted">Loading inventory detail...</div>
          <template v-else-if="activeDetail">
            <div class="rounded-2xl border border-console-edge/80 p-4">
              <div class="flex items-center justify-between gap-3"><h4 class="text-sm font-semibold uppercase tracking-[0.14em] text-console-muted">Hosts</h4><span class="text-xs text-console-muted">{{ activeDetail.hosts.length }} total</span></div>
              <div class="mt-3 space-y-2">
                <div v-for="host in activeDetail.hosts.slice(0, 5)" :key="host.id || host.name" class="flex items-start justify-between gap-3 rounded-xl bg-console-deep/30 px-3 py-2">
                  <div><p class="text-sm font-medium text-slate-900">{{ host.name }}</p><p class="text-xs text-console-muted">{{ host.address || 'No address recorded' }}</p></div>
                  <span class="text-xs text-console-muted">{{ host.groups.join(', ') || 'No groups' }}</span>
                </div>
              </div>
            </div>
            <div class="rounded-2xl border border-console-edge/80 p-4">
              <div class="flex items-center justify-between gap-3"><h4 class="text-sm font-semibold uppercase tracking-[0.14em] text-console-muted">Groups</h4><span class="text-xs text-console-muted">{{ activeDetail.groups.length }} total</span></div>
              <div class="mt-3 space-y-2">
                <div v-for="group in activeDetail.groups.slice(0, 5)" :key="group.id || group.name" class="rounded-xl bg-console-deep/30 px-3 py-2">
                  <p class="text-sm font-medium text-slate-900">{{ group.name }}</p>
                  <p class="mt-1 text-xs text-console-muted">{{ group.children.join(', ') || 'No child groups' }}</p>
                </div>
              </div>
            </div>
          </template>
          <div class="flex flex-wrap gap-2">
            <button class="btn-secondary" :disabled="isSaving || !activeSummary" @click="activeSummary && inspectInventory(activeSummary)">Refresh detail</button>
            <button class="btn-primary" :disabled="isSaving || !activeSummary" @click="activeSummary && openEdit(activeSummary)">Edit inventory</button>
          </div>
        </div>
      </section>
    </div>

    <InventoryImportWizard :open="showImport" @close="showImport = false" @saved="refreshWorkspace" />
    <DrawerPanel :open="showDeleteConfirm" title="Delete inventory" @close="closeDeleteConfirm">
      <div class="space-y-4">
        <p class="text-sm text-console-muted">Deleting <span class="font-medium text-slate-900">{{ deleteCandidate?.name }}</span> is permanent. This inventory is referenced by {{ deleteUsage.schedules_total }} schedules ({{ deleteUsage.schedules_enabled }} enabled) and {{ deleteUsage.jobs_total }} jobs ({{ deleteUsage.jobs_active }} active).</p>
        <div><label class="field-label">Type inventory name to confirm</label><input v-model="deleteConfirmText" :disabled="isSaving" placeholder="Inventory name" /></div>
        <div class="flex justify-end gap-2">
          <button class="btn-secondary" :disabled="isSaving" @click="closeDeleteConfirm">Cancel</button>
          <button class="btn-primary" :disabled="isSaving || deleteConfirmText !== (deleteCandidate?.name || '')" @click="removeInventory">{{ isSaving ? 'Deleting...' : 'Delete inventory' }}</button>
        </div>
      </div>
    </DrawerPanel>

    <DrawerPanel :open="showEditor" :title="selectedId ? 'Edit inventory' : 'Create inventory'" @close="closeEditor">
      <div class="space-y-5">
        <BannerNotice title="Guided workflow" tone="info" text="Build inventory in structured steps first. Advanced JSON is available for bulk edits, but the guided editor is the primary path." />
        <div class="grid gap-2 sm:grid-cols-4">
          <button v-for="step in editorSteps" :key="step.key" class="rounded-2xl border px-3 py-3 text-left transition" :class="editorStep === step.key ? 'border-console-glow bg-console-glow/10 text-slate-900' : 'border-console-edge text-console-muted hover:border-console-glow/40'" @click="editorStep = step.key">
            <p class="text-xs uppercase tracking-[0.14em]">{{ step.eyebrow }}</p><p class="mt-2 text-sm font-semibold">{{ step.label }}</p>
          </button>
        </div>

        <div v-if="editorStep === 'basics'" class="space-y-4">
          <div><label class="field-label">Name</label><input v-model="form.name" :disabled="isSaving" placeholder="Core WAN routers" /></div>
          <div><label class="field-label">Description</label><textarea v-model="form.description" :disabled="isSaving" placeholder="Operator-facing context for when this inventory should be used."></textarea></div>
          <div><label class="field-label">Inventory variables</label><textarea v-model="varsText" :disabled="isSaving" placeholder='{"ansible_network_os":"cisco.ios.ios"}'></textarea></div>
        </div>

        <div v-else-if="editorStep === 'hosts'" class="space-y-4">
          <div class="flex items-center justify-between"><div><h4 class="text-sm font-semibold uppercase tracking-[0.14em] text-console-muted">Hosts</h4><p class="mt-1 text-sm text-console-muted">Add only the hosts operators should target from this inventory.</p></div><button class="btn-secondary" :disabled="isSaving" @click="addHost">Add host</button></div>
          <div v-if="!formHosts.length" class="rounded-2xl border border-dashed border-console-edge bg-console-deep/30 px-4 py-6 text-sm text-console-muted">No hosts added yet. Add hosts manually or use the advanced tab for bulk JSON editing.</div>
          <div v-for="(host, index) in formHosts" :key="`host-${index}`" class="space-y-3 rounded-2xl border border-console-edge/80 p-4">
            <div class="grid gap-3 md:grid-cols-2"><input v-model="host.name" :disabled="isSaving" placeholder="Host name" /><input v-model="host.address" :disabled="isSaving" placeholder="Management IP / hostname" /></div>
            <textarea v-model="host.description" :disabled="isSaving" placeholder="Optional host description"></textarea>
            <div class="grid gap-3 md:grid-cols-2"><input v-model="host.groupsText" :disabled="isSaving" placeholder="Groups (comma separated)" /><textarea v-model="host.variablesText" :disabled="isSaving" placeholder='{"role":"edge"}'></textarea></div>
            <label class="flex items-center gap-2 text-sm text-console-muted"><input v-model="host.enabled" :disabled="isSaving" type="checkbox" class="w-auto" />Enabled for targeting</label>
            <button class="text-rose-500 transition hover:text-rose-700" :disabled="isSaving" @click="removeHost(index)">Remove host</button>
          </div>
        </div>

        <div v-else-if="editorStep === 'groups'" class="space-y-4">
          <div class="flex items-center justify-between"><div><h4 class="text-sm font-semibold uppercase tracking-[0.14em] text-console-muted">Groups</h4><p class="mt-1 text-sm text-console-muted">Use groups to create safer, reusable operator targeting scopes.</p></div><button class="btn-secondary" :disabled="isSaving" @click="addGroup">Add group</button></div>
          <div v-if="!formGroups.length" class="rounded-2xl border border-dashed border-console-edge bg-console-deep/30 px-4 py-6 text-sm text-console-muted">No groups defined yet. Add groups for region, role, or maintenance scope.</div>
          <div v-for="(group, index) in formGroups" :key="`group-${index}`" class="space-y-3 rounded-2xl border border-console-edge/80 p-4">
            <input v-model="group.name" :disabled="isSaving" placeholder="Group name" />
            <textarea v-model="group.description" :disabled="isSaving" placeholder="Optional group description"></textarea>
            <div class="grid gap-3 md:grid-cols-2"><input v-model="group.childrenText" :disabled="isSaving" placeholder="Child groups (comma separated)" /><textarea v-model="group.variablesText" :disabled="isSaving" placeholder='{"site":"dc1"}'></textarea></div>
            <button class="text-rose-500 transition hover:text-rose-700" :disabled="isSaving" @click="removeGroup(index)">Remove group</button>
          </div>
        </div>

        <div v-else class="space-y-4">
          <div class="flex items-start justify-between gap-3"><div><h4 class="text-sm font-semibold uppercase tracking-[0.14em] text-console-muted">Advanced JSON</h4><p class="mt-1 text-sm text-console-muted">Use this only for bulk or highly structured edits. Guided fields remain the default workflow.</p></div><button class="btn-secondary" :disabled="isSaving" @click="syncAdvancedFromGuided">Refresh from guided fields</button></div>
          <div><label class="field-label">Hosts JSON array</label><textarea v-model="hostsText" :disabled="isSaving" placeholder='[{"name":"edge-rtr-01","address":"10.0.0.10","groups":["wan"]}]'></textarea></div>
          <div><label class="field-label">Groups JSON array</label><textarea v-model="groupsText" :disabled="isSaving" placeholder='[{"name":"wan","children":[]}]'></textarea></div>
        </div>

        <section class="rounded-2xl border border-console-edge/80 bg-console-deep/30 p-4">
          <p class="text-xs uppercase tracking-[0.14em] text-console-muted">Editor summary</p>
          <div class="mt-3 grid gap-3 sm:grid-cols-3">
            <div><p class="text-sm font-semibold text-slate-900">{{ formHosts.length }}</p><p class="text-xs text-console-muted">Hosts configured</p></div>
            <div><p class="text-sm font-semibold text-slate-900">{{ formGroups.length }}</p><p class="text-xs text-console-muted">Groups configured</p></div>
            <div><p class="text-sm font-semibold text-slate-900">{{ selectedId ? 'Edit mode' : 'New inventory' }}</p><p class="text-xs text-console-muted">Workflow state</p></div>
          </div>
        </section>

        <div class="flex justify-end gap-2">
          <button class="btn-secondary" :disabled="isSaving" @click="closeEditor">Cancel</button>
          <button class="btn-primary" :disabled="isSaving" @click="saveInventory">{{ isSaving ? 'Saving...' : selectedId ? 'Save changes' : 'Create inventory' }}</button>
        </div>
      </div>
    </DrawerPanel>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'

import { inventoryApi, type InventoryDetail, type InventoryGroupRecord, type InventoryHostRecord, type InventorySummaryItem, type InventorySummaryStats } from '../../api/inventory'
import BannerNotice from '../../components/common/BannerNotice.vue'
import CardStat from '../../components/common/CardStat.vue'
import DataTable from '../../components/common/DataTable.vue'
import DrawerPanel from '../../components/common/DrawerPanel.vue'
import PageHeader from '../../components/common/PageHeader.vue'
import StatusBadge from '../../components/common/StatusBadge.vue'
import InventoryImportWizard from '../../components/wizards/InventoryImportWizard.vue'
import { useListQueryState } from '../../composables/useListQueryState'
import { usePagedCollection } from '../../composables/usePagedCollection'
import { useAppStore } from '../../stores/app'

type InventoryRow = InventorySummaryItem & { variable_count: number }
type InventoryMeta = { stats: InventorySummaryStats }
type GuidedHost = { name: string; address: string; description: string; variablesText: string; enabled: boolean; groupsText: string }
type GuidedGroup = { name: string; description: string; variablesText: string; childrenText: string }

const app = useAppStore()
const showImport = ref(false)
const showEditor = ref(false)
const showDeleteConfirm = ref(false)
const selectedId = ref<string | null>(null)
const editorStep = ref<'basics' | 'hosts' | 'groups' | 'advanced'>('basics')
const isSaving = ref(false)
const queryError = ref<unknown>(null)
const activeSummary = ref<InventoryRow | null>(null)
const activeDetail = ref<InventoryDetail | null>(null)
const activeDetailLoading = ref(false)
const deleteCandidate = ref<InventoryRow | null>(null)
const deleteConfirmText = ref('')
const deleteUsage = reactive({ schedules_total: 0, schedules_enabled: 0, jobs_total: 0, jobs_active: 0 })
const form = reactive({ name: '', description: '' })
const varsText = ref('{}')
const hostsText = ref('[]')
const groupsText = ref('[]')
const formHosts = ref<GuidedHost[]>([])
const formGroups = ref<GuidedGroup[]>([])
const editorSteps = [
  { key: 'basics', label: 'Basics', eyebrow: 'Step 1' },
  { key: 'hosts', label: 'Hosts', eyebrow: 'Step 2' },
  { key: 'groups', label: 'Groups', eyebrow: 'Step 3' },
  { key: 'advanced', label: 'Advanced JSON', eyebrow: 'Optional' },
] as const

const { search, sortBy, sortOrder, page, offset: routeOffset, filters, setSort, setPage } = useListQueryState({
  pageSize: 10,
  search: { key: 'search', defaultValue: '' },
  filters: [{ key: 'source', defaultValue: 'all' }, { key: 'readiness', defaultValue: 'all' }],
  sortBy: { key: 'sortBy', defaultValue: 'name' },
  sortOrder: { key: 'sortOrder', defaultValue: 'asc' },
})

const sourceFilter = filters.source
const readinessFilter = filters.readiness
const columns = [
  { key: 'name', label: 'Inventory', sortable: true },
  { key: 'source_type', label: 'Source', sortable: true },
  { key: 'hosts', label: 'Hosts' },
  { key: 'groups', label: 'Groups' },
  { key: 'readiness', label: 'Readiness' },
]

const { items: rows, isLoading, total: totalInventories, hasMore, offset, meta, load: baseLoad, refreshFromStart } = usePagedCollection<InventoryRow, InventoryMeta>({
  pageSize: 10,
  watchSources: [search, sourceFilter, readinessFilter, sortBy, sortOrder],
  onError: (error) => {
    queryError.value = error
    app.pushToast('Inventory data could not be loaded', 'error', 'Check API reachability and refresh the inventory workspace.')
  },
  query: async ({ limit, offset }) => {
    const params: Record<string, string | number | string[]> = { limit, offset, sort_by: sortBy.value, sort_order: sortOrder.value }
    if (search.value.trim()) params.search = search.value.trim()
    if (sourceFilter.value !== 'all') params.source_types = [sourceFilter.value]
    if (readinessFilter.value !== 'all') params.readiness = [readinessFilter.value]
    const response = await inventoryApi.querySummary(params)
    return { ...response.data.data, items: response.data.data.items.map((item: InventorySummaryItem) => ({ ...item, variable_count: item.variable_scope_count || 0 })) }
  },
})

const stats = computed<InventorySummaryStats>(() => meta.value.stats || { inventories: 0, hosts: 0, enabled_hosts: 0, groups: 0, variable_bearing: 0 })

async function load() {
  queryError.value = null
  await baseLoad().catch(() => undefined)
}

async function refreshWorkspace() {
  await refreshFromStart()
  if (activeSummary.value) {
    const match = rows.value.find((row) => row.id === activeSummary.value?.id)
    activeSummary.value = match || null
    if (match) await inspectInventory(match)
  }
}

function handleSort(key: string) { setSort(key) }
function goToNextPage() { if (!hasMore.value) return; setPage(page.value + 1); return load() }
function goToPreviousPage() { if (page.value <= 1) return; setPage(page.value - 1); return load() }
function resetForm() { selectedId.value = null; editorStep.value = 'basics'; form.name = ''; form.description = ''; varsText.value = '{}'; hostsText.value = '[]'; groupsText.value = '[]'; formHosts.value = []; formGroups.value = [] }
function openCreate() { resetForm(); showEditor.value = true }

function safeParseJson(text: string, fallback: unknown = {}) { return JSON.parse(text || JSON.stringify(fallback)) }

function syncAdvancedFromGuided() {
  hostsText.value = JSON.stringify(formHosts.value.filter((host) => host.name.trim()).map((host) => ({
    name: host.name.trim(),
    address: host.address.trim() || null,
    description: host.description.trim() || null,
    variables: safeParseJson(host.variablesText || '{}'),
    enabled: Boolean(host.enabled),
    groups: host.groupsText.split(',').map((item) => item.trim()).filter(Boolean),
  })), null, 2)
  groupsText.value = JSON.stringify(formGroups.value.filter((group) => group.name.trim()).map((group) => ({
    name: group.name.trim(),
    description: group.description.trim() || null,
    variables: safeParseJson(group.variablesText || '{}'),
    children: group.childrenText.split(',').map((item) => item.trim()).filter(Boolean),
  })), null, 2)
}

function populateForm(detail: InventoryDetail) {
  selectedId.value = detail.id
  form.name = detail.name
  form.description = detail.description || ''
  varsText.value = JSON.stringify(detail.variables_json || {}, null, 2)
  formHosts.value = detail.hosts.map((host) => ({ name: host.name || '', address: host.address || '', description: host.description || '', enabled: host.enabled !== false, groupsText: (host.groups || []).join(', '), variablesText: JSON.stringify(host.variables_json || host.variables || {}, null, 2) }))
  formGroups.value = detail.groups.map((group) => ({ name: group.name || '', description: group.description || '', childrenText: (group.children || []).join(', '), variablesText: JSON.stringify(group.variables_json || group.variables || {}, null, 2) }))
  syncAdvancedFromGuided()
}

async function inspectInventory(row: InventoryRow) {
  activeSummary.value = row
  activeDetailLoading.value = true
  try {
    const response = await inventoryApi.get(row.id)
    activeDetail.value = response.data.data
  } catch (error: any) {
    activeDetail.value = null
    app.pushToast(error?.response?.data?.message || 'Inventory details could not be loaded', 'error')
  } finally {
    activeDetailLoading.value = false
  }
}

async function openEdit(row: InventoryRow) {
  activeDetailLoading.value = true
  try {
    const response = await inventoryApi.get(row.id)
    const detail = response.data.data as InventoryDetail
    activeSummary.value = row
    activeDetail.value = detail
    populateForm(detail)
    showEditor.value = true
  } catch (error: any) {
    app.pushToast(error?.response?.data?.message || 'Inventory details could not be loaded', 'error')
  } finally {
    activeDetailLoading.value = false
  }
}

function closeEditor() { if (isSaving.value) return; showEditor.value = false; resetForm() }
function addHost() { formHosts.value.push({ name: '', address: '', description: '', variablesText: '{}', enabled: true, groupsText: '' }) }
function removeHost(index: number) { formHosts.value.splice(index, 1); syncAdvancedFromGuided() }
function addGroup() { formGroups.value.push({ name: '', description: '', variablesText: '{}', childrenText: '' }) }
function removeGroup(index: number) { formGroups.value.splice(index, 1); syncAdvancedFromGuided() }

function buildPayload() {
  if (editorStep.value !== 'advanced') syncAdvancedFromGuided()
  return {
    name: form.name.trim(),
    description: form.description.trim() || null,
    variables: safeParseJson(varsText.value || '{}'),
    hosts: safeParseJson(hostsText.value || '[]', []) as InventoryHostRecord[],
    groups: safeParseJson(groupsText.value || '[]', []) as InventoryGroupRecord[],
  }
}

async function saveInventory() {
  isSaving.value = true
  try {
    const payload = buildPayload()
    if (!payload.name) { app.pushToast('Inventory name is required', 'error'); return }
    if (selectedId.value) {
      await inventoryApi.update(selectedId.value, payload)
      app.pushToast('Inventory updated', 'success', 'The inventory record has been updated.')
    } else {
      await inventoryApi.create(payload)
      app.pushToast('Inventory created', 'success', 'The inventory is now available for operator targeting.')
    }
    closeEditor()
    await refreshWorkspace()
  } catch (error: any) {
    if (error instanceof SyntaxError) {
      app.pushToast('Inventory JSON input is invalid', 'error', 'Correct the invalid JSON before saving.')
      return
    }
    app.pushToast(error?.response?.data?.message || 'Inventory could not be saved', 'error')
  } finally {
    isSaving.value = false
  }
}

async function promptDelete(row: InventoryRow) {
  deleteCandidate.value = row
  deleteConfirmText.value = ''
  try {
    const response = await inventoryApi.getUsage(row.id)
    Object.assign(deleteUsage, response.data.data)
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
  Object.assign(deleteUsage, { schedules_total: 0, schedules_enabled: 0, jobs_total: 0, jobs_active: 0 })
}

async function removeInventory() {
  if (!deleteCandidate.value) return
  isSaving.value = true
  try {
    await inventoryApi.remove(deleteCandidate.value.id)
    app.pushToast('Inventory deleted', 'success')
    closeDeleteConfirm()
    await refreshWorkspace()
  } catch (error: any) {
    app.pushToast(error?.response?.data?.message || 'Inventory could not be deleted', 'error')
  } finally {
    isSaving.value = false
  }
}

watch(routeOffset, (nextOffset) => { offset.value = nextOffset }, { immediate: true })
watch(rows, async (currentRows) => {
  if (!currentRows.length) { activeSummary.value = null; activeDetail.value = null; return }
  if (!activeSummary.value || !currentRows.some((row) => row.id === activeSummary.value?.id)) await inspectInventory(currentRows[0])
})

onMounted(load)
</script>
