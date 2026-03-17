// src/router/index.ts
import {createRouter, createWebHistory, type RouteRecordRaw} from 'vue-router'
import {authGuard} from '@/router/guards'

// 导入布局组件和页面组件
const Layout = () => import('@/layout/BasicLayout.vue')

// 创建路由配置
const routes: RouteRecordRaw[] = [
    {
        path: '/',
        component: Layout,
        redirect: '/dashboard',
        children: [
            {
                path: 'dashboard',
                name: 'home',
                component: () => import('@/views/home/index.vue'),
                meta: {
                    title: '首页',
                    requiresAuth: true,
                    menu: {
                        icon: 'dashboard', // 图标名称，对应上面的映射
                        show: true,   // 是否显示在菜单中
                        order: 1      // 菜单排序
                    }
                }
            },
            {
                path: 'project',
                name: 'Project',
                component: () => import('@/views/project/index.vue'),
                meta: {
                    title: '项目',
                    requiresAuth: true,
                    menu: {
                        icon: 'project',
                        show: true,
                        order: 2
                    }
                }
            },
            {
                path: 'csse',
                name: 'Csse',
                component: () => import('@/views/case/index.vue'),
                meta: {
                    title: '用例',
                    requiresAuth: true,
                    menu: {
                        icon: 'csse',
                        show: true,
                        order: 3
                    }
                }
            },
            {
                path: 'scenario',
                name: 'Scenario',
                component: () => import('@/views/scenario/index.vue'),
                meta: {
                    title: '场景',
                    requiresAuth: true,
                    menu: {
                        icon: 'scenario',
                        show: true,
                        order: 4
                    }
                }
            },
            {
                path: 'task',
                name: 'Task',
                component: () => import('@/views/task/index.vue'),
                meta: {
                    title: '任务',
                    requiresAuth: true,
                    menu: {
                        icon: 'task',
                        show: true,
                        order: 5
                    }
                }
            },
            {
                path: 'system',
                name: 'System',
                component: () => import('@/views/system/index.vue'),
                meta: {
                    title: '设置',
                    requiresAuth: true,
                    menu: {
                        icon: 'system',
                        show: true,
                        order: 6
                    }
                }
            },

            // // 可以添加不显示在菜单中的路由
            // {
            //     path: 'project/detail/:id',
            //     name: 'ProjectDetail',
            //     component: () => import('@/views/project/Detail.vue'),
            //     meta: {
            //         title: '项目详情',
            //         requiresAuth: true,
            //         menu: {
            //             show: false // 不显示在菜单中
            //         }
            //     }
            // }
        ]
    },

    {
        path: '/monitor/:taskId?',
        name: 'Monitor',
        component: () => import('@/layout/components/MonitorLayout.vue'),
        meta: { title: '任务监控', requiresAuth: true }
    },
    {
        path: '/report/:taskId?',
        name: 'TaskReport',
        component: () => import('@/views/task/report.vue'),
        meta: { title: '任务报告', requiresAuth: true }
    },
    // 登录页
    {
        path: '/login',
        name: 'Login',
        component: () => import('@/views/user/login.vue'),
        meta: { title: '登录', requiresAuth: false }
    },
    // 404页面配置（可选）
    {
        path: '/:pathMatch(.*)*',
        name: 'NotFound',
        component: () => import('@/views/404/NotFound.vue'),
        meta: { title: '页面未找到' }
    }
]

// 创建路由实例
const router = createRouter({
    // 使用history模式，需要服务器支持
    history: createWebHistory(import.meta.env.BASE_URL),
    // 使用hash模式，兼容性更好（如需使用，请取消注释下面一行，并注释上面一行）
    // history: createWebHashHistory(import.meta.env.BASE_URL),
    routes,
    // 滚动行为
    scrollBehavior(_to, _from, savedPosition) {
        if (savedPosition) {
            return savedPosition
        } else {
            return { top: 0 }
        }
    }
})

// 全局前置守卫
router.beforeEach(authGuard)

// 全局后置守卫
router.afterEach((to, _from) => {
    // console.log(`路由跳转完成: ${from.path} -> ${to.path}`)
    document.title = to.meta.title as string || 'Vue App'
})

export default router
