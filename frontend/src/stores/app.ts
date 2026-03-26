import { defineStore } from 'pinia'

export interface ToastItem {
  id: number
  title: string
  tone: 'success' | 'error' | 'info'
}

export const useAppStore = defineStore('app', {
  state: () => ({
    toasts: [] as ToastItem[],
  }),
  actions: {
    pushToast(title: string, tone: ToastItem['tone'] = 'info') {
      const id = Date.now() + Math.floor(Math.random() * 1000)
      this.toasts.push({ id, title, tone })
      setTimeout(() => {
        this.toasts = this.toasts.filter((toast) => toast.id !== id)
      }, 5000)
    },
  },
})
