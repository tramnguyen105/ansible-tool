<template>
  <DrawerPanel :open="open" title="Import Inventory" @close="$emit('close')">
    <div class="space-y-6">
      <div class="rounded-2xl border border-console-edge bg-console-panel/50 p-4 text-sm text-console-muted">
        Step {{ step }} of 2. Upload an INI, YAML, CSV, or Excel file, review the normalized result, then commit it into the inventory database.
      </div>
      <div v-if="step === 1" class="space-y-4">
        <div>
          <label class="field-label">Source Format</label>
          <select v-model="format">
            <option value="ini">INI</option>
            <option value="yaml">YAML</option>
            <option value="csv">CSV</option>
            <option value="excel">Excel</option>
          </select>
        </div>
        <div>
          <label class="field-label">File</label>
          <input type="file" @change="onFileChange" />
        </div>
        <button class="btn-primary" @click="preview">Generate Preview</button>
      </div>
      <div v-else class="space-y-4">
        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <label class="field-label">Inventory Name</label>
            <input v-model="name" />
          </div>
          <div>
            <label class="field-label">Description</label>
            <input v-model="description" />
          </div>
        </div>
        <div class="grid gap-4 md:grid-cols-3">
          <div class="rounded-2xl border border-console-edge bg-console-deep/60 p-4">
            <p class="text-xs uppercase tracking-[0.2em] text-console-muted">Hosts</p>
            <p class="mt-2 text-2xl font-semibold">{{ previewData?.hosts.length || 0 }}</p>
          </div>
          <div class="rounded-2xl border border-console-edge bg-console-deep/60 p-4">
            <p class="text-xs uppercase tracking-[0.2em] text-console-muted">Groups</p>
            <p class="mt-2 text-2xl font-semibold">{{ previewData?.groups.length || 0 }}</p>
          </div>
          <div class="rounded-2xl border border-console-edge bg-console-deep/60 p-4">
            <p class="text-xs uppercase tracking-[0.2em] text-console-muted">Warnings</p>
            <p class="mt-2 text-2xl font-semibold">{{ previewData?.warnings.length || 0 }}</p>
          </div>
        </div>
        <div v-if="previewData?.warnings.length" class="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-100">
          <p v-for="warning in previewData.warnings" :key="warning">{{ warning }}</p>
        </div>
        <button class="btn-primary" @click="commit">Import Inventory</button>
      </div>
    </div>
  </DrawerPanel>
</template>

<script setup lang="ts">
import { ref } from 'vue'

import api from '../../api/client'
import { useAppStore } from '../../stores/app'
import DrawerPanel from '../common/DrawerPanel.vue'

const props = defineProps<{ open: boolean }>()
const emit = defineEmits(['close', 'saved'])
const app = useAppStore()

const step = ref(1)
const format = ref('ini')
const file = ref<File | null>(null)
const previewData = ref<any>(null)
const name = ref('')
const description = ref('')

function onFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  file.value = target.files?.[0] || null
}

async function preview() {
  if (!file.value) {
    app.pushToast('Choose a file before previewing', 'error')
    return
  }
  const form = new FormData()
  form.append('file', file.value)
  const response = await api.post(`/inventories/import/preview?source_format=${format.value}`, form)
  previewData.value = response.data.data
  name.value = file.value.name.replace(/\.[^.]+$/, '')
  step.value = 2
}

async function commit() {
  const response = await api.post('/inventories/import/commit', {
    name: name.value,
    description: description.value,
    preview: previewData.value,
  })
  app.pushToast('Inventory imported', 'success')
  emit('saved', response.data.data)
  emit('close')
  step.value = 1
  previewData.value = null
}
</script>
