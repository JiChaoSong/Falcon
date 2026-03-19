<script setup lang="ts">
import type { PropType } from "vue";

import EChartPanel from "@/components/EChartPanel.vue";
import type { MonitorChartConfig } from "@/layout/composables/useTaskMonitorViewModel";
import type { Stats } from "@/layout/type.ts";

defineProps({
  chartConfigs: {
    type: Array as PropType<MonitorChartConfig[]>,
    required: true,
  },
  reportSummary: {
    type: Object as PropType<{
      totalRequests: number;
      totalFailures: number;
      currentRps: number;
      failRatio: number;
      runId: number | null;
      startedAt: string | null;
      finishedAt: string | null;
      runtime: string;
      latestError: string | null;
    }>,
    required: true,
  },
  endpointSummary: {
    type: Object as PropType<{
      slowestEndpoint: string;
      riskiestEndpoint: string;
      busiestEndpoint: string;
      taskState: string;
      runCount: number;
    }>,
    required: true,
  },
  errorSummary: {
    type: Array as PropType<Stats[]>,
    required: true,
  },
  tableColumns: {
    type: Array as PropType<Record<string, unknown>[]>,
    required: true,
  },
  dataSource: {
    type: Array as PropType<Stats[]>,
    required: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
});
</script>

<template>
  <div class="app-container">
    <section class="chart-grid">
      <EChartPanel
        v-for="chart in chartConfigs"
        :key="chart.key"
        :title="chart.title"
        :subtitle="chart.subtitle"
        :labels="chart.labels"
        :legend="chart.legend"
        :series="[
          {
            name: chart.legend[0],
            data: chart.values,
            color: chart.stroke,
            areaColor: chart.fill
          },
          ...(chart.compareValues
            ? [{
                name: chart.legend[1],
                data: chart.compareValues,
                color: chart.compareStroke || '#dc2626',
                dashed: true,
                yAxisIndex: chart.key === 'failures' ? 1 : 0
              }]
            : [])
        ]"
      />
    </section>

    <section class="report-grid">
      <div class="report-card">
        <div class="section-title">本次运行摘要</div>
        <div class="report-list">
          <div class="report-item">
            <span class="report-label">总请求数</span>
            <span class="report-value">{{ reportSummary.totalRequests }}</span>
          </div>
          <div class="report-item">
            <span class="report-label">总失败数</span>
            <span class="report-value danger">{{ reportSummary.totalFailures }}</span>
          </div>
          <div class="report-item">
            <span class="report-label">当前吞吐</span>
            <span class="report-value">{{ reportSummary.currentRps }}</span>
          </div>
          <div class="report-item">
            <span class="report-label">运行时长</span>
            <span class="report-value">{{ reportSummary.runtime || "--" }}</span>
          </div>
          <div class="report-item">
            <span class="report-label">运行实例</span>
            <span class="report-value">{{ reportSummary.runId ? `#${reportSummary.runId}` : "-" }}</span>
          </div>
          <div class="report-item">
            <span class="report-label">最近错误</span>
            <span class="report-value danger">{{ reportSummary.latestError || "-" }}</span>
          </div>
        </div>
      </div>

      <div class="report-card">
        <div class="section-title">接口表现摘要</div>
        <div class="report-list">
          <div class="report-item">
            <span class="report-label">最慢接口</span>
            <span class="report-value">{{ endpointSummary.slowestEndpoint }}</span>
          </div>
          <div class="report-item">
            <span class="report-label">最高风险接口</span>
            <span class="report-value danger">{{ endpointSummary.riskiestEndpoint }}</span>
          </div>
          <div class="report-item">
            <span class="report-label">最高吞吐接口</span>
            <span class="report-value">{{ endpointSummary.busiestEndpoint }}</span>
          </div>
          <div class="report-item">
            <span class="report-label">运行状态</span>
            <span class="report-value">{{ endpointSummary.taskState }}</span>
          </div>
          <div class="report-item">
            <span class="report-label">历史运行次数</span>
            <span class="report-value">{{ endpointSummary.runCount }}</span>
          </div>
        </div>
      </div>

      <div class="report-card">
        <div class="section-title">失败接口摘要</div>
        <div v-if="errorSummary.length" class="error-list">
          <div v-for="item in errorSummary" :key="item.name" class="error-row">
            <div class="error-main">
              <span class="error-method">{{ item.method }}</span>
              <span class="error-name">{{ item.name }}</span>
            </div>
            <div class="error-meta">
              <span>{{ item.num_failures }} 次失败</span>
              <span>{{ item.current_fail_per_sec }}/s</span>
            </div>
          </div>
        </div>
        <div v-else class="empty-text">当前没有明显的高频失败接口。</div>
      </div>
    </section>

    <section class="table-panel">
      <div class="table-head">
        <div>
          <div class="section-title">接口请求统计</div>
          <div class="section-subtitle">按接口维度展示请求量、失败数、响应时间和实时吞吐，方便继续定位问题。</div>
        </div>
      </div>

      <a-table :dataSource="dataSource" :columns="tableColumns" bordered :pagination="false" :loading="loading" row-key="name" />
    </section>
  </div>
</template>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.chart-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.report-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1.2fr;
  gap: 16px;
}

.report-card,
.table-panel {
  padding: 18px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 22px;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
}

.section-title {
  font-size: 16px;
  font-weight: 800;
  color: #0f172a;
}

.section-subtitle,
.report-label,
.empty-text {
  color: #64748b;
}

.section-subtitle {
  margin-top: 4px;
  font-size: 13px;
}

.report-list,
.error-list {
  margin-top: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.report-item,
.error-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  background: #f8fafc;
  border-radius: 14px;
}

.report-value {
  font-weight: 700;
  color: #0f172a;
}

.report-value.danger,
.error-meta {
  color: #b91c1c;
}

.error-main {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.error-method {
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: 999px;
  background: #dbeafe;
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 700;
}

.error-name {
  color: #0f172a;
  font-weight: 700;
}

.error-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  font-size: 12px;
}

.table-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

@media (max-width: 1200px) {
  .report-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .chart-grid {
    grid-template-columns: 1fr;
  }
}
</style>
