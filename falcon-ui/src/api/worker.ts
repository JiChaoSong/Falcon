import type { ApiResponse } from '@/types/api'
import type { WorkerInfo, WorkerListPayload, WorkerListQuery, WorkerUpdatePayload } from '@/types/worker'
import { http } from '@/utils/requests'

export const WorkerApi = {
  workerList(data: WorkerListQuery): Promise<ApiResponse<WorkerListPayload>> {
    return http.post<ApiResponse<WorkerListPayload>>('/api/worker/list', data)
  },

  workerInfo(worker_id: string): Promise<ApiResponse<WorkerInfo>> {
    return http.post<ApiResponse<WorkerInfo>>('/api/worker/info', { worker_id })
  },

  updateWorker(data: WorkerUpdatePayload): Promise<ApiResponse<WorkerInfo>> {
    return http.post<ApiResponse<WorkerInfo>>('/api/worker/update', data)
  },
}
