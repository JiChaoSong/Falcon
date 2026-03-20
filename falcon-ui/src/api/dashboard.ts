import { http } from '@/utils/requests'
import type { ApiResponse } from '@/types/api'
import type { DashboardOverviewPayload } from '@/types/dashboard'

export const DashboardApi = {
  getOverview(): Promise<ApiResponse<DashboardOverviewPayload>> {
    return http.get<ApiResponse<DashboardOverviewPayload>>('/api/dashboard/overview')
  },
}
