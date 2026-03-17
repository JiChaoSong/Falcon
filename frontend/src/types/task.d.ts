import { BaseEntity, BaseQuery, BaseResponseList } from '@/types/base'

export interface TaskScenarioBind {
  scenario_id: number
  order: number
  weight: number
  target_users?: number | null
}

export interface TaskScenarioInfo extends TaskScenarioBind {
  scenario: string
}

export interface TaskInfo extends BaseEntity {
  name: string
  description: string | null
  owner: string
  owner_id: number
  project_id: number
  project: string
  host: string
  users: number
  spawn_rate: number
  duration: number | null
  execution_strategy: string
  status: string
  start_time: string | null
  runtime_seconds: number | null
  runtime: string | null
  finished_at: string | null
  stats: Record<string, unknown> | null
  scenarios: TaskScenarioInfo[]
}

export interface TaskList extends BaseResponseList {
  results: TaskInfo[]
}

export interface QueryTaskList extends BaseQuery {
  name?: string
  description?: string
  owner_id?: number
  scenario_id?: number
  project_id?: number
  status?: string
}

export interface QueryTaskOne {
  id: number
}

export interface TaskCreate {
  name: string
  description?: string
  owner: string
  owner_id: number
  project_id: number
  project: string
  host: string
  users: number
  spawn_rate: number
  duration: number
  execution_strategy: string
  scenarios: TaskScenarioBind[]
}

export interface TaskUpdate {
  id: number
  name?: string
  description?: string
  owner?: string
  owner_id?: number
  project_id?: number
  project?: string
  host?: string
  users?: number
  spawn_rate?: number
  duration?: number | null
  execution_strategy?: string
  status?: string
  scenarios?: TaskScenarioBind[]
}

export interface TaskRuntimeRequest {
  task_id: number
}

export interface TaskReportRequest extends TaskRuntimeRequest {
  task_run_id?: number | null
}

export interface TaskRunResult {
  task_id: number
  task_run_id: number
  status: string
}

export interface TaskMetricPoint {
  ts: string
  rps: number
  success_count: number
  fail_count: number
  avg_rt: number
  p95: number
  p99: number
  active_users: number
}

export interface TaskRuntimeStatus {
  task_id: number
  task_run_id: number | null
  task_name: string
  status: string
  started_at: string | null
  finished_at: string | null
  runtime_seconds: number
  active_users: number
  total_requests: number
  success_count: number
  fail_count: number
  success_ratio: number
  current_rps: number
  avg_rt: number
  p95: number
  p99: number
  host: string | null
  latest_error: string | null
  stats: Array<Record<string, unknown>>
  history: TaskMetricPoint[]
}

export interface TaskRunHistoryItem {
  id: number
  status: string
  started_at: string | null
  finished_at: string | null
  runtime_seconds: number
  total_requests: number
  success_count: number
  fail_count: number
  success_ratio: number
  latest_error: string | null
}

export interface TaskRunHistoryData {
  task_id: number
  runs: TaskRunHistoryItem[]
}

export interface TaskReportEndpoint {
  name: string
  method: string
  total_requests: number
  total_failures: number
  avg_response_time: number
  p95: number
  p99: number
}

export interface TaskReportData {
  task_id: number
  task_run_id: number | null
  task_name: string
  project: string
  owner: string
  host: string
  execution_strategy: string
  scenario_count: number
  status: string
  started_at: string | null
  finished_at: string | null
  runtime_seconds: number
  total_requests: number
  success_count: number
  fail_count: number
  success_ratio: number
  avg_rt: number
  p95: number
  p99: number
  latest_error: string | null
  hottest_endpoint: TaskReportEndpoint | null
  riskiest_endpoint: TaskReportEndpoint | null
  stats: Array<Record<string, unknown>>
  history: TaskMetricPoint[]
}
