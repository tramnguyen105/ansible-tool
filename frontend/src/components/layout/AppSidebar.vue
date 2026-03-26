<template>
  <aside class="border-r border-console-edge/70 bg-console-deep/70 px-4 py-6 backdrop-blur lg:sticky lg:top-0 lg:h-screen">
    <div class="mb-8 rounded-2xl border border-console-edge bg-console-panel/80 p-5 shadow-2xl shadow-sky-950/20">
      <p class="text-xs uppercase tracking-[0.28em] text-console-glow">Operations</p>
      <h1 class="mt-2 text-xl font-semibold">Ansible Automation Console</h1>
      <p class="mt-2 text-sm text-console-muted">Internal network automation workspace</p>
    </div>
    <nav class="space-y-2">
      <RouterLink v-for="item in items" :key="item.to" :to="item.to" class="block rounded-2xl px-4 py-3 text-sm transition" :class="$route.path === item.to || $route.path.startsWith(item.to + '/') ? 'bg-console-surface text-white shadow-lg shadow-cyan-950/20' : 'text-console-muted hover:bg-console-panel/80 hover:text-white'">
        {{ item.label }}
      </RouterLink>
    </nav>
  </aside>
</template>

<script setup lang="ts">
const items = [
  { label: 'Dashboard', to: '/' },
  { label: 'Inventory', to: '/inventory' },
  { label: 'Credentials', to: '/credentials' },
  { label: 'Templates', to: '/templates' },
  { label: 'Playbooks', to: '/playbooks' },
  { label: 'CLI Converter', to: '/converter' },
  { label: 'Jobs', to: '/jobs' },
  { label: 'Schedules', to: '/schedules' },
  { label: 'Audit Logs', to: '/audit' },
  { label: 'Settings', to: '/settings' },
]
</script>
