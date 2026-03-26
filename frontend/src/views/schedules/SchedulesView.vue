<template>
  <div>
    <PageHeader title="Schedules" eyebrow="Recurring Automation" description="Trigger approved jobs on cron-style schedules and monitor the next dispatch time.">
      <button class="btn-primary" @click="showDrawer = true">New Schedule</button>
    </PageHeader>
    <DataTable :columns="columns" :rows="rows" row-key="id">
      <template #enabled="{ row }">
        <StatusBadge :value="row.enabled ? 'enabled' : 'disabled'" />
      </template>
    </DataTable>
    <DrawerPanel :open="showDrawer" title="Schedule" @close="showDrawer = false">
      <div class="space-y-4">
        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <label class="field-label">Name</label>
            <input v-model="form.name" />
          </div>
          <div>
            <label class="field-label">Cron Expression</label>
            <input v-model="form.cron_expression" placeholder="0 2 * * *" />
          </div>
          <div>
            <label class="field-label">Timezone</label>
            <input v-model="form.timezone" />
          </div>
          <div>
            <label class="field-label">Inventory</label>
            <select v-model="form.inventory_id">
              <option v-for="item in inventories" :key="item.id" :value="item.id">{{ item.name }}</option>
            </select>
          </div>
          <div>
            <label class="field-label">Credential</label>
            <select v-model="form.credential_id">
              <option v-for="item in credentials" :key="item.id" :value="item.id">{{ item.name }}</option>
            </select>
          </div>
          <div>
            <label class="field-label">Playbook</label>
            <select v-model="form.playbook_id">
              <option v-for="item in playbooks" :key="item.id" :value="item.id">{{ item.name }}</option>
            </select>
          </div>
        </div>
        <div class="flex items-center gap-3 text-sm text-console-muted">
          <input v-model="form.enabled" type="checkbox" class="w-auto" />
          Enabled
        </div>
        <button class="btn-primary" @click="save">Save Schedule</button>
      </div>
    </DrawerPanel>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'

import api from '../../api/client'
import DataTable from '../../components/common/DataTable.vue'
import DrawerPanel from '../../components/common/DrawerPanel.vue'
import PageHeader from '../../components/common/PageHeader.vue'
import StatusBadge from '../../components/common/StatusBadge.vue'
import { useAppStore } from '../../stores/app'

const app = useAppStore()
const rows = ref<any[]>([])
const showDrawer = ref(false)
const inventories = ref<any[]>([])
const credentials = ref<any[]>([])
const playbooks = ref<any[]>([])
const form = reactive({
  name: 'nightly-run',
  description: '',
  cron_expression: '0 2 * * *',
  timezone: 'UTC',
  enabled: true,
  inventory_id: '',
  credential_id: '',
  playbook_id: '',
  target_type: 'all',
  target_value: '',
  extra_vars: {},
  check_mode: false,
})
const columns = [
  { key: 'name', label: 'Name' },
  { key: 'cron_expression', label: 'Cron' },
  { key: 'timezone', label: 'Timezone' },
  { key: 'enabled', label: 'Enabled' },
  { key: 'next_run_at', label: 'Next Run' },
]

async function loadLookups() {
  const [inventoryResp, credentialResp, playbookResp] = await Promise.all([
    api.get('/inventories'),
    api.get('/credentials'),
    api.get('/playbooks'),
  ])
  inventories.value = inventoryResp.data.data
  credentials.value = credentialResp.data.data
  playbooks.value = playbookResp.data.data
  form.inventory_id = inventories.value[0]?.id || ''
  form.credential_id = credentials.value[0]?.id || ''
  form.playbook_id = playbooks.value[0]?.id || ''
}

async function load() {
  const response = await api.get('/schedules')
  rows.value = response.data.data
}

watch(
  () => showDrawer.value,
  (open) => {
    if (open) loadLookups()
  },
)

async function save() {
  await api.post('/schedules', form)
  app.pushToast('Schedule saved', 'success')
  showDrawer.value = false
  load()
}

onMounted(load)
</script>
