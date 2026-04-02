<template>
  <div>
    <PageHeader
      title="CLI Converter"
      eyebrow="Deterministic Transformation"
      description="Convert Cisco IOS and IOS-XE configuration snippets into reusable Ansible artifacts with a controlled, reviewable workflow."
    >
      <button class="btn-secondary" :disabled="isLoading" @click="refreshLinkedArtifacts">{{ isLoading ? 'Refreshing...' : 'Refresh artifacts' }}</button>
      <RouterLink class="btn-primary" to="/playbooks">Review playbooks</RouterLink>
    </PageHeader>

    <div class="grid gap-4 xl:grid-cols-3">
      <CardStat label="Generated playbooks" :value="playbooks.length" tone="playbooks" :helper="playbooks.length ? 'Converted playbooks saved from the wizard.' : 'No generated playbooks saved yet.'" />
      <CardStat label="Generated templates" :value="templates.length" tone="templates" :helper="templates.length ? 'Template artifacts are available for reuse.' : 'No generated templates saved yet.'" />
      <CardStat label="Recent conversions" :value="history.length" tone="reviewed" helper="Recent conversion jobs are tracked for audit and replay." />
    </div>

    <div class="mt-6 grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
      <section class="rounded-3xl border border-console-edge bg-console-panel/80 p-5 shadow-xl shadow-slate-300/25">
        <div class="mb-5 rounded-2xl border border-cyan-500/20 bg-cyan-50 px-4 py-4 text-sm text-cyan-700">
          <p class="font-semibold uppercase tracking-[0.2em] text-cyan-200">Conversion workflow</p>
          <p class="mt-2 leading-6 text-console-ink/90">
            Paste Cisco CLI, choose an output type, review parser warnings, then save the artifact only after the raw YAML or template output looks intentional.
          </p>
        </div>
        <CliConversionWizard @saved="refreshLinkedArtifacts" />
      </section>

      <div class="space-y-6">
        <DataTable
          title="Generated Playbooks"
          description="Recently saved playbooks created from the conversion workflow."
          :columns="artifactColumns"
          :rows="playbooks"
          :loading="isLoading"
          loading-title="Loading generated playbooks"
          loading-description="Collecting generated playbook artifacts from the playbook library."
          empty-title="No generated playbooks saved"
          empty-description="Use the converter to generate and save a playbook after reviewing warnings and output."
          compact
        >
          <template #name="{ row }">
            <div>
              <p class="font-medium text-slate-900">{{ row.name }}</p>
              <p class="mt-1 text-xs text-console-muted">{{ row.description || 'Generated from CLI conversion' }}</p>
            </div>
          </template>
        </DataTable>

        <DataTable
          title="Generated Templates"
          description="Template artifacts saved from parsed Cisco configuration."
          :columns="artifactColumns"
          :rows="templates"
          :loading="isLoading"
          loading-title="Loading generated templates"
          loading-description="Collecting saved template artifacts from the template library."
          empty-title="No generated templates saved"
          empty-description="Save a reusable template when the config should stay parameterized instead of locked into one playbook."
          compact
        >
          <template #name="{ row }">
            <div>
              <p class="font-medium text-slate-900">{{ row.name }}</p>
              <p class="mt-1 text-xs text-console-muted">{{ row.description || 'Generated from CLI conversion' }}</p>
            </div>
          </template>
        </DataTable>

        <DataTable
          title="Conversion History"
          description="Most recent converter jobs with warning totals and output type."
          :columns="historyColumns"
          :rows="history"
          :loading="isLoading"
          loading-title="Loading conversion history"
          loading-description="Collecting recent CLI conversion jobs."
          empty-title="No conversion history"
          empty-description="Parse and generate a configuration to create history entries."
          compact
        >
          <template #output_type="{ row }">
            <span class="text-console-muted">{{ row.output_type }}</span>
          </template>
          <template #warning_count="{ row }">
            <span class="text-console-muted">{{ row.warning_count }}</span>
          </template>
          <template #created_at="{ row }">
            <span class="text-console-muted">{{ formatDateTime(row.created_at) }}</span>
          </template>
        </DataTable>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import api from '../../api/client'
import CardStat from '../../components/common/CardStat.vue'
import DataTable from '../../components/common/DataTable.vue'
import PageHeader from '../../components/common/PageHeader.vue'
import CliConversionWizard from '../../components/wizards/CliConversionWizard.vue'
import { useAppStore } from '../../stores/app'
import { formatDateTime } from '../../utils/format'

const app = useAppStore()
const playbooks = ref<any[]>([])
const templates = ref<any[]>([])
const history = ref<any[]>([])
const isLoading = ref(true)
const artifactColumns = [{ key: 'name', label: 'Artifact' }]
const historyColumns = [
  { key: 'output_type', label: 'Output' },
  { key: 'warning_count', label: 'Warnings' },
  { key: 'created_at', label: 'Created' },
]

async function refreshLinkedArtifacts() {
  isLoading.value = true
  try {
    const [playbookResp, templateResp, historyResp] = await Promise.all([
      api.get('/playbooks/summary?generated=true'),
      api.get('/templates/summary?source_type=converter'),
      api.get('/cli-converter/history?limit=12'),
    ])
    playbooks.value = playbookResp.data.data
    templates.value = templateResp.data.data
    history.value = historyResp.data.data
  } catch {
    app.pushToast('Generated artifacts could not be refreshed', 'error', 'Check API reachability and retry artifact synchronization.')
  } finally {
    isLoading.value = false
  }
}

onMounted(refreshLinkedArtifacts)
</script>
