<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import { message } from 'ant-design-vue'
import { useUserStore } from '@/store/modules/user'

type AccountPreference = {
  emailNotice: boolean
  taskNotice: boolean
  reportNotice: boolean
  compactMode: boolean
}

const userStore = useUserStore()
const storageKey = computed(() => `falcon.account.settings.${userStore.userId || 'guest'}`)

const preferenceForm = reactive<AccountPreference>({
  emailNotice: true,
  taskNotice: true,
  reportNotice: false,
  compactMode: false,
})

const applyDefault = () => {
  preferenceForm.emailNotice = true
  preferenceForm.taskNotice = true
  preferenceForm.reportNotice = false
  preferenceForm.compactMode = false
}

const loadPreferences = () => {
  const raw = localStorage.getItem(storageKey.value)
  if (!raw) {
    applyDefault()
    return
  }

  try {
    const parsed = JSON.parse(raw)
    preferenceForm.emailNotice = Boolean(parsed.emailNotice)
    preferenceForm.taskNotice = Boolean(parsed.taskNotice)
    preferenceForm.reportNotice = Boolean(parsed.reportNotice)
    preferenceForm.compactMode = Boolean(parsed.compactMode)
  } catch (_error) {
    localStorage.removeItem(storageKey.value)
    applyDefault()
  }
}

watch(storageKey, loadPreferences, { immediate: true })

const handleSavePreference = () => {
  localStorage.setItem(storageKey.value, JSON.stringify(preferenceForm))
  message.success('账户设置已保存')
}

const handleResetPreference = () => {
  localStorage.removeItem(storageKey.value)
  applyDefault()
  message.success('账户设置已恢复默认')
}
</script>

<template>
  <div class="settings-page">
    <section class="settings-header">
      <div>
        <p class="header-kicker">账户设置</p>
        <h1>安全、通知与个人偏好</h1>
        <p class="header-desc">这里适合放个人安全策略、通知偏好和使用习惯配置。当前先提供本地偏好设置和账户信息概览。</p>
      </div>
    </section>

    <div class="settings-grid">
      <a-card title="通知偏好" :bordered="false">
        <a-form layout="vertical">
          <a-form-item>
            <a-switch v-model:checked="preferenceForm.emailNotice" />
            <span class="switch-label">接收账户安全邮件提醒</span>
          </a-form-item>
          <a-form-item>
            <a-switch v-model:checked="preferenceForm.taskNotice" />
            <span class="switch-label">任务状态变化时提醒我</span>
          </a-form-item>
          <a-form-item>
            <a-switch v-model:checked="preferenceForm.reportNotice" />
            <span class="switch-label">报告生成完成后提醒我</span>
          </a-form-item>
          <a-form-item>
            <a-switch v-model:checked="preferenceForm.compactMode" />
            <span class="switch-label">使用更紧凑的页面布局</span>
          </a-form-item>
          <div class="button-row">
            <a-button type="primary" @click="handleSavePreference">保存设置</a-button>
            <a-button @click="handleResetPreference">恢复默认</a-button>
          </div>
        </a-form>
      </a-card>

      <a-card title="安全与会话" :bordered="false">
        <div class="security-panel">
          <div class="security-item">
            <span>当前账号</span>
            <strong>{{ userStore.username || '-' }}</strong>
          </div>
          <div class="security-item">
            <span>用户角色</span>
            <strong>{{ userStore.userInfo?.is_admin ? '管理员' : '普通用户' }}</strong>
          </div>
          <div class="security-item">
            <span>账号状态</span>
            <strong>{{ userStore.userInfo?.is_active ? '正常' : '已停用' }}</strong>
          </div>
          <a-alert
            type="info"
            show-icon
            message="密码修改和登录设备管理建议后端补专用接口后再接入，这个页面结构已经预留。"
          />
        </div>
      </a-card>
    </div>
  </div>
</template>

<style scoped>
.settings-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.settings-header {
  border-radius: 24px;
  padding: 28px;
  background: linear-gradient(135deg, #eaf4ff 0%, #ffffff 100%);
  border: 1px solid rgba(62, 110, 74, 0.1);
}

.header-kicker {
  margin: 0 0 10px;
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #7c6330;
}

.settings-header h1 {
  margin: 0 0 10px;
}

.header-desc {
  margin: 0;
  color: rgba(0, 0, 0, 0.55);
}

.settings-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(280px, 1fr);
  gap: 20px;
}

.switch-label {
  margin-left: 12px;
  vertical-align: middle;
}

.button-row {
  display: flex;
  gap: 12px;
}

.security-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.security-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

@media (max-width: 960px) {
  .settings-grid {
    grid-template-columns: 1fr;
  }
}
</style>
