import {BaseEntity} from "@/types/base";

export interface UserLogin {
    username: string
    password: string
}

export interface UserInfo extends BaseEntity {
    username: string
    name: string
    email: string
    phone: string
    avatar: string
    is_active: boolean
    is_admin: boolean
    access_token: string
}