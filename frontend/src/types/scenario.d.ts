import { BaseEntity, BaseQuery, BaseResponseList } from '@/types/base'

export interface ScenarioCaseBind {
  case_id: number
  order: number
  weight: number
}

export interface ScenarioInfo extends BaseEntity {
  name: string
  project_id: number
  project: string
  status: string
  description: string | null
  total_testcases: number
  last_run: string | null
  cases: ScenarioCaseBind[]
}

export interface ScenarioList extends BaseResponseList {
  results: ScenarioInfo[]
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
