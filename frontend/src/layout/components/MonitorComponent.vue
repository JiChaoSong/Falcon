<script setup lang="ts">
import { computed, defineAsyncComponent, ref, onMounted, onUnmounted } from 'vue';
import { formatNumber, formatNumberWithCommas, formatPercent } from '@/utils/tools';
import { MetricHistoryPoint, Metrics, Stats } from "@/layout/type.ts";

const EChartPanel = defineAsyncComponent(() => import('@/components/EChartPanel.vue'));

const props = defineProps<{
  dataSource: Stats[] | undefined;
  metrics: Metrics | undefined;
  history?: MetricHistoryPoint[] | undefined;
  loading?: boolean;
}>();

const safeMetrics = computed(() => props.metrics);
const safeDataSource = computed(() => props.dataSource ?? []);
const safeHistory = computed(() => props.history ?? []);

// 图表虚拟化相关状态
const visibleCharts = ref<Set<string>>(new Set());
const chartObserver = ref<IntersectionObserver | null>(null);

const customRender = {
  twoDecimal: (text: number) => formatNumber(text),
  integer: (text: number) => {
    if (text === undefined || text === null || isNaN(text)) {
      return '0';
    }
    return Math.round(text).toString();
  },
  withCommas: (text: number) => formatNumberWithCommas(text),
};

// 图表虚拟化相关方法
const setupChartObserver = () => {
  if (typeof window === 'undefined' || !window.IntersectionObserver) {
    // 降级：所有图表都设为可见
    chartConfigs.value.forEach(chart => visibleCharts.value.add(chart.key));
    return;
  }

  chartObserver.value = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        const chartKey = entry.target.getAttribute('data-chart-key');
        if (!chartKey) return;

        if (entry.isIntersecting) {
          visibleCharts.value.add(chartKey);
        } else {
          // 延迟移除，避免快速滚动时的闪烁
          setTimeout(() => {
            if (!entry.isIntersecting) {
              visibleCharts.value.delete(chartKey);
            }
          }, 100);
        }
      });
    },
    {
      root: null,
      rootMargin: '50px', // 提前50px开始加载
      threshold: 0.1, // 10%可见时触发
    }
  );
};

const observeChart = (element: Element, chartKey: string) => {
  if (element && chartObserver.value) {
    element.setAttribute('data-chart-key', chartKey);
    chartObserver.value.observe(element);
  }
};

const unobserveChart = (element: Element) => {
  if (element && chartObserver.value) {
    chartObserver.value.unobserve(element);
  }
};

// 生命周期钩子
onMounted(() => {
  setupChartObserver();
});

onUnmounted(() => {
  if (chartObserver.value) {
    chartObserver.value.disconnect();
    chartObserver.value = null;
  }
  visibleCharts.value.clear();
});

const summaryCards = computed(() => {
  const metrics = safeMetrics.value;
  const stats = safeDataSource.value;
  const aggregateAvgRt = stats.length
      ? stats.reduce((sum, item) => sum + item.avg_response_time, 0) / stats.length
      : 0;
  const aggregateP95 = stats.length
      ? Math.max(...stats.map((item) => item["response_time_percentile_0.95"] ?? 0))
      : 0;
  const aggregateP99 = stats.length
      ? Math.max(...stats.map((item) => item["response_time_percentile_0.99"] ?? 0))
      : 0;
  const totalRequests = stats.reduce((sum, item) => sum + item.num_requests, 0);
  const totalFailures = stats.reduce((sum, item) => sum + item.num_failures, 0);

  return [
    { title: '并发用户', value: String(metrics?.user_count ?? 0), unit: 'VUs', tone: 'primary' },
    { title: '当前吞吐', value: formatNumber(metrics?.total_rps), unit: 'RPS', tone: 'success' },
    { title: '平均响应时间', value: formatNumber(aggregateAvgRt), unit: 'ms', tone: 'default' },
    { title: 'P95 响应时间', value: formatNumber(aggregateP95), unit: 'ms', tone: 'warning' },
    { title: 'P99 响应时间', value: formatNumber(aggregateP99), unit: 'ms', tone: 'warning' },
    { title: '失败率', value: formatPercent(metrics?.fail_ratio), unit: 'Fail Ratio', tone: 'danger' },
    { title: '累计请求数', value: formatNumberWithCommas(totalRequests), unit: 'requests', tone: 'default' },
    { title: '累计失败数', value: formatNumberWithCommas(totalFailures), unit: 'fails', tone: 'danger' },
  ];
});

