import { h } from 'vue';
import { LoadingOutlined } from '@ant-design/icons-vue';

// 图标映射（动态导入）
const iconImporters: Record<string, () => Promise<any>> = {
    home: () => import('@ant-design/icons-vue').then(m => m.HomeOutlined),
    project: () => import('@ant-design/icons-vue').then(m => m.ProjectOutlined),
    csse: () => import('@ant-design/icons-vue').then(m => m.UnorderedListOutlined),
    scenario: () => import('@ant-design/icons-vue').then(m => m.SlidersOutlined),
    task: () => import('@ant-design/icons-vue').then(m => m.PlayCircleOutlined),
    system: () => import('@ant-design/icons-vue').then(m => m.SettingOutlined),
};

// 图标缓存
const iconCache: Record<string, any> = {};

/**
 * 获取图标组件
 * @param iconName 图标名称
 * @returns 图标组件的渲染函数
 */
export async function getIconComponent(iconName: string) {
    if (!iconName || !iconImporters[iconName]) {
        return undefined;
    }

    if (iconCache[iconName]) {
        return () => h(iconCache[iconName]);
    }

    try {
        const module = await iconImporters[iconName]();
        const iconComponent = module.default || module;
        iconCache[iconName] = iconComponent;
        return () => h(iconComponent);
    } catch (error) {
        console.error(`Failed to load icon: ${iconName}`, error);
        return () => h(LoadingOutlined);
    }
}