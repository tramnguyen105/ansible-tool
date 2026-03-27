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

    <div class="grid gap-4 xl:grid-cols-3">
      <CardStat label="Templates" :value="rows.length" tone="library" :helper="rows.length ? 'Reusable templates are available.' : 'No templates stored yet.'" />
      <CardStat label="Described" :value="describedCount" tone="documented" :helper="describedCount ? 'Templates include operator context.' : 'Descriptions should explain when to use a template.'" />
      <CardStat label="Content model" value="Jinja2" tone="templated" helper="Prefer reusable variables over device-specific hardcoding whenever possible." />
    </div>

    <div class="mt-6">
      <DataTable
        title="Template library"
        description="Keep template naming clear and descriptions specific so operators know which artifacts should be reused versus duplicated."
        :columns="columns"
        :rows="rows"
        :loading="isLoading"
        loading-title="Loading templates"
        loading-description="Collecting reusable Jinja2 artifacts and preview content from the backend."
        empty-title="No templates saved"
        empty-description="Create a reusable template or save one from the CLI conversion workflow after reviewing the generated content."
      >
        <template #name="{ row }">
          <div>
            <p class="font-medium text-white">{{ row.name }}</p>
            <p class="mt-1 text-xs text-console-muted">{{ row.description || 'No description provided' }}</p>
          </div>
        </template>
        <template #preview="{ row }">
          <code class="block max-w-[420px] overflow-hidden text-ellipsis whitespace-nowrap text-xs text-console-muted">{{ row.preview }}</code>
        </template>
        <template #actions="{ row }">
          <div class="flex justify-end gap-3 text-sm">
            <button class="text-console-glow transition hover:text-white" :disabled="isSaving" @click="openEdit(row)">Edit</button>
            <button class="text-rose-300 transition hover:text-rose-200 disabled:opacity-50" :disabled="isSaving" @click="removeTemplate(row)">Delete</button>
          </div>
        </template>
      </DataTable>
    </div>

    <DrawerPanel :open="showDrawer" :title="selectedId ? 'Edit template' : 'Create template'" @close="closeDrawer">
      <div class="space-y-4">
        <div>
          <label class="field-label">Name</label>
          <input v-model="form.name" :disabled="isSaving" placeholder="ios-interface-base.j2" />
        </div>
        <div>
          <label class="field-label">Description</label>
          <input v-model="form.description" :disabled="isSaving" placeholder="Reusable baseline for IOS interface configuration" />
        </div>
        <div>
          <label class="field-label">Template Content</label>
          <textarea v-model="form.content" :disabled="isSaving" class="min-h-[280px] font-mono" placeholder="interface {{ interface_name }}"></textarea>
        </div>
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
import { useAppStore } from '../../stores/app'

const app = useAppStore()
const rows = ref<any[]>([])
const showDrawer = ref(false)
const selectedId = ref<string | null>(null)
const isLoading = ref(true)
const isSaving = ref(false)
const columns = [
  { key: 'name', label: 'Template' },
  { key: 'preview', label: 'Content preview' },
]
const form = reactive({ name: '', description: '', content: '' })

const describedCount = computed(() => rows.value.filter((item) => item.description).length)

function normalizeRow(item: any) {
  return {
    ...item,
    preview: item.content.replace(/\s+/g, ' ').trim(),
  }
}

function resetForm() {
  selectedId.value = null
  form.name = ''
  form.description = ''
  form.content = ''
}

function openCreate() {
  resetForm()
  showDrawer.value = true
}

function openEdit(row: any) {
  selectedId.value = row.id
  form.name = row.name
  form.description = row.description || ''
  form.content = row.content
  showDrawer.value = true
}

function closeDrawer() {
  if (isSaving.value) return
  showDrawer.value = false
  resetForm()
}

async function load() {
  isLoading.value = true
  try {
    const response = await api.get('/templates')
    rows.value = response.data.data.map(normalizeRow)
  } catch {
    app.pushToast('Templates could not be loaded', 'error', 'Check API reachability and refresh the template library.')
  } finally {
    isLoading.value = false
  }
}

async function save() {
  isSaving.value = true
  try {
    if (selectedId.value) {
      await api.put(`/templates/${selectedId.value}`, form)
      app.pushToast('Template updated', 'success', 'The reusable template has been updated.')
    } else {
      await api.post('/templates', form)
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

async function removeTemplate(row: any) {
  if (!window.confirm(`Delete template "${row.name}"?`)) return
  try {
    await api.delete(`/templates/${row.id}`)
    app.pushToast('Template deleted', 'success')
    await load()
  } catch (error: any) {
    app.pushToast(error?.response?.data?.message || 'Template could not be deleted', 'error')
  }
}

onMounted(load)
</script>
