import axios from 'axios'

import { emitUnauthorizedSession } from '../utils/sessionEvents'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  withCredentials: true,
})

function readCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`))
  return match ? decodeURIComponent(match[1]) : null
}

api.interceptors.request.use((config) => {
  const method = (config.method || 'get').toLowerCase()
  if (['post', 'put', 'patch', 'delete'].includes(method)) {
    const csrf = readCookie('ansible_tool_csrf')
    if (csrf) {
      config.headers['X-CSRF-Token'] = csrf
    }
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status
    const url = String(error?.config?.url || '')
    const shouldHandleUnauthorized =
      status === 401 &&
      !url.includes('/auth/login') &&
      !url.includes('/auth/modes')

    if (shouldHandleUnauthorized) {
      emitUnauthorizedSession()
    }
    return Promise.reject(error)
  },
)

export default api
