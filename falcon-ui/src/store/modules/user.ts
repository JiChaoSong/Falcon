import { defineStore } from 'pinia'
import {getToken, removeToken, setToken} from "@/utils/auth.ts";
import {UserInfo, UserLogin} from "@/types/user";
import {UserApi} from "@/api/user.ts";

export const useUserStore = defineStore('user', () => {
    // ==================== State ====================

    const token = ref<string>(getToken() || "")

    const userInfo = ref<UserInfo | null>(null)

    // ==================== Getters ====================
    const isLogin = computed(() => !!token.value)
    const name = computed(() => userInfo.value?.name || '')
    const username = computed(() => userInfo.value?.username || '')
    const userId = computed(() => userInfo.value?.id || 0)
    const avatar = computed(() => userInfo.value?.avatar || '')


    // ==================== Actions ====================

    /**
     * 用户登录
     * @param loginForm - 登录参数
     */
    const login = async (loginForm: UserLogin) => {
        try {
            // 调用登录API
            const response = await UserApi.userLogin(loginForm)

            // 存储token
            const accessToken:string = response.data.access_token
            token.value = accessToken
            setToken(accessToken)

            // 获取用户信息
            await getUserInfo()

            return Promise.resolve(response)
        } catch (error) {
            // 登录失败时清除token
            token.value = ''
            removeToken()
            return Promise.reject(error)
        }
    }

    /**
     * 用户登出
     */
    const logout = async () => {
        try {
            // 调用登出API
            if (token.value) {
                await UserApi.userLogout()
            }
        } finally {
            // 无论API调用成功与否，都清除本地状态
            resetState()
        }
    }

    /**
     * 获取用户信息
     */
    const getUserInfo = async () => {
        try {
            // 如果没有token，直接返回
            if (!token.value) {
                return Promise.reject(new Error('未登录'))
            }

            const response = await UserApi.getUserInfo()

            // 更新用户信息
            userInfo.value = response.data

            return Promise.resolve(response)
        } catch (error) {
            // 获取用户信息失败时清除token
            token.value = ''
            removeToken()
            return Promise.reject(error)
        }
    }

    /**
     * 重置状态（清空用户数据）
     */
    const resetState = () => {
        token.value = ''
        userInfo.value = null
        removeToken()
    }

    /**
     * 更新用户信息
     * @param data - 更新的用户信息
     */
    const updateUserInfo = (data: Partial<UserInfo>) => {
        if (userInfo.value) {
            userInfo.value = { ...userInfo.value, ...data }
        }
    }

    return {
        // State
        token,
        userInfo,

        // Getters
        isLogin,
        username,
        userId,
        avatar,
        name,

        // Actions
        login,
        logout,
        getUserInfo,
        resetState,
        updateUserInfo
    }
})