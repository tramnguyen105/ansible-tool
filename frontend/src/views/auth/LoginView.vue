<template>
  <div class="flex min-h-screen items-center justify-center bg-[radial-gradient(circle_at_top,_rgba(78,193,210,0.22),_transparent_30%),linear-gradient(180deg,_#0d1622_0%,_#111f31_100%)] px-4">
    <div class="w-full max-w-md rounded-[28px] border border-console-edge bg-console-panel/85 p-8 shadow-2xl shadow-cyan-950/20">
      <p class="text-xs uppercase tracking-[0.28em] text-console-glow">Secure Access</p>
      <h1 class="mt-3 text-3xl font-semibold text-white">Sign in to the automation console</h1>
      <p class="mt-3 text-sm text-console-muted">Use your LDAP credentials. This platform is restricted to internal administrators.</p>
      <form class="mt-8 space-y-4" @submit.prevent="submit">
        <div>
          <label class="field-label">Username</label>
          <input v-model="username" />
        </div>
        <div>
          <label class="field-label">Password</label>
          <input v-model="password" type="password" />
        </div>
        <button class="btn-primary w-full" type="submit">Sign in</button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAppStore } from '../../stores/app'
import { useAuthStore } from '../../stores/auth'

const app = useAppStore()
const auth = useAuthStore()
const router = useRouter()
const username = ref('admin')
const password = ref('ChangeMe123!')

async function submit() {
  try {
    await auth.login({ username: username.value, password: password.value })
    app.pushToast('Signed in', 'success')
    router.push('/')
  } catch (error: any) {
    app.pushToast(error?.response?.data?.message || 'Login failed', 'error')
  }
}
</script>
