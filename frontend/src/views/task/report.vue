<script setup lang="ts">
import { computed, defineAsyncComponent, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import html2canvas from 'html2canvas'
import { jsPDF } from 'jspdf'
import { TaskApi } from '@/api/task'
import { STATE_COLORS, STATE_NAMES, STATE_UNKNOWN } from '@/layout/type'
import MonitorStatusDisplay from '@/layout/components/MonitorStatusDisplay.vue'
import type { TaskReportData, TaskRunHistoryItem } from '@/types/task'
import {
  downloadTextFile,
  formatDateTime,
  formatNumber,
  formatPercent,
  formatTimeOnly,
} from '@/utils/tools'

const EChartPanel = defineAsyncComponent(() => import('@/components/EChartPanel.vue'))

const route = useRoute()
const router = useRouter()

const taskId = ref<number>(Number(route.params.taskId) || 0)
const loading = ref(false)
const exportLoading = ref(false)
const isPdfExportMode = ref(false)
const taskReport = ref<TaskReportData | null>(null)
const taskRuns = ref<TaskRunHistoryItem[]>([])
const selectedTaskRunId = ref<number | null>(route.query.taskRunId ? Number(route.query.taskRunId) : null)
const reportExportRef = ref<HTMLElement | null>(null)

const safeReport = computed(() => taskReport.value)

const summaryCards = computed(() => {
  if (!safeReport.value) {
    return []
  }

  return [
    { title: '总请求数', value: String(safeReport.value.total_requests), tone: 'default' },
    { title: '成功率', value: formatPercent(safeReport.value.success_ratio), tone: 'success' },
    { title: '平均响应时间', value: `${formatNumber(safeReport.value.avg_rt)} ms`, tone: 'default' },
    { title: 'P95', value: `${formatNumber(safeReport.value.p95)} ms`, tone: 'warning' },
    { title: 'P99', value: `${formatNumber(safeReport.value.p99)} ms`, tone: 'warning' },
    { title: '失败数', value: String(safeReport.value.fail_count), tone: 'danger' },
  ]
})

const reportOverviewCards = computed(() => {
  if (!safeReport.value) {
    return []
  }

  return [
    { label: '总请求数', value: String(safeReport.value.total_requests), foot: '本次运行累计请求', tone: 'primary' },
    { label: '成功率', value: formatPercent(safeReport.value.success_ratio), foot: '请求成功占比', tone: 'success' },
    { label: '平均响应', value: `${formatNumber(safeReport.value.avg_rt)} ms`, foot: '平均响应时间', tone: 'primary' },
    { label: 'P95', value: `${formatNumber(safeReport.value.p95)} ms`, foot: '95 分位响应时间', tone: 'warning' },
    { label: 'P99', value: `${formatNumber(safeReport.value.p99)} ms`, foot: '99 分位响应时间', tone: 'warning' },
    { label: '失败数', value: String(safeReport.value.fail_count), foot: '本次运行失败请求', tone: 'danger' },
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
      labels: history.map(item => formatTimeOnly(item.ts)),
    },
    {
      key: 'active-users',
      title: '在线用户趋势',
      subtitle: '展示任务运行期间的并发用户变化',
      stroke: '#0f766e',
      fill: 'rgba(15, 118, 110, 0.14)',
      legend: ['在线用户'],
      values: history.map(item => item.active_users),
      labels: history.map(item => formatTimeOnly(item.ts)),
    },
    {
      key: 'rt',
      title: '响应时间趋势',
      subtitle: '平均响应时间与 P95 变化',
      stroke: '#f59e0b',
      fill: 'rgba(245, 158, 11, 0.14)',
      legend: ['平均响应时间', 'P95'],
      values: history.map(item => item.avg_rt),
      compareValues: history.map(item => item.p95),
      compareStroke: '#dc2626',
      labels: history.map(item => formatTimeOnly(item.ts)),
    },
    {
      key: 'fail',
      title: '失败趋势',
      subtitle: '每秒失败数和成功率变化',
      stroke: '#dc2626',
      fill: 'rgba(220, 38, 38, 0.12)',
      legend: ['失败次数/秒', '成功率'],
      values: history.map(item => item.fail_count),
      compareValues: history.map(item => {
        const total = item.success_count + item.fail_count
        return total ? Number(((item.success_count / total) * 100).toFixed(2)) : 100
      }),
      compareAxisIndex: 1,
      compareStroke: '#0f766e',
      labels: history.map(item => formatTimeOnly(item.ts)),
    },
  ]
})

