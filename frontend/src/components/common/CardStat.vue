<template>
  <section class="rounded-2xl border border-slate-800 bg-slate-900 p-5">
    <div class="flex items-start justify-between gap-3">
      <div>
        <p class="text-[0.8rem] font-medium uppercase tracking-[0.12em] text-slate-500">{{ label }}</p>
        <p class="mt-3 text-[2rem] font-semibold text-white">{{ value }}</p>
      </div>
      <span class="rounded-full px-2.5 py-1 text-[0.72rem] font-medium uppercase tracking-[0.1em]" :class="toneClass">{{ tone }}</span>
    </div>
    <p v-if="helper" class="mt-3 text-[0.96rem] leading-7 text-slate-400">{{ helper }}</p>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  label: string
  value: string | number
  tone?: string
  helper?: string
}>()

const toneClass = computed(() => {
  switch (props.tone) {
    case 'managed':
    case 'identity':
      return 'bg-sky-500/10 text-sky-200'
    case 'secured':
    case 'auth':
      return 'bg-emerald-500/10 text-emerald-200'
    case 'validated':
    case 'runtime':
      return 'bg-violet-500/10 text-violet-200'
    case 'tracked':
    case 'minutes':
      return 'bg-amber-500/10 text-amber-200'
    default:
      return 'bg-slate-800 text-slate-300'
  }
})
</script>