const chartConfigs = computed(() => {
  const history = safeHistory.value;
  return [
    {
      key: 'rps',
      title: 'Requests per Second',
      subtitle: '实时吞吐曲线',
      stroke: '#2563eb',
      fill: 'rgba(37, 99, 235, 0.12)',
      unit: 'RPS',
      legend: ['RPS'],
      values: history.map((item) => item.total_rps),
      labels: history.map((item) => item.time),
    },
    {
      key: 'users',
      title: 'Users',
      subtitle: '并发用户变化',
      stroke: '#0f766e',
      fill: 'rgba(15, 118, 110, 0.12)',
      unit: 'users',
      legend: ['Users'],
      values: history.map((item) => item.user_count),
      labels: history.map((item) => item.time),
    },
    {
      key: 'response-time',
      title: 'Response Time',
      subtitle: '平均响应与尾延迟',
      stroke: '#f59e0b',
      fill: 'rgba(245, 158, 11, 0.14)',
      unit: 'ms',
      legend: ['Average RT', 'P95 RT'],
      values: history.map((item) => item.avg_response_time),
      compareValues: history.map((item) => item.p95_response_time),
      compareStroke: '#dc2626',
      labels: history.map((item) => item.time),
    },
    {
      key: 'failures',
      title: 'Failures',
      subtitle: '失败率与失败速率',
      stroke: '#b91c1c',
      fill: 'rgba(185, 28, 28, 0.12)',
      unit: '%',
      legend: ['Fail Ratio', 'Failures/s'],
      values: history.map((item) => Number((item.fail_ratio * 100).toFixed(2))),
      compareValues: history.map((item) => item.total_fail_per_sec),
      compareStroke: '#7c3aed',
      labels: history.map((item) => item.time),
    }
  ];
});

const reportSummary = computed(() => {
  const stats = safeDataSource.value;
  const metrics = safeMetrics.value;
  const totalRequests = stats.reduce((sum, item) => sum + item.num_requests, 0);
  const totalFailures = stats.reduce((sum, item) => sum + item.num_failures, 0);
  const slowestEndpoint = [...stats].sort((a, b) => b.avg_response_time - a.avg_response_time)[0];
  const mostFailedEndpoint = [...stats].sort((a, b) => b.num_failures - a.num_failures)[0];
  const highestRpsEndpoint = [...stats].sort((a, b) => b.current_rps - a.current_rps)[0];

  return {
    totalRequests,
    totalFailures,
    currentRps: metrics?.total_rps ?? 0,
    failRatio: metrics?.fail_ratio ?? 0,
    slowestEndpoint,
    mostFailedEndpoint,
    highestRpsEndpoint,
  };
});

const errorSummary = computed(() => {
  return safeDataSource.value
      .filter((item) => item.num_failures > 0)
      .sort((a, b) => b.num_failures - a.num_failures)
      .slice(0, 5);
});

