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
      <CardStat label="Validation" value="Required" tone="yaml" helper="Validate YAML before saving changes to production-facing playbooks." />
    </div>

    <div class="mt-6">
      <DataTable
        title="Playbook library"
        description="Review execution content, revision depth, and generation source before selecting a playbook for jobs or schedules."
        :columns="columns"
        :rows="rows"
        :loading="isLoading"
        loading-title="Loading playbooks"
        loading-description="Collecting execution content, generated artifacts, and revision metadata from the backend."
        empty-title="No playbooks saved"
        empty-description="Create a playbook manually or save one from the CLI converter after reviewing the generated output."
      >
        <template #name="{ row }">
          <div>
            <p class="font-medium text-white">{{ row.name }}</p>
            <p class="mt-1 text-xs text-console-muted">{{ row.description || 'No description provided' }}</p>
          </div>
        </template>
        <template #is_generated="{ row }">
          <StatusBadge :value="row.is_generated ? 'ready' : 'manual'" />
          <p class="mt-2 text-xs text-console-muted">{{ row.is_generated ? 'Generated from converter' : 'Authored manually' }}</p>
        </template>
        <template #revision_count="{ row }">
          <div>
            <p class="text-white">{{ row.revision_count }} revisions</p>
            <p class="mt-1 text-xs text-console-muted">{{ row.last_change_note }}</p>
          </div>
        </template>
        <template #actions="{ row }">
          <div class="flex justify-end gap-3 text-sm">
            <button class="text-console-glow transition hover:text-white" :disabled="isSaving || isValidating" @click="openEdit(row)">Edit</button>
            <button class="text-rose-300 transition hover:text-rose-200 disabled:opacity-50" :disabled="isSaving || isValidating" @click="removePlaybook(row)">Delete</button>
          </div>
        </template>
      </DataTable>
    </div>

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
        <BannerNotice
          title="Validation"
          tone="info"
          text="Run YAML validation before save. Valid syntax does not guarantee safe device behavior, so still review target scope and module intent."
        />
        <div class="flex justify-end gap-3">
          <button class="btn-secondary" :disabled="isValidating || isSaving" @click="validate">{{ isValidating ? 'Validating...' : 'Validate YAML' }}</button>
          <button class="btn-primary" :disabled="isSaving || isValidating" @click="save">{{ isSaving ? 'Saving...' : selectedId ? 'Save changes' : 'Save playbook' }}</button>
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
import YamlEditor from '../../components/forms/YamlEditor.vue'
import { useAppStore } from '../../stores/app'

const app = useAppStore()
const rows = ref<any[]>([])
const showDrawer = ref(false)
const selectedId = ref<string | null>(null)
const isLoading = ref(true)
const isValidating = ref(false)
const isSaving = ref(false)
const columns = [
  { key: 'name', label: 'Playbook' },
  { key: 'is_generated', label: 'Source' },
  { key: 'revision_count', label: 'Revision history' },
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

function normalizeRow(item: any) {
  const revisions = item.revisions || []
  return {
    ...item,
    revision_count: revisions.length,
    last_change_note: revisions[0]?.change_note || 'No change note recorded yet.',
  }
}

function resetForm() {
  selectedId.value = null
  form.name = ''
  form.description = ''
  form.yaml_content = '- hosts: all\n  gather_facts: false\n  tasks: []'
  form.is_generated = false
  form.change_note = 'Initial draft'
}

function openCreate() {
  resetForm()
  showDrawer.value = true
}

function openEdit(row: any) {
  selectedId.value = row.id
  form.name = row.name
  form.description = row.description || ''
  form.yaml_content = row.yaml_content
  form.is_generated = row.is_generated
  form.change_note = 'Updated via GUI'
  showDrawer.value = true
}

function closeDrawer() {
  if (isSaving.value || isValidating.value) return
  showDrawer.value = false
  resetForm()
}

async function load() {
  isLoading.value = true
  try {
    const response = await api.get('/playbooks')
    rows.value = response.data.data.map(normalizeRow)
  } catch {
    app.pushToast('Playbooks could not be loaded', 'error', 'Check API reachability and refresh the playbook library.')
  } finally {
    isLoading.value = false
  }
}

async function validate() {
  isValidating.value = true
  try {
    const response = await api.post('/playbooks/validate-yaml', { content: form.yaml_content })
    app.pushToast(
      response.data.data.valid ? 'YAML is valid' : 'YAML validation failed',
      response.data.data.valid ? 'success' : 'error',
      response.data.data.valid ? 'The playbook syntax parsed successfully.' : 'Review the YAML structure before saving.',
    )
  } catch (error: any) {
    app.pushToast(error?.response?.data?.message || 'YAML validation failed', 'error')
  } finally {
    isValidating.value = false
  }
}

async function save() {
  isSaving.value = true
  try {
    if (selectedId.value) {
      await api.put(`/playbooks/${selectedId.value}`, {
        name: form.name,
        description: form.description,
        yaml_content: form.yaml_content,
        change_note: form.change_note,
      })
      app.pushToast('Playbook updated', 'success', 'The latest revision has been stored.')
    } else {
      await api.post('/playbooks', form)
      app.pushToast('Playbook saved', 'success', 'The playbook is now available for job execution.')
    }
    closeDrawer()
    await load()
  } catch (error: any) {
    app.pushToast(error?.response?.data?.message || 'Playbook could not be saved', 'error')
  } finally {
    isSaving.value = false
  }
}

async function removePlaybook(row: any) {
  if (!window.confirm(`Delete playbook "${row.name}"?`)) return
  try {
    await api.delete(`/playbooks/${row.id}`)
    app.pushToast('Playbook deleted', 'success')
    await load()
  } catch (error: any) {
    app.pushToast(error?.response?.data?.message || 'Playbook could not be deleted', 'error')
  }
}

onMounted(load)
</script>
