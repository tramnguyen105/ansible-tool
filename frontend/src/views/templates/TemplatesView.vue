<template>
  <div>
    <PageHeader
      title="Templates"
      eyebrow="Reusable Config"
      description="Store reusable Jinja2 content for repeatable configuration rendering and generated artifacts from the CLI conversion workflow."
    >
      <button class="btn-secondary" :disabled="isLoading || isSaving" @click="load">{{ isLoading ? 'Refreshing...' : 'Refresh' }}</button>
      <button class="btn-primary" :disabled="isSaving" @click="openCreate">New template</button>
    </PageHeader>

    <div class="grid gap-4 xl:grid-cols-4">
      <CardStat label="Templates" :value="rows.length" tone="library" :helper="rows.length ? 'Reusable templates are available.' : 'No templates stored yet.'" />
      <CardStat label="Described" :value="describedCount" tone="documented" :helper="describedCount ? 'Templates include operator context.' : 'Descriptions should explain when to use a template.'" />
      <CardStat label="Generated" :value="generatedCount" tone="templated" :helper="generatedCount ? 'Templates created via CLI converter are tracked.' : 'No converter-generated templates yet.'" />
      <CardStat label="Recent updates" :value="recentCount" tone="reviewed" :helper="recentCount ? 'Templates updated in the last 30 days.' : 'No template updated in the last 30 days.'" />
    </div>

    <section class="mt-6 rounded-3xl border border-console-edge bg-console-panel/80 p-5 shadow-xl shadow-slate-300/25">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p class="text-xs uppercase tracking-[0.22em] text-console-glow">Template Controls</p>
          <h3 class="mt-2 text-xl font-semibold text-slate-900">Template library</h3>
          <p class="mt-2 max-w-3xl text-sm leading-6 text-console-muted">
            Keep template naming clear, metadata accurate, and syntax validated before reusing content across jobs and generated artifacts.
          </p>
        </div>
        <div class="grid gap-3 sm:grid-cols-2 lg:min-w-[420px] xl:grid-cols-3">
          <input v-model="search" :disabled="isLoading" placeholder="Search by template name" />
          <select v-model="sourceFilter" :disabled="isLoading">
            <option value="all">All sources</option>
            <option value="manual">Manual</option>
            <option value="converter">Converter</option>
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
        title="Template library"
        description="Review source, revision, and content preview before editing or reusing template artifacts."
        :columns="columns"
        :rows="filteredRows"
        :loading="isLoading"
        loading-title="Loading templates"
        loading-description="Collecting reusable template summaries and metadata from the backend."
        :empty-title="hasActiveFilters ? 'No templates match your current filters' : 'No templates saved'"
        :empty-description="hasActiveFilters
          ? 'Adjust or clear filters to review additional template artifacts.'
          : 'Create a reusable template or save one from the CLI conversion workflow after reviewing the generated content.'"
      >
        <template #name="{ row }">
          <div>
            <p class="font-medium text-slate-900">{{ row.name }}</p>
            <p class="mt-1 text-xs text-console-muted">{{ row.description || 'No description provided' }}</p>
          </div>
        </template>
        <template #source_type="{ row }">
          <StatusBadge :value="row.source_type === 'converter' ? 'ready' : 'manual'" />
          <p class="mt-2 text-xs text-console-muted">{{ row.source_type_label }}</p>
        </template>
        <template #revision="{ row }">
          <div>
            <p class="text-slate-900">v{{ row.revision }}</p>
            <p class="mt-1 text-xs text-console-muted">{{ formatDateTime(row.updated_at) }}</p>
          </div>
        </template>
        <template #preview="{ row }">
          <code class="block max-w-[420px] overflow-hidden text-ellipsis whitespace-nowrap text-xs text-console-muted">{{ row.preview || 'No preview available' }}</code>
        </template>
        <template #actions="{ row }">
          <div class="flex justify-end gap-3 text-sm">
            <button class="text-console-glow transition hover:text-slate-900" :disabled="isSaving" @click="openEdit(row)">Edit</button>
            <button class="text-rose-300 transition hover:text-rose-200 disabled:opacity-50" :disabled="isSaving" @click="promptDelete(row)">Delete</button>
          </div>
        </template>
      </DataTable>
    </div>

    <DrawerPanel :open="showDeleteConfirm" title="Delete template" @close="closeDeleteConfirm">
      <div class="space-y-4">
        <p class="text-sm text-console-muted">
          Deleting <span class="font-medium text-slate-900">{{ deleteCandidate?.name }}</span> is permanent.
          Source: {{ deleteCandidate?.source_type === 'converter' ? 'Converter generated' : 'Manual' }}.
          Revision: v{{ deleteCandidate?.revision || 1 }}.
          Last updated: {{ deleteCandidate?.updated_at ? formatDateTime(deleteCandidate.updated_at) : 'Unknown' }}.
        </p>
        <div>
          <label class="field-label">Type template name to confirm</label>
          <input v-model="deleteConfirmText" :disabled="isSaving" placeholder="Template name" />
        </div>
        <div class="flex justify-end gap-2">
          <button class="btn-secondary" :disabled="isSaving" @click="closeDeleteConfirm">Cancel</button>
          <button class="btn-primary" :disabled="isSaving || deleteConfirmText !== (deleteCandidate?.name || '')" @click="removeTemplate">
            {{ isSaving ? 'Deleting...' : 'Delete template' }}
          </button>
        </div>
      </div>
    </DrawerPanel>

    <DrawerPanel :open="showDrawer" :title="selectedId ? 'Edit template' : 'Create template'" @close="closeDrawer">
      <div class="space-y-4">
        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <label class="field-label">Name</label>
            <input v-model="form.name" :disabled="isSaving" placeholder="ios-interface-base.j2" />
          </div>
          <div>
            <label class="field-label">Description</label>
            <input v-model="form.description" :disabled="isSaving" placeholder="Reusable baseline for IOS interface configuration" />
          </div>
        </div>
        <div>
          <label class="field-label">Template Content</label>
          <textarea v-model="form.content" :disabled="isSaving" class="min-h-[280px] font-mono" placeholder="interface {{ interface_name }}"></textarea>
        </div>
        <div class="flex items-center justify-between gap-3 rounded-2xl border border-console-edge bg-console-deep/40 px-4 py-3">
          <p class="text-sm text-console-muted">
            Source: <span class="text-slate-900">{{ selectedSourceLabel }}</span>
            <span v-if="selectedRevisionLabel"> · Revision {{ selectedRevisionLabel }}</span>
          </p>
          <button class="btn-secondary" :disabled="isSaving || !form.content.trim()" @click="validateTemplateContent">
            {{ isValidating ? 'Validating...' : 'Validate template' }}
          </button>
        </div>
        <BannerNotice v-if="formError" title="Fix template form errors" tone="warn" :text="formError" />
        <BannerNotice v-if="validationMessage" :title="validationTone === 'info' ? 'Template syntax valid' : 'Template syntax invalid'" :tone="validationTone" :text="validationMessage" />
        <BannerNotice
          title="Template guidance"
          tone="info"
          text="Keep generated and hand-authored templates parameterized. If a template only fits one device, it should probably remain a playbook instead."
        />
        <div class="flex justify-end gap-2">
          <button class="btn-secondary" :disabled="isSaving" @click="closeDrawer">Cancel</button>
          <button class="btn-primary" :disabled="isSaving" @click="save">{{ isSaving ? 'Saving...' : selectedId ? 'Save changes' : 'Save template' }}</button>
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
import { useAppStore } from '../../stores/app'
import { formatDateTime } from '../../utils/format'

