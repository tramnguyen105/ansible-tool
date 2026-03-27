import { defineStore } from 'pinia'

export interface ToastItem {
  id: number
  title: string
  description?: string
  tone: 'success' | 'error' | 'info'
}

export const useAppStore = defineStore('app', {
  state: () => ({
    toasts: [] as ToastItem[],
  }),
  actions: {
    pushToast(title: string, tone: ToastItem['tone'] = 'info', description?: string) {
      const id = Date.now() + Math.floor(Math.random() * 1000)
      this.toasts.push({ id, title, tone, description })
      setTimeout(() => {
        this.toasts = this.toasts.filter((toast) => toast.id !== id)
      }, 5000)
    },
  },
})
