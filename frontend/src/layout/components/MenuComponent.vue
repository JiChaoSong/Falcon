<script setup lang="ts">
import {ref, watch} from 'vue';
import { useRouter, useRoute } from 'vue-router';
import {MenuProps} from 'ant-design-vue';
import {generateMenuFromRoutes} from "@/utils/menu.ts";

const router = useRouter();
const route = useRoute();

const current = ref<string[]>(['project']);


// 获取路由并生成菜单项
const menuItems = computed(() => {
  const routes = router.getRoutes();
  // 找到 Layout 路由的子路由
  const layoutRoute = routes.find(r => r.path === '/' && r.children);

  return layoutRoute ? generateMenuFromRoutes(layoutRoute.children || []) : [];
});

// 转换为 Ant Design Menu 需要的格式
const items = computed<MenuProps['items']>(() =>
    menuItems.value.map(item => ({
      key: item.key,
      label: item.label,
      title: item.title,
      icon: item.icon,
    }))
);
// 根据当前路由更新选中状态
const updateCurrentMenu = () => {
  const currentPath = route.path;

  // 精确匹配优先
  const exactMatch = menuItems.value.find(item => item.path === currentPath);
  if (exactMatch) {
    current.value = [exactMatch.key];
    return;
  }

  // 模糊匹配（对于嵌套路由）
  const matchedItem = menuItems.value.find(item =>
      currentPath.startsWith(item.path) && item.path !== '/'
  );
  if (matchedItem) {
    current.value = [matchedItem.key];
    return;
  }

  // 如果没有匹配，使用默认值
  current.value = menuItems.value.length > 0 ? [menuItems.value[0].key] : [];
};

// 监听路由变化
watch(
    () => route.path,
    () => {
      updateCurrentMenu();
    },
    { immediate: true }
);

// 菜单点击事件
const handleMenuClick: MenuProps['onClick'] = (e) => {
  const menuKey = String(e.key);
  const menuItem = menuItems.value.find(item => item.key === menuKey);
  if (menuItem?.path) {
    router.push(menuItem.path);
  }
};


// 初始更新
onMounted(() => {
  updateCurrentMenu();
});

</script>

<template>
  <a-menu
      v-model:selectedKeys="current"
      mode="horizontal"
      :items="items"
      theme="light"
      class="header-menu"
      @click="handleMenuClick"
  />
</template>

<style scoped>
  .header-menu {
    line-height: 64px;
    border-bottom: 1px solid #f0f0f0;
  }
</style>
