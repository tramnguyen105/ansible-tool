<template>
  <DrawerPanel :open="open" title="Import Inventory" @close="emitClose">
    <div class="space-y-6">
      <div class="rounded-2xl border border-console-edge bg-console-panel/50 p-4 text-sm text-console-muted">
        Step {{ step }} of 2. Upload an INI, YAML, CSV, or Excel file, review the normalized result, then commit it into the inventory database.
      </div>

      <div v-if="step === 1" class="space-y-4">
        <div>
          <label class="field-label">Source Format</label>
          <select v-model="format" :disabled="isPreviewing">
            <option value="ini">INI</option>
            <option value="yaml">YAML</option>
            <option value="csv">CSV</option>
            <option value="excel">Excel</option>
          </select>
        </div>

        <div>
          <label class="field-label">File</label>
          <input type="file" :disabled="isPreviewing" @change="onFileChange" />
          <p class="mt-2 text-xs text-console-muted">Use preview first so operators can inspect normalized hosts, groups, and warnings before anything is committed.</p>
        </div>

        <div class="flex items-center gap-3">
          <button class="btn-primary" :disabled="isPreviewing || !file" @click="preview">
            {{ isPreviewing ? 'Generating preview...' : 'Generate Preview' }}
          </button>
          <span v-if="selectedFileLabel" class="text-sm text-console-muted">{{ selectedFileLabel }}</span>
        </div>
      </div>

      <div v-else class="space-y-4">
        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <label class="field-label">Inventory Name</label>
            <input v-model="name" :disabled="isImporting" />
          </div>
          <div>
            <label class="field-label">Description</label>
            <input v-model="description" :disabled="isImporting" />
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

        <div class="grid gap-4 md:grid-cols-2">
          <div class="rounded-2xl border border-console-edge bg-console-deep/60 p-4">
            <p class="text-xs uppercase tracking-[0.2em] text-console-muted">Detected Host Column</p>
            <p class="mt-2 text-sm text-white">{{ previewData?.metadata?.host_column || 'N/A' }}</p>
          </div>
          <div class="rounded-2xl border border-console-edge bg-console-deep/60 p-4">
            <p class="text-xs uppercase tracking-[0.2em] text-console-muted">Detected Group Column</p>
            <p class="mt-2 text-sm text-white">{{ previewData?.metadata?.group_column || 'N/A' }}</p>
          </div>
        </div>

        <div v-if="previewData?.metadata?.inferred_variable_columns?.length" class="rounded-2xl border border-console-edge/80 bg-console-deep/50 p-4 text-sm text-console-muted">
          <p class="text-xs uppercase tracking-[0.2em] text-console-muted">Inferred Variable Columns</p>
          <p class="mt-2">{{ previewData.metadata.inferred_variable_columns.join(', ') }}</p>
        </div>

        <div v-if="previewData?.hosts?.length" class="rounded-2xl border border-console-edge bg-console-deep/40 p-4">
          <p class="text-xs uppercase tracking-[0.2em] text-console-muted">Sample Hosts</p>
          <div class="mt-3 overflow-x-auto">
            <table class="min-w-full divide-y divide-console-edge/60 text-sm">
              <thead>
                <tr>
                  <th class="px-2 py-2 text-left text-console-muted">Name</th>
                  <th class="px-2 py-2 text-left text-console-muted">Address</th>
                  <th class="px-2 py-2 text-left text-console-muted">Groups</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-console-edge/40">
                <tr v-for="host in previewData.hosts.slice(0, 6)" :key="host.name">
                  <td class="px-2 py-2 text-white">{{ host.name }}</td>
                  <td class="px-2 py-2 text-console-muted">{{ host.address || 'N/A' }}</td>
                  <td class="px-2 py-2 text-console-muted">{{ host.groups?.length ? host.groups.join(', ') : 'None' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div v-if="previewData?.groups?.length" class="rounded-2xl border border-console-edge bg-console-deep/40 p-4">
          <p class="text-xs uppercase tracking-[0.2em] text-console-muted">Sample Groups</p>
          <div class="mt-3 overflow-x-auto">
            <table class="min-w-full divide-y divide-console-edge/60 text-sm">
              <thead>
                <tr>
                  <th class="px-2 py-2 text-left text-console-muted">Name</th>
                  <th class="px-2 py-2 text-left text-console-muted">Children</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-console-edge/40">
                <tr v-for="group in previewData.groups.slice(0, 6)" :key="group.name">
                  <td class="px-2 py-2 text-white">{{ group.name }}</td>
                  <td class="px-2 py-2 text-console-muted">{{ group.children?.length ? group.children.join(', ') : 'None' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div v-if="previewData?.warnings.length" class="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-100">
          <p v-for="warning in previewData.warnings" :key="warning">{{ warning }}</p>
        </div>

        <div class="rounded-2xl border border-console-edge/80 bg-console-deep/50 p-4 text-sm text-console-muted">
          Review the preview carefully. Unsupported rows or ambiguous grouping should be corrected before import so later job targeting stays predictable.
        </div>

        <div class="flex flex-wrap items-center gap-3">
          <button class="btn-secondary" :disabled="isImporting" @click="step = 1">Back</button>
          <button class="btn-primary" :disabled="isImporting || !canCommit" @click="commit">
            {{ isImporting ? 'Importing inventory...' : 'Import Inventory' }}
          </button>
        </div>
      </div>
    </div>
  </DrawerPanel>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

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
const previewId = ref('')
const previewChecksum = ref('')
const name = ref('')
const description = ref('')
const isPreviewing = ref(false)
const isImporting = ref(false)

const selectedFileLabel = computed(() => file.value?.name ?? '')
const canCommit = computed(() => Boolean(name.value.trim() && previewData.value && previewId.value && previewChecksum.value))

watch(
  () => props.open,
  (open) => {
    if (!open) {
      resetState()
    }
  },
)

function resetState() {
  step.value = 1
  format.value = 'ini'
  file.value = null
  previewData.value = null
  previewId.value = ''
  previewChecksum.value = ''
  name.value = ''
  description.value = ''
  isPreviewing.value = false
  isImporting.value = false
}

function emitClose() {
  emit('close')
}

function onFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  file.value = target.files?.[0] || null
}

async function preview() {
  if (!file.value) {
    app.pushToast('Choose a file before previewing', 'error', 'The import wizard needs a source file to normalize.')
    return
  }

  isPreviewing.value = true
  try {
    const form = new FormData()
    form.append('file', file.value)
    const response = await api.post(`/inventories/import/preview?source_format=${format.value}`, form)
    previewData.value = response.data.data.preview
    previewId.value = response.data.data.preview_id
    previewChecksum.value = response.data.data.checksum
    name.value = file.value.name.replace(/\.[^.]+$/, '')
    step.value = 2
    app.pushToast('Preview generated', 'success', 'Review hosts, groups, and warnings before saving to the inventory database.')
  } catch (error: any) {
    const detail = error?.response?.data?.message ?? 'The uploaded file could not be normalized. Check format selection and source content.'
    app.pushToast('Preview failed', 'error', detail)
  } finally {
    isPreviewing.value = false
  }
}

async function commit() {
  if (!previewData.value) {
    app.pushToast('Generate a preview first', 'error', 'The wizard only imports reviewed normalized data.')
    return
  }
  if (!name.value.trim()) {
    app.pushToast('Inventory name is required', 'error', 'Set a clear inventory name before committing the preview.')
    return
  }

  isImporting.value = true
  try {
    const response = await api.post('/inventories/import/commit', {
      name: name.value.trim(),
      description: description.value.trim(),
      preview_id: previewId.value,
      checksum: previewChecksum.value,
    })
    app.pushToast('Inventory imported', 'success', 'The normalized inventory is now available for targeting and job execution.')
    emit('saved', response.data.data)
    emit('close')
    resetState()
  } catch (error: any) {
    const detail = error?.response?.data?.message ?? 'The preview could not be committed to the database.'
    app.pushToast('Import failed', 'error', detail)
  } finally {
    isImporting.value = false
  }
}
</script>
