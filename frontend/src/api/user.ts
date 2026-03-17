import {UserLogin} from "@/types/user";
import {ApiResponse} from "@/types/api";
import { http } from '@/utils/requests'


export const UserApi = {
    // 登录
    userLogin(data: UserLogin): Promise<ApiResponse> {
        return http.post<ApiResponse<ApiResponse>>('/api/user/login', data)
    },

    // 登出
    userLogout(): Promise<ApiResponse> {
      return http.post<ApiResponse>('/api/user/logout')
    },

    // // 用户列表
    // userList(data: T): Promise<ApiResponse> {
    //     return http.post<ApiResponse>('/api/user/list', data)
    // },

    // 用户信息
    getUserInfo(): Promise<ApiResponse> {
        return http.post<ApiResponse>('/api/user/info')
    }
}