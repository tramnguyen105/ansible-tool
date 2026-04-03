<template>
  <DrawerPanel :open="open" title="Run Job" @close="emitClose">
    <div class="space-y-5">
      <BannerNotice title="Execution safety" tone="warn" text="Check mode stays enabled by default. Only launch live execution after reviewing the target scope, credential, and playbook." />

      <div v-if="formError" class="rounded-2xl border border-rose-500/30 bg-rose-50 p-4 text-sm text-rose-700">
        {{ formError }}
      </div>

      <div v-if="isLoadingLookups" class="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
        Loading inventories, credentials, and playbooks...
      </div>

      <div class="grid gap-2 sm:grid-cols-4">
        <button v-for="step in steps" :key="step.key" class="rounded-2xl border px-3 py-3 text-left transition"
          :class="stepKey === step.key ? 'border-console-glow bg-console-glow/10 text-slate-900' : 'border-console-edge text-console-muted hover:border-console-glow/40'"
          @click="stepKey = step.key"
        >
          <p class="text-xs uppercase tracking-[0.14em]">{{ step.eyebrow }}</p>
          <p class="mt-2 text-sm font-semibold">{{ step.label }}</p>
        </button>
      </div>

      <div v-if="stepKey === 'scope'" class="space-y-4">
        <div>
          <label class="field-label">Job name</label>
          <input v-model="form.name" :disabled="isSubmitting || isLoadingLookups" placeholder="edge-switch-check" />
        </div>
        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <label class="field-label">Inventory</label>
            <select v-model="form.inventory_id" :disabled="isSubmitting || isLoadingLookups">
              <option v-for="item in inventories" :key="item.id" :value="item.id">{{ item.name }}</option>
            </select>
          </div>
          <div>
            <label class="field-label">Target type</label>
            <select v-model="form.target_type" :disabled="isSubmitting || isLoadingLookups">
              <option value="all">All managed hosts</option>
              <option value="hosts">Specific hosts</option>
              <option value="groups">Specific groups</option>
            </select>
          </div>
        </div>
        <div>
          <label class="field-label">Target value</label>
          <input v-model="form.target_value" :disabled="isSubmitting || isLoadingLookups" :placeholder="form.target_type === 'all' ? 'Optional selector' : 'Required for hosts or groups'" />
        </div>
      </div>

      <div v-else-if="stepKey === 'automation'" class="space-y-4">
        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <label class="field-label">Credential</label>
            <select v-model="form.credential_id" :disabled="isSubmitting || isLoadingLookups">
              <option v-for="item in credentials" :key="item.id" :value="item.id">{{ item.name }}</option>
            </select>
          </div>
          <div>
            <label class="field-label">Playbook</label>
            <select v-model="form.playbook_id" :disabled="isSubmitting || isLoadingLookups">
              <option v-for="item in playbooks" :key="item.id" :value="item.id">{{ item.name }}</option>
            </select>
          </div>
        </div>
        <label class="flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-[0.97rem] text-slate-700">
          <input v-model="form.check_mode" :disabled="isSubmitting || isLoadingLookups" type="checkbox" class="w-auto" />
          Run in Ansible check mode
        </label>
      </div>

      <div v-else-if="stepKey === 'vars'" class="space-y-4">
        <div>
          <label class="field-label">Extra vars JSON</label>
          <textarea v-model="extraVarsText" :disabled="isSubmitting || isLoadingLookups" placeholder='{"interface":"GigabitEthernet1/0/1"}'></textarea>
        </div>
        <p class="text-sm text-console-muted">Use extra vars only when the playbook already expects them. Keep production overrides minimal and explicit.</p>
      </div>

      <div v-else class="space-y-4">
        <section class="rounded-2xl border border-console-edge/80 bg-console-deep/30 p-4">
          <p class="text-xs uppercase tracking-[0.14em] text-console-muted">Review</p>
          <div class="mt-3 grid gap-3 sm:grid-cols-2">
            <div><p class="text-xs uppercase tracking-[0.12em] text-console-muted">Job name</p><p class="mt-1 text-sm font-semibold text-slate-900">{{ form.name || 'Not set' }}</p></div>
            <div><p class="text-xs uppercase tracking-[0.12em] text-console-muted">Mode</p><p class="mt-1 text-sm font-semibold text-slate-900">{{ form.check_mode ? 'Check mode validation' : 'Live execution' }}</p></div>
            <div><p class="text-xs uppercase tracking-[0.12em] text-console-muted">Inventory</p><p class="mt-1 text-sm font-semibold text-slate-900">{{ selectedInventoryName }}</p></div>
            <div><p class="text-xs uppercase tracking-[0.12em] text-console-muted">Target</p><p class="mt-1 text-sm font-semibold text-slate-900">{{ targetSummary }}</p></div>
            <div><p class="text-xs uppercase tracking-[0.12em] text-console-muted">Credential</p><p class="mt-1 text-sm font-semibold text-slate-900">{{ selectedCredentialName }}</p></div>
            <div><p class="text-xs uppercase tracking-[0.12em] text-console-muted">Playbook</p><p class="mt-1 text-sm font-semibold text-slate-900">{{ selectedPlaybookName }}</p></div>
          </div>
        </section>

        <BannerNotice
          :title="form.check_mode ? 'Validation run' : 'Live execution'"
          :tone="form.check_mode ? 'info' : 'warn'"
          :text="form.check_mode ? 'This run should not make device changes unless the playbook ignores check mode.' : 'This job may immediately change production systems. Confirm scope and credential before queueing.'"
        />
      </div>

      <div class="flex items-center justify-between gap-3">
        <div class="flex gap-2">
          <button class="btn-secondary" :disabled="isSubmitting || stepIndex === 0" @click="previousStep">Back</button>
          <button v-if="stepIndex < steps.length - 1" class="btn-secondary" :disabled="isSubmitting" @click="nextStep">Next</button>
        </div>
        <button class="btn-primary" :disabled="isSubmitting || isLoadingLookups || !canSubmit" @click="submit">
          {{ isSubmitting ? 'Queueing...' : 'Queue job' }}
        </button>
      </div>
    </div>
  </DrawerPanel>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'

