import api from './client'

export type ScheduleItem = {
  id: string
  name: string
  description?: string | null
  cron_expression: string
  timezone: string
  enabled: boolean
  inventory_id?: string | null
  credential_id?: string | null
  playbook_id?: string | null
  target_type: string
  target_value?: string | null
  extra_vars_json: Record<string, unknown>
  check_mode: boolean
  next_run_at?: string | null
  last_run_at?: string | null
  created_at: string
}

export type ScheduleListSummary = {
  total: number
  enabled: number
  check_mode: number
  next_due_at?: string | null
}

export type ScheduleQueryResponse = {
  items: ScheduleItem[]
  total: number
  limit: number
  offset: number
  has_more: boolean
  summary: ScheduleListSummary
}

export const schedulesApi = {
  query: (params: Record<string, string | number>) => api.get('/schedules/query', { params }),
  list: () => api.get('/schedules'),
  create: (payload: Record<string, unknown>) => api.post('/schedules', payload),
  update: (scheduleId: string, payload: Record<string, unknown>) => api.put(`/schedules/${scheduleId}`, payload),
  remove: (scheduleId: string) => api.delete(`/schedules/${scheduleId}`),
}
