<template>
  <div class="fixed bottom-5 right-5 z-50 flex w-full max-w-sm flex-col gap-3">
    <div
      v-for="toast in app.toasts"
      :key="toast.id"
      class="rounded-2xl border px-4 py-3 text-sm shadow-xl"
      :class="toast.tone === 'error' ? 'border-rose-500/40 bg-rose-500/12 text-rose-100' : toast.tone === 'success' ? 'border-emerald-500/40 bg-emerald-500/12 text-emerald-100' : 'border-cyan-500/40 bg-cyan-500/12 text-cyan-50'"
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
