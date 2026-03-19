export interface DashboardOverview {
  project_count: number
  case_count: number
  scenario_count: number
  task_count: number
  running_task_count: number
  stopping_task_count: number
  failed_task_count: number
  online_worker_count: number
}

export interface DashboardTaskItem {
  id: number
  name: string
  project: string
  host: string | null
  users: number
  status: string
  runtime: string | null
  start_time: string | null
}

export interface DashboardWorkerSummary {
  online: number
  busy: number
  degraded: number
  offline: number
}

export interface DashboardWorkerHighlight {
  worker_id: string
  address: string
  status: string
  running_tasks: number
  capacity: number
}

export interface DashboardTrendPoint {
  label: string
  task_runs: number
  success_ratio: number
  total_requests: number
  fail_count: number
}

export interface DashboardAlertItem {
  level: string
  title: string
  summary: string
  action: string
}

export interface DashboardOverviewPayload {
  overview: DashboardOverview
  running_tasks: DashboardTaskItem[]
  attention_tasks: DashboardTaskItem[]
  recent_tasks: DashboardTaskItem[]
  worker_summary: DashboardWorkerSummary
  worker_highlights: DashboardWorkerHighlight[]
  today_trend: DashboardTrendPoint[]
  alerts: DashboardAlertItem[]
}
