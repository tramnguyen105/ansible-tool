<template>
  <DrawerPanel :open="open" title="Run Job" @close="$emit('close')">
    <div class="space-y-5">
      <div class="rounded-2xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-100">
        Live execution targets production infrastructure. Review inventory, credential, and playbook selections before queueing the job.
      </div>
      <div class="grid gap-4 md:grid-cols-2">
        <div>
          <label class="field-label">Job Name</label>
          <input v-model="form.name" />
        </div>
        <div>
          <label class="field-label">Target Type</label>
          <select v-model="form.target_type">
            <option value="all">All</option>
            <option value="hosts">Hosts</option>
            <option value="groups">Groups</option>
          </select>
        </div>
        <div>
          <label class="field-label">Inventory</label>
          <select v-model="form.inventory_id">
            <option v-for="item in inventories" :key="item.id" :value="item.id">{{ item.name }}</option>
          </select>
        </div>
        <div>
          <label class="field-label">Credential</label>
          <select v-model="form.credential_id">
            <option v-for="item in credentials" :key="item.id" :value="item.id">{{ item.name }}</option>
          </select>
        </div>
        <div>
          <label class="field-label">Playbook</label>
          <select v-model="form.playbook_id">
            <option v-for="item in playbooks" :key="item.id" :value="item.id">{{ item.name }}</option>
          </select>
        </div>
        <div>
          <label class="field-label">Target Value</label>
          <input v-model="form.target_value" placeholder="core-switches or router01,router02" />
        </div>
      </div>
      <div class="flex items-center gap-3 text-sm text-console-muted">
        <input v-model="form.check_mode" type="checkbox" class="w-auto" />
        Run in Ansible check mode
      </div>
      <div>
        <label class="field-label">Extra Vars JSON</label>
        <textarea v-model="extraVarsText"></textarea>
      </div>
      <button class="btn-primary" @click="submit">Queue Job</button>
    </div>
  </DrawerPanel>
</template>

<script setup lang="ts">
import { reactive, ref, watch } from 'vue'

import api from '../../api/client'
import { useAppStore } from '../../stores/app'
import DrawerPanel from '../common/DrawerPanel.vue'

const props = defineProps<{ open: boolean }>()
const emit = defineEmits(['close', 'saved'])
const app = useAppStore()

const inventories = ref<any[]>([])
const credentials = ref<any[]>([])
const playbooks = ref<any[]>([])
const extraVarsText = ref('{}')
const form = reactive({
  name: 'network-change',
  inventory_id: '',
  credential_id: '',
  playbook_id: '',
  target_type: 'all',
  target_value: '',
  check_mode: false,
})

watch(
  () => props.open,
  async (value) => {
    if (!value) return
    const [inventoryResp, credentialResp, playbookResp] = await Promise.all([
      api.get('/inventories'),
      api.get('/credentials'),
      api.get('/playbooks'),
    ])
    inventories.value = inventoryResp.data.data
    credentials.value = credentialResp.data.data
    playbooks.value = playbookResp.data.data
    form.inventory_id = inventories.value[0]?.id || ''
    form.credential_id = credentials.value[0]?.id || ''
    form.playbook_id = playbooks.value[0]?.id || ''
  },
  { immediate: true },
)

async function submit() {
  const payload = {
    ...form,
    extra_vars: JSON.parse(extraVarsText.value || '{}'),
    execute_now: true,
  }
  const response = await api.post('/jobs', payload)
  app.pushToast('Job queued', 'success')
  emit('saved', response.data.data)
  emit('close')
}
</script>
