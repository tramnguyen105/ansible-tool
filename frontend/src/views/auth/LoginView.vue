<template>
  <div class="flex min-h-screen items-center justify-center bg-slate-950 px-4 py-10">
    <div class="w-full max-w-md rounded-3xl border border-slate-800 bg-slate-900/95 p-8 shadow-2xl shadow-slate-950/40">
      <p class="text-xs font-medium uppercase tracking-[0.22em] text-slate-400">Ansible Automation Console</p>
      <h1 class="mt-3 text-3xl font-semibold text-white">Sign in</h1>
      <p class="mt-3 text-sm leading-6 text-slate-300">
        {{ authDescription }}
      </p>

      <div v-if="authModesLabel" class="mt-4 rounded-2xl border border-slate-800 bg-slate-950/70 px-4 py-3 text-sm text-slate-300">
        <span class="font-medium text-slate-100">Available sign-in methods:</span>
        {{ authModesLabel }}
      </div>

      <div v-if="formError" class="mt-4 rounded-2xl border border-red-900/60 bg-red-950/40 px-4 py-3 text-sm text-red-200">
        {{ formError }}
      </div>

      <form class="mt-8 space-y-4" @submit.prevent="submit">
        <div>
          <label class="field-label" for="login-username">Username</label>
          <input
            id="login-username"
            v-model.trim="username"
            autocomplete="username"
            placeholder="Enter your username"
            :disabled="isSubmitting"
          />
        </div>

        <div>
          <div class="mb-2 flex items-center justify-between">
            <label class="field-label mb-0" for="login-password">Password</label>
            <button
              class="text-sm text-slate-400 transition hover:text-slate-200"
              type="button"
              :disabled="isSubmitting"
              @click="showPassword = !showPassword"
            >
              {{ showPassword ? 'Hide' : 'Show' }}
            </button>
          </div>
          <input
            id="login-password"
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            autocomplete="current-password"
            placeholder="Enter your password"
            :disabled="isSubmitting"
          />
        </div>

        <button class="btn-primary w-full disabled:cursor-not-allowed disabled:opacity-60" type="submit" :disabled="isSubmitting || !canSubmit">
          {{ isSubmitting ? 'Signing in…' : 'Sign in' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import api from '../../api/client'
import { useAppStore } from '../../stores/app'
import { useAuthStore } from '../../stores/auth'

const app = useAppStore()
const auth = useAuthStore()
const router = useRouter()

const username = ref('')
const password = ref('')
const showPassword = ref(false)
const isSubmitting = ref(false)
const formError = ref('')
const runtimeSettings = ref({
  ldap_enabled: false,
  allow_local_auth: false,
})

const canSubmit = computed(() => username.value.length > 0 && password.value.length > 0)

const authModesLabel = computed(() => {
  const modes: string[] = []
  if (runtimeSettings.value.ldap_enabled) modes.push('LDAP')
  if (runtimeSettings.value.allow_local_auth) modes.push('Local account')
  return modes.join(' and ')
})

const authDescription = computed(() => {
  const ldap = runtimeSettings.value.ldap_enabled
  const local = runtimeSettings.value.allow_local_auth

  if (ldap && local) {
    return 'Sign in with your LDAP credentials or an approved local administrator account.'
  }
  if (ldap) {
    return 'Sign in with your LDAP credentials to access the console.'
  }
  if (local) {
    return 'Sign in with your local administrator account to access the console.'
  }
  return 'Sign in with an administrator account to access the console.'
})

onMounted(async () => {
  try {
    const response = await api.get('/system/settings')
    runtimeSettings.value = {
      ldap_enabled: !!response.data.data?.ldap_enabled,
      allow_local_auth: !!response.data.data?.allow_local_auth,
    }
  } catch {
    // Keep login usable even if settings cannot be loaded.
  }
})

async function submit() {
  formError.value = ''

  if (!canSubmit.value) {
    formError.value = 'Enter both username and password.'
    return
  }

  isSubmitting.value = true
  try {
    await auth.login({ username: username.value, password: password.value })
    app.pushToast('Signed in', 'success')
    router.push('/')
  } catch (error: any) {
    formError.value = error?.response?.data?.message || 'Login failed. Check your credentials and try again.'
    app.pushToast(formError.value, 'error')
  } finally {
    isSubmitting.value = false
  }
}
</script>
