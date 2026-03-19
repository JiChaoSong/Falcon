import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { authGuard } from '@/router/guards'

const Layout = () => import('@/layout/BasicLayout.vue')

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Home',
        component: () => import('@/views/home/index.vue'),
        meta: {
          title: '控制台',
          requiresAuth: true,
          menu: { icon: 'dashboard', show: true, order: 1 },
        },
      },
      {
        path: 'project',
        name: 'Project',
        component: () => import('@/views/project/index.vue'),
        meta: {
          title: '项目管理',
          requiresAuth: true,
          menu: { icon: 'project', show: true, order: 2 },
        },
      },
      {
        path: 'case',
        name: 'case',
        component: () => import('@/views/case/index.vue'),
        meta: {
          title: '用例管理',
          requiresAuth: true,
          menu: { icon: 'csse', show: true, order: 3 },
        },
      },
      {
        path: 'scenario',
        name: 'Scenario',
        component: () => import('@/views/scenario/index.vue'),
        meta: {
          title: '场景管理',
          requiresAuth: true,
          menu: { icon: 'scenario', show: true, order: 4 },
        },
      },
      {
        path: 'task',
        name: 'Task',
        component: () => import('@/views/task/index.vue'),
        meta: {
          title: '任务管理',
          requiresAuth: true,
          menu: { icon: 'task', show: true, order: 5 },
        },
      },
      {
        path: 'task/detail/:taskId',
        name: 'TaskDetail',
        component: () => import('@/views/task/detail.vue'),
        meta: {
          title: '任务详情',
          requiresAuth: true,
          menu: { show: false },
        },
      },
      {
        path: 'system',
        name: 'System',
        component: () => import('@/views/system/index.vue'),
        meta: {
          title: '系统管理',
          requiresAuth: true,
          menu: { icon: 'system', show: true, order: 6 },
        },
      },
      {
        path: 'profile',
        name: 'UserProfile',
        component: () => import('@/views/user/profile/index.vue'),
        meta: {
          title: '个人中心',
          requiresAuth: true,
          menu: { show: false },
        },
      },
      {
        path: 'account/settings',
        name: 'AccountSettings',
        component: () => import('@/views/user/settings/index.vue'),
        meta: {
          title: '账号设置',
          requiresAuth: true,
          menu: { show: false },
        },
      },
    ],
  },
  {
    path: '/monitor/:taskId?',
    name: 'Monitor',
    component: () => import('@/layout/components/MonitorLayout.vue'),
    meta: { title: '任务监控', requiresAuth: true },
  },
  {
    path: '/report/:taskId?',
    name: 'TaskReport',
    component: () => import('@/views/task/report.vue'),
    meta: { title: '任务报告', requiresAuth: true },
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/user/login.vue'),
    meta: { title: '登录', requiresAuth: false },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/404/NotFound.vue'),
    meta: { title: '页面不存在' },
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(_to, _from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    }
    return { top: 0 }
  },
})

router.beforeEach(authGuard)

router.afterEach((to) => {
  document.title = (to.meta.title as string) || 'Falcon'
})

export default router
