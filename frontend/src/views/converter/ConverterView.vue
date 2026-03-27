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
      <CardStat label="Workflow" value="Guided" tone="reviewed" helper="Operators can parse, validate, edit, and save before execution." />
    </div>

    <div class="mt-6 grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
      <section class="rounded-3xl border border-console-edge bg-console-panel/80 p-5 shadow-xl shadow-slate-950/20">
        <div class="mb-5 rounded-2xl border border-cyan-500/20 bg-cyan-500/8 px-4 py-4 text-sm text-cyan-50">
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
              <p class="font-medium text-white">{{ row.name }}</p>
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
              <p class="font-medium text-white">{{ row.name }}</p>
              <p class="mt-1 text-xs text-console-muted">{{ row.description || 'Generated from CLI conversion' }}</p>
            </div>
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

const app = useAppStore()
const playbooks = ref<any[]>([])
const templates = ref<any[]>([])
const isLoading = ref(true)
const artifactColumns = [{ key: 'name', label: 'Artifact' }]

async function refreshLinkedArtifacts() {
  isLoading.value = true
  try {
    const [playbookResp, templateResp] = await Promise.all([api.get('/playbooks'), api.get('/templates')])
    playbooks.value = playbookResp.data.data.filter((item: any) => item.is_generated)
    templates.value = templateResp.data.data
  } catch {
    app.pushToast('Generated artifacts could not be refreshed', 'error', 'Check API reachability and retry artifact synchronization.')
  } finally {
    isLoading.value = false
  }
}

onMounted(refreshLinkedArtifacts)
</script>
