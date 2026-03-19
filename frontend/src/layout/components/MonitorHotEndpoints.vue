<template>
  <div class="endpoint-card">
    <div class="endpoint-head">
      <div class="endpoint-eyebrow">热点接口</div>
      <div class="endpoint-title">热点接口</div>
      <div class="endpoint-subtitle">按失败压力和延迟权重排序，优先显示最值得排查的路径。</div>
    </div>

    <div v-if="endpoints.length" class="endpoint-list">
      <div v-for="(item, index) in endpoints" :key="item.name" class="endpoint-row">
        <div class="endpoint-rank">0{{ index + 1 }}</div>
        <div class="endpoint-main">
          <div class="endpoint-name">
            <span class="endpoint-method">{{ item.method }}</span>
            <span class="endpoint-path">{{ item.name }}</span>
          </div>
          <div class="endpoint-hint">
            RPS {{ formatNumber(item.current_rps) }} | P95 {{ formatNumber(item.p95) }} ms | Avg {{ formatNumber(item.avg_response_time) }} ms
          </div>
        </div>
        <div class="endpoint-risk">
          <span class="risk-value">{{ formatNumber(item.current_fail_per_sec) }}/s</span>
          <span class="risk-label">失败速率</span>
        </div>
      </div>
    </div>

    <div v-else class="endpoint-empty">
      压测开始并产生接口级明细后，这里会展示当前最热的高风险接口。
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatNumber } from "@/utils/tools";
import type { HotEndpointItem } from "@/layout/composables/useTaskMonitorViewModel";

defineProps<{
  endpoints: HotEndpointItem[];
}>();
</script>

<style scoped>
.endpoint-card {
  padding: 24px;
  border-radius: 22px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.94) 100%);
  box-shadow: 0 18px 36px rgba(15, 23, 42, 0.08);
}

.endpoint-head {
  margin-bottom: 18px;
}

.endpoint-eyebrow {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #64748b;
}

.endpoint-title {
  margin-top: 6px;
  font-size: 20px;
  line-height: 1.15;
  font-weight: 800;
  color: #0f172a;
}

.endpoint-subtitle {
  margin-top: 6px;
  font-size: 13px;
  color: #64748b;
}

.endpoint-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.endpoint-row {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 14px;
  align-items: center;
  padding: 14px 16px;
  border-radius: 18px;
  border: 1px solid rgba(226, 232, 240, 0.9);
  background: rgba(248, 250, 252, 0.9);
}

.endpoint-rank {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 14px;
  background: linear-gradient(180deg, #eff6ff 0%, #dbeafe 100%);
  color: #1d4ed8;
  font-size: 13px;
  font-weight: 800;
}

.endpoint-main {
  min-width: 0;
}

.endpoint-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.endpoint-method {
  padding: 3px 8px;
  border-radius: 999px;
  background: #2563eb;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
}

.endpoint-path {
  word-break: break-word;
  color: #0f172a;
  font-size: 14px;
  font-weight: 700;
}

.endpoint-hint,
.risk-label,
.endpoint-empty {
  color: #64748b;
}

.endpoint-hint {
  margin-top: 6px;
  font-size: 12px;
}

.endpoint-risk {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.risk-value {
  font-size: 18px;
  font-weight: 800;
  color: #dc2626;
}

.risk-label {
  margin-top: 3px;
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.endpoint-empty {
  padding: 18px;
  border-radius: 16px;
  background: rgba(248, 250, 252, 0.82);
  font-size: 13px;
  line-height: 1.6;
}

@media (max-width: 768px) {
  .endpoint-row {
    grid-template-columns: 1fr;
  }

  .endpoint-risk {
    align-items: flex-start;
  }
}
</style>
