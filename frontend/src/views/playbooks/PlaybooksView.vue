<template>
  <div>
    <PageHeader
      title="Playbooks"
      eyebrow="Execution Content"
      description="Manage validated playbooks, keep revision history visible, and make operator edits deliberate before they reach live jobs."
    >
      <button class="btn-secondary" :disabled="isLoading || isSaving || isValidating" @click="load">{{ isLoading ? 'Refreshing...' : 'Refresh' }}</button>
      <button class="btn-primary" :disabled="isSaving || isValidating" @click="openCreate">New playbook</button>
    </PageHeader>

    <div class="grid gap-4 xl:grid-cols-4">
      <CardStat label="Playbooks" :value="rows.length" tone="cataloged" :helper="rows.length ? 'Playbooks are available for execution.' : 'No playbooks have been created yet.'" />
      <CardStat label="Generated" :value="generatedCount" tone="generated" :helper="generatedCount ? 'Artifacts created by the CLI converter are present.' : 'No generated playbooks saved yet.'" />
      <CardStat label="Revisions" :value="revisionTotal" tone="history" :helper="revisionTotal ? 'Revision history is available for operator review.' : 'No revision history recorded yet.'" />
      <CardStat label="Recent updates" :value="recentCount" tone="yaml" :helper="recentCount ? 'Playbooks updated in the last 30 days.' : 'No playbook updated in the last 30 days.'" />
    </div>

    <section class="mt-6 rounded-3xl border border-console-edge bg-console-panel/80 p-5 shadow-xl shadow-slate-300/25">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p class="text-xs uppercase tracking-[0.22em] text-console-glow">Playbook Controls</p>
          <h3 class="mt-2 text-xl font-semibold text-slate-900">Playbook library</h3>
          <p class="mt-2 max-w-3xl text-sm leading-6 text-console-muted">
            Filter by source and freshness, validate YAML after edits, and keep revision context visible before scheduling production changes.
          </p>
        </div>
        <div class="grid gap-3 sm:grid-cols-2 lg:min-w-[420px] xl:grid-cols-3">
          <input v-model="search" :disabled="isLoading" placeholder="Search by playbook name" />
          <select v-model="sourceFilter" :disabled="isLoading">
            <option value="all">All sources</option>
            <option value="manual">Manual</option>
            <option value="generated">Generated</option>
          </select>
          <select v-model="updatedFilter" :disabled="isLoading">
            <option value="all">Any update time</option>
            <option value="7d">Updated in last 7 days</option>
            <option value="30d">Updated in last 30 days</option>
          </select>
        </div>
      </div>
    </section>

    <div class="mt-6">
      <DataTable
        title="Playbook library"
        description="Review source, revision depth, and recent notes before selecting a playbook for jobs or schedules."
        :columns="columns"
        :rows="filteredRows"
        :loading="isLoading"
        loading-title="Loading playbooks"
        loading-description="Collecting execution content summaries from the backend."
        :empty-title="hasActiveFilters ? 'No playbooks match your filters' : 'No playbooks saved'"
        :empty-description="hasActiveFilters
          ? 'Adjust filters to review additional playbooks.'
          : 'Create a playbook manually or save one from the CLI converter after reviewing output.'"
      >
        <template #name="{ row }">
          <div>
            <p class="font-medium text-slate-900">{{ row.name }}</p>
            <p class="mt-1 text-xs text-console-muted">{{ row.description || 'No description provided' }}</p>
          </div>
        </template>
        <template #source="{ row }">
          <StatusBadge :value="row.is_generated ? 'ready' : 'manual'" />
          <p class="mt-2 text-xs text-console-muted">{{ row.is_generated ? 'Generated from converter' : 'Authored manually' }}</p>
        </template>
        <template #revision_count="{ row }">
          <div>
            <p class="text-slate-900">{{ row.revision_count }} revisions</p>
            <p class="mt-1 text-xs text-console-muted">{{ row.last_change_note || 'No change note recorded yet.' }}</p>
          </div>
        </template>
        <template #updated_at="{ row }">
          <p class="text-sm text-console-muted">{{ formatDateTime(row.updated_at) }}</p>
        </template>
        <template #actions="{ row }">
          <div class="flex justify-end gap-3 text-sm">
            <button class="text-console-glow transition hover:text-slate-900" :disabled="isSaving || isValidating" @click="openEdit(row)">Edit</button>
            <button class="text-rose-300 transition hover:text-rose-200 disabled:opacity-50" :disabled="isSaving || isValidating" @click="promptDelete(row)">Delete</button>
          </div>
        </template>
      </DataTable>
    </div>

    <DrawerPanel :open="showDeleteConfirm" title="Delete playbook" @close="closeDeleteConfirm">
      <div class="space-y-4">
        <p class="text-sm text-console-muted">
          Deleting <span class="font-medium text-slate-900">{{ deleteCandidate?.name }}</span> is permanent.
          <span v-if="deleteUsage?.total">
            It is currently referenced by {{ deleteUsage.total }} jobs/schedules and cannot be deleted until those references are removed.
          </span>
        </p>
        <div class="grid gap-2 rounded-xl border border-console-edge bg-console-deep/40 p-3 text-xs text-console-muted">
          <p>Main jobs: {{ deleteUsage?.jobs_main || 0 }} · Main schedules: {{ deleteUsage?.schedules_main || 0 }}</p>
          <p>Pre-check jobs: {{ deleteUsage?.jobs_pre_check || 0 }} · Pre-check schedules: {{ deleteUsage?.schedules_pre_check || 0 }}</p>
          <p>Post-check jobs: {{ deleteUsage?.jobs_post_check || 0 }} · Post-check schedules: {{ deleteUsage?.schedules_post_check || 0 }}</p>
        </div>
        <div>
          <label class="field-label">Type playbook name to confirm</label>
          <input v-model="deleteConfirmText" :disabled="isSaving || Boolean(deleteUsage?.total)" placeholder="Playbook name" />
        </div>
        <div class="flex justify-end gap-2">
          <button class="btn-secondary" :disabled="isSaving" @click="closeDeleteConfirm">Cancel</button>
          <button
            class="btn-primary"
            :disabled="isSaving || Boolean(deleteUsage?.total) || deleteConfirmText !== (deleteCandidate?.name || '')"
            @click="removePlaybook"
          >
            {{ isSaving ? 'Deleting...' : 'Delete playbook' }}
          </button>
        </div>
      </div>
    </DrawerPanel>

    <DrawerPanel :open="showDrawer" :title="selectedId ? 'Edit playbook' : 'Create playbook'" @close="closeDrawer">
      <div class="space-y-4">
        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <label class="field-label">Name</label>
            <input v-model="form.name" :disabled="isSaving || isValidating" placeholder="IOS compliance check" />
          </div>
          <div>
            <label class="field-label">Description</label>
            <input v-model="form.description" :disabled="isSaving || isValidating" placeholder="Short operator-facing summary" />
          </div>
        </div>
        <div>
          <label class="field-label">Change Note</label>
          <input v-model="form.change_note" :disabled="isSaving || isValidating" :placeholder="selectedId ? 'Describe this edit' : 'Initial draft for lab validation'" />
        </div>
        <YamlEditor v-model="form.yaml_content" />
        <BannerNotice v-if="formError" title="Fix playbook form errors" tone="warn" :text="formError" />
        <BannerNotice
          v-if="validationMessage"
          :title="hasValidatedYaml ? 'YAML validation passed' : 'YAML validation required'"
          :tone="hasValidatedYaml ? 'info' : 'warn'"
          :text="validationMessage"
        />
        <BannerNotice
          title="Validation"
          :tone="hasValidatedYaml ? 'info' : 'warn'"
          :text="hasValidatedYaml
            ? 'YAML validated for current content. You can save safely.'
            : 'Run YAML validation after edits. Save is disabled until current content validates.'"
        />
        <div v-if="revisionPreview.length" class="rounded-2xl border border-console-edge bg-console-deep/40 p-4">
          <p class="text-xs uppercase tracking-[0.16em] text-console-glow">Recent revisions</p>
          <div class="mt-3 space-y-2 text-sm">
            <div v-for="revision in revisionPreview" :key="revision.id" class="flex items-start justify-between gap-4 text-console-muted">
              <p>v{{ revision.version }} · {{ revision.change_note || 'No note' }}</p>
              <p class="whitespace-nowrap">{{ formatDateTime(revision.created_at) }}</p>
            </div>
          </div>
        </div>
        <div class="flex justify-end gap-3">
          <button class="btn-secondary" :disabled="isValidating || isSaving" @click="validate">{{ isValidating ? 'Validating...' : 'Validate YAML' }}</button>
          <button class="btn-primary" :disabled="!canSave || isSaving || isValidating" @click="save">{{ isSaving ? 'Saving...' : selectedId ? 'Save changes' : 'Save playbook' }}</button>
        </div>
      </div>
    </DrawerPanel>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'

