<template>
  <div class="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(78,193,210,0.18),_transparent_30%),linear-gradient(180deg,_#0d1622_0%,_#111f31_45%,_#0f1825_100%)] text-console-ink">
    <div class="mx-auto grid min-h-screen max-w-[1680px] grid-cols-1 lg:grid-cols-[280px_1fr]">
      <AppSidebar />
      <div class="flex min-h-screen flex-col">
        <AppHeader />
        <main class="flex-1 px-5 py-6 lg:px-8">
          <slot />
        </main>
      </div>
    </div>
    <ToastContainer />
  </div>
</template>

<script setup lang="ts">
import AppHeader from './AppHeader.vue'
import AppSidebar from './AppSidebar.vue'
import ToastContainer from '../common/ToastContainer.vue'
</script>
