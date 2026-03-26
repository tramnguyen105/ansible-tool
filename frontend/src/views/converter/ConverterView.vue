<template>
  <div>
    <PageHeader title="CLI Converter" eyebrow="Deterministic Transformation" description="Convert Cisco IOS / IOS-XE CLI into a reusable template, a task list, or a full playbook.">
      <button class="btn-secondary" @click="refreshLinkedArtifacts">Refresh Saved Artifacts</button>
    </PageHeader>
    <div class="grid gap-6 xl:grid-cols-[1.25fr_0.9fr]">
      <div class="rounded-3xl border border-console-edge bg-console-panel/70 p-5">
        <CliConversionWizard @saved="refreshLinkedArtifacts" />
      </div>
      <div class="space-y-6">
        <div class="rounded-3xl border border-console-edge bg-console-panel/70 p-5">
          <h3 class="text-lg font-semibold">Generated Playbooks</h3>
          <div class="mt-4 space-y-3 text-sm">
            <div v-for="item in playbooks" :key="item.id" class="rounded-2xl border border-console-edge/80 bg-console-deep/70 px-4 py-3">{{ item.name }}</div>
          </div>
        </div>
        <div class="rounded-3xl border border-console-edge bg-console-panel/70 p-5">
          <h3 class="text-lg font-semibold">Generated Templates</h3>
          <div class="mt-4 space-y-3 text-sm">
            <div v-for="item in templates" :key="item.id" class="rounded-2xl border border-console-edge/80 bg-console-deep/70 px-4 py-3">{{ item.name }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import api from '../../api/client'
import PageHeader from '../../components/common/PageHeader.vue'
import CliConversionWizard from '../../components/wizards/CliConversionWizard.vue'

const playbooks = ref<any[]>([])
const templates = ref<any[]>([])

async function refreshLinkedArtifacts() {
  const [playbookResp, templateResp] = await Promise.all([api.get('/playbooks'), api.get('/templates')])
  playbooks.value = playbookResp.data.data.filter((item: any) => item.is_generated)
  templates.value = templateResp.data.data
}

onMounted(refreshLinkedArtifacts)
</script>
