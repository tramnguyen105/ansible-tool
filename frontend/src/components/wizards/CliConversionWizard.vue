<template>
  <div class="space-y-6">
    <div class="rounded-2xl border border-console-edge bg-console-panel/60 p-4 text-sm text-console-muted">
      Step {{ step }} of 3. Paste Cisco IOS/IOS-XE configuration, choose the output artifact, then review and save the generated result.
    </div>

    <div v-if="step === 1" class="space-y-4">
      <label class="field-label">Cisco Configuration</label>
      <textarea v-model="configText" :disabled="isParsing" class="min-h-[240px] font-mono"></textarea>
      <button class="btn-primary" :disabled="isParsing || !configText.trim()" @click="parse">{{ isParsing ? 'Parsing...' : 'Parse Configuration' }}</button>
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
      <div v-if="parsed?.warnings?.length" class="rounded-2xl border border-amber-500/30 bg-amber-50 p-4 text-sm text-amber-700">
        <p class="mb-2 font-semibold uppercase tracking-[0.18em] text-amber-200">Parser warnings</p>
        <p v-for="warning in parsed.warnings" :key="`${warning.code}-${warning.line || 0}-${warning.message}`">
          {{ warning.line ? `Line ${warning.line}: ` : '' }}{{ warning.message }}
        </p>
      </div>
      <div>
        <label class="field-label">Output Type</label>
        <select v-model="outputType" :disabled="isGenerating">
          <option value="template">Reusable Jinja2 Template</option>
          <option value="tasks">Ansible Task List</option>
          <option value="playbook">Full Playbook</option>
        </select>
      </div>
      <div class="flex gap-3">
        <button class="btn-secondary" :disabled="isGenerating" @click="step = 1">Back</button>
        <button class="btn-primary" :disabled="isGenerating || !parsed" @click="generate">{{ isGenerating ? 'Generating...' : 'Generate Artifact' }}</button>
      </div>
    </div>

    <div v-else class="space-y-4">
      <div v-if="generated?.warnings.length" class="rounded-2xl border border-amber-500/30 bg-amber-50 p-4 text-sm text-amber-700">
        <p v-for="warning in generated.warnings" :key="`${warning.code}-${warning.line || 0}-${warning.message}`">
          {{ warning.line ? `Line ${warning.line}: ` : '' }}{{ warning.message }}
        </p>
      </div>
      <YamlEditor v-model="generatedContent" />
      <div class="rounded-2xl border border-console-edge bg-console-deep/50 p-4 text-sm">
        <p class="text-console-muted">
          Save mode:
          <span class="text-slate-900" v-if="outputType === 'template'">Template artifact</span>
          <span class="text-slate-900" v-else-if="outputType === 'tasks'">Task list will be wrapped into a runnable playbook on save</span>
          <span class="text-slate-900" v-else>Full playbook artifact</span>
        </p>
      </div>
      <div class="grid gap-4 md:grid-cols-2">
        <div>
          <label class="field-label">Artifact Name</label>
          <input v-model="artifactName" :disabled="isSaving" />
        </div>
        <div>
          <label class="field-label">Description</label>
          <input v-model="artifactDescription" :disabled="isSaving" />
        </div>
      </div>
      <div v-if="validationMessage" class="rounded-2xl border px-4 py-3 text-sm" :class="validationValid ? 'border-emerald-500/30 bg-emerald-50 text-emerald-700' : 'border-rose-500/30 bg-rose-50 text-rose-700'">
        {{ validationMessage }}
      </div>
      <div class="flex gap-3">
        <button class="btn-secondary" :disabled="isSaving || isValidating || !generatedContent.trim()" @click="validateGenerated">
          {{ isValidating ? 'Validating...' : 'Validate Artifact' }}
        </button>
        <button class="btn-primary" :disabled="isSaving || !generatedContent.trim() || !artifactName.trim() || !validationValid" @click="save">{{ isSaving ? 'Saving...' : 'Save' }}</button>
        <button class="btn-secondary" :disabled="isSaving" @click="step = 2">Back</button>
        <button class="btn-secondary" :disabled="isSaving || isParsing || isGenerating || isValidating" @click="resetWizard">Start New</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineAsyncComponent, ref, watch } from 'vue'

