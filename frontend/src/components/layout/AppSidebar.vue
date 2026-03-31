<template>
  <aside class="border-r border-console-edge/60 bg-slate-950/90 px-4 py-5 backdrop-blur lg:sticky lg:top-0 lg:h-screen">
    <div class="mb-5 px-2">
      <p class="text-[1rem] font-semibold text-white">Ansible Automation Console</p>
      <p class="mt-1 text-[0.82rem] text-slate-400">Network automation operations</p>
    </div>

    <div class="space-y-6">
      <section v-for="group in groups" :key="group.label">
        <p class="px-2 text-[0.78rem] font-medium uppercase tracking-[0.12em] text-slate-500">{{ group.label }}</p>
        <nav class="mt-2 space-y-1">
          <RouterLink
            v-for="item in group.items"
            :key="item.to"
            :to="item.to"
            class="flex items-center rounded-xl px-3 py-2.5 text-[0.97rem] transition"
            :class="isActive(item.to)
              ? 'bg-slate-800 text-white'
              : 'text-slate-300 hover:bg-slate-900 hover:text-white'"
          >
            {{ item.label }}
          </RouterLink>
        </nav>
      </section>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()

const groups = [
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
  {
    label: 'Administration',
    items: [
      { label: 'Audit Logs', to: '/audit' },
      { label: 'Settings', to: '/settings' },
    ],
  },
]

function isActive(path: string) {
  return route.path === path || route.path.startsWith(path + '/')
}
</script>