import api from '../../api/client'
import BannerNotice from '../../components/common/BannerNotice.vue'
import CardStat from '../../components/common/CardStat.vue'
import DataTable from '../../components/common/DataTable.vue'
import DrawerPanel from '../../components/common/DrawerPanel.vue'
import PageHeader from '../../components/common/PageHeader.vue'
import StatusBadge from '../../components/common/StatusBadge.vue'
import YamlEditor from '../../components/forms/YamlEditor.vue'
import { useAppStore } from '../../stores/app'
import { formatDateTime } from '../../utils/format'

const app = useAppStore()
const rows = ref<any[]>([])
const showDrawer = ref(false)
const showDeleteConfirm = ref(false)
const selectedId = ref<string | null>(null)
const selectedUpdatedAt = ref<string | null>(null)
const revisionPreview = ref<any[]>([])
const isLoading = ref(true)
const isValidating = ref(false)
const isSaving = ref(false)
const formError = ref('')
const validationMessage = ref('')
const hasValidatedYaml = ref(false)
const lastValidatedContent = ref('')
const baselineSnapshot = ref('')
const search = ref('')
const sourceFilter = ref('all')
const updatedFilter = ref('all')
const deleteCandidate = ref<any | null>(null)
const deleteUsage = ref<any | null>(null)
const deleteConfirmText = ref('')
const columns = [
  { key: 'name', label: 'Playbook' },
  { key: 'source', label: 'Source' },
  { key: 'revision_count', label: 'Revision history' },
  { key: 'updated_at', label: 'Last updated' },
]
const form = reactive<any>({
  name: '',
  description: '',
  yaml_content: '- hosts: all\n  gather_facts: false\n  tasks: []',
  is_generated: false,
  change_note: 'Initial draft',
})

