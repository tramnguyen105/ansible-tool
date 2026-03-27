<template>
  <div>
    <PageHeader
      title="Credentials"
      eyebrow="Encrypted Secrets"
      description="Store operator credentials securely for job execution. Secrets are encrypted at rest and never returned in plain text after save."
    >
      <button class="btn-secondary" :disabled="isLoading || isSaving" @click="load">{{ isLoading ? 'Refreshing...' : 'Refresh' }}</button>
      <button class="btn-primary" :disabled="isSaving" @click="openCreate">New credential</button>
    </PageHeader>

    <div class="grid gap-4 xl:grid-cols-4">
      <CardStat label="Credentials" :value="rows.length" tone="stored" :helper="rows.length ? 'Encrypted credential records available.' : 'No credentials stored yet.'" />
      <CardStat label="Password auth" :value="passwordCredentials" tone="password" :helper="passwordCredentials ? 'Username/password credentials are available.' : 'No password-based credentials saved.'" />
      <CardStat label="Key auth" :value="keyCredentials" tone="keys" :helper="keyCredentials ? 'Private-key authentication is configured.' : 'No key-based credentials saved.'" />
      <CardStat label="Active" :value="activeCredentials" tone="active" :helper="activeCredentials ? 'Active credentials may be selected for jobs.' : 'All credentials are currently inactive.'" />
    </div>

    <section class="mt-6 rounded-3xl border border-console-edge bg-console-panel/80 p-5 shadow-xl shadow-slate-950/20">
      <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p class="text-xs uppercase tracking-[0.22em] text-console-glow">Credential Control</p>
          <h3 class="mt-2 text-xl font-semibold text-white">Operator credential catalog</h3>
          <p class="mt-2 max-w-3xl text-sm leading-6 text-console-muted">
            Keep credential naming explicit, distinguish authentication methods clearly, and avoid storing secrets that operators no longer need.
          </p>
        </div>
        <div class="grid gap-3 sm:grid-cols-2 lg:min-w-[420px]">
          <input v-model="search" :disabled="isLoading" placeholder="Search by credential name or username" />
          <select v-model="typeFilter" :disabled="isLoading">
            <option value="all">All credential types</option>
            <option value="ssh_password">SSH username/password</option>
            <option value="ssh_private_key">SSH private key</option>
          </select>
        </div>
      </div>
    </section>

    <div class="mt-6">
      <DataTable
        title="Credential records"
        description="Review authentication type and masked capabilities before associating a credential with a job or schedule."
        :columns="columns"
        :rows="filteredRows"
        :loading="isLoading"
        loading-title="Loading credentials"
        loading-description="Collecting encrypted credential metadata and availability state from the backend."
        empty-title="No credentials match your filters"
        empty-description="Create a new credential or adjust the current filters to review existing records."
      >
        <template #name="{ row }">
          <div>
            <p class="font-medium text-white">{{ row.name }}</p>
            <p class="mt-1 text-xs text-console-muted">{{ row.description || 'No description provided' }}</p>
          </div>
        </template>
        <template #credential_type="{ row }">
          <StatusBadge :value="row.credential_type === 'ssh_password' ? 'manual' : 'ready'" />
          <p class="mt-2 text-xs text-console-muted">{{ row.credential_type_label }}</p>
        </template>
        <template #username="{ row }">
          <div>
            <p class="text-white">{{ row.username }}</p>
            <p class="mt-1 text-xs text-console-muted">{{ row.secretSummary }}</p>
          </div>
        </template>
        <template #is_active="{ row }">
          <StatusBadge :value="row.is_active ? 'enabled' : 'disabled'" />
        </template>
        <template #actions="{ row }">
          <div class="flex justify-end gap-3 text-sm">
            <button class="text-console-glow transition hover:text-white" :disabled="isSaving" @click="openEdit(row)">Edit</button>
            <button class="text-rose-300 transition hover:text-rose-200 disabled:opacity-50" :disabled="isSaving" @click="removeCredential(row)">Delete</button>
          </div>
        </template>
      </DataTable>
    </div>

    <DrawerPanel :open="showDrawer" :title="selectedId ? 'Edit credential' : 'Create credential'" @close="closeDrawer">
      <div class="space-y-4">
        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <label class="field-label">Name</label>
            <input v-model="form.name" :disabled="isSaving" placeholder="Prod core IOS credential" />
          </div>
          <div>
            <label class="field-label">Type</label>
            <select v-model="form.credential_type" :disabled="!!selectedId || isSaving">
              <option value="ssh_password">SSH Username/Password</option>
              <option value="ssh_private_key">SSH Private Key</option>
            </select>
          </div>
          <div>
            <label class="field-label">Username</label>
            <input v-model="form.username" :disabled="isSaving" placeholder="netops-admin" />
          </div>
          <div>
            <label class="field-label">Description</label>
            <input v-model="form.description" :disabled="isSaving" placeholder="Optional operator context" />
          </div>
        </div>

        <div class="flex items-center gap-2 text-sm text-console-muted" v-if="selectedId">
          <input v-model="form.is_active" :disabled="isSaving" type="checkbox" class="w-auto" />
          Credential is active
        </div>

        <div v-if="form.credential_type === 'ssh_password'">
          <label class="field-label">Password</label>
          <input v-model="form.password" :disabled="isSaving" type="password" :placeholder="selectedId ? 'Leave blank to keep current secret' : 'Stored encrypted after save'" />
        </div>

        <div v-else class="space-y-4">
          <div>
            <label class="field-label">Private Key</label>
            <textarea v-model="form.private_key" :disabled="isSaving" class="min-h-[220px] font-mono" :placeholder="selectedId ? 'Leave blank to keep current key' : '-----BEGIN OPENSSH PRIVATE KEY-----'"></textarea>
          </div>
          <div>
            <label class="field-label">Passphrase</label>
            <input v-model="form.passphrase" :disabled="isSaving" type="password" placeholder="Optional" />
          </div>
        </div>

        <BannerNotice
          title="Secret handling"
          tone="info"
          text="Credential secrets are encrypted at rest and masked in all later API responses. Store only credentials needed for real operator workflows."
        />

        <div class="flex justify-end gap-2">
          <button class="btn-secondary" :disabled="isSaving" @click="closeDrawer">Cancel</button>
          <button class="btn-primary" :disabled="isSaving" @click="save">{{ isSaving ? 'Saving...' : selectedId ? 'Save changes' : 'Save credential' }}</button>
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

