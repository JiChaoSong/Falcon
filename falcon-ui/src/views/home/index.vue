<template>
  <div class="console-page">
    <section class="console-header">
      <div>
        <div class="console-eyebrow">控制台</div>
        <h1 class="console-title">Falcon工作台</h1>
        <p class="console-subtitle">
          聚合平台规模、重点任务、最近运行和 Worker 状态，作为进入任务详情、实时监控和报告分析的统一入口。
        </p>
      </div>

      <div class="console-actions">
        <a-button type="primary" size="large" @click="goTo('/task')">进入任务列表</a-button>
        <a-button size="large" @click="goTo('/system')">查看 Worker</a-button>
      </div>
    </section>

    <section class="overview-grid">
      <a-card
        v-for="card in overviewCards"
        :key="card.label"
        class="overview-card"
        :class="{ clickable: Boolean(card.onClick) }"
        :loading="loading"
        @click="card.onClick?.()"
      >
        <div class="overview-label">{{ card.label }}</div>
        <div class="overview-value">{{ card.value }}</div>
        <div class="overview-foot">{{ card.foot }}</div>
      </a-card>
    </section>

    <section class="main-grid">
      <div class="left-column">
        <a-card class="console-card" :loading="loading">
          <div class="card-head">
            <div>
              <div class="card-eyebrow">重点关注</div>
              <h2 class="card-title">运行中的任务</h2>
            </div>
            <a-button type="link" @click="goTo('/task')">全部任务</a-button>
          </div>

          <div v-if="runningTasks.length" class="focus-list">
            <div v-for="task in runningTasks" :key="task.id" class="focus-item">
              <div class="focus-main">
                <div class="focus-name">{{ task.name }}</div>
                <div class="focus-meta">
                  <span>所属项目：{{ task.project }}</span>
                  <span>主机：{{ task.host || '-' }}</span>
                  <span>并发：{{ task.users }}</span>
                </div>
              </div>
              <div class="focus-side">
                <a-tag :color="getStatusColor(task.status)">{{ getStatusName(task.status) }}</a-tag>
                <div class="focus-actions">
                  <a-button type="link" size="small" @click="openMonitor(task.id)">进入监控</a-button>
                  <a-button type="link" size="small" @click="openTaskDetail(task.id)">查看详情</a-button>
                </div>
              </div>
            </div>
          </div>
          <a-empty v-else description="当前没有运行中的任务" />
        </a-card>

        <a-card class="console-card" :loading="loading">
          <div class="card-head">
            <div>
              <div class="card-eyebrow">重点关注</div>
              <h2 class="card-title">需要关注的任务</h2>
            </div>
            <a-button type="link" @click="goTo('/task')">进入任务管理</a-button>
          </div>

          <div v-if="attentionTasks.length" class="focus-list">
            <div v-for="task in attentionTasks" :key="task.id" class="focus-item warning">
              <div class="focus-main">
                <div class="focus-name">{{ task.name }}</div>
                <div class="focus-meta">
                  <span>状态：{{ getStatusName(task.status) }}</span>
                  <span>最近运行：{{ task.runtime || '-' }}</span>
                  <span>开始时间：{{ formatDateTime(task.start_time) }}</span>
                </div>
              </div>
              <div class="focus-side">
                <a-tag :color="getStatusColor(task.status)">{{ getStatusName(task.status) }}</a-tag>
                <div class="focus-actions">
                  <a-button type="link" size="small" @click="openTaskDetail(task.id)">查看详情</a-button>
                  <a-button type="link" size="small" @click="openReport(task.id)">查看报告</a-button>
                </div>
              </div>
            </div>
          </div>
          <a-empty v-else description="当前没有需要重点关注的任务" />
        </a-card>

        <a-card class="console-card" :loading="loading">
          <div class="card-head">
            <div>
              <div class="card-eyebrow">最近运行</div>
              <h2 class="card-title">任务记录概览</h2>
            </div>
          </div>

          <a-table
            :columns="recentTaskColumns"
            :data-source="recentTasks"
            row-key="id"
            :pagination="false"
            :scroll="{ x: 980 }"
            size="middle"
          >
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'name'">
                <div class="task-name-cell">
                  <div class="task-name">{{ record.name }}</div>
                  <div class="task-subline">{{ record.project }}</div>
                </div>
              </template>

              <template v-if="column.key === 'status'">
                <a-tag :color="getStatusColor(record.status)">{{ getStatusName(record.status) }}</a-tag>
              </template>

              <template v-if="column.key === 'started_at'">
                {{ formatDateTime(record.start_time) }}
              </template>

              <template v-if="column.key === 'runtime'">
                {{ record.runtime || '-' }}
              </template>

              <template v-if="column.key === 'actions'">
                <a-space size="small">
                  <a-button type="link" size="small" @click="openTaskDetail(record.id)">详情</a-button>
                  <a-button type="link" size="small" @click="openMonitor(record.id)">监控</a-button>
                  <a-button type="link" size="small" @click="openReport(record.id)">报告</a-button>
                </a-space>
              </template>
            </template>
          </a-table>
        </a-card>

        <a-card class="console-card" :loading="loading">
          <div class="card-head">
            <div>
              <div class="card-eyebrow">今日趋势</div>
              <h2 class="card-title">平台运行趋势</h2>
            </div>
          </div>

          <div class="trend-grid">
            <EChartPanel
              title="任务运行次数"
              subtitle="按小时查看今日任务运行分布"
              :labels="trendLabels"
              :series="[
                {
                  name: '运行次数',
                  data: trendTaskRuns,
                  color: '#2563eb',
                  areaColor: 'rgba(37, 99, 235, 0.12)',
                },
              ]"
              :legend="['运行次数']"
              :height="240"
            />

            <EChartPanel
              title="成功率与失败数"
              subtitle="成功率使用右轴，失败数使用左轴"
              :labels="trendLabels"
              :series="[
                {
                  name: '失败数',
                  data: trendFailCounts,
                  color: '#dc2626',
                  areaColor: 'rgba(220, 38, 38, 0.10)',
                },
                {
                  name: '成功率',
                  data: trendSuccessRatio,
                  color: '#0f766e',
                  yAxisIndex: 1,
                },
              ]"
              :legend="['失败数', '成功率']"
              :height="240"
            />
          </div>
        </a-card>
      </div>

      <div class="right-column">
        <a-card class="console-card" :loading="loading">
          <div class="card-head">
            <div>
              <div class="card-eyebrow">快捷入口</div>
              <h2 class="card-title">常用操作</h2>
            </div>
          </div>

          <div class="quick-grid">
            <button
              v-for="action in quickActions"
              :key="action.title"
              class="quick-card"
              type="button"
              @click="action.onClick"
            >
              <div class="quick-title">{{ action.title }}</div>
              <div class="quick-desc">{{ action.description }}</div>
              <div class="quick-cta">{{ action.cta }}</div>
            </button>
          </div>
        </a-card>

        <a-card class="console-card" :loading="loading">
          <div class="card-head">
            <div>
              <div class="card-eyebrow">执行环境</div>
              <h2 class="card-title">Worker 状态</h2>
            </div>
            <a-button type="link" @click="goTo('/system')">系统管理</a-button>
          </div>

          <div class="worker-metrics">
            <div class="worker-metric">
              <span>在线节点</span>
              <strong>{{ onlineWorkers }}</strong>
            </div>
            <div class="worker-metric">
              <span>忙碌节点</span>
              <strong>{{ busyWorkers }}</strong>
            </div>
            <div class="worker-metric">
              <span>降级节点</span>
              <strong>{{ degradedWorkers }}</strong>
            </div>
            <div class="worker-metric">
              <span>离线节点</span>
              <strong>{{ offlineWorkers }}</strong>
            </div>
          </div>

          <div v-if="workerHighlights.length" class="worker-list">
            <div v-for="worker in workerHighlights" :key="worker.worker_id" class="worker-item">
              <div class="worker-main">
                <div class="worker-name">{{ worker.worker_id }}</div>
                <div class="worker-desc">{{ worker.address }}</div>
              </div>
              <div class="worker-side">
                <a-tag :color="getWorkerStatusColor(worker.status)">{{ getWorkerStatusName(worker.status) }}</a-tag>
                <span class="worker-meta">{{ worker.running_tasks }}/{{ worker.capacity }} 任务</span>
              </div>
            </div>
          </div>
          <a-empty v-else description="暂无 Worker 数据" />
        </a-card>

        <a-card class="console-card" :loading="loading">
          <div class="card-head">
            <div>
              <div class="card-eyebrow">平台告警</div>
              <h2 class="card-title">规则化风险摘要</h2>
            </div>
          </div>

          <div v-if="alerts.length" class="alert-list">
            <div v-for="item in alerts" :key="`${item.level}-${item.title}`" class="alert-item" :data-level="item.level">
              <div class="alert-top">
                <strong>{{ item.title }}</strong>
                <a-tag :color="getAlertColor(item.level)">{{ getAlertName(item.level) }}</a-tag>
              </div>
              <div class="alert-summary">{{ item.summary }}</div>
              <button type="button" class="alert-action" @click="handleAlertAction(item.level)">{{ item.action }}</button>
            </div>
          </div>
          <a-empty v-else description="当前没有平台告警" />
        </a-card>

      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, defineAsyncComponent, onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useRouter } from 'vue-router'
