<template>
  <div>
    <PageHeader title="Audit Logs" eyebrow="Immutable Activity" description="Review authentication, credential usage, playbook edits, and job execution events." />
    <div class="mb-4 grid gap-4 md:grid-cols-4">
      <input v-model="filters.action" placeholder="Action" />
      <input v-model="filters.resource_type" placeholder="Resource type" />
      <input v-model="filters.status" placeholder="Status" />
      <button class="btn-primary" @click="load">Apply Filters</button>
    </div>
    <DataTable :columns="columns" :rows="rows" row-key="id" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'

import api from '../../api/client'
import DataTable from '../../components/common/DataTable.vue'
import PageHeader from '../../components/common/PageHeader.vue'

const rows = ref<any[]>([])
const filters = reactive({ action: '', resource_type: '', status: '' })
const columns = [
  { key: 'created_at', label: 'Time' },
  { key: 'action', label: 'Action' },
  { key: 'resource_type', label: 'Resource' },
  { key: 'status', label: 'Status' },
  { key: 'message', label: 'Message' },
]

async function load() {
  const response = await api.get('/audit-logs', { params: { ...filters } })
  rows.value = response.data.data
}

onMounted(load)
</script>
