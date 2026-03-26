import { defineStore } from 'pinia'

import { authApi } from '../api/modules'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as null | { username: string; display_name?: string },
    ready: false,
  }),
  getters: {
    isAuthenticated: (state) => !!state.user,
  },
  actions: {
    async ensureSession() {
      if (this.ready) {
        return
      }
      try {
        const response = await authApi.me()
        this.user = response.data.data.user
      } catch {
        this.user = null
      } finally {
        this.ready = true
      }
    },
    async login(payload: { username: string; password: string }) {
      const response = await authApi.login(payload)
      this.user = response.data.data.user
      this.ready = true
      return response.data.data
    },
    async logout() {
      try {
        await authApi.logout()
      } finally {
        this.user = null
      }
    },
  },
})
