import type { NavigationGuardNext, RouteLocationNormalized } from 'vue-router'
import { useUserStore } from '@/store/modules/user'

/**
 * 认证守卫
 */
export async function authGuard(
    to: RouteLocationNormalized,
    _from: RouteLocationNormalized,
    next: NavigationGuardNext
) {

    const userStore = useUserStore()

    console.log('userStore', userStore)
    const { token } = userStore

    if (!to.meta.requiresAuth) {
        return next()
    }

    if (!token) {
        return next({
            path: '/login',
            query: { redirect: to.fullPath },
        })
    }

    // 如果有 token 但没有用户信息，先获取用户信息
    if (!userStore.userInfo) {
        try {
            await userStore.getUserInfo()
        } catch (error) {
            // 获取用户信息失败，清除 token 并跳转到登录页
            userStore.resetState()
            return next({
                path: '/login',
                query: {
                    redirect: to.fullPath
                }
            })
        }
    }


    next()
}
