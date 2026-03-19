<template>
  <div class="container-header">
    <LogoComponent />

    <div class="header-content">
      <div class="header-main">
        <div class="header-eyebrow">任务监控</div>
        <div class="header-title-row">
          <h1 class="header-title">{{ taskInfo?.name || "未命名任务" }}</h1>
          <div class="status-group">
            <span class="ws-pill" :data-connected="wsConnected ? 'yes' : 'no'">
              <span class="ws-dot"></span>
              {{ wsConnected ? "实时连接" : "轮询兜底" }}
            </span>
            <a-tag :color="getStatusColor(metrics?.state)">
              {{ getStatusName(metrics?.state) }}
            </a-tag>
          </div>
        </div>

        <div class="meta-list">
          <div class="meta-item">
            <span class="meta-label">任务 ID</span>
            <span class="meta-value">#{{ taskId }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">目标地址</span>
            <span class="meta-value">{{ taskInfo?.host || "-" }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">开始时间</span>
            <span class="meta-value">{{ formatDateTime(metrics?.start_time) }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">运行时长</span>
            <span class="meta-value">{{ metrics?.runtime || "--" }}</span>
          </div>
        </div>
      </div>

      <div class="header-actions">
        <a-button type="primary" class="action-btn" :loading="controlLoading" :disabled="taskRunning" @click="$emit('startTest')">
          开始
        </a-button>
        <a-button
          type="primary"
          danger
          class="action-btn"
          :loading="controlLoading"
          :disabled="!taskRunning || metrics?.state === 'stopping'"
          @click="$emit('stopTest')"
        >
          停止
        </a-button>
        <WarningButton class="action-btn warning-btn" :disabled="!taskRunning || metrics?.state === 'stopping'" @click="$emit('pauseTest')">
          暂停
        </WarningButton>
        <a-button class="action-btn ghost-btn" :disabled="taskRunning" @click="$emit('resumeTest')">
          恢复
        </a-button>
      </div>
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
  return STATE_NAMES[state || "missing"] || "未知";
};

const getStatusColor = (state?: SystemState): string => {
  return STATE_COLORS[state || "missing"] || "default";
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
  width: 100%;
  min-height: 88px;
  padding: 14px 10%;
  box-sizing: border-box;
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
  background: rgba(255, 255, 255, 0.84);
  backdrop-filter: blur(18px);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  flex: 1;
  margin-left: 24px;
}

.header-main {
  flex: 1;
  min-width: 0;
}

.header-eyebrow {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #64748b;
}

.header-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 6px;
}

.header-title {
  margin: 0;
  font-size: 28px;
  line-height: 1.1;
  font-weight: 800;
  color: #0f172a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-group {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.ws-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.05);
  color: #334155;
  font-size: 12px;
  font-weight: 700;
}

.ws-pill[data-connected="yes"] {
  background: rgba(16, 185, 129, 0.12);
  color: #047857;
}

.ws-pill[data-connected="no"] {
  background: rgba(245, 158, 11, 0.14);
  color: #b45309;
}

.ws-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: currentColor;
  box-shadow: 0 0 0 4px rgba(255, 255, 255, 0.42);
}

.meta-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 12px;
}

.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 36px;
  padding: 0 12px;
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(248, 250, 252, 0.92);
}

.meta-label {
  color: #64748b;
  font-size: 12px;
  font-weight: 600;
}

.meta-value {
  color: #0f172a;
  font-size: 13px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 8px;
}

.action-btn {
  min-width: 88px;
  height: 40px;
  border-radius: 12px;
  font-weight: 700;
}

.ghost-btn {
  background: rgba(255, 255, 255, 0.88);
  border-color: rgba(148, 163, 184, 0.24);
}

@media (max-width: 1200px) {
  .container-header {
    padding: 14px 5%;
  }

  .header-title {
    font-size: 24px;
  }
}

@media (max-width: 768px) {
  .container-header {
    min-height: auto;
    padding: 16px;
  }

  .header-content {
    margin-left: 0;
    flex-direction: column;
    align-items: stretch;
  }

  .header-title-row {
    flex-direction: column;
    align-items: flex-start;
  }

  .header-title {
    white-space: normal;
  }

  .header-actions {
    justify-content: stretch;
  }

  .action-btn {
    flex: 1 1 calc(50% - 6px);
  }
}
</style>
