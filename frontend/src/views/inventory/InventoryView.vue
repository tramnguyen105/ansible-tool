<template>
  <div>
    <PageHeader title="Inventory" eyebrow="Managed Targets" description="Create inventories manually or import and normalize them from common file formats.">
      <button class="btn-secondary" @click="showCreate = true">New Inventory</button>
      <button class="btn-primary" @click="showImport = true">Import</button>
    </PageHeader>
    <div class="mb-4">
      <input v-model="search" placeholder="Search inventories" />
    </div>
    <DataTable :columns="columns" :rows="filteredRows" row-key="id" />
    <InventoryImportWizard :open="showImport" @close="showImport = false" @saved="load" />
    <DrawerPanel :open="showCreate" title="Create Inventory" @close="showCreate = false">
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
          <label class="field-label">Inventory Vars JSON</label>
          <textarea v-model="varsText"></textarea>
        </div>
        <div>
          <label class="field-label">Hosts JSON Array</label>
          <textarea v-model="hostsText"></textarea>
        </div>
        <div>
          <label class="field-label">Groups JSON Array</label>
          <textarea v-model="groupsText"></textarea>
        </div>
        <button class="btn-primary" @click="createInventory">Create</button>
      </div>
    </DrawerPanel>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import api from '../../api/client'
import DataTable from '../../components/common/DataTable.vue'
import DrawerPanel from '../../components/common/DrawerPanel.vue'
import PageHeader from '../../components/common/PageHeader.vue'
import InventoryImportWizard from '../../components/wizards/InventoryImportWizard.vue'
import { useAppStore } from '../../stores/app'

const app = useAppStore()
const rows = ref<any[]>([])
const search = ref('')
const showImport = ref(false)
const showCreate = ref(false)
const varsText = ref('{}')
const hostsText = ref('[]')
const groupsText = ref('[]')
const form = reactive({ name: '', description: '' })
const columns = [
  { key: 'name', label: 'Name' },
  { key: 'source_type', label: 'Source' },
  { key: 'host_count', label: 'Hosts' },
  { key: 'group_count', label: 'Groups' },
]

const filteredRows = computed(() =>
  rows.value.filter((item) => item.name.toLowerCase().includes(search.value.toLowerCase())),
)

async function load() {
  const response = await api.get('/inventories')
  rows.value = response.data.data.map((item: any) => ({ ...item, host_count: item.hosts.length, group_count: item.groups.length }))
}

async function createInventory() {
  await api.post('/inventories', {
    name: form.name,
    description: form.description,
    variables: JSON.parse(varsText.value || '{}'),
    hosts: JSON.parse(hostsText.value || '[]'),
    groups: JSON.parse(groupsText.value || '[]'),
  })
  app.pushToast('Inventory created', 'success')
  showCreate.value = false
  load()
}

onMounted(load)
</script>