const statusCodeChart = computed(() => {
  const entries = Object.entries(safeReport.value?.status_code_counts || {}).sort((a, b) => Number(a[0]) - Number(b[0]))
  return {
    labels: entries.map(([code]) => code),
    values: entries.map(([, count]) => count),
  }
})

const errorTypeChart = computed(() => {
  const entries = Object.entries(safeReport.value?.error_type_counts || {}).sort((a, b) => b[1] - a[1]).slice(0, 8)
  return {
    labels: entries.map(([label]) => label),
    values: entries.map(([, count]) => count),
  }
})

const failureSamples = computed(() => (safeReport.value?.failure_samples || []).slice(0, 8))

const statsColumns = [
  { title: '方法', dataIndex: 'method', key: 'method', width: 100 },
  { title: '接口名称', dataIndex: 'name', key: 'name', width: 240 },
  { title: '请求数', dataIndex: 'num_requests', key: 'num_requests', width: 100 },
  { title: '失败数', dataIndex: 'num_failures', key: 'num_failures', width: 100 },
  { title: '平均响应时间(ms)', dataIndex: 'avg_response_time', key: 'avg_response_time', width: 140 },
  { title: 'P95(ms)', dataIndex: 'response_time_percentile_0.95', key: 'response_time_percentile_0.95', width: 110 },
  { title: 'P99(ms)', dataIndex: 'response_time_percentile_0.99', key: 'response_time_percentile_0.99', width: 110 },
  { title: '当前 RPS', dataIndex: 'current_rps', key: 'current_rps', width: 110 },
]

const getStatusName = (status: string) =>
  STATE_NAMES[(status in STATE_NAMES ? status : STATE_UNKNOWN) as keyof typeof STATE_NAMES] || status || '状态未知'

const getStatusColor = (status: string) =>
  STATE_COLORS[(status in STATE_COLORS ? status : STATE_UNKNOWN) as keyof typeof STATE_COLORS] || 'default'

const wait = (ms: number) => new Promise(resolve => window.setTimeout(resolve, ms))

