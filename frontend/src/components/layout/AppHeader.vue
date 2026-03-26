<template>
  <header class="border-b border-console-edge/70 bg-console-deep/60 px-5 py-4 backdrop-blur lg:px-8">
    <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
      <div>
        <p class="text-xs uppercase tracking-[0.28em] text-console-glow">Enterprise Operations</p>
        <p class="mt-1 text-sm text-console-muted">Production-safe automation console for network admins</p>
      </div>
      <div class="flex items-center gap-3">
        <div class="rounded-full border border-console-edge bg-console-panel px-4 py-2 text-sm text-console-muted">
          {{ auth.user?.display_name || auth.user?.username }}
        </div>
        <button class="rounded-full border border-console-edge px-4 py-2 text-sm hover:bg-console-panel" @click="logout">Sign out</button>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

import { useAppStore } from '../../stores/app'
import { useAuthStore } from '../../stores/auth'

const auth = useAuthStore()
const app = useAppStore()
const router = useRouter()

async function logout() {
  await auth.logout()
  app.pushToast('Session closed', 'info')
  router.push('/login')
}
</script>
