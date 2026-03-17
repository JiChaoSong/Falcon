import { http } from '@/utils/requests'
import type { ApiResponse } from '@/types/api'
import type {
  CaseConfig,
  CaseImportCommitData,
  CaseImportCommitRequest,
  CaseCreate,
  CaseInfo,
  CaseImportPreviewData,
  CaseImportPreviewRequest,
  CaseList,
  CaseUpdate,
  QueryCaseList,
  QueryCaseOne,
} from '@/types/case'

export const CaseApi = {
  getCaseList(data: QueryCaseList): Promise<ApiResponse<CaseList>> {
    return http.post<ApiResponse<CaseList>>('/api/case/list', data)
  },

  getCaseInfo(data: QueryCaseOne): Promise<ApiResponse<CaseInfo>> {
    return http.post<ApiResponse<CaseInfo>>('/api/case/info', data)
  },

  createCase(data: CaseCreate): Promise<ApiResponse<CaseInfo>> {
    return http.post<ApiResponse<CaseInfo>>('/api/case/create', data)
  },

  updateCase(data: CaseUpdate): Promise<ApiResponse<CaseInfo>> {
    return http.post<ApiResponse<CaseInfo>>('/api/case/update', data)
  },

  configCase(data: CaseConfig): Promise<ApiResponse<CaseInfo>> {
    return http.post<ApiResponse<CaseInfo>>('/api/case/config', data)
  },

  deleteCase(data: QueryCaseOne): Promise<ApiResponse<null>> {
    return http.post<ApiResponse<null>>('/api/case/delete', data)
  },

  previewImport(data: CaseImportPreviewRequest): Promise<ApiResponse<CaseImportPreviewData>> {
    return http.post<ApiResponse<CaseImportPreviewData>>('/api/case/import/preview', data)
  },

  commitImport(data: CaseImportCommitRequest): Promise<ApiResponse<CaseImportCommitData>> {
    return http.post<ApiResponse<CaseImportCommitData>>('/api/case/import/commit', data)
  },
}
