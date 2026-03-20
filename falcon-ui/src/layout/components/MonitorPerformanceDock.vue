<template>
  <div class="performance-dock">
    <div class="dock-title">实时性能指标</div>

    <div class="dock-grid">
      <div class="dock-item">
        <span class="dock-label">连接状态</span>
        <span class="dock-value">{{ wsConnected ? "实时连接中" : "轮询兜底中" }}</span>
      </div>
      <div class="dock-item">
        <span class="dock-label">Worker 节点</span>
        <span class="dock-value">{{ workerSnapshot?.worker_id || "-" }}</span>
      </div>
      <div class="dock-item">
        <span class="dock-label">Worker CPU</span>
        <span class="dock-value" :class="{ muted: workerSnapshot?.resources.cpu_percent == null }">
          {{ formatPercentValue(workerSnapshot?.resources.cpu_percent) }}
        </span>
      </div>
      <div class="dock-item">
        <span class="dock-label">Worker 内存</span>
        <span class="dock-value" :class="{ muted: workerSnapshot?.resources.memory_percent == null }">
          {{ formatMemoryUsage(workerSnapshot) }}
        </span>
      </div>
      <div class="dock-item">
        <span class="dock-label">进程 CPU</span>
        <span class="dock-value" :class="{ muted: workerSnapshot?.process.cpu_percent == null }">
          {{ formatPercentValue(workerSnapshot?.process.cpu_percent) }}
        </span>
      </div>
      <div class="dock-item">
        <span class="dock-label">进程内存</span>
        <span class="dock-value" :class="{ muted: workerSnapshot?.process.memory_mb == null }">
          {{ formatMegabytes(workerSnapshot?.process.memory_mb) }}
        </span>
      </div>
      <div class="dock-item">
        <span class="dock-label">网络上行</span>
        <span class="dock-value" :class="{ muted: workerSnapshot?.resources.net_sent_kbps == null }">
          {{ formatRate(workerSnapshot?.resources.net_sent_kbps) }}
        </span>
      </div>
      <div class="dock-item">
        <span class="dock-label">网络下行</span>
        <span class="dock-value" :class="{ muted: workerSnapshot?.resources.net_recv_kbps == null }">
          {{ formatRate(workerSnapshot?.resources.net_recv_kbps) }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { WorkerSnapshot } from "@/types/task";
import type { Metrics } from "@/layout/type.ts";
import type { TaskInfo } from "@/types/task";

defineProps<{
  taskInfo: TaskInfo | null;
  metrics: Metrics | null;
  workerSnapshot: WorkerSnapshot | null;
  wsConnected: boolean;
}>();

const formatPercentValue = (value?: number | null) => {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return "待接入";
  }
  return `${value.toFixed(2)}%`;
};

const formatMegabytes = (value?: number | null) => {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return "待接入";
  }
  return `${value.toFixed(0)} MB`;
};

const formatRate = (value?: number | null) => {
  if (value === undefined || value === null || Number.isNaN(value)) {
    return "待接入";
  }
  return `${value.toFixed(2)} KB/s`;
};

const formatMemoryUsage = (snapshot?: WorkerSnapshot | null) => {
  const percent = snapshot?.resources.memory_percent;
  const used = snapshot?.resources.memory_used_mb;
  if (percent === undefined || percent === null || used === undefined || used === null) {
    return "待接入";
  }
  return `${percent.toFixed(2)}% / ${used.toFixed(0)} MB`;
};
</script>

<style scoped>
.performance-dock {
  position: fixed;
  left: 28px;
  right: 28px;
  bottom: 16px;
  z-index: 900;
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 12px 18px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 20px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.95) 100%);
  box-shadow: 0 18px 36px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(12px);
}

.dock-title {
  min-width: 108px;
  color: #0f172a;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.01em;
}

.dock-grid {
  display: grid;
  grid-template-columns: repeat(8, minmax(0, 1fr));
  gap: 12px;
  flex: 1;
}

.dock-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  padding: 8px 10px;
  border-radius: 14px;
  background: rgba(248, 250, 252, 0.82);
  border: 1px solid rgba(148, 163, 184, 0.1);
}

.dock-label {
  color: #64748b;
  font-size: 11px;
}

.dock-value {
  color: #0f172a;
  font-size: 13px;
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dock-value.muted {
  color: #b45309;
}
</style>