const generatedCount = computed(() => rows.value.filter((item) => item.is_generated).length)
const revisionTotal = computed(() => rows.value.reduce((total, item) => total + item.revision_count, 0))
const recentCount = computed(() => rows.value.filter((item) => isWithinDays(item.updated_at, 30)).length)
const hasActiveFilters = computed(() => Boolean(search.value.trim() || sourceFilter.value !== 'all' || updatedFilter.value !== 'all'))
const filteredRows = computed(() => {
  return rows.value.filter((item) => {
    const matchesSearch = item.name.toLowerCase().includes(search.value.trim().toLowerCase())
    const matchesSource =
      sourceFilter.value === 'all' ||
      (sourceFilter.value === 'generated' && item.is_generated) ||
      (sourceFilter.value === 'manual' && !item.is_generated)
    const matchesUpdated =
      updatedFilter.value === 'all' ||
      (updatedFilter.value === '7d' && isWithinDays(item.updated_at, 7)) ||
      (updatedFilter.value === '30d' && isWithinDays(item.updated_at, 30))
    return matchesSearch && matchesSource && matchesUpdated
  })
})
const canSave = computed(() => Boolean(form.name.trim() && form.yaml_content.trim() && hasValidatedYaml.value))
const hasUnsavedChanges = computed(() => showDrawer.value && snapshotForm() !== baselineSnapshot.value)