import api from '../../api/client'
import { useAppStore } from '../../stores/app'
import BannerNotice from '../common/BannerNotice.vue'
import DrawerPanel from '../common/DrawerPanel.vue'

const props = defineProps<{ open: boolean }>()
const emit = defineEmits(['close', 'saved'])
const app = useAppStore()

const inventories = ref<any[]>([])
const credentials = ref<any[]>([])
const playbooks = ref<any[]>([])
const extraVarsText = ref('{}')
const isSubmitting = ref(false)
const isLoadingLookups = ref(false)
const formError = ref('')
const stepKey = ref<'scope' | 'automation' | 'vars' | 'review'>('scope')
const form = reactive({
  name: '',
  inventory_id: '',
  credential_id: '',
  playbook_id: '',
  target_type: 'all',
  target_value: '',
  check_mode: true,
})

const steps = [
  { key: 'scope', label: 'Scope', eyebrow: 'Step 1' },
  { key: 'automation', label: 'Automation', eyebrow: 'Step 2' },
  { key: 'vars', label: 'Variables', eyebrow: 'Step 3' },
  { key: 'review', label: 'Review', eyebrow: 'Step 4' },
] as const

const stepIndex = computed(() => steps.findIndex((step) => step.key === stepKey.value))
const canSubmit = computed(() => Boolean(form.name.trim() && form.inventory_id && form.credential_id && form.playbook_id && (form.target_type === 'all' || form.target_value.trim())))
const selectedInventoryName = computed(() => inventories.value.find((item) => item.id === form.inventory_id)?.name || 'Not selected')
const selectedCredentialName = computed(() => credentials.value.find((item) => item.id === form.credential_id)?.name || 'Not selected')
const selectedPlaybookName = computed(() => playbooks.value.find((item) => item.id === form.playbook_id)?.name || 'Not selected')
const targetSummary = computed(() => form.target_type === 'all' ? 'All managed hosts' : `${form.target_type}: ${form.target_value.trim() || 'Not set'}`)

function resetState() {
  extraVarsText.value = '{}'
  formError.value = ''
  stepKey.value = 'scope'
  form.name = ''
  form.inventory_id = ''
  form.credential_id = ''
  form.playbook_id = ''
  form.target_type = 'all'
  form.target_value = ''
  form.check_mode = true
}

function emitClose() {
  if (isSubmitting.value) return
  emit('close')
}

async function loadLookups() {
  isLoadingLookups.value = true
  try {
    const [inventoryResp, credentialResp, playbookResp] = await Promise.all([
      api.get('/inventories'),
      api.get('/credentials?active_only=true'),
      api.get('/playbooks'),
    ])
    inventories.value = inventoryResp.data.data
    credentials.value = credentialResp.data.data
    playbooks.value = playbookResp.data.data
    form.inventory_id = inventories.value[0]?.id || ''
    form.credential_id = credentials.value[0]?.id || ''
    form.playbook_id = playbooks.value[0]?.id || ''
  } catch {
    app.pushToast('Job dependencies could not be loaded', 'error', 'Inventories, credentials, and playbooks must be available before queueing a job.')
  } finally {
    isLoadingLookups.value = false
  }
}

function validateCurrentStep() {
  if (stepKey.value === 'scope') {
    if (!form.name.trim()) return 'Job name is required.'
    if (!form.inventory_id) return 'Inventory is required.'
    if (form.target_type !== 'all' && !form.target_value.trim()) return 'Target value is required for hosts or groups.'
  }
  if (stepKey.value === 'automation') {
    if (!form.credential_id || !form.playbook_id) return 'Credential and playbook are required.'
  }
  if (stepKey.value === 'vars') {
    try {
      JSON.parse(extraVarsText.value || '{}')
    } catch {
      return 'Extra vars JSON is invalid.'
    }
  }
  return ''
}

function nextStep() {
  formError.value = validateCurrentStep()
  if (formError.value) return
  if (stepIndex.value < steps.length - 1) stepKey.value = steps[stepIndex.value + 1].key
}

function previousStep() {
  if (stepIndex.value > 0) stepKey.value = steps[stepIndex.value - 1].key
}

watch(
  () => props.open,
  async (value) => {
    if (!value) {
      resetState()
      return
    }
    await loadLookups()
  },
  { immediate: true },
)

async function submit() {
  formError.value = validateCurrentStep() || (!canSubmit.value ? 'Job name, inventory, credential, and playbook are required.' : '')
  if (formError.value) return

  isSubmitting.value = true
  try {
    const payload = {
      ...form,
      name: form.name.trim(),
      target_value: form.target_value.trim() || null,
      extra_vars: JSON.parse(extraVarsText.value || '{}'),
      execute_now: true,
    }
    const response = await api.post('/jobs', payload)
    app.pushToast('Job queued', 'success', 'The worker will execute the job asynchronously.')
    emit('saved', response.data.data)
    emit('close')
    resetState()
  } catch (error: any) {
    if (error instanceof SyntaxError) {
      formError.value = 'Extra vars JSON is invalid.'
      app.pushToast('Extra vars JSON is invalid', 'error', 'Correct the JSON structure before queueing the job.')
      return
    }
    formError.value = error?.response?.data?.message || 'Job could not be queued.'
    app.pushToast(formError.value, 'error')
  } finally {
    isSubmitting.value = false
  }
}
</script>
