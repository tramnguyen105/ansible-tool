<template>
  <div>
    <PageHeader title="Credentials" eyebrow="Encrypted Secrets" description="Credentials are encrypted at rest and never returned in plain text after save.">
      <button class="btn-primary" @click="showDrawer = true">New Credential</button>
    </PageHeader>
    <DataTable :columns="columns" :rows="rows" row-key="id" />
    <DrawerPanel :open="showDrawer" title="Credential" @close="showDrawer = false">
      <div class="space-y-4">
        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <label class="field-label">Name</label>
            <input v-model="form.name" />
          </div>
          <div>
            <label class="field-label">Type</label>
            <select v-model="form.credential_type">
              <option value="ssh_password">SSH Username/Password</option>
              <option value="ssh_private_key">SSH Private Key</option>
            </select>
          </div>
          <div>
            <label class="field-label">Username</label>
            <input v-model="form.username" />
          </div>
          <div>
            <label class="field-label">Description</label>
            <input v-model="form.description" />
          </div>
        </div>
        <div v-if="form.credential_type === 'ssh_password'">
          <label class="field-label">Password</label>
          <input v-model="form.password" type="password" />
        </div>
        <div v-else class="space-y-4">
          <div>
            <label class="field-label">Private Key</label>
            <textarea v-model="form.private_key" class="min-h-[220px] font-mono"></textarea>
          </div>
          <div>
            <label class="field-label">Passphrase</label>
            <input v-model="form.passphrase" type="password" />
          </div>
        </div>
        <button class="btn-primary" @click="save">Save Credential</button>
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
  { key: 'credential_type', label: 'Type' },
  { key: 'username', label: 'Username' },
  { key: 'is_active', label: 'Active' },
]
const form = reactive({
  name: '',
  description: '',
  credential_type: 'ssh_password',
  username: '',
  password: '',
  private_key: '',
  passphrase: '',
})

async function load() {
  const response = await api.get('/credentials')
  rows.value = response.data.data
}

async function save() {
  await api.post('/credentials', form)
  app.pushToast('Credential saved', 'success')
  showDrawer.value = false
  load()
}

onMounted(load)
</script>
