<template>
  <div>
    <PageHeader
      title="Settings"
      eyebrow="System Context"
      description="Read-only environment context surfaced from the backend so operators understand the current runtime posture before they run automation."
    />

    <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <CardStat label="Application" :value="settings.app_name || 'n/a'" tone="identity" helper="Runtime application name returned by the backend." />
      <CardStat label="Environment" :value="settings.environment || 'n/a'" tone="runtime" helper="Use development values only for lab testing, not production change control." />
      <CardStat label="LDAP" :value="settings.ldap_enabled ? 'Enabled' : 'Disabled'" tone="auth" helper="Current authentication mode exposed to the UI." />
      <CardStat label="Session TTL" :value="ttlLabel" tone="minutes" helper="Configured browser session lifetime before re-authentication is required." />
    </div>

    <section class="mt-6 rounded-3xl border border-console-edge bg-console-panel/80 p-5 shadow-xl shadow-slate-950/20">
      <p class="text-xs uppercase tracking-[0.22em] text-console-glow">Operator Guidance</p>
      <h3 class="mt-2 text-xl font-semibold text-white">Current runtime posture</h3>
      <div class="mt-5 grid gap-4 lg:grid-cols-3">
        <div class="rounded-2xl border border-console-edge/70 bg-console-deep/60 p-4 text-sm text-console-ink/90">
          <p class="text-xs uppercase tracking-[0.18em] text-console-muted">Authentication</p>
          <p class="mt-3">{{ settings.ldap_enabled ? 'LDAP is active for sign-in. Local access should remain restricted.' : 'Local authentication is enabled. This is appropriate for lab validation only.' }}</p>
        </div>
        <div class="rounded-2xl border border-console-edge/70 bg-console-deep/60 p-4 text-sm text-console-ink/90">
          <p class="text-xs uppercase tracking-[0.18em] text-console-muted">Environment</p>
          <p class="mt-3">{{ settings.environment === 'production' ? 'Treat all jobs as production-impacting changes.' : 'This runtime is marked as non-production. Validate UI and workflow behavior before hardening for production.' }}</p>
        </div>
        <div class="rounded-2xl border border-console-edge/70 bg-console-deep/60 p-4 text-sm text-console-ink/90">
          <p class="text-xs uppercase tracking-[0.18em] text-console-muted">Session behavior</p>
          <p class="mt-3">Operator sessions currently expire after {{ ttlLabel }}. Long-running job review should account for re-authentication windows.</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive } from 'vue'

import api from '../api/client'
import CardStat from '../components/common/CardStat.vue'
import PageHeader from '../components/common/PageHeader.vue'
import { useAppStore } from '../stores/app'

const app = useAppStore()
const settings = reactive<any>({})
const ttlLabel = computed(() => (settings.session_ttl_minutes ? `${settings.session_ttl_minutes} minutes` : 'n/a'))

onMounted(async () => {
  try {
    const response = await api.get('/system/settings')
    Object.assign(settings, response.data.data)
  } catch {
    app.pushToast('System settings could not be loaded', 'error')
  }
})
</script>
