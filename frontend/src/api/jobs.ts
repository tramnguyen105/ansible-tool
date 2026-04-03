import api from './client'

export type JobListSummary = {
  queued: number
  running: number
  success: number
  failed: number
  check_mode: number
}

export type JobListItem = {
  id: string
  name: string
  status: string
  inventory_id?: string | null
  credential_id?: string | null
  playbook_id?: string | null
  target_type: string
  target_value?: string | null
  extra_vars_json: Record<string, unknown>
  check_mode: boolean
  celery_task_id?: string | null
  started_at?: string | null
  finished_at?: string | null
  created_at: string
  result?: unknown
}

export type JobQueryResponse = {
  items: JobListItem[]
  total: number
  limit: number
  offset: number
  has_more: boolean
  summary: JobListSummary
}

export const jobsApi = {
  query: (params: Record<string, string | number | string[]>) => api.get('/jobs/query', { params }),
}