const tableColumns = [
  { title: 'Type', dataIndex: 'method', key: 'method' },
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: '# Requests', dataIndex: 'num_requests', key: 'num_requests', customRender: ({ text }: { text: number }) => customRender.withCommas(text) },
  { title: '# Fails', dataIndex: 'num_failures', key: 'num_failures', customRender: ({ text }: { text: number }) => customRender.withCommas(text) },
  { title: 'Median(ms)', dataIndex: 'median_response_time', key: 'median_response_time', customRender: ({ text }: { text: number }) => customRender.twoDecimal(text) },
  { title: '95%ile(ms)', dataIndex: 'response_time_percentile_0.95', key: 'response_time_percentile_0.95', customRender: ({ text }: { text: number }) => customRender.twoDecimal(text) },
  { title: '99%ile(ms)', dataIndex: 'response_time_percentile_0.99', key: 'response_time_percentile_0.99', customRender: ({ text }: { text: number }) => customRender.twoDecimal(text) },
  { title: 'Average(ms)', dataIndex: 'avg_response_time', key: 'avg_response_time', customRender: ({ text }: { text: number }) => customRender.twoDecimal(text) },
  { title: 'Min(ms)', dataIndex: 'min_response_time', key: 'min_response_time', customRender: ({ text }: { text: number }) => customRender.twoDecimal(text) },
  { title: 'Max(ms)', dataIndex: 'max_response_time', key: 'max_response_time', customRender: ({ text }: { text: number }) => customRender.twoDecimal(text) },
  { title: 'Average(bytes)', dataIndex: 'avg_content_length', key: 'avg_content_length', customRender: ({ text }: { text: number }) => customRender.integer(text) },
  { title: 'Current(RPS)', dataIndex: 'current_rps', key: 'current_rps', customRender: ({ text }: { text: number }) => customRender.twoDecimal(text) },
  { title: 'Current Failures/s', dataIndex: 'current_fail_per_sec', key: 'current_fail_per_sec', customRender: ({ text }: { text: number }) => customRender.twoDecimal(text) },
];
</script>

<template>
  <div class="app-container">
    <section class="summary-grid">
      <div class="summary-card" v-for="item in summaryCards" :key="item.title" :data-tone="item.tone">
        <div class="summary-title">{{ item.title }}</div>
        <div class="summary-value">{{ item.value }}</div>
        <div class="summary-unit">{{ item.unit }}</div>
      </div>
    </section>

    <section class="chart-grid">
      <div
        v-for="chart in chartConfigs"
        :key="chart.key"
        ref="observeChart($el, chart.key)"
        class="chart-container"
      >
        <EChartPanel
          v-if="visibleCharts.has(chart.key)"
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
                  color: chart.compareStroke,
                  dashed: true,
                  yAxisIndex: chart.key === 'failures' ? 1 : 0
                }]
              : [])
          ]"
        />
        <!-- 占位符，保持布局 -->
        <div v-else class="chart-placeholder" :style="{ height: '400px' }">
          <div class="placeholder-content">
            <div class="placeholder-title">{{ chart.title }}</div>
            <div class="placeholder-subtitle">{{ chart.subtitle }}</div>
          </div>
        </div>
      </div>
    </section>

    <section class="report-grid">
      <div class="report-card">
        <div class="section-title">运行摘要</div>
        <div class="report-list">
          <div class="report-item">
            <span class="report-label">累计请求数</span>
            <span class="report-value">{{ formatNumberWithCommas(reportSummary.totalRequests) }}</span>
          </div>
          <div class="report-item">
            <span class="report-label">累计失败数</span>
            <span class="report-value danger">{{ formatNumberWithCommas(reportSummary.totalFailures) }}</span>
          </div>
          <div class="report-item">
            <span class="report-label">当前总 RPS</span>
            <span class="report-value">{{ formatNumber(reportSummary.currentRps) }}</span>
          </div>
          <div class="report-item">
            <span class="report-label">当前失败率</span>
            <span class="report-value danger">{{ formatPercent(reportSummary.failRatio) }}</span>
          </div>
        </div>
      </div>

      <div class="report-card">
        <div class="section-title">热点接口摘要</div>
        <div class="report-list">
          <div class="report-item">
            <span class="report-label">最慢接口</span>
            <span class="report-value">{{ reportSummary.slowestEndpoint?.name || '-' }}</span>
          </div>
          <div class="report-item">
            <span class="report-label">最高失败接口</span>
            <span class="report-value danger">{{ reportSummary.mostFailedEndpoint?.name || '-' }}</span>
          </div>
          <div class="report-item">
            <span class="report-label">最高吞吐接口</span>
            <span class="report-value">{{ reportSummary.highestRpsEndpoint?.name || '-' }}</span>
          </div>
          <div class="report-item">
            <span class="report-label">任务状态</span>
            <span class="report-value">{{ safeMetrics?.state || '-' }}</span>
          </div>
        </div>
      </div>

      <div class="report-card">
        <div class="section-title">错误摘要</div>
        <div class="error-list" v-if="errorSummary.length">
          <div class="error-row" v-for="item in errorSummary" :key="item.name">
            <div class="error-main">
              <span class="error-method">{{ item.method }}</span>
              <span class="error-name">{{ item.name }}</span>
            </div>
            <div class="error-meta">
              <span>{{ item.num_failures }} fails</span>
              <span>{{ formatNumber(item.current_fail_per_sec) }}/s</span>
            </div>
          </div>
        </div>
        <div class="empty-text" v-else>当前没有失败接口。</div>
      </div>
    </section>

    <section class="table-panel">
      <div class="table-head">
        <div>
          <div class="section-title">Statistics</div>
          <div class="section-subtitle">按 Locust 风格展示接口级请求、延迟和错误情况</div>
        </div>
      </div>

      <a-table :dataSource="safeDataSource" :columns="tableColumns" bordered :pagination="false" :loading="loading" row-key="name" />
    </section>
  </div>
