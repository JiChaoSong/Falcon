<script setup lang="ts">

import UserInfoComponent from "@/layout/components/UserInfoComponent.vue";
import {LogoutOutlined, SettingOutlined, UserOutlined} from "@ant-design/icons-vue";

const router = useRouter()

const userStore = useUserStore()


const userInfo = reactive({
  name: userStore.name,
  avatar: userStore.avatar
})

// 退出登录
const handleLogout = () => {
  Modal.confirm({
    title: '确认退出',
    content: '确定要退出登录吗？',
    onOk() {
      userStore.logout()
      message.success('已退出登录')
      router.push('/login')
    }
  })
}
</script>

<template>
  <div class="header-user">
    <a-dropdown placement="bottomRight">
      <user-info-component :userInfo="userInfo"/>
      <template #overlay>
        <a-menu>
          <a-menu-item>
            <user-outlined />
            个人中心
          </a-menu-item>
          <a-menu-item>
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