import { DashboardApi } from '@/api/dashboard'
import { STATE_COLORS, STATE_NAMES, STATE_UNKNOWN } from '@/layout/type'
import type { DashboardOverviewPayload } from '@/types/dashboard'
import type { WorkerStatus } from '@/types/worker'
import { formatDateTime } from '@/utils/tools'

const EChartPanel = defineAsyncComponent(() => import('@/components/EChartPanel.vue'))
const router = useRouter()

const loading = ref(false)
const dashboard = ref<DashboardOverviewPayload | null>(null)

const fetchHomeData = async () => {
  loading.value = true
  try {
    const response = await DashboardApi.getOverview()
    dashboard.value = response.data
  } catch (error) {
    console.error('控制台数据加载失败:', error)
    message.error('控制台数据加载失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const safeDashboard = computed(() => dashboard.value)
const overview = computed(() => safeDashboard.value?.overview)
const workerSummary = computed(() => safeDashboard.value?.worker_summary)

const overviewCards = computed(() => [
  { label: '项目总数', value: String(overview.value?.project_count || 0), foot: '当前项目规模', onClick: () => goTo('/project') },
  { label: '用例总数', value: String(overview.value?.case_count || 0), foot: '接口与脚本用例', onClick: () => goTo('/csse') },
  { label: '场景总数', value: String(overview.value?.scenario_count || 0), foot: '已编排的执行场景', onClick: () => goTo('/scenario') },
  { label: '任务总数', value: String(overview.value?.task_count || 0), foot: '平台任务资产', onClick: () => goTo('/task') },
  { label: '运行中任务', value: String(overview.value?.running_task_count || 0), foot: '当前正在执行', onClick: () => openTaskListWithStatus('running') },
  { label: '停止中任务', value: String(overview.value?.stopping_task_count || 0), foot: '等待停止完成', onClick: () => openTaskListWithStatus('stopping') },
  { label: '失败任务', value: String(overview.value?.failed_task_count || 0), foot: '当前需关注异常', onClick: () => openTaskListWithStatus('failed') },
  { label: '在线 Worker', value: String(overview.value?.online_worker_count || 0), foot: '可参与调度节点', onClick: () => openWorkerListWithStatus('online') },
])

const runningTasks = computed(() => safeDashboard.value?.running_tasks || [])
const attentionTasks = computed(() => safeDashboard.value?.attention_tasks || [])
const recentTasks = computed(() => safeDashboard.value?.recent_tasks || [])
const workerHighlights = computed(() => safeDashboard.value?.worker_highlights || [])
const alerts = computed(() => safeDashboard.value?.alerts || [])
const todayTrend = computed(() => safeDashboard.value?.today_trend || [])

const trendLabels = computed(() => todayTrend.value.map(item => item.label))
const trendTaskRuns = computed(() => todayTrend.value.map(item => item.task_runs))
const trendSuccessRatio = computed(() => todayTrend.value.map(item => item.success_ratio))
const trendFailCounts = computed(() => todayTrend.value.map(item => item.fail_count))

const recentTaskColumns = [
  { title: '任务', key: 'name', width: 220 },
  { title: '状态', key: 'status', width: 120 },
  { title: '开始时间', key: 'started_at', width: 200 },
  { title: '运行时长', key: 'runtime', width: 140 },
  { title: '并发用户', dataIndex: 'users', key: 'users', width: 110 },
  { title: '操作', key: 'actions', width: 180, fixed: 'right' as const },
]

const quickActions = [
  {
    title: '任务管理',
    description: '查看任务列表，进入任务详情、实时监控和任务报告。',
    cta: '进入任务列表',
    onClick: () => goTo('/task'),
  },
  {
    title: '场景管理',
    description: '进入场景页面，维护执行编排、场景绑定和结构配置。',
    cta: '查看场景',
    onClick: () => goTo('/scenario'),
  },
  {
    title: '用例管理',
    description: '进入用例页面，维护接口、脚本和断言规则。',
    cta: '查看用例',
    onClick: () => goTo('/case'),
  },
  {
    title: '系统管理',
    description: '查看 Worker 节点状态、资源概况和系统配置项。',
    cta: '进入系统',
    onClick: () => goTo('/system'),
  },
]

const onlineWorkers = computed(() => workerSummary.value?.online || 0)
const busyWorkers = computed(() => workerSummary.value?.busy || 0)
const degradedWorkers = computed(() => workerSummary.value?.degraded || 0)
const offlineWorkers = computed(() => workerSummary.value?.offline || 0)

const getStatusName = (status: string) =>
  STATE_NAMES[(status in STATE_NAMES ? status : STATE_UNKNOWN) as keyof typeof STATE_NAMES] || status || '状态未知'

const getStatusColor = (status: string) =>
  STATE_COLORS[(status in STATE_COLORS ? status : STATE_UNKNOWN) as keyof typeof STATE_COLORS] || 'default'

const getWorkerStatusName = (status: WorkerStatus) => {
  const map: Record<WorkerStatus, string> = {
    online: '在线',
    busy: '忙碌',
    degraded: '降级',
    offline: '离线',
    disabled: '已禁用',
  }
  return map[status]
}

const getWorkerStatusColor = (status: WorkerStatus) => {
  const map: Record<WorkerStatus, string> = {
    online: 'green',
    busy: 'blue',
    degraded: 'orange',
    offline: 'red',
    disabled: 'default',
  }
  return map[status]
}

const getAlertName = (level: string) => {
  const map: Record<string, string> = {
    danger: '高风险',
    warning: '需关注',
    success: '正常',
    info: '提示',
  }
  return map[level] || '提示'
}

const getAlertColor = (level: string) => {
  const map: Record<string, string> = {
    danger: 'red',
    warning: 'orange',
    success: 'green',
    info: 'blue',
  }
  return map[level] || 'default'
}

const goTo = (path: string) => {
  router.push(path)
}

const openTaskDetail = (taskId: number) => {
  router.push(`/task/detail/${taskId}`)
}

const openMonitor = (taskId: number) => {
  router.push(`/monitor/${taskId}`)
}

const openReport = (taskId: number) => {
  router.push(`/report/${taskId}`)
}

const openTaskListWithStatus = (status: string) => {
  router.push({
    path: '/task',
    query: {
      status,
      page: '1',
    },
  })
}

const openWorkerListWithStatus = (status: WorkerStatus) => {
  router.push({
    path: '/system',
    query: {
      tab: 'workers',
      workerStatus: status,
      workerPage: '1',
    },
  })
}

const handleAlertAction = (level: string) => {
  if (degradedWorkers.value || offlineWorkers.value) {
    openWorkerListWithStatus(degradedWorkers.value ? 'degraded' : 'offline')
    return
  }

  if (level === 'danger' || level === 'warning') {
    openTaskListWithStatus('failed')
    return
  }

  if (runningTasks.value.length) {
    openMonitor(runningTasks.value[0].id)
    return
  }

  goTo('/task')
}

onMounted(() => {
  fetchHomeData()
})
</script>

<style scoped>
.console-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 8px 0 4px;
}

.console-header,
.console-card,
.overview-card {
  border-radius: 22px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.95) 100%);
  box-shadow: 0 14px 32px rgba(15, 23, 42, 0.06);
}

