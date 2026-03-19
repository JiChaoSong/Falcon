<template>
  <div class="endpoint-card">
    <div class="endpoint-head">
      <div class="ai-eyebrow">热点接口</div>
      <div class="endpoint-subtitle">按失败速率和延迟综合排序</div>
    </div>

    <div class="endpoint-list">
      <div class="endpoint-row" v-for="item in hotEndpoints" :key="item.name">
        <div class="endpoint-main">
          <div class="endpoint-name">
            <span class="endpoint-method">{{ item.method }}</span>
            <span>{{ item.name }}</span>
          </div>
          <div class="endpoint-hint">RPS {{ formatNumber(item.current_rps) }} / P95 {{ formatNumber(item.p95) }}ms</div>
        </div>
        <div class="endpoint-risk">
          <span class="risk-value">{{ formatNumber(item.current_fail_per_sec) }}/s</span>
          <span class="risk-label">失败速率</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { formatNumber } from '@/utils/tools';
import { Stats } from "@/layout/type.ts";

const props = defineProps<{
  dataSource: Stats[];
}>();

const hotEndpoints = computed(() => {
  return [...props.dataSource]
      .sort((a, b) => {
        const aScore = a.current_fail_per_sec * 100 + a.avg_response_time;
        const bScore = b.current_fail_per_sec * 100 + b.avg_response_time;
        return bScore - aScore;
      })
      .slice(0, 3)
      .map((item) => ({
        ...item,
        p95: item["response_time_percentile_0.95"] ?? 0
      }));
});
</script>

<style scoped>
.endpoint-card {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.endpoint-head {
  margin-bottom: 20px;
}

.ai-eyebrow {
  font-size: 12px;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}

.endpoint-subtitle {
  font-size: 13px;
  color: #6b7280;
}

.endpoint-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.endpoint-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.endpoint-main {
  flex: 1;
}

.endpoint-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 4px;
}

.endpoint-method {
  background: #3b82f6;
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
}

.endpoint-hint {
  font-size: 12px;
  color: #6b7280;
}

.endpoint-risk {
  text-align: right;
}

.risk-value {
  display: block;
  font-size: 16px;
  font-weight: 600;
  color: #dc2626;
  margin-bottom: 2px;
}

.risk-label {
  font-size: 11px;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

@media (max-width: 768px) {
  .endpoint-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .endpoint-risk {
    text-align: left;
  }
}
</style>