const syncSelectedRun = () => {
  if (!taskRuns.value.length) {
    selectedTaskRunId.value = null
    return
  }

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
    message.error('加载任务报告失败，请稍后重试。')
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

const downloadStatsCsv = () => {
  if (!safeReport.value) {
    return
  }

  const headers = [
    'method',
    'name',
    'num_requests',
    'num_failures',
    'success_ratio',
    'avg_response_time',
    'p95',
    'p99',
    'current_rps',
    'latest_error',
  ]

  const rows = (safeReport.value.stats || []).map((item: Record<string, unknown>) => [
    item.method,
    `"${String(item.name || '').replaceAll('"', '""')}"`,
    item.num_requests,
    item.num_failures,
    item.success_ratio ?? '',
    item.avg_response_time,
    item['response_time_percentile_0.95'] ?? '',
    item['response_time_percentile_0.99'] ?? '',
    item.current_rps,
    `"${String(item.latest_error || '').replaceAll('"', '""')}"`,
  ].join(','))

  downloadTextFile(
    `task-report-${safeReport.value.task_id}-${safeReport.value.task_run_id || 'latest'}.csv`,
    [headers.join(','), ...rows].join('\n'),
    'text/csv;charset=utf-8'
  )
}

const downloadSummaryJson = () => {
  if (!safeReport.value) {
    return
  }

  downloadTextFile(
    `task-report-${safeReport.value.task_id}-${safeReport.value.task_run_id || 'latest'}.json`,
    JSON.stringify(safeReport.value, null, 2),
    'application/json;charset=utf-8'
  )
}

const exportPdf = async () => {
  if (!safeReport.value) {
    return
  }

  if (!reportExportRef.value) {
    message.warning('报告内容尚未准备好，请稍后重试。')
    return
  }

  exportLoading.value = true
  try {
    isPdfExportMode.value = true
    await nextTick()
    window.dispatchEvent(new Event('resize'))
    await wait(500)

    const canvas = await html2canvas(reportExportRef.value, {
      scale: 2,
      useCORS: true,
      backgroundColor: '#ffffff',
      windowWidth: reportExportRef.value.scrollWidth,
    })

    const imageData = canvas.toDataURL('image/png')
    const pdfWidth = 210
    const pdfHeight = (canvas.height * pdfWidth) / canvas.width
    const pdf = new jsPDF({
      orientation: 'p',
      unit: 'mm',
      format: [pdfWidth, pdfHeight],
      compress: true,
    })

    pdf.addImage(imageData, 'PNG', 0, 0, pdfWidth, pdfHeight)
    pdf.save(`task-report-${safeReport.value.task_id}-${safeReport.value.task_run_id || 'latest'}.pdf`)
  } catch (error) {
    console.error('导出 PDF 失败:', error)
    message.error('导出 PDF 失败，请稍后重试。')
  } finally {
    isPdfExportMode.value = false
    exportLoading.value = false
  }
}

watch(
  () => route.query.taskRunId,
  async value => {
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
          聚焦单次运行的关键指标、热点接口、错误样本和历史趋势，方便快速复盘和结果沉淀。
        </p>
      </div>
      <div class="report-actions">
        <a-button @click="goBack">返回监控</a-button>
<!--        <a-button @click="exportPdf" :loading="exportLoading" :disabled="!safeReport">导出 PDF</a-button>-->
<!--        <a-button @click="downloadStatsCsv" :disabled="!safeReport">导出 CSV</a-button>-->
<!--        <a-button @click="downloadSummaryJson" :disabled="!safeReport">导出 JSON</a-button>-->
        <a-button type="primary" :loading="loading" @click="refreshPage">刷新报告</a-button>
      </div>
    </div>

    <div class="report-layout">
      <aside class="report-sidebar">
        <a-card class="sidebar-card" title="运行记录" :loading="loading">
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
                <a-tag :color="getStatusColor(item.status)">{{ getStatusName(item.status) }}</a-tag>
              </div>
              <div class="history-meta">
                <span>请求数 {{ item.total_requests }}</span>
                <span>成功率 {{ formatPercent(item.success_ratio) }}</span>
                <span>时长 {{ item.runtime_seconds }}s</span>
              </div>
              <div class="history-time">{{ formatDateTime(item.started_at) }}</div>
            </button>
          </template>
          <a-empty v-else description="暂无运行记录" />
        </a-card>
      </aside>

      <div ref="reportExportRef" class="report-export-sheet" :class="{ 'pdf-export-mode': isPdfExportMode }">
        <main class="report-main">
          <a-card class="report-card report-overview-card" :loading="loading">
            <div class="report-card-head report-overview-head">
              <div>
                <div class="section-eyebrow">运行概况</div>
                <h2 class="section-title">本次运行基础信息</h2>
              </div>
              <a-tag v-if="safeReport" :color="getStatusColor(safeReport.status)">{{ getStatusName(safeReport.status) }}</a-tag>
            </div>

            <div class="base-grid report-overview-grid" v-if="safeReport">
              <div class="base-item report-overview-item">
                <span class="base-label">运行 ID</span>
                <span class="base-value">{{ safeReport.task_run_id || '-' }}</span>
              </div>
              <div class="base-item report-overview-item">
                <span class="base-label">所属项目</span>
                <span class="base-value">{{ safeReport.project }}</span>
              </div>
              <div class="base-item report-overview-item">
                <span class="base-label">负责人</span>
                <span class="base-value">{{ safeReport.owner }}</span>
              </div>
              <div class="base-item report-overview-item">
                <span class="base-label">执行策略</span>
                <span class="base-value">{{ safeReport.execution_strategy }}</span>
              </div>
              <div class="base-item report-overview-item">
                <span class="base-label">目标主机</span>
                <span class="base-value host-value" :title="safeReport.host">{{ safeReport.host }}</span>
              </div>
              <div class="base-item report-overview-item">
                <span class="base-label">场景数量</span>
                <span class="base-value">{{ safeReport.scenario_count }}</span>
              </div>
              <div class="base-item report-overview-item">
                <span class="base-label">开始时间</span>
                <span class="base-value">{{ formatDateTime(safeReport.started_at) }}</span>
              </div>
              <div class="base-item report-overview-item">
                <span class="base-label">结束时间</span>
                <span class="base-value">{{ formatDateTime(safeReport.finished_at) }}</span>
              </div>
              <div class="base-item report-overview-item">
                <span class="base-label">运行时长</span>
                <span class="base-value">{{ safeReport.runtime_seconds }}s</span>
              </div>
            </div>
          </a-card>

          <MonitorStatusDisplay :cards="reportOverviewCards" />

          <a-card class="report-card" v-if="safeReport">
            <div class="report-card-head">
              <div>
                <div class="section-eyebrow">重点摘要</div>
                <h2 class="section-title">热点接口与风险接口</h2>
              </div>
            </div>

            <div class="highlight-grid">
              <div class="highlight-item">
                <span class="highlight-label">最热接口</span>
                <span class="highlight-value">{{ safeReport.hottest_endpoint?.name || '-' }}</span>
                <span class="highlight-desc">
                  {{ safeReport.hottest_endpoint?.method || '-' }} / 请求 {{ safeReport.hottest_endpoint?.total_requests || 0 }}
                </span>
              </div>
              <div class="highlight-item highlight-item-danger">
                <span class="highlight-label">风险最高接口</span>
                <span class="highlight-value">{{ safeReport.riskiest_endpoint?.name || '-' }}</span>
                <span class="highlight-desc">
                  {{ safeReport.riskiest_endpoint?.method || '-' }} / 失败 {{ safeReport.riskiest_endpoint?.total_failures || 0 }}
                </span>
              </div>
              <div class="highlight-item full">
                <span class="highlight-label">最近错误</span>
                <span class="highlight-value danger">{{ safeReport.latest_error || '暂无错误' }}</span>
              </div>
            </div>
          </a-card>

          <section class="chart-grid" v-if="safeReport?.history?.length">
            <div v-for="chart in chartConfigs" :key="chart.key" class="chart-card">
              <EChartPanel
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
                        yAxisIndex: chart.compareAxisIndex ?? 0,
                      }]
                    : [])
                ]"
              />
            </div>
          </section>

          <section class="chart-grid">
            <div v-if="statusCodeChart.labels.length" class="chart-card">
              <EChartPanel
                title="状态码分布"
                subtitle="查看不同状态码返回次数"
                :labels="statusCodeChart.labels"
                :legend="['响应数']"
                :series="[{ name: '响应数', data: statusCodeChart.values, color: '#2563eb' }]"
                mode="bar"
                :height="240"
              />
            </div>
            <div  class="chart-card">
              <EChartPanel
                title="错误类型分布"
                subtitle="按错误类型统计失败次数"
                :labels="errorTypeChart.labels"
                :legend="['错误数']"
                :series="[{ name: '错误数', data: errorTypeChart.values, color: '#dc2626' }]"
                mode="bar"
                :height="240"
              />
            </div>
          </section>

          <a-card class="report-card" title="失败样本" v-if="failureSamples.length">
            <div class="failure-list">
              <div class="failure-item" v-for="(item, index) in failureSamples" :key="`${item.name}-${index}`">
                <div class="failure-main">
                  <span class="failure-method">{{ item.method || 'REQ' }}</span>
                  <span class="failure-name">{{ item.name || '-' }}</span>
                </div>
                <div class="failure-meta">
                  <span>状态码 {{ item.status_code || 0 }}</span>
                  <span>{{ item.error_type || 'request_failed' }}</span>
                </div>
                <div class="failure-message">{{ item.message || '暂无错误详情' }}</div>
              </div>
            </div>
          </a-card>

          <a-card class="report-card" title="接口统计明细" :loading="loading">
          <a-table
            :columns="statsColumns"
            :data-source="safeReport?.stats || []"
            :pagination="false"
            row-key="name"
            :scroll="{ x: 1200 }"
          />
          </a-card>
        </main>
      </div>
    </div>
  </div>
