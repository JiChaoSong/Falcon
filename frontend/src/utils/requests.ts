import axios, {
    AxiosInstance, AxiosRequestConfig, AxiosResponse, InternalAxiosRequestConfig
} from "axios";

import {message} from "ant-design-vue";
import type { ApiResponse } from '@/types/api'


const service:AxiosInstance = axios.create({
    baseURL: import.meta.env.VUE_APP_BASE_URL,
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
    }else {
        message.error(res.message || "请求失败", 5)
        return Promise.reject(new Error(res.message || 'Error'))
    }
}, error => {
    message.error(error);
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