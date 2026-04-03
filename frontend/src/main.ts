import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { useAppStore } from './stores/app'
import { useAuthStore } from './stores/auth'
import './styles/main.css'
import { onUnauthorizedSession } from './utils/sessionEvents'

if (!globalThis.crypto) {
  ;(globalThis as typeof globalThis & { crypto: Crypto }).crypto = {} as Crypto
}

if (typeof globalThis.crypto.randomUUID !== 'function') {
  globalThis.crypto.randomUUID = () =>
    'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (char) => {
      const random = Math.floor(Math.random() * 16)
      const value = char === 'x' ? random : (random & 0x3) | 0x8
      return value.toString(16)
    })
}

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)

const auth = useAuthStore(pinia)
const appStore = useAppStore(pinia)

onUnauthorizedSession(async () => {
  auth.invalidateSession()
  if (router.currentRoute.value.path !== '/login') {
    appStore.pushToast('Your session expired', 'info', 'Sign in again to continue.')
    await router.push('/login')
  }
})

document.addEventListener('visibilitychange', () => {
  if (document.visibilityState !== 'visible') return
  if (router.currentRoute.value.path === '/login') return
  auth.ensureSession(true)
})

app.mount('#app')