</template>

<style scoped>
.report-page {
  height: 100vh;
  padding: 28px 36px;
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  gap: 20px;
  overflow: hidden;
  background:
    radial-gradient(circle at top left, rgba(219, 234, 254, 0.95), transparent 28%),
    radial-gradient(circle at top right, rgba(255, 237, 213, 0.82), transparent 24%),
    linear-gradient(180deg, #f8fbff 0%, #eef4fb 100%);
}

.report-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  min-height: 0;
}

.report-eyebrow,
.section-eyebrow {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: #64748b;
  text-transform: uppercase;
}

.report-title {
  margin: 8px 0 10px;
  font-size: 32px;
  line-height: 1.15;
  color: #0f172a;
}

.report-subtitle {
  max-width: 760px;
  margin: 0;
  color: #475569;
  line-height: 1.7;
}

.report-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.report-layout {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 18px;
  align-items: stretch;
  min-height: 0;
  overflow: hidden;
}

.report-sidebar {
  min-height: 0;
  overflow: hidden;
}

.sidebar-card,
.report-card {
  border-radius: 24px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  background:
    radial-gradient(circle at top right, rgba(219, 234, 254, 0.42), transparent 28%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.97) 0%, rgba(248, 250, 252, 0.95) 100%);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
}

.report-export-sheet {
  min-width: 0;
  min-height: 0;
  overflow: auto;
  padding-right: 6px;
}

