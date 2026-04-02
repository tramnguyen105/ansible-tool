<template>
  <div class="min-h-screen bg-slate-50 text-console-ink">
    <div class="grid min-h-screen grid-cols-1 lg:grid-cols-[260px_minmax(0,1fr)] 2xl:grid-cols-[280px_minmax(0,1fr)]">
      <AppSidebar />
      <div class="flex min-h-screen min-w-0 flex-col lg:h-screen lg:overflow-hidden">
        <AppHeader />
        <main class="pretty-scrollbar flex-1 px-4 py-5 sm:px-6 lg:overflow-y-auto lg:px-8 2xl:px-10">
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
