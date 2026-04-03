import api from './client'
export { jobsApi } from './jobs'
export { inventoryApi } from './inventory'
export { schedulesApi } from './schedules'

export const authApi = {
  login: (payload: { username: string; password: string }) => api.post('/auth/login', payload),
  me: () => api.get('/auth/me'),
  logout: () => api.post('/auth/logout'),
}

export const crudApi = {
  list: (path: string) => api.get(path),
  get: (path: string, id: string) => api.get(`${path}/${id}`),
  create: (path: string, payload: unknown) => api.post(path, payload),
  update: (path: string, id: string, payload: unknown) => api.put(`${path}/${id}`, payload),
  remove: (path: string, id: string) => api.delete(`${path}/${id}`),
}
