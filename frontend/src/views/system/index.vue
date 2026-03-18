<script setup lang="ts">
import { computed, ref } from 'vue'
import SystemConfigPanel from '@/views/system/components/SystemConfigPanel.vue'
import UserManagementPanel from '@/views/system/components/UserManagementPanel.vue'
import WorkerManagementPanel from '@/views/system/components/WorkerManagementPanel.vue'
import { useUserStore } from '@/store/modules/user'

const userStore = useUserStore()
const activeKey = ref(userStore.userInfo?.is_admin ? 'users' : 'config')

const tabs = computed(() => {
  const items = [
    {
      key: 'workers',
      label: '节点管理',
      component: WorkerManagementPanel,
    },
    {
      key: 'config',
      label: '系统配置',
      component: SystemConfigPanel,
    },

  ]

  if (userStore.userInfo?.is_admin) {
    items.unshift(
      {
        key: 'users',
        label: '用户管理',
        component: UserManagementPanel,
      },
    )
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
        <h1>系统设置</h1>
        <p>统一管理平台配置、账号权限和执行节点。</p>
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
