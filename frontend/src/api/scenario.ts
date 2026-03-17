import { http } from '@/utils/requests'
import type { ApiResponse } from '@/types/api'
import type {
  QueryScenarioList,
  QueryScenarioOne,
  ScenarioCreate,
  ScenarioInfo,
  ScenarioList,
  ScenarioUpdate,
} from '@/types/scenario'

export const ScenarioApi = {
  getScenarioList(data: QueryScenarioList): Promise<ApiResponse<ScenarioList>> {
    return http.post<ApiResponse<ScenarioList>>('/api/scenario/list', data)
  },

  getScenarioInfo(data: QueryScenarioOne): Promise<ApiResponse<ScenarioInfo>> {
    return http.post<ApiResponse<ScenarioInfo>>('/api/scenario/info', data)
  },

  createScenario(data: ScenarioCreate): Promise<ApiResponse<ScenarioInfo>> {
    return http.post<ApiResponse<ScenarioInfo>>('/api/scenario/create', data)
  },

  updateScenario(data: ScenarioUpdate): Promise<ApiResponse<ScenarioInfo>> {
    return http.post<ApiResponse<ScenarioInfo>>('/api/scenario/update', data)
  },

  deleteScenario(data: QueryScenarioOne): Promise<ApiResponse<null>> {
    return http.post<ApiResponse<null>>('/api/scenario/delete', data)
  },
}