const app = useAppStore()
const rows = ref<any[]>([])
const showDrawer = ref(false)
const showDeleteConfirm = ref(false)
const selectedId = ref<string | null>(null)
const selectedSource = ref<'manual' | 'converter'>('manual')
const selectedRevision = ref<number>(1)
const isLoading = ref(true)
const isSaving = ref(false)
const isValidating = ref(false)
const formError = ref('')
const validationMessage = ref('')
const validationTone = ref<'info' | 'warn'>('info')
const search = ref('')
const sourceFilter = ref('all')
const updatedFilter = ref('all')
const deleteCandidate = ref<any | null>(null)
const deleteConfirmText = ref('')
const columns = [
  { key: 'name', label: 'Template' },
  { key: 'source_type', label: 'Source' },
  { key: 'revision', label: 'Revision' },
  { key: 'preview', label: 'Content preview' },
]
const form = reactive({ name: '', description: '', content: '' })

const describedCount = computed(() => rows.value.filter((item) => item.description).length)
const generatedCount = computed(() => rows.value.filter((item) => item.source_type === 'converter').length)
const recentCount = computed(() => rows.value.filter((item) => isWithinDays(item.updated_at, 30)).length)
const hasActiveFilters = computed(() => Boolean(search.value.trim() || sourceFilter.value !== 'all' || updatedFilter.value !== 'all'))
const selectedSourceLabel = computed(() => (selectedSource.value === 'converter' ? 'Converter generated' : 'Manual'))
const selectedRevisionLabel = computed(() => (selectedId.value ? `${selectedRevision.value}` : ''))
const filteredRows = computed(() => {
  return rows.value.filter((item) => {
    const matchesSearch = item.name.toLowerCase().includes(search.value.trim().toLowerCase())
    const matchesSource = sourceFilter.value === 'all' || item.source_type === sourceFilter.value
    const matchesUpdated =
      updatedFilter.value === 'all' ||
      (updatedFilter.value === '7d' && isWithinDays(item.updated_at, 7)) ||
      (updatedFilter.value === '30d' && isWithinDays(item.updated_at, 30))
    return matchesSearch && matchesSource && matchesUpdated
  })
})

