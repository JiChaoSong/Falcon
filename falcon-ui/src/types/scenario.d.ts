import { BaseEntity, BaseQuery, BaseResponseList } from '@/types/base'

export interface ScenarioCaseBind {
  case_id: number
  order: number
  weight: number
}

export interface ScenarioCaseSummary extends ScenarioCaseBind {
  id: number
  name: string
  method?: string | null
  url: string
  status: string
}

export interface ScenarioCaseDetail extends ScenarioCaseSummary {
  type: string
  project_id: number
  project: string
  description?: string | null
  headers?: unknown
  body?: string | null
  expected_status?: string | null
  expected_response_time?: number | null
  assertion?: string | null
  pre_request_script?: string | null
  post_request_script?: string | null
  extract?: unknown
}

export interface ScenarioInfo extends BaseEntity {
  name: string
  project_id: number
  project: string
  status: string
  description: string | null
  total_testcases: number
  last_run: string | null
  cases: ScenarioCaseDetail[]
}

export interface ScenarioListItem extends BaseEntity {
  name: string
  project_id: number
  project: string
  status: string
  description: string | null
  total_testcases: number
  last_run: string | null
  cases: ScenarioCaseSummary[]
}

export interface ScenarioList extends BaseResponseList {
  results: ScenarioListItem[]
}

export interface QueryScenarioList extends BaseQuery {
  name?: string
  project_id?: number
  description?: string
  status?: string
}

export interface QueryScenarioOne {
  id: number
}

export interface ScenarioCreate {
  name: string
  project_id: number
  project: string
  description?: string
  cases: ScenarioCaseBind[]
}

export interface ScenarioUpdate {
  id: number
  name?: string
  project_id?: number
  project?: string
  description?: string
  status?: string
  cases?: ScenarioCaseBind[]
}
