<template>
  <div class="space-y-6">
    <div class="rounded-2xl border border-console-edge bg-console-panel/60 p-4 text-sm text-console-muted">
      Step {{ step }} of 3. Paste Cisco IOS/IOS-XE configuration, choose the output artifact, then review and save the generated result.
    </div>
    <div v-if="step === 1" class="space-y-4">
      <label class="field-label">Cisco Configuration</label>
      <textarea v-model="configText" class="min-h-[240px] font-mono"></textarea>
      <button class="btn-primary" @click="parse">Parse Configuration</button>
    </div>
    <div v-else-if="step === 2" class="space-y-4">
      <div class="grid gap-4 md:grid-cols-3">
        <div class="rounded-2xl border border-console-edge bg-console-deep/60 p-4">
          <p class="text-xs uppercase tracking-[0.2em] text-console-muted">Global Lines</p>
          <p class="mt-2 text-2xl font-semibold">{{ parsed?.global_lines.length || 0 }}</p>
        </div>
        <div class="rounded-2xl border border-console-edge bg-console-deep/60 p-4">
          <p class="text-xs uppercase tracking-[0.2em] text-console-muted">Blocks</p>
          <p class="mt-2 text-2xl font-semibold">{{ parsed?.blocks.length || 0 }}</p>
        </div>
        <div class="rounded-2xl border border-console-edge bg-console-deep/60 p-4">
          <p class="text-xs uppercase tracking-[0.2em] text-console-muted">Warnings</p>
          <p class="mt-2 text-2xl font-semibold">{{ parsed?.warnings.length || 0 }}</p>
        </div>
      </div>
      <div>
        <label class="field-label">Output Type</label>
        <select v-model="outputType">
          <option value="template">Reusable Jinja2 Template</option>
          <option value="tasks">Ansible Task List</option>
          <option value="playbook">Full Playbook</option>
        </select>
      </div>
      <button class="btn-primary" @click="generate">Generate Artifact</button>
    </div>
    <div v-else class="space-y-4">
      <div v-if="generated?.warnings.length" class="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-100">
        <p v-for="warning in generated.warnings" :key="warning">{{ warning }}</p>
      </div>
      <YamlEditor v-model="generatedContent" />
      <div class="grid gap-4 md:grid-cols-2">
        <div>
          <label class="field-label">Artifact Name</label>
          <input v-model="artifactName" />
        </div>
        <div>
          <label class="field-label">Description</label>
          <input v-model="artifactDescription" />
        </div>
      </div>
      <div class="flex gap-3">
        <button class="btn-primary" @click="save">Save</button>
        <button class="btn-secondary" @click="step = 2">Back</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

import api from '../../api/client'
import { useAppStore } from '../../stores/app'
import YamlEditor from '../forms/YamlEditor.vue'

const emit = defineEmits(['saved'])
const app = useAppStore()

const step = ref(1)
const configText = ref('')
const outputType = ref('playbook')
const parsed = ref<any>(null)
const generated = ref<any>(null)
const generatedContent = ref('')
const artifactName = ref('generated-artifact')
const artifactDescription = ref('Generated from Cisco CLI')

async function parse() {
  const response = await api.post('/cli-converter/parse', { config_text: configText.value })
  parsed.value = response.data.data
  step.value = 2
}

async function generate() {
  const response = await api.post('/cli-converter/generate', {
    config_text: configText.value,
    output_type: outputType.value,
  })
  generated.value = response.data.data
  generatedContent.value = generated.value.generated_content
  artifactName.value = `generated-${outputType.value}`
  step.value = 3
}

async function save() {
  if (outputType.value === 'template') {
    await api.post('/cli-converter/save-as-template', {
      name: artifactName.value,
      description: artifactDescription.value,
      generated_content: generatedContent.value,
      source_config: configText.value,
    })
  } else {
    await api.post('/cli-converter/save-as-playbook', {
      name: artifactName.value,
      description: artifactDescription.value,
      generated_content: generatedContent.value,
      source_config: configText.value,
    })
  }
  app.pushToast('Generated artifact saved', 'success')
  emit('saved')
}
</script>
