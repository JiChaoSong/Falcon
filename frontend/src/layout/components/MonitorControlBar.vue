<template>
  <div class="container-header">
    <LogoComponent />
    <div class="operation-container">
      <div class="spacer"></div>
      <div class="right-group">
        <div class="header-menu">
          <div class="menu">
            <span class="menu-label">任务ID</span>
            <span class="menu-value">{{ taskId }}</span>
          </div>
          <div class="menu-divider"></div>
          <div class="menu">
            <span class="menu-label">任务名称</span>
            <span class="menu-value">{{ taskInfo?.name || '未命名任务' }}</span>
          </div>
          <div class="menu-divider"></div>
          <div class="menu">
            <span class="menu-label">目标主机</span>
            <span class="menu-value">{{ taskInfo?.host || '-' }}</span>
          </div>
          <div class="menu-divider"></div>
          <div class="menu">
            <span class="menu-label">状态</span>
            <a-tag :color="getStatusColor(metrics?.state)">
              {{ getStatusName(metrics?.state) }}
            </a-tag>
          </div>
          <div class="menu-divider"></div>
          <div class="menu">
            <span class="menu-label">开始时间</span>
            <span class="menu-value">{{ formatDateTime(metrics?.start_time) }}</span>
          </div>
          <div class="menu-divider"></div>
          <div class="menu">
            <span class="menu-label">运行时间</span>
            <span class="menu-value">{{ metrics?.runtime || '--' }}</span>
          </div>
        </div>
        <div class="header-user">
          <a-button
              type="primary"
              @click="$emit('startTest')"
              :loading="controlLoading"
              :disabled="taskRunning"
          >
            开始压测
          </a-button>
          <a-button
              type="primary"
              danger
              @click="$emit('stopTest')"
              :loading="controlLoading"
              :disabled="!taskRunning || metrics?.state === 'stopping'"
          >
            停止
          </a-button>
          <warning-button class="warning-btn" @click="$emit('pauseTest')" :disabled="!taskRunning || metrics?.state === 'stopping'">
            暂停
          </warning-button>
          <a-button @click="$emit('resumeTest')" :disabled="taskRunning">
            恢复
          </a-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import LogoComponent from "@/layout/components/LogoComponent.vue";
import WarningButton from "@/components/WarningButton.vue";
import { formatDateTime } from "@/utils/tools";
import { Metrics, STATE_COLORS, STATE_NAMES, SystemState } from "@/layout/type.ts";
import type { TaskInfo } from "@/types/task";

const props = defineProps<{
  taskId: number;
  taskInfo: TaskInfo | null;
  metrics: Metrics | null;
  taskRunning: boolean;
  controlLoading: boolean;
}>();

const emit = defineEmits<{
  startTest: [];
  stopTest: [];
  pauseTest: [];
  resumeTest: [];
}>();

const getStatusName = (state?: SystemState): string => {
  return STATE_NAMES[state || 'missing'] || "未知状态";
};

const getStatusColor = (state?: SystemState): string => {
  return STATE_COLORS[state || 'missing'] || "gray";
};
</script>

<style scoped>
.container-header {
  position: fixed;
  top: 0;
  left: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 10%;
  height: 64px;
  border-bottom: 1px solid #e8e8e8;
  background: #fff;
  width: 100%;
  box-sizing: border-box;
}

.operation-container {
  display: flex;
  align-items: center;
  flex: 1;
  margin-left: 24px;
}

.spacer {
  flex: 1;
}

.right-group {
  display: flex;
  align-items: center;
  gap: 24px;
}

.header-menu {
  display: flex;
  align-items: center;
  gap: 0;
  font-size: 13px;
}

.menu {
  display: flex;
  align-items: center;
  gap: 6px;
}

.menu-label {
  color: #666;
  font-weight: 500;
}

.menu-value {
  color: #1f2937;
  font-weight: 600;
}

.menu-divider {
  width: 1px;
  height: 16px;
  background: #e8e8e8;
  margin: 0 12px;
}

.header-user {
  display: flex;
  align-items: center;
  gap: 8px;
}

.warning-btn {
  margin-left: 4px;
}

@media (max-width: 1200px) {
  .container-header {
    padding: 0 5%;
  }

  .header-menu {
    display: none;
  }
}

@media (max-width: 768px) {
  .container-header {
    padding: 0 16px;
    height: auto;
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
    padding-top: 16px;
    padding-bottom: 16px;
  }

  .operation-container {
    margin-left: 0;
  }

  .right-group {
    flex-direction: column;
    gap: 12px;
    width: 100%;
  }

  .header-user {
    justify-content: center;
    flex-wrap: wrap;
  }
}
</style>
