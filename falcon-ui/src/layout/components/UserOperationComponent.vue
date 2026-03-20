<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import UserInfoComponent from '@/layout/components/UserInfoComponent.vue'
import { LogoutOutlined, SettingOutlined, UserOutlined } from '@ant-design/icons-vue'
import { useUserStore } from '@/store/modules/user'

const router = useRouter()
const userStore = useUserStore()

const userInfo = computed(() => ({
  name: userStore.name || userStore.username || '未命名用户',
  avatar: userStore.avatar,
}))

const handleOpenProfile = () => {
  router.push('/profile')
}

const handleOpenSettings = () => {
  router.push('/account/settings')
}

const handleLogout = () => {
  Modal.confirm({
    title: '确认退出登录？',
    content: '退出后将返回登录页，如有未保存内容请先处理。',
    async onOk() {
      await userStore.logout()
      message.success('已退出登录')
      router.push('/login')
    },
  })
}
</script>

<template>
  <div class="header-user">
    <a-dropdown placement="bottomRight">
      <user-info-component :userInfo="userInfo" />
      <template #overlay>
        <a-menu>
          <a-menu-item @click="handleOpenProfile">
            <user-outlined />
            个人中心
          </a-menu-item>
          <a-menu-item @click="handleOpenSettings">
            <setting-outlined />
            账户设置
          </a-menu-item>
          <a-menu-divider />
          <a-menu-item @click="handleLogout">
            <logout-outlined />
            退出登录
          </a-menu-item>
        </a-menu>
      </template>
    </a-dropdown>
  </div>
</template>

<style scoped>
</style>
