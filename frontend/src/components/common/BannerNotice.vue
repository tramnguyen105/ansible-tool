<template>
  <div class="rounded-2xl border px-4 py-3 text-sm" :class="toneClass">
    <strong class="mr-2 uppercase tracking-[0.2em]">{{ title }}</strong>
    <span>{{ text }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ title: string; text: string; tone?: 'warn' | 'info' | 'error' }>()

const toneClass = computed(() => {
  if (props.tone === 'error') return 'border-rose-500/40 bg-rose-500/10 text-rose-100'
  if (props.tone === 'warn') return 'border-amber-500/40 bg-amber-500/10 text-amber-100'
  return 'border-cyan-500/40 bg-cyan-500/10 text-cyan-50'
})
</script>
