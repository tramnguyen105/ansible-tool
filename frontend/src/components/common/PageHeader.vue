<template>
  <div class="flex flex-col gap-4 border-b border-slate-800 pb-5 md:flex-row md:items-end md:justify-between">
    <div>
      <p v-if="eyebrow" class="text-[0.8rem] font-medium uppercase tracking-[0.14em] text-slate-500">{{ eyebrow }}</p>
      <h2 class="mt-2 text-[1.75rem] font-semibold text-white">{{ title }}</h2>
      <p v-if="description" class="mt-2 max-w-3xl text-[0.98rem] leading-7 text-slate-400">{{ description }}</p>
    </div>
    <div class="flex flex-wrap gap-2">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ title: string; description?: string; eyebrow?: string }>()
</script>
