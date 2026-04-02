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
  if (props.tone === 'error') return 'border-rose-500/40 bg-rose-50 text-rose-700'
  if (props.tone === 'warn') return 'border-amber-500/40 bg-amber-50 text-amber-700'
  return 'border-cyan-500/40 bg-cyan-50 text-cyan-700'
})
</script>
