<template>
  <section class="compare-panel">
    <div class="panel-head">
      <div>
        <div class="panel-eyebrow">历史对比</div>
        <h2 class="panel-title">运行差异分析</h2>
      </div>
      <div class="panel-note">{{ compareReports.length === 2 ? '已选择 2 次运行' : '请选择 2 次运行进行对比' }}</div>
    </div>

    <template v-if="compareReports.length === 2 && compareCards.length">
      <div class="compare-grid">
        <article v-for="item in compareCards" :key="item.key" class="compare-card">
          <span class="compare-label">{{ item.label }}</span>
          <div class="compare-values">
            <div class="compare-side">
              <span class="side-title">运行 {{ firstReport?.task_run_id }}</span>
              <strong>{{ item.current }}</strong>
            </div>
            <div class="compare-side">
              <span class="side-title">运行 {{ secondReport?.task_run_id }}</span>
              <strong>{{ item.previous }}</strong>
            </div>
          </div>
          <span class="compare-diff" :class="item.trend">{{ item.diff }}</span>
        </article>
      </div>

      <div class="endpoint-grid">
        <article class="endpoint-card">
          <div class="endpoint-head">
            <h3>热点接口对比</h3>
            <span class="endpoint-tip">关注吞吐最高的接口</span>
          </div>
          <div class="endpoint-body">
            <div class="endpoint-side">
              <span class="endpoint-run">运行 {{ firstReport?.task_run_id }}</span>
              <strong>{{ firstReport?.hottest_endpoint?.name || '无' }}</strong>
              <span>{{ formatEndpointSummary(firstReport?.hottest_endpoint) }}</span>
            </div>
            <div class="endpoint-side">
              <span class="endpoint-run">运行 {{ secondReport?.task_run_id }}</span>
              <strong>{{ secondReport?.hottest_endpoint?.name || '无' }}</strong>
              <span>{{ formatEndpointSummary(secondReport?.hottest_endpoint) }}</span>
            </div>
          </div>
        </article>

        <article class="endpoint-card endpoint-card-danger">
          <div class="endpoint-head">
            <h3>风险接口对比</h3>
            <span class="endpoint-tip">关注失败与延迟最高的接口</span>
          </div>
          <div class="endpoint-body">
            <div class="endpoint-side">
              <span class="endpoint-run">运行 {{ firstReport?.task_run_id }}</span>
              <strong>{{ firstReport?.riskiest_endpoint?.name || '无' }}</strong>
              <span>{{ formatEndpointSummary(firstReport?.riskiest_endpoint) }}</span>
            </div>
            <div class="endpoint-side">
              <span class="endpoint-run">运行 {{ secondReport?.task_run_id }}</span>
              <strong>{{ secondReport?.riskiest_endpoint?.name || '无' }}</strong>
              <span>{{ formatEndpointSummary(secondReport?.riskiest_endpoint) }}</span>
            </div>
          </div>
        </article>
      </div>
    </template>

    <div v-else class="empty-state">
      先在执行历史中勾选两次运行。这里会展示核心指标、热点接口和风险接口的差异，帮助你快速判断是否出现性能回归。
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { formatNumber, formatPercent } from '@/utils/tools'
import type { TaskReportData, TaskReportEndpoint } from '@/types/task'

const props = defineProps<{
  compareReports: TaskReportData[]
}>()

const firstReport = computed(() => props.compareReports[0] || null)
const secondReport = computed(() => props.compareReports[1] || null)

const buildDelta = (current: number, previous: number, formatter: (value: number) => string, inverse = false) => {
  const delta = current - previous
  const trend = delta === 0 ? 'flat' : (delta > 0 ? 'up' : 'down')
  const normalizedTrend = inverse ? (trend === 'up' ? 'down' : trend === 'down' ? 'up' : 'flat') : trend
  const prefix = delta > 0 ? '+' : ''
  return {
    diff: `${prefix}${formatter(delta)}`,
    trend: normalizedTrend,
  }
}

