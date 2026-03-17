<script setup lang="ts">
type UserInfo = {
  name: string;
  avatar: string;
}

defineProps<{ userInfo: UserInfo }>()
</script>

<template>
  <div class="header-user">
    <a-avatar :size="36" class="user-avatar">
      {{ userInfo.name.charAt(0) }}
    </a-avatar>
    <div class="user-name">
      <span>{{ userInfo.name }}</span>
    </div>
  </div>
</template>

<style scoped>
/* 用户信息区域 - 控制用户区域宽度 */
.header-user {
  display: flex;
  align-items: center;
}

.user-avatar {
  cursor: pointer;
  background-color: #1890ff;
}

.user-name {
  font-size: 16px;
  color: #262626;
  margin-left: 7px;
}
</style>