.console-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 24px 26px;
}

.console-eyebrow,
.card-eyebrow {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #64748b;
}

.console-title {
  margin: 10px 0 8px;
  font-size: 30px;
  line-height: 1.15;
  color: #0f172a;
}

.console-subtitle {
  max-width: 760px;
  margin: 0;
  color: #475569;
  line-height: 1.75;
}

.console-actions {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.overview-card {
  padding: 14px 16px;
  border-radius: 20px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(249, 250, 251, 0.94) 100%);
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05);
}

.overview-card.clickable {
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.overview-card.clickable:hover {
  transform: translateY(-1px);
  border-color: rgba(59, 130, 246, 0.22);
  box-shadow: 0 16px 30px rgba(15, 23, 42, 0.08);
}

.overview-label {
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
}

.overview-value {
  margin-top: 8px;
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.1;
}

.overview-foot {
  margin-top: 6px;
  font-size: 12px;
  line-height: 1.5;
  color: #94a3b8;
}

.main-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(340px, 0.9fr);
  gap: 16px;
}

.left-column,
.right-column {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

.console-card {
  padding: 20px;
}

.card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}

.card-title {
  margin: 6px 0 0;
  font-size: 18px;
  color: #0f172a;
}

.focus-list,
.worker-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.focus-item,
.worker-item,
.resource-item,
.worker-metric,
.quick-card {
  border-radius: 18px;
  border: 1px solid rgba(226, 232, 240, 0.9);
  background: rgba(248, 250, 252, 0.86);
}

