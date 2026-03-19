<template>
  <div class="status-display">
    <div class="status-head">
      <div>
        <div class="status-eyebrow">实时快照</div>
        <h2 class="status-title">运行总览</h2>
      </div>
      <div class="status-caption">首屏只保留一套核心指标，用来快速判断当前压测是否稳定、是否出现失败抬升或尾延迟恶化。</div>
    </div>

    <div class="status-grid">
      <div v-for="item in cards" :key="item.label" class="status-item" :data-tone="item.tone">
        <div class="status-label">{{ item.label }}</div>
        <div class="status-value">{{ item.value }}</div>
        <div class="status-foot">{{ item.foot }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { MonitorStatCard } from "@/layout/composables/useTaskMonitorViewModel";

defineProps<{
  cards: MonitorStatCard[];
}>();
</script>

<style scoped>
.status-display {
  padding: 24px;
  border-radius: 24px;
  background:
    radial-gradient(circle at top right, rgba(219, 234, 254, 0.42), transparent 28%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.97) 0%, rgba(248, 250, 252, 0.95) 100%);
  border: 1px solid rgba(148, 163, 184, 0.16);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
}

.status-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.status-eyebrow {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #64748b;
}

.status-title {
  margin: 6px 0 0;
  font-size: 22px;
  line-height: 1.15;
  font-weight: 800;
  color: #0f172a;
}

.status-caption {
  max-width: 460px;
  font-size: 13px;
  line-height: 1.5;
  color: #64748b;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.status-item {
  padding: 18px;
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.98) 0%, rgba(255, 255, 255, 0.98) 100%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.92);
}

.status-item[data-tone="primary"] {
  border-color: rgba(59, 130, 246, 0.16);
  background: linear-gradient(180deg, #eff6ff 0%, #ffffff 100%);
}

.status-item[data-tone="success"] {
  border-color: rgba(16, 185, 129, 0.16);
  background: linear-gradient(180deg, #ecfdf5 0%, #ffffff 100%);
}

.status-item[data-tone="warning"] {
  border-color: rgba(245, 158, 11, 0.16);
  background: linear-gradient(180deg, #fff7ed 0%, #ffffff 100%);
}

.status-item[data-tone="danger"] {
  border-color: rgba(239, 68, 68, 0.16);
  background: linear-gradient(180deg, #fef2f2 0%, #ffffff 100%);
}

.status-label,
.status-foot {
  color: #64748b;
}

.status-label {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.status-value {
  margin-top: 10px;
  font-size: 28px;
  line-height: 1.1;
  font-weight: 800;
  color: #0f172a;
}

.status-foot {
  margin-top: 8px;
  font-size: 12px;
}
</style>
