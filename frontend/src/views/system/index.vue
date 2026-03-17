<script setup lang="ts">
import { computed, ref } from 'vue'
import UserManagementPanel from '@/views/system/components/UserManagementPanel.vue'
import SystemConfigPanel from '@/views/system/components/SystemConfigPanel.vue'
import { useUserStore } from '@/store/modules/user'

const userStore = useUserStore()
const activeKey = ref(userStore.userInfo?.is_admin ? 'users' : 'config')

const tabs = computed(() => {
  const items = [
    {
      key: 'config',
      label: '系统设置',
      component: SystemConfigPanel,
    },
  ]

  if (userStore.userInfo?.is_admin) {
    items.unshift({
      key: 'users',
      label: '用户管理',
      component: UserManagementPanel,
    })
  }

  return items
})

const currentPanel = computed(() => {
  return tabs.value.find(item => item.key === activeKey.value)?.component || SystemConfigPanel
})
</script>

<template>
  <div class="system-page">
    <div class="page-header">
      <div>
        <h1>设置中心</h1>
        <p>用户管理和系统配置统一收敛到这里，避免新增顶级导航。</p>
      </div>
    </div>

    <a-card>
      <a-tabs v-model:activeKey="activeKey">
        <a-tab-pane v-for="item in tabs" :key="item.key" :tab="item.label" />
      </a-tabs>
      <component :is="currentPanel" />
    </a-card>
  </div>
</template>

<style scoped>
.system-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header h1 {
  margin: 0 0 8px;
}

.page-header p {
  margin: 0;
  color: rgba(0, 0, 0, 0.45);
}
</style>
