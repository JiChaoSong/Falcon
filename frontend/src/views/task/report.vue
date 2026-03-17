<script setup lang="ts">
import { computed, defineAsyncComponent, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { TaskApi } from '@/api/task'
import type { TaskReportData, TaskRunHistoryItem } from '@/types/task'
import { formatNumber, formatPercent } from '@/utils/tools'

const EChartPanel = defineAsyncComponent(() => import('@/components/EChartPanel.vue'))

const route = useRoute()
const router = useRouter()
const taskId = ref<number>(Number(route.params.taskId) || 0)
const loading = ref(false)
const taskReport = ref<TaskReportData | null>(null)
const taskRuns = ref<TaskRunHistoryItem[]>([])
const selectedTaskRunId = ref<number | null>(route.query.taskRunId ? Number(route.query.taskRunId) : null)

const safeReport = computed(() => taskReport.value)

const summaryCards = computed(() => {
  if (!safeReport.value) {
    return []
  }

  return [
    { title: '总请求数', value: String(safeReport.value.total_requests), tone: 'default' },
    { title: '成功率', value: formatPercent(safeReport.value.success_ratio), tone: 'success' },
    { title: '平均响应', value: `${formatNumber(safeReport.value.avg_rt)} ms`, tone: 'default' },
    { title: 'P95', value: `${formatNumber(safeReport.value.p95)} ms`, tone: 'warning' },
    { title: 'P99', value: `${formatNumber(safeReport.value.p99)} ms`, tone: 'warning' },
    { title: '失败数', value: String(safeReport.value.fail_count), tone: 'danger' },
  ]
})

const chartConfigs = computed(() => {
  const history = safeReport.value?.history || []
  return [
    {
      key: 'rps',
      title: '吞吐趋势',
      subtitle: '按秒聚合的 RPS 变化',
      stroke: '#2563eb',
      fill: 'rgba(37, 99, 235, 0.12)',
      legend: ['RPS'],
      values: history.map(item => item.rps),
      labels: history.map(item => new Date(item.ts).toLocaleTimeString()),
    },
    {
      key: 'rt',
      title: '响应时间趋势',
      subtitle: '平均响应时间与 P95',
      stroke: '#f59e0b',
      fill: 'rgba(245, 158, 11, 0.14)',
      legend: ['Avg RT', 'P95'],
      values: history.map(item => item.avg_rt),
      compareValues: history.map(item => item.p95),
      compareStroke: '#dc2626',
      labels: history.map(item => new Date(item.ts).toLocaleTimeString()),
    },
  ]
})

const statsColumns = [
  { title: '方法', dataIndex: 'method', key: 'method' },
  { title: '接口名称', dataIndex: 'name', key: 'name' },
  { title: '请求数', dataIndex: 'num_requests', key: 'num_requests' },
  { title: '失败数', dataIndex: 'num_failures', key: 'num_failures' },
  { title: '平均响应(ms)', dataIndex: 'avg_response_time', key: 'avg_response_time' },
  { title: 'P95(ms)', dataIndex: 'response_time_percentile_0.95', key: 'response_time_percentile_0.95' },
  { title: 'P99(ms)', dataIndex: 'response_time_percentile_0.99', key: 'response_time_percentile_0.99' },
  { title: '当前 RPS', dataIndex: 'current_rps', key: 'current_rps' },
]

const syncSelectedRun = () => {
  if (!taskRuns.value.length) {
    selectedTaskRunId.value = null
    return
  }

  // Prefer the run from the route, otherwise keep the current selection, otherwise default latest.
  const routeRunId = route.query.taskRunId ? Number(route.query.taskRunId) : null
  const preferredRunId = routeRunId || selectedTaskRunId.value
  const matchedRun = taskRuns.value.find(item => item.id === preferredRunId)
  selectedTaskRunId.value = matchedRun ? matchedRun.id : taskRuns.value[0].id
}

const fetchTaskRuns = async () => {
  const response = await TaskApi.getTaskRuns({ task_id: taskId.value })
  taskRuns.value = response.data.runs || []
  syncSelectedRun()
}

const fetchTaskReport = async () => {
  const response = await TaskApi.getTaskReport({
    task_id: taskId.value,
    task_run_id: selectedTaskRunId.value,
  })
  taskReport.value = response.data
}

const refreshPage = async () => {
  if (!taskId.value) {
    return
  }

  loading.value = true
  try {
    await fetchTaskRuns()
    await fetchTaskReport()
  } catch (error) {
    console.error('加载任务报告失败:', error)
    message.error('任务报告加载失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const handleSelectRun = async (runId: number) => {
  selectedTaskRunId.value = runId
  await router.replace({
    path: `/report/${taskId.value}`,
    query: runId ? { taskRunId: String(runId) } : undefined,
  })
  await fetchTaskReport()
}

const goBack = () => {
  router.push(`/monitor/${taskId.value}`)
}

watch(
  () => route.query.taskRunId,
  async (value) => {
    const nextRunId = value ? Number(value) : null
    if (nextRunId !== selectedTaskRunId.value) {
      selectedTaskRunId.value = nextRunId
      await refreshPage()
    }
  }
)

onMounted(async () => {
  await refreshPage()
})
</script>

<template>
  <div class="report-page">
    <div class="report-header">
      <div>
        <div class="report-eyebrow">任务报告</div>
        <h1 class="report-title">{{ safeReport?.task_name || `任务 ${taskId}` }}</h1>
        <p class="report-subtitle">
          查看指定运行实例的吞吐、稳定性和接口级统计，作为复盘与容量基线的基础依据。
        </p>
      </div>
      <div class="report-actions">
        <a-button @click="goBack">返回监控</a-button>
        <a-button type="primary" :loading="loading" @click="refreshPage">刷新报告</a-button>
      </div>
    </div>

    <div class="report-layout">
      <aside class="report-sidebar">
        <a-card title="运行历史" :loading="loading">
          <template v-if="taskRuns.length">
            <button
              v-for="item in taskRuns"
              :key="item.id"
              class="history-item"
              :class="{ active: item.id === selectedTaskRunId }"
              type="button"
              @click="handleSelectRun(item.id)"
            >
              <div class="history-main">
                <span class="history-id">#{{ item.id }}</span>
                <a-tag>{{ item.status }}</a-tag>
              </div>
              <div class="history-meta">
                <span>请求 {{ item.total_requests }}</span>
                <span>成功率 {{ formatPercent(item.success_ratio) }}</span>
                <span>时长 {{ item.runtime_seconds }}s</span>
              </div>
            </button>
          </template>
          <a-empty v-else description="暂无运行历史" />
        </a-card>
      </aside>

      <main class="report-main">
        <a-card :loading="loading">
          <div class="base-grid" v-if="safeReport">
            <div class="base-item">
              <span class="base-label">运行实例</span>
              <span class="base-value">{{ safeReport.task_run_id || '-' }}</span>
            </div>
            <div class="base-item">
              <span class="base-label">所属项目</span>
              <span class="base-value">{{ safeReport.project }}</span>
            </div>
            <div class="base-item">
              <span class="base-label">负责人</span>
              <span class="base-value">{{ safeReport.owner }}</span>
            </div>
            <div class="base-item">
              <span class="base-label">执行策略</span>
              <span class="base-value">{{ safeReport.execution_strategy }}</span>
            </div>
            <div class="base-item">
              <span class="base-label">目标主机</span>
              <span class="base-value">{{ safeReport.host }}</span>
            </div>
            <div class="base-item">
              <span class="base-label">场景数量</span>
              <span class="base-value">{{ safeReport.scenario_count }}</span>
            </div>
          </div>
        </a-card>

        <section class="summary-grid">
          <div
            v-for="card in summaryCards"
            :key="card.title"
            class="summary-card"
            :data-tone="card.tone"
          >
            <div class="summary-title">{{ card.title }}</div>
            <div class="summary-value">{{ card.value }}</div>
          </div>
        </section>

        <div class="report-highlight" v-if="safeReport">
          <a-card title="关键发现">
            <div class="highlight-grid">
              <div class="highlight-item">
                <span class="highlight-label">最高吞吐接口</span>
                <span class="highlight-value">{{ safeReport.hottest_endpoint?.name || '-' }}</span>
              </div>
              <div class="highlight-item">
                <span class="highlight-label">风险接口</span>
                <span class="highlight-value danger">{{ safeReport.riskiest_endpoint?.name || '-' }}</span>
              </div>
              <div class="highlight-item full">
                <span class="highlight-label">最近错误</span>
                <span class="highlight-value danger">{{ safeReport.latest_error || '无' }}</span>
              </div>
            </div>
          </a-card>
        </div>

        <section class="chart-grid" v-if="safeReport?.history?.length">
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
                    color: chart.compareStroke,
                    dashed: true,
                  }]
                : [])
            ]"
          />
        </section>

        <a-card title="接口明细" :loading="loading">
          <a-table
            :columns="statsColumns"
            :data-source="safeReport?.stats || []"
            :pagination="{ pageSize: 10 }"
            row-key="name"
            :scroll="{ x: 1200 }"
          />
        </a-card>
      </main>
    </div>
  </div>
