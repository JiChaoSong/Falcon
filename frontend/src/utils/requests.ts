import axios, {
    AxiosInstance, AxiosRequestConfig, AxiosResponse, InternalAxiosRequestConfig
} from "axios";

import {message} from "ant-design-vue";
import type { ApiResponse } from '@/types/api'
import { useUserStore } from '@/store/modules/user'
import router from '@/router'


let isRedirectingToLogin = false

const redirectToLogin = async () => {
    const userStore = useUserStore()
    const currentRoute = router.currentRoute.value
    const redirect = currentRoute.fullPath && currentRoute.path !== '/login'
        ? currentRoute.fullPath
        : '/dashboard'

    userStore.resetState()

    if (isRedirectingToLogin || currentRoute.path === '/login') {
        return
    }

    isRedirectingToLogin = true
    try {
        await router.replace({
            path: '/login',
            query: { redirect },
        })
    } finally {
        isRedirectingToLogin = false
    }
}


const service:AxiosInstance = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json;charset=utf-8'
    }
})

// 请求拦截器
service.interceptors.request.use((config:InternalAxiosRequestConfig) => {
    const userStore = useUserStore()
    config.headers['Authorization'] = userStore.token
    return config
}, error => {
    return Promise.reject(error);
})

// 响应拦截器
service.interceptors.response.use((response:AxiosResponse) => {
    const res = response.data as ApiResponse
    if (res.code === 20000) {
        return response.data
    } else {
        const isAuthExpired = res.code === 40001
            || res.code === 42001
            || String(res.message || '').includes('登录信息失效')

        if (isAuthExpired) {
            message.error(res.message || "登录信息失效，请重新登录！", 3)
            void redirectToLogin()
            return Promise.reject(new Error(res.message || 'Login expired'))
        }

        message.error(res.message || "请求失败", 5)
        return Promise.reject(new Error(res.message || 'Error'))
    }
}, error => {
    const status = error?.response?.status
    const responseMessage = error?.response?.data?.message

    if (status === 401 || status === 403) {
        message.error(responseMessage || "登录信息失效，请重新登录！", 3)
        void redirectToLogin()
        return Promise.reject(error)
    }

    message.error(responseMessage || error?.message || "请求失败");
    return Promise.reject(error);
})

// 封装通用的请求方法
export const http = {
    get<T = any>(url: string, params?: object, config?: AxiosRequestConfig): Promise<T> {
        return service.get(url, { params, ...config })
    },

    post<T = any>(url: string, data?: object, config?: AxiosRequestConfig): Promise<T> {
        return service.post(url, data, config)
    },

    put<T = any>(url: string, data?: object, config?: AxiosRequestConfig): Promise<T> {
        return service.put(url, data, config)
    },

    delete<T = any>(url: string, params?: object, config?: AxiosRequestConfig): Promise<T> {
        return service.delete(url, { params, ...config })
    },

    patch<T = any>(url: string, data?: object, config?: AxiosRequestConfig): Promise<T> {
        return service.patch(url, data, config)
    },

    // 文件上传
    upload<T = any>(url: string, formData: FormData, config?: AxiosRequestConfig): Promise<T> {
        return service.post(url, formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            ...config
        })
    },

    // 文件下载
    download(url: string, params?: object, filename?: string): Promise<void> {
        return service.get(url, {
            params,
            responseType: 'blob'
        }).then((response) => {
            const blob = new Blob([response.data])
            const downloadUrl = window.URL.createObjectURL(blob)
            const link = document.createElement('a')
            link.href = downloadUrl
            link.download = filename || 'download'
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
            window.URL.revokeObjectURL(downloadUrl)
        })
    }
}

// 导出原始的axios实例，用于特殊需求
export default service
