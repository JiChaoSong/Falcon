import {ApiResponse} from "@/types/api";
import { http } from '@/utils/requests'
import {ProjectInfoList, QueryProjectList, GetProjectInfo, ProjectUpdate, ProjectCreate} from "@/types/project";


export const ProjectApi = {

    // 项目列表
    getProjectList(data:QueryProjectList): Promise<ApiResponse<ProjectInfoList>> {
        return http.post<ApiResponse>('/api/project/list', data)
    },

    // 新增项目
    createProject(data:ProjectCreate): Promise<ApiResponse> {
        return http.post<ApiResponse>('/api/project/create', data)
    },

    // 更新项目
    updateProject(data:ProjectUpdate): Promise<ApiResponse> {
        return http.post<ApiResponse>('/api/project/update', data)
    },

    // 删除项目
    deleteProject(data:GetProjectInfo): Promise<ApiResponse> {
        return http.post<ApiResponse>('/api/project/delete', data)
    },

    // 更新项目
    getProjectInfo(data:GetProjectInfo): Promise<ApiResponse> {
        return http.post<ApiResponse>('/api/project/info', data)
    },
}