import api from './client'

export type InventorySummaryStats = {
  inventories: number
  hosts: number
  enabled_hosts: number
  groups: number
  variable_bearing: number
}

export type InventorySummaryItem = {
  id: string
  name: string
  description?: string | null
  source_type: string
  host_count: number
  enabled_host_count: number
  group_count: number
  variable_scope_count: number
  readiness: string
  readiness_note: string
}

export type InventoryHostRecord = {
  id?: string
  name: string
  address?: string | null
  description?: string | null
  variables_json?: Record<string, unknown>
  variables?: Record<string, unknown>
  enabled: boolean
  groups: string[]
}

export type InventoryGroupRecord = {
  id?: string
  name: string
  description?: string | null
  variables_json?: Record<string, unknown>
  variables?: Record<string, unknown>
  children: string[]
  hosts?: string[]
}

export type InventoryDetail = {
  id: string
  name: string
  description?: string | null
  source_type: string
  variables_json: Record<string, unknown>
  hosts: InventoryHostRecord[]
  groups: InventoryGroupRecord[]
}

export type InventoryUsage = {
  schedules_total: number
  schedules_enabled: number
  jobs_total: number
  jobs_active: number
}

export type InventorySummaryQueryResponse = {
  items: InventorySummaryItem[]
  total: number
  limit: number
  offset: number
  has_more: boolean
  stats: InventorySummaryStats
}

export const inventoryApi = {
  querySummary: (params: Record<string, string | number | string[]>) => api.get('/inventories/summary/query', { params }),
  get: (inventoryId: string) => api.get(`/inventories/${inventoryId}`),
  getUsage: (inventoryId: string) => api.get(`/inventories/${inventoryId}/usage`),
  create: (payload: Record<string, unknown>) => api.post('/inventories', payload),
  update: (inventoryId: string, payload: Record<string, unknown>) => api.put(`/inventories/${inventoryId}`, payload),
  remove: (inventoryId: string) => api.delete(`/inventories/${inventoryId}`),
}
