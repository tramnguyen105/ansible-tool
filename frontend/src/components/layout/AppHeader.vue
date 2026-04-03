<template>
  <header class="border-b border-console-edge/70 bg-console-panel/90 px-4 py-4 backdrop-blur sm:px-6 lg:px-8">
    <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
      <div>
        <p class="text-[0.76rem] font-semibold uppercase tracking-[0.22em] text-console-glow">Workspace</p>
        <p class="mt-1 text-[1.2rem] font-semibold text-slate-900">{{ pageTitle }}</p>
        <p class="mt-0.5 text-[0.96rem] text-console-muted">{{ pageSubtitle }}</p>
      </div>

      <div class="flex flex-wrap items-center gap-2 md:justify-end">
        <span class="rounded-full border border-console-edge/80 bg-white/70 px-3 py-1 text-[0.72rem] font-medium uppercase tracking-[0.1em] text-slate-700">
          {{ environmentLabel }}
        </span>
        <span class="rounded-full border border-console-edge/80 bg-white/70 px-3 py-1.5 text-[0.96rem] text-slate-700">
          {{ auth.user?.display_name || auth.user?.username }}
        </span>
        <button class="rounded-full border border-console-edge/80 bg-white/70 px-4 py-1.5 text-[0.96rem] text-slate-800 transition hover:bg-white" @click="logout">
          Sign out
        </button>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import api from '../../api/client'
import { useAppStore } from '../../stores/app'
import { useAuthStore } from '../../stores/auth'

const auth = useAuthStore()
const app = useAppStore()
const route = useRoute()
const router = useRouter()
const environment = ref('runtime')

const routeMeta: Record<string, { title: string; subtitle: string }> = {
  '/': { title: 'Dashboard', subtitle: 'Current job activity, schedules, and automation readiness.' },
  '/inventory': { title: 'Inventory', subtitle: 'Managed hosts, groups, and imported sources.' },
  '/credentials': { title: 'Credentials', subtitle: 'Stored credentials available for automation runs.' },
  '/templates': { title: 'Templates', subtitle: 'Reusable templates for generated automation content.' },
  '/playbooks': { title: 'Playbooks', subtitle: 'Runbook definitions and generated automation artifacts.' },
  '/converter': { title: 'CLI Converter', subtitle: 'Convert device CLI input into reusable automation content.' },
  '/jobs': { title: 'Jobs', subtitle: 'Execution history and active automation runs.' },
  '/schedules': { title: 'Schedules', subtitle: 'Planned automation runs and recurring execution.' },
  '/audit': { title: 'Audit Logs', subtitle: 'Authentication, change, and execution records.' },
  '/users': { title: 'Users', subtitle: 'RBAC assignments and local or LDAP user accounts.' },
  '/settings': { title: 'Settings', subtitle: 'Runtime posture and environment context.' },
}

const currentMeta = computed(() => {
  const matched = Object.entries(routeMeta).find(([path]) => route.path === path || route.path.startsWith(path + '/'))
  return matched?.[1] || { title: 'Ansible Automation Console', subtitle: 'Network automation operations.' }
})

const pageTitle = computed(() => currentMeta.value.title)
const pageSubtitle = computed(() => currentMeta.value.subtitle)
const environmentLabel = computed(() => environment.value || 'runtime')

onMounted(async () => {
  try {
    const response = await api.get('/health')
    environment.value = response.data.data?.environment || 'runtime'
  } catch {
    environment.value = 'runtime'
  }
})

async function logout() {
  await auth.logout()
  app.pushToast('Session closed', 'info')
  router.push('/login')
}
</script>
