import { http } from '@/utils/requests'
import type { ApiResponse } from '@/types/api'
import type {
  QueryTaskList,
  QueryTaskOne,
  TaskCreate,
  TaskInfo,
  TaskList,
  TaskReportData,
  TaskReportRequest,
  TaskRunResult,
  TaskRunHistoryData,
  TaskRuntimeRequest,
  TaskRuntimeStatus,
  TaskUpdate,
} from '@/types/task'

export const TaskApi = {
  getTaskList(data: QueryTaskList): Promise<ApiResponse<TaskList>> {
    return http.post<ApiResponse<TaskList>>('/api/task/list', data)
  },

  getTaskInfo(data: QueryTaskOne): Promise<ApiResponse<TaskInfo>> {
    return http.post<ApiResponse<TaskInfo>>('/api/task/info', data)
  },

  createTask(data: TaskCreate): Promise<ApiResponse<TaskInfo>> {
    return http.post<ApiResponse<TaskInfo>>('/api/task/create', data)
  },

  updateTask(data: TaskUpdate): Promise<ApiResponse<TaskInfo>> {
    return http.post<ApiResponse<TaskInfo>>('/api/task/update', data)
  },

  deleteTask(data: QueryTaskOne): Promise<ApiResponse<null>> {
    return http.post<ApiResponse<null>>('/api/task/delete', data)
  },

  runTask(data: TaskRuntimeRequest): Promise<ApiResponse<TaskRunResult>> {
    return http.post<ApiResponse<TaskRunResult>>('/api/task/run', data)
  },

  stopTask(data: TaskRuntimeRequest): Promise<ApiResponse<TaskRunResult>> {
    return http.post<ApiResponse<TaskRunResult>>('/api/task/stop', data)
  },

  getTaskStatus(data: TaskRuntimeRequest): Promise<ApiResponse<TaskRuntimeStatus>> {
    return http.post<ApiResponse<TaskRuntimeStatus>>('/api/task/status', data)
  },

  getTaskRuns(data: TaskRuntimeRequest): Promise<ApiResponse<TaskRunHistoryData>> {
    return http.post<ApiResponse<TaskRunHistoryData>>('/api/task/runs', data)
  },

  getTaskReport(data: TaskReportRequest): Promise<ApiResponse<TaskReportData>> {
    return http.post<ApiResponse<TaskReportData>>('/api/task/report', data)
  },
}
