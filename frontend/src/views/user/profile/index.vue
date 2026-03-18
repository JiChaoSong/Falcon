<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import { UserApi } from '@/api/user'
import { useUserStore } from '@/store/modules/user'
import { formatDateTime } from '@/utils/tools'

const userStore = useUserStore()
const saving = ref(false)

const profileForm = reactive({
  name: '',
  email: '',
  phone: '',
  avatar: '',
})

watch(
  () => userStore.userInfo,
  (user) => {
    profileForm.name = user?.name || ''
    profileForm.email = user?.email || ''
    profileForm.phone = user?.phone || ''
    profileForm.avatar = user?.avatar || ''
  },
  { immediate: true },
)

const displayName = computed(() => userStore.name || userStore.username || '未命名用户')
const profileInitial = computed(() => displayName.value.slice(0, 1).toUpperCase() || 'U')

const formattedLastLogin = computed(() => {
  return formatDateTime(userStore.userInfo?.last_login_at, '暂无记录')
})

const handleSave = async () => {
  if (!userStore.userId) {
    message.error('当前用户信息未加载完成')
    return
  }

  saving.value = true
  try {
    const response = await UserApi.updateUser({
      id: userStore.userId,
      name: profileForm.name.trim(),
      email: profileForm.email.trim() || undefined,
      phone: profileForm.phone.trim() || undefined,
      avatar: profileForm.avatar.trim() || undefined,
    })
    userStore.updateUserInfo(response.data)
    message.success('个人资料已更新')
  } catch (_error) {
    message.error('个人资料更新失败')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="profile-page">
    <section class="hero-card">
      <div class="hero-content">
        <a-avatar :size="72" class="hero-avatar">{{ profileInitial }}</a-avatar>
        <div class="hero-copy">
          <p class="eyebrow">个人中心</p>
          <h1>{{ displayName }}</h1>
          <p class="hero-meta">@{{ userStore.username || 'unknown' }}</p>
        </div>
      </div>
      <div class="hero-stats">
        <div class="stat-card">
          <span class="stat-label">账户状态</span>
          <strong>{{ userStore.userInfo?.is_active ? '正常' : '已停用' }}</strong>
        </div>
        <div class="stat-card">
          <span class="stat-label">角色</span>
          <strong>{{ userStore.userInfo?.is_admin ? '管理员' : '普通用户' }}</strong>
        </div>
        <div class="stat-card">
          <span class="stat-label">最近登录</span>
          <strong>{{ formattedLastLogin }}</strong>
        </div>
      </div>
    </section>

    <div class="content-grid">
      <a-card title="基础资料" :bordered="false">
        <a-form layout="vertical">
          <a-form-item label="姓名">
            <a-input v-model:value="profileForm.name" placeholder="请输入姓名" />
          </a-form-item>
          <a-form-item label="邮箱">
            <a-input v-model:value="profileForm.email" placeholder="请输入邮箱" />
          </a-form-item>
          <a-form-item label="手机号">
            <a-input v-model:value="profileForm.phone" placeholder="请输入手机号" />
          </a-form-item>
          <a-form-item label="头像地址">
            <a-input v-model:value="profileForm.avatar" placeholder="请输入头像地址" />
          </a-form-item>
          <a-button type="primary" :loading="saving" @click="handleSave">保存资料</a-button>
        </a-form>
      </a-card>

      <a-card title="账户信息" :bordered="false">
        <div class="info-list">
          <div class="info-row">
            <span>用户 ID</span>
            <strong>{{ userStore.userId || '-' }}</strong>
          </div>
          <div class="info-row">
            <span>登录账号</span>
            <strong>{{ userStore.username || '-' }}</strong>
          </div>
          <div class="info-row">
            <span>显示名称</span>
            <strong>{{ userStore.name || '-' }}</strong>
          </div>
          <div class="info-row">
            <span>邮箱</span>
            <strong>{{ userStore.userInfo?.email || '-' }}</strong>
          </div>
          <div class="info-row">
            <span>手机号</span>
            <strong>{{ userStore.userInfo?.phone || '-' }}</strong>
          </div>
        </div>
      </a-card>
    </div>
  </div>
</template>

<style scoped>
.profile-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.hero-card {
  background: linear-gradient(135deg, #eaf4ff 0%, #ffffff 100%);
  border: 1px solid rgba(25, 62, 94, 0.08);
  border-radius: 24px;
  padding: 28px;
  display: flex;
  justify-content: space-between;
  gap: 24px;
  flex-wrap: wrap;
}

.hero-content {
  display: flex;
  align-items: center;
  gap: 18px;
}

.hero-avatar {
  background: #1890ff;
  color: #fff;
  font-size: 28px;
  font-weight: 700;
}

.eyebrow {
  margin: 0 0 8px;
  color: #7b5a2c;
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.hero-copy h1 {
  margin: 0;
  font-size: 32px;
  line-height: 1.1;
}

.hero-meta {
  margin: 8px 0 0;
  color: rgba(0, 0, 0, 0.55);
}

.hero-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(140px, 1fr));
  gap: 12px;
  flex: 1;
  min-width: 280px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.72);
  border-radius: 18px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stat-label {
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(280px, 1fr);
  gap: 20px;
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.info-row span {
  color: rgba(0, 0, 0, 0.45);
}

@media (max-width: 960px) {
  .content-grid {
    grid-template-columns: 1fr;
  }

  .hero-stats {
    grid-template-columns: 1fr;
  }
}
</style>
