import {ApiResponse} from "@/types/api";
import { http } from '@/utils/requests'
import {
    GetProjectInfo,
    ProjectCreate,
    ProjectInfo,
    ProjectInfoList,
    ProjectMemberCreate,
    ProjectMemberInfo,
    ProjectMemberUpdate,
    ProjectUpdate,
    QueryProjectList
} from "@/types/project";


export const ProjectApi = {

    // 项目列表
    getProjectList(data:QueryProjectList): Promise<ApiResponse<ProjectInfoList>> {
        return http.post<ApiResponse>('/api/project/list', data)
    },

    // 新增项目
    createProject(data:ProjectCreate): Promise<ApiResponse<ProjectInfo>> {
        return http.post<ApiResponse<ProjectInfo>>('/api/project/create', data)
    },

    // 更新项目
    updateProject(data:ProjectUpdate): Promise<ApiResponse<ProjectInfo>> {
        return http.post<ApiResponse<ProjectInfo>>('/api/project/update', data)
    },

    // 删除项目
    deleteProject(data:GetProjectInfo): Promise<ApiResponse> {
        return http.post<ApiResponse>('/api/project/delete', data)
    },

    // 更新项目
    getProjectInfo(data:GetProjectInfo): Promise<ApiResponse<ProjectInfo>> {
        return http.post<ApiResponse<ProjectInfo>>('/api/project/info', data)
    },

    getProjectMembers(data: GetProjectInfo): Promise<ApiResponse<ProjectMemberInfo[]>> {
        return http.post<ApiResponse<ProjectMemberInfo[]>>('/api/project/member/list', data)
    },

    addProjectMember(data: ProjectMemberCreate): Promise<ApiResponse<ProjectMemberInfo>> {
        return http.post<ApiResponse<ProjectMemberInfo>>('/api/project/member/add', data)
    },

    updateProjectMemberRole(data: ProjectMemberUpdate): Promise<ApiResponse<ProjectMemberInfo>> {
        return http.post<ApiResponse<ProjectMemberInfo>>('/api/project/member/update-role', data)
    },

    removeProjectMember(projectId: number, memberId: number): Promise<ApiResponse<null>> {
        return http.post<ApiResponse<null>>('/api/project/member/remove', {
            project_id: projectId,
            member_id: memberId,
        })
    },
}
