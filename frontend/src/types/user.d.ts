import {BaseEntity, BaseQuery, BaseResponseList} from "@/types/base";

export interface UserLogin {
    username: string
    password: string
}

export interface UserInfo extends BaseEntity {
    username: string
    name: string
    email: string | null
    phone: string | null
    avatar: string | null
    is_active: boolean
    is_admin: boolean
    last_login_at?: string | null
}

export interface UserLoginInfo extends UserInfo {
    access_token: string
    refresh_token: string
    token_type: string
    expires_in: number
}

export interface UserListQuery extends BaseQuery {
    username?: string
    name?: string
    email?: string
    phone?: string
    is_active?: boolean
}

export interface UserListData extends BaseResponseList {
    results: UserInfo[]
}

export interface UserCreate {
    username: string
    password: string
    name: string
    email?: string
    phone?: string
    avatar?: string
    is_active?: boolean
    is_admin?: boolean
}

export interface UserUpdate {
    id: number
    username?: string
    name?: string
    email?: string
    phone?: string
    avatar?: string
    is_active?: boolean
    is_admin?: boolean
}

export interface ResetPasswordPayload {
    id: number
    password: string
}

export interface UserOption {
    id: number
    username: string
    name: string
}