watch(
  () => form.yaml_content,
  (value) => {
    if (value !== lastValidatedContent.value) {
      hasValidatedYaml.value = false
      if (!validationMessage.value || validationMessage.value.startsWith('YAML validated')) {
        validationMessage.value = 'YAML content changed. Validate again before saving.'
      }
    }
  },
)

function normalizeRow(item: any) {
  return {
    ...item,
    last_change_note: item.last_change_note || 'No change note recorded yet.',
  }
}

function snapshotForm() {
  return JSON.stringify({
    id: selectedId.value,
    name: form.name,
    description: form.description,
    yaml_content: form.yaml_content,
    change_note: form.change_note,
  })
}

function setBaseline() {
  baselineSnapshot.value = snapshotForm()
}

function resetForm() {
  selectedId.value = null
  selectedUpdatedAt.value = null
  form.name = ''
  form.description = ''
  form.yaml_content = '- hosts: all\n  gather_facts: false\n  tasks: []'
  form.is_generated = false
  form.change_note = 'Initial draft'
  revisionPreview.value = []
}

function resetValidationState() {
  formError.value = ''
  validationMessage.value = ''
  hasValidatedYaml.value = false
  lastValidatedContent.value = ''
}

function openCreate() {
  resetForm()
  resetValidationState()
  showDrawer.value = true
  setBaseline()
}

async function openEdit(row: any) {
  resetValidationState()
  selectedId.value = row.id
  selectedUpdatedAt.value = row.updated_at
  try {
    const response = await api.get(`/playbooks/${row.id}`)
    const detail = response.data.data
    form.name = detail.name
    form.description = detail.description || ''
    form.yaml_content = detail.yaml_content || ''
    form.is_generated = detail.is_generated
    form.change_note = 'Updated via GUI'
    revisionPreview.value = (detail.revisions || []).slice(0, 5)
    hasValidatedYaml.value = true
    lastValidatedContent.value = form.yaml_content
    validationMessage.value = 'Current YAML is from saved revision. Re-validate after making edits.'
    showDrawer.value = true
    setBaseline()
  } catch (error: any) {
    app.pushToast(error?.response?.data?.message || 'Playbook details could not be loaded', 'error')
  }
}

function closeDrawer() {
  if (isSaving.value || isValidating.value) return
  if (hasUnsavedChanges.value && !window.confirm('Discard unsaved changes to this playbook?')) return
  showDrawer.value = false
  resetForm()
  resetValidationState()
}

function closeDeleteConfirm() {
  if (isSaving.value) return
  showDeleteConfirm.value = false
  deleteCandidate.value = null
  deleteUsage.value = null
  deleteConfirmText.value = ''
}

function validateForm() {
  if (!form.name.trim()) return 'Playbook name is required.'
  if (!form.yaml_content.trim()) return 'YAML content is required.'
  if (!hasValidatedYaml.value) return 'Validate YAML after your latest edits before saving.'
  return ''
}

async function load() {
  isLoading.value = true
  try {
    const response = await api.get('/playbooks/summary')
    rows.value = response.data.data.map(normalizeRow)
  } catch {
    app.pushToast('Playbooks could not be loaded', 'error', 'Check API reachability and refresh the playbook library.')
  } finally {
    isLoading.value = false
  }
}

