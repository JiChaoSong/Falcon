
// Token 相关操作
const TOKEN_KEY = 'access_token'

/**
 * 获取token
 */
export function getToken(): string {
    return localStorage.getItem(TOKEN_KEY) || ''
}

/**
 * 设置token
 */
export function setToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token)
}

/**
 * 移除token
 */
export function removeToken(): void {
    localStorage.removeItem(TOKEN_KEY)
}

/**
 * 检查token是否有效
 */
export function isValidToken(token: string): boolean {
    if (!token) return false

    // 解析JWT token的payload部分
    try {
        const payload = JSON.parse(atob(token.split('.')[1]))
        const currentTime = Math.floor(Date.now() / 1000)

        // 检查token是否过期
        return payload.exp > currentTime
    } catch {
        return false
    }
}