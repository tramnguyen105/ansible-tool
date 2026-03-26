<template>
  <div>
    <PageHeader title="Playbooks" eyebrow="Execution Content" description="Manage validated playbooks and keep revision history visible for operational edits.">
      <button class="btn-primary" @click="showDrawer = true">New Playbook</button>
    </PageHeader>
    <DataTable :columns="columns" :rows="rows" row-key="id" />
    <DrawerPanel :open="showDrawer" title="Playbook" @close="showDrawer = false">
      <div class="space-y-4">
        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <label class="field-label">Name</label>
            <input v-model="form.name" />
          </div>
          <div>
            <label class="field-label">Description</label>
            <input v-model="form.description" />
          </div>
        </div>
        <YamlEditor v-model="form.yaml_content" />
        <div class="flex gap-3">
          <button class="btn-secondary" @click="validate">Validate YAML</button>
          <button class="btn-primary" @click="save">Save Playbook</button>
        </div>
      </div>
    </DrawerPanel>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'

import api from '../../api/client'
import DataTable from '../../components/common/DataTable.vue'
import DrawerPanel from '../../components/common/DrawerPanel.vue'
import PageHeader from '../../components/common/PageHeader.vue'
import YamlEditor from '../../components/forms/YamlEditor.vue'
import { useAppStore } from '../../stores/app'

const app = useAppStore()
const rows = ref<any[]>([])
const showDrawer = ref(false)
const columns = [
  { key: 'name', label: 'Name' },
  { key: 'description', label: 'Description' },
  { key: 'revision_count', label: 'Revisions' },
]
const form = reactive({ name: '', description: '', yaml_content: '- hosts: all\n  gather_facts: false\n  tasks: []' })

async function load() {
  const response = await api.get('/playbooks')
  rows.value = response.data.data.map((item: any) => ({ ...item, revision_count: item.revisions.length }))
}

async function validate() {
  const response = await api.post('/playbooks/validate-yaml', { content: form.yaml_content })
  app.pushToast(response.data.data.valid ? 'YAML is valid' : 'YAML validation failed', response.data.data.valid ? 'success' : 'error')
}

async function save() {
  await api.post('/playbooks', form)
  app.pushToast('Playbook saved', 'success')
  showDrawer.value = false
  load()
}

onMounted(load)
</script>