.report-main {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.sidebar-card {
  height: 100%;
}

.sidebar-card :deep(.ant-card-body) {
  height: 100%;
  overflow: auto;
}

.history-item {
  width: 100%;
  margin-bottom: 10px;
  padding: 12px 14px;
  border-radius: 16px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  background:
    radial-gradient(circle at top right, rgba(239, 246, 255, 0.72), transparent 36%),
    #f8fbff;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
}

.history-item:hover,
.history-item.active {
  border-color: rgba(37, 99, 235, 0.26);
  box-shadow: 0 10px 24px rgba(37, 99, 235, 0.1);
  transform: translateY(-1px);
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
  margin-top: 10px;
  flex-wrap: wrap;
  font-size: 12px;
  color: #5b6b80;
}

.history-time {
  margin-top: 8px;
  font-size: 12px;
  color: #94a3b8;
}

.report-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.report-overview-card {
  position: relative;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.98);
}

.report-overview-head {
  align-items: center;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(226, 232, 240, 0.9);
}

.report-overview-grid {
  gap: 12px;
}

.report-overview-item {
  position: relative;
  min-height: 92px;
  padding: 16px 18px;
  border-radius: 14px;
  border: 1px solid rgba(226, 232, 240, 0.95);
  background: #fbfdff;
  box-shadow: none;
}

.report-overview-item:nth-child(3n + 1) {
  border-color: rgba(226, 232, 240, 0.95);
}

.report-overview-item:nth-child(3n + 2) {
  border-color: rgba(226, 232, 240, 0.95);
}

