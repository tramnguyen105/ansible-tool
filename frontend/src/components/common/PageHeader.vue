<template>
  <div class="mb-6 flex flex-col gap-3 border-b border-console-edge/50 pb-5 md:flex-row md:items-end md:justify-between">
    <div>
      <p v-if="eyebrow" class="text-xs uppercase tracking-[0.26em] text-console-glow">{{ eyebrow }}</p>
      <h2 class="mt-2 text-2xl font-semibold text-white">{{ title }}</h2>
      <p v-if="description" class="mt-2 max-w-3xl text-sm leading-6 text-console-muted">{{ description }}</p>
    </div>
    <div class="flex flex-wrap gap-2">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ title: string; description?: string; eyebrow?: string }>()
</script>
