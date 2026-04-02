<template>
  <div>
    <PageHeader
      title="Users"
      eyebrow="Administration"
      description="Manage local and LDAP user accounts, status, and role-based access controls."
    >
      <button class="btn-secondary" :disabled="isLoading" @click="load">{{ isLoading ? 'Refreshing...' : 'Refresh' }}</button>
      <button class="btn-primary" :disabled="isLoading" @click="openCreate">Create user</button>
    </PageHeader>

    <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <CardStat label="Total users" :value="rows.length" tone="identity" helper="All local and LDAP users." />
      <CardStat label="Admins" :value="adminCount" tone="runtime" helper="Users with full administration access." />
      <CardStat label="LDAP users" :value="ldapCount" tone="success" helper="Directory-backed identities." />
      <CardStat label="Local users" :value="localCount" tone="info" helper="Accounts managed directly in this app." />
    </div>

    <div class="mt-6 rounded-2xl border border-slate-200 bg-white p-4">
      <label class="field-label">Search</label>
      <input v-model.trim="search" placeholder="Filter by username, display name, email, or role" :disabled="isLoading" />
    </div>

    <section v-if="isEditorOpen" class="mt-6 rounded-2xl border border-slate-200 bg-white p-5">
      <div class="mb-4 flex items-center justify-between gap-3">
        <h3 class="text-lg font-semibold text-slate-900">{{ editingId ? 'Update user' : 'Create user' }}</h3>
        <button class="btn-secondary" :disabled="isSaving" @click="closeEditor">Cancel</button>
      </div>
      <div class="grid gap-4 sm:grid-cols-2">
        <label>
          <span class="field-label">Username</span>
          <input v-model.trim="form.username" :disabled="!!editingId || isSaving" placeholder="jane.doe" />
        </label>
        <label>
          <span class="field-label">Auth source</span>
          <select v-model="form.auth_source" :disabled="!!editingId || isSaving">
            <option value="local">Local</option>
            <option value="ldap">LDAP</option>
          </select>
        </label>
        <label>
          <span class="field-label">Display name</span>
          <input v-model.trim="form.display_name" :disabled="isSaving" placeholder="Jane Doe" />
        </label>
        <label>
          <span class="field-label">Email</span>
          <input v-model.trim="form.email" :disabled="isSaving" placeholder="jane.doe@example.com" />
        </label>
        <label v-if="form.auth_source === 'ldap'" class="sm:col-span-2">
          <span class="field-label">LDAP DN</span>
          <input v-model.trim="form.ldap_dn" :disabled="isSaving" placeholder="cn=jane.doe,ou=users,dc=example,dc=internal" />
        </label>
        <label v-if="!editingId && form.auth_source === 'local'" class="sm:col-span-2">
          <span class="field-label">Initial password</span>
          <input v-model="form.password" type="password" :disabled="isSaving" autocomplete="new-password" />
        </label>
      </div>

      <div class="mt-4 rounded-xl border border-slate-200 p-3">
        <p class="field-label">Roles</p>
        <div class="mt-2 flex flex-wrap gap-2">
          <label v-for="role in roleOptions" :key="role" class="inline-flex items-center gap-2 rounded-full border border-slate-200 px-3 py-1.5 text-sm text-slate-700">
            <input v-model="form.role_names" :value="role" type="checkbox" class="w-auto" :disabled="isSaving" />
            <span>{{ role }}</span>
          </label>
        </div>
      </div>

      <label class="mt-4 inline-flex items-center gap-2 text-sm text-slate-700">
        <input v-model="form.is_active" type="checkbox" class="w-auto" :disabled="isSaving" />
        <span>Active account</span>
      </label>

      <div class="mt-4 flex justify-end">
        <button class="btn-primary" :disabled="isSaving" @click="saveUser">{{ isSaving ? 'Saving...' : editingId ? 'Save changes' : 'Create user' }}</button>
      </div>
    </section>

    <div class="mt-6">
      <DataTable
        title="User accounts"
        description="Control access with explicit role assignments."
        :columns="columns"
        :rows="filteredRows"
        :loading="isLoading"
        loading-title="Loading users"
        loading-description="Collecting user and role assignments."
        empty-title="No users found"
        empty-description="Create a user account to start managing access."
      >
        <template #username="{ row }">
          <div>
            <p class="font-medium text-slate-900">{{ row.username }}</p>
            <p class="mt-1 text-xs text-slate-500">{{ row.display_name || 'No display name' }}</p>
          </div>
        </template>
        <template #roles="{ row }">
          <div class="flex flex-wrap gap-1">
            <span
              v-for="role in row.roles"
              :key="role.name"
              class="rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-xs uppercase tracking-[0.08em] text-slate-600"
            >
              {{ role.name }}
            </span>
          </div>
        </template>
        <template #status="{ row }">
          <span :class="row.is_active ? 'text-emerald-700' : 'text-rose-700'">{{ row.is_active ? 'Active' : 'Disabled' }}</span>
        </template>
        <template #actions="{ row }">
          <div class="inline-flex gap-3">
            <button class="text-sm text-slate-700 hover:text-slate-900" @click="openEdit(row)">Edit</button>
            <button
              v-if="row.auth_source === 'local'"
              class="text-sm text-slate-700 hover:text-slate-900"
              @click="resetPassword(row)"
            >
              Reset password
            </button>
          </div>
        </template>
      </DataTable>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import api from '../../api/client'
