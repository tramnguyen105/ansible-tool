<template>
  <span class="inline-flex rounded-full px-3 py-1 text-xs font-medium uppercase tracking-[0.2em]" :class="badgeClass">
    {{ value }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ value: string }>()

const badgeClass = computed(() => {
  if (['success', 'running'].includes(props.value)) return 'bg-emerald-500/15 text-emerald-300'
  if (['failed', 'error'].includes(props.value)) return 'bg-rose-500/15 text-rose-300'
  if (['queued', 'pending'].includes(props.value)) return 'bg-amber-500/15 text-amber-200'
  return 'bg-slate-500/20 text-slate-200'
})
</script>
