<template>
  <div>
    <PageHeader title="Settings" eyebrow="System Context" description="Read-only operational settings surfaced from the backend for environment awareness." />
    <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <CardStat label="App" :value="settings.app_name || 'n/a'" tone="identity" />
      <CardStat label="Environment" :value="settings.environment || 'n/a'" tone="runtime" />
      <CardStat label="LDAP" :value="settings.ldap_enabled ? 'Enabled' : 'Disabled'" tone="auth" />
      <CardStat label="Session TTL" :value="settings.session_ttl_minutes || 'n/a'" tone="minutes" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive } from 'vue'

import api from '../api/client'
import CardStat from '../components/common/CardStat.vue'
import PageHeader from '../components/common/PageHeader.vue'

const settings = reactive<any>({})

onMounted(async () => {
  const response = await api.get('/system/settings')
  Object.assign(settings, response.data.data)
})
</script>