import CardStat from '../../components/common/CardStat.vue'
import DataTable from '../../components/common/DataTable.vue'
import PageHeader from '../../components/common/PageHeader.vue'
import { useAppStore } from '../../stores/app'

type Role = { name: string; description?: string }
type UserRow = {
  id: string
  username: string
  display_name?: string
  email?: string
  auth_source: 'local' | 'ldap'
  ldap_dn?: string
  is_active: boolean
  last_login_at?: string | null
  roles: Role[]
}

const app = useAppStore()
const isLoading = ref(false)
const isSaving = ref(false)
const isEditorOpen = ref(false)
const editingId = ref<string | null>(null)
const search = ref('')
const rows = ref<UserRow[]>([])
const roleOptions = ref<string[]>(['admin', 'operator', 'viewer'])

const form = reactive({
  username: '',
  display_name: '',
  email: '',
  auth_source: 'local' as 'local' | 'ldap',
  ldap_dn: '',
  password: '',
  role_names: ['operator'] as string[],
  is_active: true,
})

const columns = [
  { key: 'username', label: 'User' },
  { key: 'auth_source', label: 'Auth source' },
  { key: 'roles', label: 'Roles' },
  { key: 'status', label: 'Status' },
  { key: 'last_login_at', label: 'Last login' },
]

const filteredRows = computed(() => {
  const needle = search.value.toLowerCase()
  if (!needle) return rows.value
  return rows.value.filter((item) => {
    const roles = item.roles.map((role) => role.name).join(' ')
    return `${item.username} ${item.display_name || ''} ${item.email || ''} ${roles}`.toLowerCase().includes(needle)
  })
})

const adminCount = computed(() => rows.value.filter((item) => item.roles.some((role) => role.name === 'admin')).length)
const ldapCount = computed(() => rows.value.filter((item) => item.auth_source === 'ldap').length)
const localCount = computed(() => rows.value.filter((item) => item.auth_source === 'local').length)

function resetForm() {
  form.username = ''
  form.display_name = ''
  form.email = ''
  form.auth_source = 'local'
  form.ldap_dn = ''
  form.password = ''
  form.role_names = ['operator']
  form.is_active = true
}

function openCreate() {
  editingId.value = null
  resetForm()
  isEditorOpen.value = true
}

function openEdit(row: UserRow) {
  editingId.value = row.id
  form.username = row.username
  form.display_name = row.display_name || ''
  form.email = row.email || ''
  form.auth_source = row.auth_source
  form.ldap_dn = row.ldap_dn || ''
  form.password = ''
  form.role_names = row.roles.map((role) => role.name)
  form.is_active = row.is_active
  isEditorOpen.value = true
}

function closeEditor() {
  isEditorOpen.value = false
  editingId.value = null
}

async function load() {
  isLoading.value = true
  try {
    const [usersRes, rolesRes] = await Promise.all([api.get('/users'), api.get('/users/roles')])
    rows.value = usersRes.data.data || []
    roleOptions.value = (rolesRes.data.data || []).map((role: Role) => role.name)
    if (!roleOptions.value.length) roleOptions.value = ['admin', 'operator', 'viewer']
  } catch (error: any) {
    app.pushToast(error?.response?.data?.message || 'Users data could not be loaded', 'error')
  } finally {
    isLoading.value = false
  }
}

async function saveUser() {
  if (!form.username.trim() && !editingId.value) {
    app.pushToast('Username is required', 'error')
    return
  }
  if (!form.role_names.length) {
    app.pushToast('Select at least one role', 'error')
    return
  }
  if (!editingId.value && form.auth_source === 'local' && form.password.length < 8) {
    app.pushToast('Initial password must be at least 8 characters', 'error')
    return
  }

  isSaving.value = true
  try {
    if (editingId.value) {
      await api.put(`/users/${editingId.value}`, {
        display_name: form.display_name.trim() || null,
        email: form.email.trim() || null,
        ldap_dn: form.auth_source === 'ldap' ? form.ldap_dn.trim() || null : null,
        role_names: form.role_names,
        is_active: !!form.is_active,
      })
      app.pushToast('User updated', 'success')
    } else {
      await api.post('/users', {
        username: form.username.trim(),
        display_name: form.display_name.trim() || null,
        email: form.email.trim() || null,
        auth_source: form.auth_source,
        ldap_dn: form.auth_source === 'ldap' ? form.ldap_dn.trim() || null : null,
        password: form.auth_source === 'local' ? form.password : null,
        role_names: form.role_names,
        is_active: !!form.is_active,
      })
      app.pushToast('User created', 'success')
    }
    closeEditor()
    await load()
  } catch (error: any) {
    app.pushToast(error?.response?.data?.message || 'Unable to save user', 'error')
  } finally {
    isSaving.value = false
  }
}

async function resetPassword(row: UserRow) {
  const newPassword = window.prompt(`Set a new password for ${row.username} (minimum 8 characters):`)
  if (!newPassword) return
  if (newPassword.length < 8) {
    app.pushToast('Password must be at least 8 characters', 'error')
    return
  }
  try {
    await api.post(`/users/${row.id}/reset-password`, { new_password: newPassword })
    app.pushToast('Password updated', 'success')
  } catch (error: any) {
    app.pushToast(error?.response?.data?.message || 'Unable to reset password', 'error')
  }
}

onMounted(load)
</script>
