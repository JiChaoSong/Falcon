<template>
  <div class="monitor-topbar">
    <LogoComponent />

    <div class="topbar-main">
      <div class="task-identity">
        <span class="task-name">{{ taskInfo?.name || "未命名任务" }}</span>
        <a-tag :color="getStatusColor(metrics?.state)">
          {{ getStatusName(metrics?.state) }}
        </a-tag>
        <span class="connection-pill" :data-connected="wsConnected ? 'yes' : 'no'">
          <span class="connection-dot"></span>
          {{ wsConnected ? "实时连接" : "轮询兜底" }}
        </span>
      </div>

      <div class="task-brief">
        <span>任务 #{{ taskId }}</span>
        <span>目标主机 {{ taskInfo?.host || "-" }}</span>
        <span>开始时间 {{ formatDateTime(metrics?.start_time) }}</span>
        <span>运行时长 {{ metrics?.runtime || "--" }}</span>
      </div>
    </div>

    <div class="topbar-actions">
      <a-button type="primary" size="small" :loading="controlLoading" :disabled="taskRunning" @click="$emit('startTest')">
        开始
      </a-button>
      <a-button
        type="primary"
        danger
        size="small"
        :loading="controlLoading"
        :disabled="!taskRunning || metrics?.state === 'stopping'"
        @click="$emit('stopTest')"
      >
        停止
      </a-button>
      <WarningButton size="small" :disabled="!taskRunning || metrics?.state === 'stopping'" @click="$emit('pauseTest')">
        暂停
      </WarningButton>
      <a-button size="small" :disabled="taskRunning" @click="$emit('resumeTest')">
        恢复
      </a-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import LogoComponent from "@/layout/components/LogoComponent.vue";
import WarningButton from "@/components/WarningButton.vue";
import { formatDateTime } from "@/utils/tools";
import { STATE_COLORS, STATE_NAMES, type Metrics, type SystemState } from "@/layout/type.ts";
import type { TaskInfo } from "@/types/task";

defineProps<{
  taskId: number;
  taskInfo: TaskInfo | null;
  metrics: Metrics | null;
  taskRunning: boolean;
  controlLoading: boolean;
  wsConnected: boolean;
}>();

defineEmits<{
  startTest: [];
  stopTest: [];
  pauseTest: [];
  resumeTest: [];
}>();

const getStatusName = (state?: SystemState): string => {
  return STATE_NAMES[state || "missing"] || "运行异常";
};

const getStatusColor = (state?: SystemState): string => {
  return STATE_COLORS[state || "missing"] || "default";
};
</script>

<style scoped>
.monitor-topbar {
  position: fixed;
  top: 0;
  left: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  gap: 18px;
  width: 100%;
  height: 64px;
  padding: 0 28px;
  box-sizing: border-box;
  border-bottom: 1px solid rgba(148, 163, 184, 0.16);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.96) 0%, rgba(248, 250, 252, 0.92) 100%);
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.05);
  backdrop-filter: blur(16px);
}

.topbar-main {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 6px;
  min-width: 0;
  flex: 1;
}

.task-identity {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

:deep(.task-identity .ant-tag) {
  margin-inline-end: 0;
  border-radius: 999px;
  font-weight: 700;
}

.task-name {
  max-width: 360px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 18px;
  font-weight: 800;
  color: #0f172a;
}

.connection-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.06);
  color: #475569;
  font-size: 12px;
  font-weight: 700;
}

.connection-pill[data-connected="yes"] {
  background: rgba(16, 185, 129, 0.14);
  color: #047857;
}

.connection-pill[data-connected="no"] {
  background: rgba(245, 158, 11, 0.16);
  color: #b45309;
}

.connection-dot {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: currentColor;
}

.task-brief {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #64748b;
  font-size: 12px;
  flex-wrap: wrap;
}

.task-brief span {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(241, 245, 249, 0.92);
  border: 1px solid rgba(148, 163, 184, 0.12);
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-left: 10px;
  border-left: 1px solid rgba(148, 163, 184, 0.16);
}
</style>
