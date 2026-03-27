import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import './styles/main.css'

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
app.use(createPinia())
app.use(router)
app.mount('#app')
