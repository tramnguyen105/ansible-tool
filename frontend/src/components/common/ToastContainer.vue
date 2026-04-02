<template>
  <div class="pointer-events-none fixed right-4 top-4 z-50 flex w-full max-w-sm flex-col gap-3">
    <div
      v-for="toast in app.toasts"
      :key="toast.id"
      class="pointer-events-auto rounded-xl border px-4 py-3 shadow-lg"
      :class="toast.tone === 'error'
        ? 'border-rose-500/30 bg-rose-50 text-rose-700'
        : toast.tone === 'success'
          ? 'border-emerald-500/30 bg-emerald-50 text-emerald-700'
          : 'border-slate-300 bg-white text-slate-900'"
    >
      <p class="font-medium">{{ toast.title }}</p>
      <p v-if="toast.description" class="mt-1 text-xs leading-5 opacity-90">{{ toast.description }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAppStore } from '../../stores/app'

const app = useAppStore()
</script>