const app = useAppStore()
const rows = ref<any[]>([])
const showDrawer = ref(false)
const selectedId = ref<string | null>(null)
const search = ref('')
const typeFilter = ref('all')
const isLoading = ref(true)
const isSaving = ref(false)
const columns = [
  { key: 'name', label: 'Credential' },
  { key: 'credential_type', label: 'Type' },
  { key: 'username', label: 'Operator username' },
  { key: 'is_active', label: 'State' },
]
const form = reactive<any>({
  name: '',
  description: '',
  credential_type: 'ssh_password',
  username: '',
  password: '',
  private_key: '',
  passphrase: '',
  is_active: true,
})

const filteredRows = computed(() => {
  return rows.value.filter((item) => {
    const haystack = `${item.name} ${item.username}`.toLowerCase()
    const matchesSearch = haystack.includes(search.value.toLowerCase())
    const matchesType = typeFilter.value === 'all' || item.credential_type === typeFilter.value
    return matchesSearch && matchesType
  })
})

const passwordCredentials = computed(() => rows.value.filter((item) => item.credential_type === 'ssh_password').length)
const keyCredentials = computed(() => rows.value.filter((item) => item.credential_type === 'ssh_private_key').length)
const activeCredentials = computed(() => rows.value.filter((item) => item.is_active).length)

function normalizeRow(item: any) {
  return {
    ...item,
    credential_type_label: item.credential_type === 'ssh_password' ? 'SSH username/password' : 'SSH private key',
    secretSummary: [
      item.has_password ? 'Password stored' : null,
      item.has_private_key ? 'Private key stored' : null,
      item.has_passphrase ? 'Passphrase stored' : null,
    ]
      .filter(Boolean)
      .join(' • '),
  }
}

function resetForm() {
  selectedId.value = null
  form.name = ''
  form.description = ''
  form.credential_type = 'ssh_password'
  form.username = ''
  form.password = ''
  form.private_key = ''
  form.passphrase = ''
  form.is_active = true
}

function openCreate() {
  resetForm()
  showDrawer.value = true
}

function openEdit(row: any) {
  selectedId.value = row.id
  form.name = row.name
  form.description = row.description || ''
  form.credential_type = row.credential_type
  form.username = row.username
  form.password = ''
  form.private_key = ''
  form.passphrase = ''
  form.is_active = row.is_active
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
    const response = await api.get('/credentials')
    rows.value = response.data.data.map(normalizeRow)
  } catch {
    app.pushToast('Credentials could not be loaded', 'error', 'Check API reachability and refresh the credential catalog.')
  } finally {
    isLoading.value = false
  }
}

async function save() {
  isSaving.value = true
  try {
    const payload: any = {
      name: form.name,
      description: form.description,
      username: form.username,
      is_active: form.is_active,
    }

    if (selectedId.value) {
      if (form.password) payload.password = form.password
      if (form.private_key) payload.private_key = form.private_key
      if (form.passphrase) payload.passphrase = form.passphrase
      await api.put(`/credentials/${selectedId.value}`, payload)
      app.pushToast('Credential updated', 'success', 'Encrypted credential metadata has been updated.')
    } else {
      payload.credential_type = form.credential_type
      payload.password = form.password || undefined
      payload.private_key = form.private_key || undefined
      payload.passphrase = form.passphrase || undefined
      await api.post('/credentials', payload)
      app.pushToast('Credential saved', 'success', 'The encrypted credential is now available for jobs and schedules.')
    }

    closeDrawer()
    await load()
  } catch (error: any) {
    app.pushToast(error?.response?.data?.message || 'Credential could not be saved', 'error')
  } finally {
    isSaving.value = false
  }
}

async function removeCredential(row: any) {
  if (!window.confirm(`Delete credential "${row.name}"?`)) return
  try {
    await api.delete(`/credentials/${row.id}`)
    app.pushToast('Credential deleted', 'success')
    await load()
  } catch (error: any) {
    app.pushToast(error?.response?.data?.message || 'Credential could not be deleted', 'error')
  }
}

onMounted(load)
</script>
