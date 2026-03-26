<template>
  <div v-if="open" class="fixed inset-0 z-40 flex justify-end bg-slate-950/55 backdrop-blur-sm" @click.self="$emit('close')">
    <div class="h-full w-full max-w-2xl overflow-y-auto border-l border-console-edge bg-console-deep px-6 py-6 shadow-2xl shadow-slate-950/40">
      <div class="mb-5 flex items-center justify-between">
        <h3 class="text-xl font-semibold">{{ title }}</h3>
        <button class="rounded-full border border-console-edge px-3 py-1 text-sm" @click="$emit('close')">Close</button>
      </div>
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ open: boolean; title: string }>()
defineEmits(['close'])
</script>
