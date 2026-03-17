import {BaseEntity, BaseQuery, BaseResponseList} from "@/types/base"

export enum ProjectStatus {
    ACTIVE = "ACTIVE",
    INACTIVE = "INACTIVE",
    ARCHIVED = "ARCHIVED",

}
export enum ProjectPriority {
    LOW = "LOW",
    MEDIUM = "MEDIUM",
    HIGH = "HIGH",
}

export interface ProjectInfo extends BaseEntity{
    name: string
    description: string | null
    status: string | null
    priority: string | null
    tags: string[] | string | null
    owner_id: number
    owner_name: string
    scenario_count: number
    task_count: number
    members?: ProjectMemberInfo[]
}

export interface QueryProjectList extends BaseQuery{
    name?: string
    status?: string
    priority?: string
    tags?: string[]
    owner_id?: number
    owner_name?: string
}

export interface ProjectInfoList extends BaseResponseList{
    results: ProjectInfo[]
}

export interface ProjectCreate {
    name: string
    description?: string
    priority?: string
    tags?: string[]
    owner_id: number
    owner_name: string
}

export interface ProjectUpdate {
    id: number
    name: string
    description?: string
    status?: string
    priority?: string
    tags?: string[]
    owner_id?: number
    owner_name?: string
}

export interface GetProjectInfo {
    id: number
}

export interface ProjectMemberInfo {
    id: number
    member_id: number
    member_name: string
    member_role: string
    is_active: boolean
    join_time?: string | null
}

export interface ProjectMemberCreate {
    project_id: number
    member_id: number
    member_role: string
}

export interface ProjectMemberUpdate {
    project_id: number
    member_id: number
    member_role: string
}
