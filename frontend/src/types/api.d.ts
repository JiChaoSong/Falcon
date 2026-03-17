// src/types/api.d.ts
// API响应数据格式
export interface ApiResponse<T = any> {
    code: number
    message: string
    data: T
    systemTime:string
    type: string
    error: string
    request_id: string
}

// 分页请求参数
export interface PageParams {
    page?: number
    pageSize?: number
    [key: string]: any
}

// 分页响应数据
export interface PageResponse<T = any> {
    results: T[]
    total: number
    page: number
    page_size: number
    total_page: number
}

// 上传文件响应
export interface UploadResponse {
    url: string
    name: string
    size: number
}