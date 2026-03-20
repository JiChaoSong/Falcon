<script setup lang="ts">

import {AreaChartOutlined} from "@ant-design/icons-vue";
import router from "@/router";
import {SETTINGS} from "@/settings.ts";
// 点击logo
const handleLogoClick = () => {
  router.push('/');
}
</script>

<template>
  <div class="header-logo" @click="handleLogoClick">
    <div class="logo-icon">
      <area-chart-outlined />
    </div>
    <div class="logo-text">{{ SETTINGS.title }}</div>
  </div>
</template>

<style scoped>
/* Logo区域 - 控制logo区域宽度 */
.header-logo {
  display: flex;
  align-items: center;
  margin-right: 40px;
}

.logo-icon {
  font-size: 24px;
  color: #1890ff;
  margin-right: 8px;
}

.logo-text {
  font-size: 20px;
  font-weight: 700;
  color: #1890ff;
}
</style>