</template>

<style scoped>
.report-page {
  min-height: 100vh;
  padding: 28px 5%;
  background:
    radial-gradient(circle at top left, rgba(236, 244, 255, 0.95), transparent 32%),
    linear-gradient(180deg, #f7f9fc 0%, #f2f5f9 100%);
}

.report-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.report-eyebrow {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: #6b7a90;
  text-transform: uppercase;
}

.report-title {
  margin: 6px 0 8px;
  font-size: 28px;
  line-height: 1.2;
  color: #10233f;
}

.report-subtitle {
  margin: 0;
  color: #4a5c76;
  line-height: 1.7;
}

.report-actions {
  display: flex;
  gap: 10px;
}

.report-layout {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 18px;
}

.report-main {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.history-item {
  width: 100%;
  margin-bottom: 10px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid rgba(20, 86, 163, 0.08);
  background: #f7faff;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
}

.history-item:hover,
.history-item.active {
  border-color: rgba(20, 86, 163, 0.3);
  box-shadow: 0 8px 18px rgba(32, 60, 96, 0.08);
}

.history-main,
.history-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.history-id {
  font-size: 13px;
  font-weight: 700;
  color: #183153;
}

.history-meta {
  margin-top: 8px;
  font-size: 12px;
  color: #5b6b80;
  flex-wrap: wrap;
}

.base-grid,
.highlight-grid,
.summary-grid {
  display: grid;
  gap: 12px;
}

.base-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.base-item,
.highlight-item,
.summary-card {
  padding: 14px 16px;
  border-radius: 14px;
  background: #f7faff;
}

.base-label,
.highlight-label,
.summary-title {
  display: block;
  font-size: 12px;
  color: #73839a;
}

.base-value,
.highlight-value,
.summary-value {
  display: block;
  margin-top: 6px;
  font-size: 15px;
  font-weight: 700;
  color: #183153;
  word-break: break-word;
}

.summary-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.summary-card[data-tone='danger'] .summary-value,
.highlight-value.danger {
  color: #b42318;
}

.highlight-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.highlight-item.full {
  grid-column: 1 / -1;
}

.chart-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

@media (max-width: 1280px) {
  .report-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .report-header {
    flex-direction: column;
  }

  .report-actions,
  .base-grid,
  .summary-grid,
  .highlight-grid,
  .chart-grid {
    grid-template-columns: 1fr;
  }
}
</style>