import api from '../../api/client'
import { useAppStore } from '../../stores/app'
const emit = defineEmits(['saved'])
const app = useAppStore()
const YamlEditor = defineAsyncComponent(() => import('../forms/YamlEditor.vue'))

const step = ref(1)
const configText = ref('')
const outputType = ref('playbook')
const parsed = ref<any>(null)
const generated = ref<any>(null)
const generatedContent = ref('')
const artifactName = ref('generated-artifact')
const artifactDescription = ref('Generated from Cisco CLI')
const isParsing = ref(false)
const isGenerating = ref(false)
const isSaving = ref(false)
const isValidating = ref(false)
const validationValid = ref(false)
const validationMessage = ref('')

watch(generatedContent, () => {
  if (step.value !== 3) return
  if (!validationValid.value && !validationMessage.value) return
  validationValid.value = false
  validationMessage.value = 'Generated content changed. Validate again before saving.'
})

async function parse() {
  isParsing.value = true
  try {
    const response = await api.post('/cli-converter/parse', { config_text: configText.value.trim() })
    parsed.value = response.data.data
    generated.value = null
    generatedContent.value = ''
    validationValid.value = false
    validationMessage.value = ''
    step.value = 2
    app.pushToast('CLI parsed', 'success', 'Review parser warnings before generating an artifact.')
  } catch (error: any) {
    app.pushToast(error?.response?.data?.message || 'CLI parsing failed', 'error')
  } finally {
    isParsing.value = false
  }
}

async function generate() {
  isGenerating.value = true
  try {
    const response = await api.post('/cli-converter/generate', {
      config_text: configText.value.trim(),
      output_type: outputType.value,
      parsed: parsed.value,
    })
    generated.value = response.data.data
    generatedContent.value = generated.value.generated_content
    artifactName.value = `generated-${outputType.value}`
    validationValid.value = false
    validationMessage.value = 'Validate generated content before saving.'
    step.value = 3
    app.pushToast('Artifact generated', 'success', 'Review the generated output and warnings before saving.')
  } catch (error: any) {
    app.pushToast(error?.response?.data?.message || 'Artifact generation failed', 'error')
  } finally {
    isGenerating.value = false
  }
}

async function validateGenerated() {
  isValidating.value = true
  try {
    const response = await api.post('/cli-converter/validate-generated', {
      output_type: outputType.value,
      generated_content: generatedContent.value,
    })
    const result = response.data.data
    validationValid.value = Boolean(result.valid)
    if (validationValid.value) {
      if (result.normalized_content && outputType.value !== 'template') {
        generatedContent.value = result.normalized_content
      }
      validationMessage.value = 'Generated artifact is valid for save.'
      app.pushToast('Artifact validation passed', 'success')
    } else {
      validationMessage.value = (result.errors || []).join(' | ') || 'Validation failed.'
      app.pushToast('Artifact validation failed', 'error')
    }
  } catch (error: any) {
    validationValid.value = false
    validationMessage.value = error?.response?.data?.message || 'Artifact validation failed'
    app.pushToast(validationMessage.value, 'error')
  } finally {
    isValidating.value = false
  }
}

async function save() {
  if (!validationValid.value) {
    app.pushToast('Validate generated content before saving', 'error')
    return
  }
  isSaving.value = true
  try {
    const payload = {
      name: artifactName.value.trim(),
      description: artifactDescription.value.trim(),
      generated_content: generatedContent.value,
      conversion_job_id: generated.value?.conversion_job_id || null,
      output_type: outputType.value,
    }
    if (outputType.value === 'template') {
      await api.post('/cli-converter/save-as-template', payload)
    } else {
      await api.post('/cli-converter/save-as-playbook', payload)
    }
    app.pushToast('Generated artifact saved', 'success', 'The artifact is now available in the library view.')
    emit('saved')
    resetWizard()
  } catch (error: any) {
    app.pushToast(error?.response?.data?.message || 'Generated artifact could not be saved', 'error')
  } finally {
    isSaving.value = false
  }
}

function resetWizard() {
  step.value = 1
  outputType.value = 'playbook'
  parsed.value = null
  generated.value = null
  generatedContent.value = ''
  artifactName.value = 'generated-artifact'
  artifactDescription.value = 'Generated from Cisco CLI'
  validationValid.value = false
  validationMessage.value = ''
}
</script>