</template>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.summary-card,
.report-card,
.table-panel {
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 18px;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.06);
}

.summary-card {
  padding: 18px 20px;
}

.summary-card[data-tone="primary"] {
  background: linear-gradient(180deg, #eff6ff 0%, #ffffff 100%);
}

.summary-card[data-tone="success"] {
  background: linear-gradient(180deg, #ecfdf5 0%, #ffffff 100%);
}

.summary-card[data-tone="warning"] {
  background: linear-gradient(180deg, #fff7ed 0%, #ffffff 100%);
}

.summary-card[data-tone="danger"] {
  background: linear-gradient(180deg, #fef2f2 0%, #ffffff 100%);
}

.summary-title,
.chart-subtitle,
.section-subtitle,
.summary-unit,
.report-label,
.empty-text {
  color: #64748b;
}

.summary-title {
  font-size: 13px;
  margin-bottom: 10px;
}

.summary-value {
  font-size: 28px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.2;
}

.summary-unit {
  margin-top: 6px;
  font-size: 12px;
}

.chart-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.chart-head,
.table-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.section-title {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}

.report-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1.2fr;
  gap: 16px;
}

.report-card,
.table-panel {
  padding: 18px;
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
  font-weight: 600;
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
  font-weight: 600;
}

.error-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  font-size: 12px;
}

.section-subtitle {
  margin-top: 4px;
  font-size: 13px;
}

.chart-container {
  position: relative;
}

.chart-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fafafa;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  transition: background-color 0.3s ease;
}

.chart-placeholder:hover {
  background: #f5f5f5;
}

.placeholder-content {
  text-align: center;
  color: #999;
}

.placeholder-title {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 4px;
}

.placeholder-subtitle {
  font-size: 12px;
}

@media (max-width: 1200px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
  }

  .chart-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px;
  }

  .report-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .summary-card {
    padding: 16px;
  }

  .summary-value {
    font-size: 28px;
  }
}

@media (max-width: 768px) {
  .app-container {
    padding: 16px;
  }

  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
  }

  .chart-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .summary-card {
    padding: 12px;
  }

  .summary-title {
    font-size: 12px;
  }

  .summary-value {
    font-size: 24px;
  }

  .summary-unit {
    font-size: 10px;
  }

  .chart-placeholder {
    height: 300px !important;
  }

  .placeholder-title {
    font-size: 14px;
  }

  .placeholder-subtitle {
    font-size: 11px;
  }
}

@media (max-width: 480px) {
  .app-container {
    padding: 8px;
  }

  .summary-grid {
    grid-template-columns: 1fr;
    gap: 8px;
  }

  .summary-card {
    padding: 10px;
  }

  .summary-title {
    font-size: 11px;
  }

  .summary-value {
    font-size: 20px;
  }

  .summary-unit {
    font-size: 9px;
  }

  .chart-placeholder {
    height: 250px !important;
  }

  .placeholder-content {
    padding: 16px;
  }
}
</style>
