<template>
  <span class="inline-flex rounded-full px-3 py-1 text-xs font-medium uppercase tracking-[0.2em]" :class="badgeClass">
    {{ value }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ value: string }>()

const badgeClass = computed(() => {
  const value = props.value.toLowerCase()

  if (['success', 'running', 'ready', 'enabled', 'completed'].includes(value)) {
    return 'bg-emerald-500/15 text-emerald-700'
  }
  if (['failed', 'error', 'disabled'].includes(value)) {
    return 'bg-rose-500/15 text-rose-700'
  }
  if (['queued', 'pending', 'review', 'manual'].includes(value)) {
    return 'bg-amber-500/15 text-amber-700'
  }
  if (['incomplete'].includes(value)) {
    return 'bg-violet-500/15 text-violet-700'
  }
  return 'bg-slate-500/20 text-slate-800'
})
</script>
