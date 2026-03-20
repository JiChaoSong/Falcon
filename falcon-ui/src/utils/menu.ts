// src/utils/menu.ts
import type { RouteRecordRaw } from 'vue-router'
import { h } from 'vue'
interface MenuMeta  {
    icon:string
    show:boolean
    order:number
}
// 导入所有图标组件
import {
    HomeOutlined,
    ProjectOutlined,
    UnorderedListOutlined,
    SlidersOutlined,
    PlayCircleOutlined,
    SettingOutlined
} from '@ant-design/icons-vue'

// 图标映射
const iconMap: Record<string, any> = {
    home: HomeOutlined,
    project: ProjectOutlined,
    case: UnorderedListOutlined,
    scenario: SlidersOutlined,
    task: PlayCircleOutlined,
    system: SettingOutlined
}

/**
 * 从路由配置生成菜单项
 * @param routes 路由配置数组
 * @returns 菜单项数组
 */
export function generateMenuFromRoutes(routes: RouteRecordRaw[]) {
    const menuItems: any[] = []
    console.log('routes', routes)
    const processRoute = (route: RouteRecordRaw, basePath = '') => {
        // 1. 计算真实路径
        const currentPath = route.path.startsWith('/')
            ? route.path
            : `${basePath}/${route.path}`.replace(/\/+/g, '/')

        // 2. 先处理子路由（优先）
        if (route.children?.length) {
            route.children.forEach(child => {
                processRoute(child, currentPath)
            })
        }

        // 3. 是否显示
        const menuMeta:MenuMeta = route.meta?.menu as MenuMeta

        if (!route.meta?.title || menuMeta?.show === false) {
            return
        }

        const iconName = menuMeta?.icon
        const iconComponent = iconName ? iconMap[iconName] : null

        menuItems.push({
            key: route.name as string,
            label: route.meta.title,
            title: route.meta.title,
            path: currentPath,
            icon: iconComponent ? () => h(iconComponent) : undefined,
            order: menuMeta?.order ?? 999
        })
    }

    routes.forEach(route => processRoute(route))

    return menuItems.sort((a, b) => a.order - b.order)
}
