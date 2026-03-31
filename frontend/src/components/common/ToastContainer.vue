<template>
  <div class="pointer-events-none fixed right-4 top-4 z-50 flex w-full max-w-sm flex-col gap-3">
    <div
      v-for="toast in app.toasts"
      :key="toast.id"
      class="pointer-events-auto rounded-xl border px-4 py-3 shadow-lg"
      :class="toast.tone === 'error'
        ? 'border-rose-500/30 bg-slate-900 text-rose-100'
        : toast.tone === 'success'
          ? 'border-emerald-500/30 bg-slate-900 text-emerald-100'
          : 'border-slate-700 bg-slate-900 text-slate-100'"
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
