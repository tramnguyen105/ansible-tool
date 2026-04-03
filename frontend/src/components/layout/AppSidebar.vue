<template>
  <aside class="pretty-scrollbar border-r border-console-edge/70 bg-console-panel/90 px-4 py-5 backdrop-blur lg:sticky lg:top-0 lg:h-screen lg:overflow-y-auto">
    <div class="mb-6 rounded-2xl border border-console-edge/80 bg-white/60 px-4 py-4">
      <p class="text-[0.76rem] font-semibold uppercase tracking-[0.24em] text-console-glow">Operations Console</p>
      <p class="mt-2 text-[1.05rem] font-semibold text-slate-900">Ansible Automation</p>
      <p class="mt-1 text-[0.84rem] text-console-muted">Network automation operations</p>
    </div>

    <div class="space-y-6">
      <section v-for="group in groups" :key="group.label">
        <p class="px-2 text-[0.76rem] font-medium uppercase tracking-[0.16em] text-console-muted">{{ group.label }}</p>
        <nav class="mt-2 space-y-1">
          <RouterLink
            v-for="item in group.items"
            :key="item.to"
            :to="item.to"
            class="flex items-center rounded-2xl px-3 py-2.5 text-[0.97rem] transition"
            :class="isActive(item.to)
              ? 'border border-console-edge/80 bg-white text-slate-900 shadow-sm'
              : 'text-slate-700 hover:bg-white/70 hover:text-slate-900'"
          >
            {{ item.label }}
          </RouterLink>
        </nav>
      </section>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import { useAuthStore } from '../../stores/auth'

const route = useRoute()
const auth = useAuthStore()

const groups = computed(() => {
  const result = [
    {
      label: 'Overview',
      items: [
        { label: 'Dashboard', to: '/' },
        { label: 'Jobs', to: '/jobs' },
        { label: 'Schedules', to: '/schedules' },
      ],
    },
    {
      label: 'Configuration',
      items: [
        { label: 'Inventory', to: '/inventory' },
        { label: 'Credentials', to: '/credentials' },
        { label: 'Templates', to: '/templates' },
        { label: 'Playbooks', to: '/playbooks' },
      ],
    },
    {
      label: 'Tools',
      items: [
        { label: 'CLI Converter', to: '/converter' },
      ],
    },
  ]
  if (auth.isAdmin) {
    result.push({
      label: 'Administration',
      items: [
        { label: 'Audit Logs', to: '/audit' },
        { label: 'Users', to: '/users' },
        { label: 'Settings', to: '/settings' },
      ],
    })
  }
  return result
})

function isActive(path: string) {
  return route.path === path || route.path.startsWith(path + '/')
}
</script>
