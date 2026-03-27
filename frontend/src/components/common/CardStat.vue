<template>
  <div class="rounded-3xl border border-console-edge bg-console-panel/80 p-5 shadow-xl shadow-slate-950/20">
    <div class="flex items-start justify-between gap-4">
      <div>
        <p class="text-xs uppercase tracking-[0.26em] text-console-muted">{{ label }}</p>
        <p class="mt-4 text-3xl font-semibold text-white">{{ value }}</p>
      </div>
      <span v-if="tone" class="rounded-full bg-console-deep/80 px-3 py-1 text-[11px] uppercase tracking-[0.18em] text-console-glow">{{ tone }}</span>
    </div>
    <p v-if="helper" class="mt-4 text-sm text-console-muted">{{ helper }}</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{ label: string; value: string | number; tone?: string; helper?: string }>()
</script>
