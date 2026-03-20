import {ApiResponse} from "@/types/api";
import { http } from '@/utils/requests'

export interface TaskInfo {
    task_id: number | null
}

export interface TaskInfoResult {
    task_id: number | null
    task_name: string
    cases: any[]
    run_time: number
    users: number
    spawn_time: number
    host: string
    status: string
}

export const tasksApi =  {
    // 任务查询
    taskInfo(data: TaskInfo): Promise<ApiResponse<TaskInfoResult>> {
        return http.post<ApiResponse<TaskInfoResult>>('/api/task/info', { id: data.task_id })
    }
}
