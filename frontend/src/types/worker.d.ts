export type WorkerStatus = 'online' | 'busy' | 'degraded' | 'offline' | 'disabled'

export interface WorkerInfo {
  id: number
  worker_id: string
  host: string
  port: number
  address: string
  version?: string | null
  status: WorkerStatus
  capacity: number
  running_tasks: number
  scheduling_weight: number
  tags: string[]
  metadata_json?: Record<string, unknown> | null
  registered_at: string
  last_heartbeat_at: string
  last_seen_error?: string | null
  is_timeout: boolean
  created_at: string
  updated_at: string
}

export interface WorkerListQuery {
  page: number
  page_size: number
  worker_id?: string
  status?: WorkerStatus
  tag?: string
}

export interface WorkerListPayload {
  results: WorkerInfo[]
  total: number
}

export interface WorkerUpdatePayload {
  worker_id: string
  status?: WorkerStatus
  capacity?: number
  scheduling_weight?: number
  tags?: string[]
  metadata_json?: Record<string, unknown>
}
