<script setup lang="ts">
import LogoComponent from "@/layout/components/LogoComponent.vue";
import MenuComponent from "@/layout/components/MenuComponent.vue";
import UserOperationComponent from "@/layout/components/UserOperationComponent.vue";


</script>

<template>
  <div class="container-header">
    <logo-component/>
    <menu-component/>
    <user-operation-component/>
  </div >
  <div class="main-container">
    <router-view/>
  </div>
</template>

<style scoped>

/* 导航栏整体容器 - 固定定位 */
.container-header {
  position: fixed; /* 固定定位 */
  top: 0;
  left: 0;
  z-index: 1000; /* 确保在最上层 */
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 10%;
  height: var(--header-height);
  border-bottom: 1px solid #e8e8e8;
  background: #fff;
  width: 100%;
  box-sizing: border-box;
}

/* 主要内容区域 - 添加上边距避免被导航栏遮挡 */
.main-container {
  margin-top: var(--header-height, 64px);
  flex: 1;
  padding: 10px 10%;
  background-color: #F9FAFB;
  overflow-y: auto;
  min-height: 100vh;
}

/* 导航菜单核心 - 控制菜单整体宽度、选项间距、高度 */
.header-menu {
  flex: 1;
  border-bottom: none;
  display: flex;
  justify-content: center;
  height: 100%; /* 菜单高度与导航栏一致 */
}

/* 调整单个菜单项的尺寸和间距（关键） */
:deep(.ant-menu-horizontal) {
  height: 100%; /* 菜单整体高度 */
}
:deep(.ant-menu-item) {
  height: 100%; /* 单个菜单项高度与导航栏一致 */
  line-height: 64px; /* 文字垂直居中（与导航栏height一致） */
  padding: 0 30px; /* 菜单项内边距（控制选项宽度，可调整：如20px/40px） */
  margin: 0 10px; /* 菜单项之间的间距（可调整） */
  font-size: 16px; /* 菜单文字大小（可选） */
}

/* 悬停和选中状态 */
:deep(.ant-menu-item:hover),
:deep(.ant-menu-item-selected) {
  color: #1890ff;
}

</style>