.focus-item {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 16px;
}

.focus-item.warning {
  border-color: rgba(251, 191, 36, 0.28);
}

.focus-main {
  min-width: 0;
}

.focus-name,
.worker-name,
.quick-title {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}

.focus-meta,
.worker-desc,
.quick-desc {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 14px;
  margin-top: 8px;
  font-size: 13px;
  color: #64748b;
}

.focus-side,
.worker-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10px;
  flex-shrink: 0;
}

.focus-actions {
  display: flex;
  gap: 4px;
}

.task-name-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.task-name {
  font-weight: 700;
  color: #0f172a;
}

.task-subline {
  font-size: 12px;
  color: #94a3b8;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.quick-card {
  padding: 18px;
  text-align: left;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.quick-card:hover {
  transform: translateY(-1px);
  border-color: rgba(59, 130, 246, 0.24);
  box-shadow: 0 12px 26px rgba(15, 23, 42, 0.08);
}

.quick-desc {
  min-height: 68px;
  line-height: 1.7;
}

.quick-cta {
  margin-top: 14px;
  font-size: 13px;
  font-weight: 700;
  color: #2563eb;
}

.worker-metrics,
.resource-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.worker-metric,
.resource-item {
  padding: 16px;
}

.worker-metric span,
.resource-item span,
.worker-meta {
  font-size: 12px;
  color: #64748b;
}

.worker-metric strong,
.resource-item strong {
  display: block;
  margin-top: 8px;
  font-size: 24px;
  color: #0f172a;
}

.worker-item {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  padding: 14px 16px;
  margin-top: 14px;
}

.trend-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.alert-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.alert-item {
  border-radius: 18px;
  border: 1px solid rgba(226, 232, 240, 0.9);
  background: rgba(248, 250, 252, 0.86);
  padding: 16px;
}

.alert-item[data-level='danger'] {
  border-color: rgba(248, 113, 113, 0.28);
  background: linear-gradient(180deg, rgba(255, 245, 245, 0.96) 0%, rgba(255, 250, 250, 0.92) 100%);
}

.alert-item[data-level='warning'] {
  border-color: rgba(251, 191, 36, 0.28);
  background: linear-gradient(180deg, rgba(255, 249, 235, 0.96) 0%, rgba(255, 252, 245, 0.92) 100%);
}

.alert-item[data-level='success'] {
  border-color: rgba(74, 222, 128, 0.24);
  background: linear-gradient(180deg, rgba(240, 253, 244, 0.96) 0%, rgba(248, 255, 250, 0.92) 100%);
}

.alert-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  color: #0f172a;
}

.alert-summary {
  margin-top: 10px;
  line-height: 1.7;
  color: #475569;
}

.alert-action {
  margin-top: 10px;
  font-size: 13px;
  font-weight: 600;
  color: #2563eb;
  padding: 0;
  border: 0;
  background: transparent;
  cursor: pointer;
}

@media (max-width: 1360px) {
  .overview-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .main-grid {
    grid-template-columns: 1fr;
  }

  .trend-grid {
    grid-template-columns: 1fr;
  }
}
</style>
