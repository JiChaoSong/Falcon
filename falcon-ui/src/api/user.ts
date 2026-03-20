import {
    ResetPasswordPayload,
    UserCreate,
    UserInfo,
    UserListData,
    UserListQuery,
    UserLogin,
    UserLoginInfo,
    UserOption,
    UserUpdate
} from "@/types/user";
import {ApiResponse} from "@/types/api";
import { http } from '@/utils/requests'


export const UserApi = {
    // 登录
    userLogin(data: UserLogin): Promise<ApiResponse<UserLoginInfo>> {
        return http.post<ApiResponse<UserLoginInfo>>('/api/user/login', data)
    },

    // 登出
    userLogout(): Promise<ApiResponse<null>> {
      return http.post<ApiResponse>('/api/user/logout')
    },

    userList(data: UserListQuery): Promise<ApiResponse<UserListData>> {
        return http.post<ApiResponse<UserListData>>('/api/user/list', data)
    },

    createUser(data: UserCreate): Promise<ApiResponse<UserInfo>> {
        return http.post<ApiResponse<UserInfo>>('/api/user/create', data)
    },

    updateUser(data: UserUpdate): Promise<ApiResponse<UserInfo>> {
        return http.post<ApiResponse<UserInfo>>('/api/user/update', data)
    },

    deleteUser(id: number): Promise<ApiResponse<null>> {
        return http.post<ApiResponse<null>>('/api/user/delete', { id })
    },

    resetPassword(data: ResetPasswordPayload): Promise<ApiResponse<null>> {
        return http.post<ApiResponse<null>>('/api/user/reset-password', data)
    },

    userOptions(): Promise<ApiResponse<UserOption[]>> {
        return http.post<ApiResponse<UserOption[]>>('/api/user/options')
    },

    // 用户信息
    getUserInfo(): Promise<ApiResponse<UserInfo>> {
        return http.post<ApiResponse<UserInfo>>('/api/user/info')
    }
}
