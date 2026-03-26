<template>
  <div>
    <PageHeader title="Templates" eyebrow="Reusable Config" description="Store and maintain reusable Jinja2 templates for generated or hand-authored network configurations.">
      <button class="btn-primary" @click="showDrawer = true">New Template</button>
    </PageHeader>
    <DataTable :columns="columns" :rows="rows" row-key="id" />
    <DrawerPanel :open="showDrawer" title="Template" @close="showDrawer = false">
      <div class="space-y-4">
        <div>
          <label class="field-label">Name</label>
          <input v-model="form.name" />
        </div>
        <div>
          <label class="field-label">Description</label>
          <input v-model="form.description" />
        </div>
        <div>
          <label class="field-label">Template Content</label>
          <textarea v-model="form.content" class="min-h-[280px] font-mono"></textarea>
        </div>
        <button class="btn-primary" @click="save">Save Template</button>
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
import { useAppStore } from '../../stores/app'

const app = useAppStore()
const rows = ref<any[]>([])
const showDrawer = ref(false)
const columns = [
  { key: 'name', label: 'Name' },
  { key: 'description', label: 'Description' },
]
const form = reactive({ name: '', description: '', content: '' })

async function load() {
  const response = await api.get('/templates')
  rows.value = response.data.data
}

async function save() {
  await api.post('/templates', form)
  app.pushToast('Template saved', 'success')
  showDrawer.value = false
  load()
}

onMounted(load)
</script>