function normalizeRow(item: any) {
  return {
    ...item,
    source_type_label: item.source_type === 'converter' ? 'Converter generated' : 'Manual',
    preview: item.preview || '',
  }
}

function resetForm() {
  selectedId.value = null
  selectedSource.value = 'manual'
  selectedRevision.value = 1
  form.name = ''
  form.description = ''
  form.content = ''
}

function resetValidationState() {
  formError.value = ''
  validationMessage.value = ''
  validationTone.value = 'info'
}

function openCreate() {
  resetValidationState()
  resetForm()
  showDrawer.value = true
}

async function openEdit(row: any) {
  resetValidationState()
  selectedId.value = row.id
  selectedSource.value = row.source_type
  selectedRevision.value = row.revision || 1
  try {
    const response = await api.get(`/templates/${row.id}`)
    const detail = response.data.data
    form.name = detail.name
    form.description = detail.description || ''
    form.content = detail.content
    showDrawer.value = true
  } catch (error: any) {
    app.pushToast(error?.response?.data?.message || 'Template detail could not be loaded', 'error')
  }
}

function closeDrawer() {
  if (isSaving.value) return
  showDrawer.value = false
  resetValidationState()
  resetForm()
}

function closeDeleteConfirm() {
  if (isSaving.value) return
  showDeleteConfirm.value = false
  deleteCandidate.value = null
  deleteConfirmText.value = ''
}

function validateForm() {
  if (!form.name.trim()) return 'Template name is required.'
  if (!form.content.trim()) return 'Template content is required.'
  return ''
}

async function validateTemplateContent() {
  formError.value = ''
  validationMessage.value = ''
  if (!form.content.trim()) {
    formError.value = 'Template content is required.'
    return
  }
  isValidating.value = true
  try {
    const response = await api.post('/templates/validate', { content: form.content })
    validationTone.value = 'info'
    validationMessage.value = response.data.data?.message || 'Template syntax is valid.'
    app.pushToast('Template syntax is valid', 'success')
  } catch (error: any) {
    validationTone.value = 'warn'
    const details = error?.response?.data?.details || {}
    const lineText = details?.line ? `Line ${details.line}: ` : ''
    validationMessage.value = `${lineText}${details?.error || error?.response?.data?.message || 'Template syntax is invalid.'}`
    app.pushToast(error?.response?.data?.message || 'Template syntax is invalid', 'error')
  } finally {
    isValidating.value = false
  }
}

async function load() {
  isLoading.value = true
  try {
    const response = await api.get('/templates/summary')
    rows.value = response.data.data.map(normalizeRow)
  } catch {
    app.pushToast('Templates could not be loaded', 'error', 'Check API reachability and refresh the template library.')
  } finally {
    isLoading.value = false
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
      content: form.content,
    }
    if (selectedId.value) {
      await api.put(`/templates/${selectedId.value}`, payload)
      app.pushToast('Template updated', 'success', 'The reusable template has been updated.')
    } else {
      await api.post('/templates', payload)
      app.pushToast('Template saved', 'success', 'The template is now available for reuse and conversion workflows.')
    }
    closeDrawer()
    await load()
  } catch (error: any) {
    app.pushToast(error?.response?.data?.message || 'Template could not be saved', 'error')
  } finally {
    isSaving.value = false
  }
}

function promptDelete(row: any) {
  deleteCandidate.value = row
  deleteConfirmText.value = ''
  showDeleteConfirm.value = true
}

async function removeTemplate() {
  if (!deleteCandidate.value) return
  if (deleteConfirmText.value !== deleteCandidate.value.name) return
  try {
    await api.delete(`/templates/${deleteCandidate.value.id}`)
    app.pushToast('Template deleted', 'success')
    closeDeleteConfirm()
    await load()
  } catch (error: any) {
    app.pushToast(error?.response?.data?.message || 'Template could not be deleted', 'error')
  }
}

function isWithinDays(timestamp: string | null | undefined, days: number) {
  if (!timestamp) return false
  const now = Date.now()
  const then = new Date(timestamp).getTime()
  if (Number.isNaN(then)) return false
  return now - then <= days * 24 * 60 * 60 * 1000
}

onMounted(load)
</script>