const compareCards = computed(() => {
  if (!firstReport.value || !secondReport.value) {
    return []
  }

  return [
    {
      key: 'requests',
      label: '总请求数',
      current: String(firstReport.value.total_requests),
      previous: String(secondReport.value.total_requests),
      ...buildDelta(firstReport.value.total_requests, secondReport.value.total_requests, value => String(Math.round(value))),
    },
    {
      key: 'success',
      label: '成功率',
      current: formatPercent(firstReport.value.success_ratio),
      previous: formatPercent(secondReport.value.success_ratio),
      ...buildDelta(firstReport.value.success_ratio, secondReport.value.success_ratio, value => formatPercent(value)),
    },
    {
      key: 'avg',
      label: '平均响应时间',
      current: `${formatNumber(firstReport.value.avg_rt)} ms`,
      previous: `${formatNumber(secondReport.value.avg_rt)} ms`,
      ...buildDelta(firstReport.value.avg_rt, secondReport.value.avg_rt, value => `${formatNumber(value)} ms`, true),
    },
    {
      key: 'p95',
      label: 'P95',
      current: `${formatNumber(firstReport.value.p95)} ms`,
      previous: `${formatNumber(secondReport.value.p95)} ms`,
      ...buildDelta(firstReport.value.p95, secondReport.value.p95, value => `${formatNumber(value)} ms`, true),
    },
  ]
})

const formatEndpointSummary = (endpoint?: TaskReportEndpoint | null) => {
  if (!endpoint) {
    return '暂无接口摘要'
  }
  return `${endpoint.method} / 请求 ${endpoint.total_requests} / 失败 ${endpoint.total_failures} / P95 ${formatNumber(endpoint.p95)} ms`
}
</script>

<style scoped>
.compare-panel {
  padding: 22px;
  border-radius: 28px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 16px 32px rgba(15, 23, 42, 0.06);
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.panel-eyebrow {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #64748b;
}

.panel-title {
  margin: 8px 0 0;
  font-size: 22px;
  color: #0f172a;
}

.panel-note {
  color: #64748b;
  font-size: 13px;
}

.compare-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.compare-card,
.endpoint-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 152px;
  padding: 18px;
  border-radius: 22px;
  border: 1px solid rgba(148, 163, 184, 0.12);
  background:
    radial-gradient(circle at top right, rgba(239, 246, 255, 0.78), transparent 32%),
    #ffffff;
}

.compare-label {
  color: #64748b;
  font-size: 13px;
}

.compare-values,
.endpoint-body {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.compare-side,
.endpoint-side {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 14px;
  border-radius: 18px;
  background: rgba(248, 250, 252, 0.96);
}

.side-title,
.endpoint-run,
.endpoint-tip {
  color: #64748b;
  font-size: 12px;
}

.compare-side strong,
.endpoint-side strong {
  color: #0f172a;
  font-size: 20px;
}

.compare-diff {
  font-size: 13px;
  font-weight: 700;
}

.compare-diff.up {
  color: #0f766e;
}

.compare-diff.down {
  color: #dc2626;
}

.compare-diff.flat {
  color: #64748b;
}

.endpoint-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.endpoint-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.endpoint-head h3 {
  margin: 0;
  color: #0f172a;
  font-size: 16px;
}

.endpoint-side span {
  color: #64748b;
  font-size: 12px;
  line-height: 1.6;
}

.endpoint-card-danger {
  border-color: rgba(248, 113, 113, 0.18);
  background:
    radial-gradient(circle at top right, rgba(254, 226, 226, 0.82), transparent 34%),
    #ffffff;
}

.empty-state {
  padding: 18px;
  border-radius: 18px;
  background: rgba(248, 250, 252, 0.92);
  color: #64748b;
  font-size: 13px;
}
</style>
