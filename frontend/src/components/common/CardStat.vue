<template>
  <div class="rounded-3xl border border-console-edge bg-console-panel/80 p-5 shadow-xl shadow-slate-950/20">
    <p class="text-xs uppercase tracking-[0.26em] text-console-muted">{{ label }}</p>
    <div class="mt-4 flex items-end justify-between">
      <p class="text-3xl font-semibold">{{ value }}</p>
      <span class="rounded-full bg-console-deep/70 px-3 py-1 text-xs text-console-glow">{{ tone }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ label: string; value: string | number; tone?: string }>()
</script>