async function validate() {
  formError.value = ''
  if (!form.yaml_content.trim()) {
    formError.value = 'YAML content is required.'
    return
  }
  isValidating.value = true
  try {
    const response = await api.post('/playbooks/validate-yaml', { content: form.yaml_content })
    const errors = response.data?.data?.errors || []
    if (response.data?.data?.valid) {
      hasValidatedYaml.value = true
      lastValidatedContent.value = form.yaml_content
      validationMessage.value = 'YAML validated for current content.'
      app.pushToast('YAML is valid', 'success', 'The playbook syntax and structure parsed successfully.')
    } else {
      hasValidatedYaml.value = false
      validationMessage.value = errors.join('\n') || 'YAML validation failed.'
      app.pushToast('YAML validation failed', 'error', 'Fix validation errors before saving.')
    }
  } catch (error: any) {
    hasValidatedYaml.value = false
    const details = error?.response?.data?.data?.details
    validationMessage.value = (details?.errors || []).join('\n') || error?.response?.data?.message || 'YAML validation failed'
    app.pushToast(error?.response?.data?.message || 'YAML validation failed', 'error')
  } finally {
    isValidating.value = false
  }
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
      name: form.name.trim(),
      description: form.description.trim(),
      yaml_content: form.yaml_content,
      change_note: form.change_note.trim(),
      expected_updated_at: selectedUpdatedAt.value,
    }
    if (selectedId.value) {
      await api.put(`/playbooks/${selectedId.value}`, payload)
      app.pushToast('Playbook updated', 'success', 'The latest revision has been stored.')
    } else {
      await api.post('/playbooks', payload)
      app.pushToast('Playbook saved', 'success', 'The playbook is now available for job execution.')
    }
    closeDrawer()
    await load()
  } catch (error: any) {
    const code = error?.response?.data?.data?.code
    if (code === 'PLAYBOOK_EDIT_CONFLICT') {
      app.pushToast('Edit conflict detected', 'error', 'This playbook was updated by another operator. Refresh and retry.')
      await load()
    } else {
      app.pushToast(error?.response?.data?.message || 'Playbook could not be saved', 'error')
    }
  } finally {
    isSaving.value = false
  }
}

async function promptDelete(row: any) {
  deleteCandidate.value = row
  deleteUsage.value = null
  deleteConfirmText.value = ''
  showDeleteConfirm.value = true
  try {
    const usageResp = await api.get(`/playbooks/${row.id}/usage`)
    deleteUsage.value = usageResp.data.data
  } catch {
    deleteUsage.value = { jobs_main: 0, jobs_pre_check: 0, jobs_post_check: 0, schedules_main: 0, schedules_pre_check: 0, schedules_post_check: 0, total: 0 }
  }
}

async function removePlaybook() {
  if (!deleteCandidate.value) return
  if (deleteUsage.value?.total) return
  if (deleteConfirmText.value !== deleteCandidate.value.name) return
  try {
    await api.delete(`/playbooks/${deleteCandidate.value.id}`)
    app.pushToast('Playbook deleted', 'success')
    closeDeleteConfirm()
    await load()
  } catch (error: any) {
    const code = error?.response?.data?.data?.code
    if (code === 'PLAYBOOK_IN_USE') {
      deleteUsage.value = error?.response?.data?.data?.details || deleteUsage.value
      app.pushToast('Playbook is in use', 'error', 'Remove job/schedule references before deleting this playbook.')
      return
    }
    app.pushToast(error?.response?.data?.message || 'Playbook could not be deleted', 'error')
  }
}

function isWithinDays(timestamp: string | null | undefined, days: number) {
  if (!timestamp) return false
  const now = Date.now()
  const then = new Date(timestamp).getTime()
  if (Number.isNaN(then)) return false
  return now - then <= days * 24 * 60 * 60 * 1000
}

function handleBeforeUnload(event: BeforeUnloadEvent) {
  if (!hasUnsavedChanges.value) return
  event.preventDefault()
  event.returnValue = ''
}

onBeforeRouteLeave(() => {
  if (!hasUnsavedChanges.value) return true
  return window.confirm('You have unsaved playbook changes. Leave this page?')
})

onMounted(() => {
  window.addEventListener('beforeunload', handleBeforeUnload)
  load()
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload)
})
</script>
