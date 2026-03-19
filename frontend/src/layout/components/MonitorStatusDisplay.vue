<template>
  <div class="status-display">
    <div class="status-grid">
      <div class="status-item">
        <div class="status-label">并发用户数</div>
        <div class="status-value">{{ metrics?.user_count || 0 }}</div>
      </div>
      <div class="status-item">
        <div class="status-label">总请求数</div>
        <div class="status-value">{{ metrics?.stats?.reduce((sum, stat) => sum + stat.num_requests, 0) || 0 }}</div>
      </div>
      <div class="status-item">
        <div class="status-label">成功请求数</div>
        <div class="status-value">{{ (metrics?.stats?.reduce((sum, stat) => sum + stat.num_requests, 0) || 0) - (metrics?.stats?.reduce((sum, stat) => sum + stat.num_failures, 0) || 0) }}</div>
      </div>
      <div class="status-item">
        <div class="status-label">失败请求数</div>
        <div class="status-value">{{ metrics?.stats?.reduce((sum, stat) => sum + stat.num_failures, 0) || 0 }}</div>
      </div>
      <div class="status-item">
        <div class="status-label">平均响应时间</div>
        <div class="status-value">{{ formatTime(metrics?.stats?.reduce((sum, stat) => sum + stat.avg_response_time, 0) / (metrics?.stats?.length || 1)) }}</div>
      </div>
      <div class="status-item">
        <div class="status-label">最大响应时间</div>
        <div class="status-value">{{ formatTime(Math.max(...(metrics?.stats?.map(stat => stat.max_response_time) || [0]))) }}</div>
      </div>
      <div class="status-item">
        <div class="status-label">最小响应时间</div>
        <div class="status-value">{{ formatTime(Math.min(...(metrics?.stats?.map(stat => stat.min_response_time) || [0]))) }}</div>
      </div>
      <div class="status-item">
        <div class="status-label">QPS</div>
        <div class="status-value">{{ metrics?.total_rps?.toFixed(2) || '0.00' }}</div>
      </div>
      <div class="status-item">
        <div class="status-label">TPS</div>
        <div class="status-value">{{ metrics?.total_rps?.toFixed(2) || '0.00' }}</div>
      </div>
      <div class="status-item">
        <div class="status-label">错误率</div>
        <div class="status-value">{{ formatPercentage(metrics?.fail_ratio) }}</div>
      </div>
      <div class="status-item">
        <div class="status-label">CPU使用率</div>
        <div class="status-value">--</div>
      </div>
      <div class="status-item">
        <div class="status-label">内存使用率</div>
        <div class="status-value">--</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Metrics } from "@/layout/type.ts";

const props = defineProps<{
  metrics: Metrics | null;
}>();

const formatTime = (time?: number): string => {
  if (!time) return '--';
  if (time < 1000) return `${time.toFixed(2)}ms`;
  return `${(time / 1000).toFixed(2)}s`;
};

const formatPercentage = (value?: number): string => {
  if (value === undefined || value === null) return '--';
  return `${(value * 100).toFixed(2)}%`;
};
</script>

<style scoped>
.status-display {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.status-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.status-label {
  font-size: 12px;
  color: #6c757d;
  margin-bottom: 8px;
  font-weight: 500;
  text-align: center;
}

.status-value {
  font-size: 18px;
  font-weight: 600;
  color: #495057;
}

@media (max-width: 1200px) {
  .status-grid {
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 16px;
  }

  .status-item {
    padding: 12px;
  }

  .status-value {
    font-size: 16px;
  }
}

@media (max-width: 768px) {
  .status-display {
    padding: 16px;
    margin-bottom: 16px;
  }

  .status-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }

  .status-item {
    padding: 10px;
  }

  .status-label {
    font-size: 11px;
    margin-bottom: 6px;
  }

  .status-value {
    font-size: 14px;
  }
}

@media (max-width: 480px) {
  .status-grid {
    grid-template-columns: 1fr;
  }
}
</style>