.report-overview-item:nth-child(3n) {
  border-color: rgba(226, 232, 240, 0.95);
}

.section-title {
  margin: 8px 0;
  font-size: 22px;
  color: #0f172a;
}

.base-grid,
.highlight-grid {
  display: grid;
  gap: 14px;
}

.base-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.base-item,
.highlight-item {
  padding: 16px 18px;
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.1);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.96));
}

.base-label,
.highlight-label {
  display: block;
  font-size: 12px;
  color: #64748b;
}

.base-value,
.highlight-value {
  display: block;
  margin-top: 8px;
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
  word-break: break-word;
}

.report-overview-item .base-label {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.02em;
  text-transform: none;
  color: #64748b;
}

.report-overview-item .base-value {
  margin-top: 12px;
  font-size: 16px;
  line-height: 1.2;
  font-weight: 700;
  color: #0f172a;
}

.host-value {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.highlight-value.danger {
  color: #b42318;
}

.highlight-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.highlight-item.full {
  grid-column: 1 / -1;
}

.highlight-item-danger {
  border-color: rgba(248, 113, 113, 0.16);
  background:
    radial-gradient(circle at top right, rgba(254, 226, 226, 0.7), transparent 36%),
    #ffffff;
}

.highlight-desc {
  display: block;
  margin-top: 8px;
  font-size: 12px;
  color: #64748b;
}

.chart-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.chart-card {
  min-width: 0;
}

.chart-card :deep(.chart-card) {
  border-radius: 24px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  background:
    radial-gradient(circle at top right, rgba(219, 234, 254, 0.34), transparent 26%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.97) 0%, rgba(248, 250, 252, 0.95) 100%);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
}

.failure-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.failure-item {
  padding: 16px 18px;
  border-radius: 16px;
  border: 1px solid rgba(248, 113, 113, 0.14);
  background:
    radial-gradient(circle at top right, rgba(254, 242, 242, 0.8), transparent 36%),
    #fffefe;
}

.failure-main,
.failure-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.failure-method {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 48px;
  padding: 2px 8px;
  border-radius: 999px;
  background: #fee2e2;
  color: #b91c1c;
  font-size: 12px;
  font-weight: 700;
}

.failure-name {
  flex: 1;
  font-weight: 600;
  color: #183153;
}

.failure-meta {
  margin-top: 8px;
  font-size: 12px;
  color: #b42318;
}

.failure-message {
  margin-top: 8px;
  font-size: 12px;
  color: #6a7b92;
  line-height: 1.6;
}

.pdf-export-mode {
  width: 860px;
  padding: 12px;
  background: #ffffff;
}

.pdf-export-mode .report-main {
  gap: 12px;
}

.pdf-export-mode .report-card,
.pdf-export-mode .highlight-item {
  box-shadow: none;
}

.pdf-export-mode .base-grid,
.pdf-export-mode .highlight-grid,
.pdf-export-mode .chart-grid {
  grid-template-columns: 1fr;
}

.pdf-export-mode :deep(.chart-card) {
  width: 100%;
  overflow: hidden;
}

.pdf-export-mode :deep(.chart-canvas) {
  width: 100% !important;
}

@media (max-width: 1280px) {
  .report-layout {
    grid-template-columns: 1fr;
    overflow: visible;
  }

  .report-sidebar {
    overflow: visible;
  }

  .report-export-sheet {
    overflow: visible;
    padding-right: 0;
  }

  .sidebar-card {
    height: auto;
  }

  .sidebar-card :deep(.ant-card-body) {
    height: auto;
    overflow: visible;
  }
}

@media (max-width: 860px) {
  .report-page {
    height: auto;
    min-height: 100vh;
    padding: 20px;
    overflow: visible;
  }

  .report-header {
    flex-direction: column;
  }

  .report-actions,
  .base-grid,
  .highlight-grid,
  .chart-grid {
    grid-template-columns: 1fr;
  }
}
</style>
