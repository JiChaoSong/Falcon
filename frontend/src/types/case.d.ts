import { BaseEntity, BaseQuery, BaseResponseList } from '@/types/base'

export interface CaseHeaderItem {
  name: string
  value: string
}

export interface CaseInfo extends BaseEntity {
  name: string
  type: string
  project_id: number
  project: string
  method: string | null
  url: string | null
  status: string
  description: string | null
  headers: CaseHeaderItem[] | null
  body: string | null
  expected_status: string | null
  expected_response_time: number | null
  assertion: string | null
  pre_request_script: string | null
  post_request_script: string | null
  extract: Record<string, string> | null
}

export interface CaseList extends BaseResponseList {
  results: CaseInfo[]
}

export interface QueryCaseList extends BaseQuery {
  name?: string
  project_id?: number
  type?: string
  method?: string
  url?: string
  status?: string
}

export interface QueryCaseOne {
  id: number
}

export interface CaseCreate {
  name: string
  type: string
  project_id: number
  project: string
  method: string
  url: string
  description?: string
}

export interface CaseUpdate {
  id: number
  name?: string
  type?: string
  project_id?: number
  project?: string
  method?: string
  url?: string
  description?: string
  status?: string
}

export interface CaseConfig {
  id: number
  headers?: CaseHeaderItem[]
  body?: string
  expected_status?: string
  expected_response_time?: number | null
  assertion?: string
  pre_request_script?: string
  post_request_script?: string
  extract?: Record<string, string>
}

export type CaseImportSourceType = 'openapi_url' | 'openapi_json'

export type CaseImportConflictPolicy = 'skip' | 'overwrite'

export interface CaseImportPreviewRequest {
  project_id: number
  source_type: CaseImportSourceType
  source_url?: string
  document_content?: string
}

export interface CaseImportItem {
  name: string
  method: string
  url: string
  description?: string | null
  tags: string[]
  headers: CaseHeaderItem[]
  body?: string | null
  expected_status?: string | null
  exists: boolean
  duplicate_case_id?: number | null
  duplicate_case_name?: string | null
}

export interface CaseImportPreviewData {
  project_id: number
  project_name: string
  source_type: CaseImportSourceType
  total_count: number
  duplicate_count: number
  importable_count: number
  results: CaseImportItem[]
}

export interface CaseImportCommitRequest extends CaseImportPreviewRequest {
  items: CaseImportItem[]
  conflict_policy: CaseImportConflictPolicy
  default_status: string
}

export interface CaseImportCommitData {
  project_id: number
  project_name: string
  created_count: number
  updated_count: number
  skipped_count: number
  failed_count: number
  created_case_ids: number[]
  failed_items: Array<{
    name: string
    method: string
    url: string
    reason: string
  }>
}
