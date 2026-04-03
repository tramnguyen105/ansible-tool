import { defineStore } from 'pinia'

import { authApi } from '../api/modules'

const SESSION_REFRESH_MS = 2 * 60 * 1000

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as null | { id: string; username: string; display_name?: string; roles?: Array<{ name: string }> },
    ready: false,
    lastValidatedAt: 0,
    validationPromise: null as Promise<void> | null,
  }),
  getters: {
    isAuthenticated: (state) => !!state.user,
    isAdmin: (state) => !!state.user?.roles?.some((role) => role.name === 'admin'),
    needsRevalidation: (state) => !state.lastValidatedAt || Date.now() - state.lastValidatedAt > SESSION_REFRESH_MS,
  },
  actions: {
    async ensureSession(force = false) {
      if (!force && this.ready && !this.needsRevalidation) {
        return
      }
      if (this.validationPromise) {
        return this.validationPromise
      }
      this.validationPromise = (async () => {
        try {
          const response = await authApi.me()
          this.user = response.data.data.user
        } catch {
          this.user = null
        } finally {
          this.ready = true
          this.lastValidatedAt = Date.now()
          this.validationPromise = null
        }
      })()
      return this.validationPromise
    },
    async login(payload: { username: string; password: string }) {
      const response = await authApi.login(payload)
      this.user = response.data.data.user
      this.ready = true
      this.lastValidatedAt = Date.now()
      return response.data.data
    },
    invalidateSession() {
      this.user = null
      this.ready = true
      this.lastValidatedAt = 0
      this.validationPromise = null
    },
    async logout() {
      try {
        await authApi.logout()
      } finally {
        this.invalidateSession()
      }
    },
  },
})
