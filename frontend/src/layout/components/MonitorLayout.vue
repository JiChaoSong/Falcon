<script setup lang="ts">
import LogoComponent from "@/layout/components/LogoComponent.vue";
import MonitorComponent from "@/layout/components/MonitorComponent.vue";
import MonitorAiPanel from "@/layout/components/MonitorAiPanel.vue";
import MonitorHotEndpoints from "@/layout/components/MonitorHotEndpoints.vue";
import MonitorControlBar from "@/layout/components/MonitorControlBar.vue";
import MonitorStatusDisplay from "@/layout/components/MonitorStatusDisplay.vue";
import EChartPanel from "@/components/EChartPanel.vue";
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { MetricHistoryPoint, Metrics, STATE_COLORS, STATE_NAMES, Stats, SystemState } from "@/layout/type.ts";
import { message, Modal } from "ant-design-vue";
import { formatDateTime, formatNumber, formatPercent } from "@/utils/tools";
import { TaskApi } from "@/api/task";
import type { TaskInfo, TaskReportData, TaskRunHistoryItem, TaskRuntimeStatus } from "@/types/task";
import { getToken } from "@/utils/auth";
import { taskRuntimeSocket, type TaskRuntimeSocketMessage } from "@/utils/websocket";

type MonitorRiskLevel = "success" | "warning" | "danger";

interface AiInsight {
  title: string;
  summary: string;
  level: MonitorRiskLevel;
  reasons: string[];
  actions: string[];
  confidence: number;
}

const route = useRoute();
const router = useRouter();
const loading = ref(false);
const controlLoading = ref(false);
const taskRunning = ref(false);
const wsConnected = ref(false);
const currentTaskId = ref<number>(Number(route.params.taskId) || 0);
const FALLBACK_ACTIVATION_DELAY_MS = 4000;
const FALLBACK_STATUS_POLL_MS = 5000;
const FALLBACK_DETAILS_POLL_MS = 15000;

const defaultMetric: Metrics = {
  stats: [],
  host: '',
  errors: [],
  total_rps: 0,
  total_fail_per_sec: 0,
  fail_ratio: 0,
  state: 'missing' as SystemState,
  user_count: 0,
  start_time: '--',
  runtime: '--',
  runtime_seconds: 0,
  status_code_counts: {},
  error_type_counts: {},
  failure_samples: [],
};

const defaultTaskInfo: TaskInfo = {
  id: currentTaskId.value,
  name: '未命名任务',
  description: null,
  owner: '',
  owner_id: 0,
  project_id: 0,
  project: '',
  host: '',
  users: 0,
  spawn_rate: 0,
  duration: 0,
  status: 'pending',
  start_time: null,
  runtime_seconds: 0,
  runtime: null,
  finished_at: null,
  stats: null,
  scenarios: [],
  created_at: '',
  created_by: 0,
  created_by_name: '',
  updated_at: '',
  updated_by: 0,
  updated_by_name: '',
  is_deleted: false,
  execution_strategy: 'default',
};

const taskInfo = ref<TaskInfo>({ ...defaultTaskInfo });
const taskReport = ref<TaskReportData | null>(null);
const taskRuns = ref<TaskRunHistoryItem[]>([]);
const selectedTaskRunId = ref<number | null>(null);
const dataSource = ref<Stats[]>([]);
const metrics = ref<Metrics>({ ...defaultMetric });
const metricHistory = ref<MetricHistoryPoint[]>([]);
let fallbackActivationTimer: ReturnType<typeof setTimeout> | null = null;
let fallbackStatusPollingTimer: ReturnType<typeof setInterval> | null = null;
let fallbackDetailsPollingTimer: ReturnType<typeof setInterval> | null = null;
let lastReportRefreshAt = 0;

const safeMetrics = computed(() => metrics.value || defaultMetric);
const safeTaskInfo = computed(() => taskInfo.value || defaultTaskInfo);
const safeTaskReport = computed(() => taskReport.value);
const selectedTaskRun = computed(() =>
  taskRuns.value.find(item => item.id === selectedTaskRunId.value) || null
);

const statusCodeChart = computed(() => {
  const counts = safeTaskReport.value?.status_code_counts || safeMetrics.value.status_code_counts || {};
  const entries = Object.entries(counts).sort((a, b) => Number(a[0]) - Number(b[0]));
  return {
    labels: entries.map(([code]) => code),
    values: entries.map(([, count]) => count),
  };
});

const errorTypeChart = computed(() => {
  const counts = safeTaskReport.value?.error_type_counts || safeMetrics.value.error_type_counts || {};
  const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 6);
  return {
    labels: entries.map(([type]) => type),
    values: entries.map(([, count]) => count),
  };
});

const runtimeQualityCards = computed(() => {
  const report = safeTaskReport.value;
  const statusCodes = Object.keys(report?.status_code_counts || {}).length;
  const errorTypes = Object.keys(report?.error_type_counts || {}).length;
  const failures = report?.failure_samples?.length || 0;
  const latestRun = selectedTaskRun.value;

  return [
    { title: '状态码种类', value: String(statusCodes), tone: 'default', hint: '响应分布' },
    { title: '错误类型', value: String(errorTypes), tone: 'warning', hint: '失败分类' },
    { title: '失败样本', value: String(failures), tone: 'danger', hint: '最近 20 条' },
    { title: '当前实例', value: latestRun ? `#${latestRun.id}` : '-', tone: 'success', hint: formatDateTime(latestRun?.started_at) },
  ];
});

const failureSamples = computed(() => {
  return (safeTaskReport.value?.failure_samples || []).slice(0, 5) as Array<Record<string, unknown>>;
});

const getStatusName = (state: SystemState): string => {
  return STATE_NAMES[state] || "未知状态";
};

const getStatusColor = (state: SystemState): string => {
  return STATE_COLORS[state] || "gray";
};

const buildRuntime = (seconds: number) => {
  const hour = String(Math.floor(seconds / 3600)).padStart(2, '0');
  const minute = String(Math.floor((seconds % 3600) / 60)).padStart(2, '0');
  const second = String(seconds % 60).padStart(2, '0');
  return `${hour}:${minute}:${second}`;
};

const mapTaskStatusToSystemState = (status?: string): SystemState => {
  switch ((status || '').toLowerCase()) {
    case 'running':
      return 'running';
    case 'stopping':
      return 'stopping';
    case 'pending':
      return 'ready';
    case 'completed':
      return 'stopped';
    case 'canceled':
      return 'stopped';
    case 'failed':
      return 'missing';
    default:
      return 'ready';
  }
};

const createAggregateStats = (runtime: TaskRuntimeStatus): Stats[] => {
  const runtimeStats = Array.isArray(runtime.stats)
    ? runtime.stats as unknown as Stats[]
    : [];

  if (runtimeStats.length) {
    return runtimeStats;
  }

  if (!runtime.total_requests && !runtime.current_rps) {
    return [];
  }

  return [
    {
      method: 'TASK',
      name: runtime.task_name,
      num_requests: runtime.total_requests,
      num_failures: runtime.fail_count,
      min_response_time: runtime.avg_rt,
      max_response_time: runtime.p99,
      current_rps: runtime.current_rps,
      current_fail_per_sec: runtime.history.length
        ? runtime.history[runtime.history.length - 1]?.fail_count || 0
        : 0,
      avg_response_time: runtime.avg_rt,
      median_response_time: runtime.avg_rt,
      total_rps: runtime.current_rps,
      total_fail_per_sec: runtime.history.length
        ? runtime.history[runtime.history.length - 1]?.fail_count || 0
        : 0,
      avg_content_length: 0,
      "response_time_percentile_0.95": runtime.p95,
      "response_time_percentile_0.99": runtime.p99,
    }
  ];
};

const applyRuntimeStatus = (runtime: TaskRuntimeStatus) => {
  const failRatio = runtime.total_requests
    ? runtime.fail_count / runtime.total_requests
    : 0;

  taskRunning.value = runtime.status === 'running' || runtime.status === 'stopping';
  dataSource.value = createAggregateStats(runtime);
  metrics.value = {
    stats: dataSource.value,
    errors: runtime.latest_error ? [{ message: runtime.latest_error }] : [],
    total_rps: runtime.current_rps,
    total_fail_per_sec: runtime.history.length
      ? runtime.history[runtime.history.length - 1]?.fail_count || 0
      : 0,
    fail_ratio: Number(failRatio.toFixed(4)),
    state: mapTaskStatusToSystemState(runtime.status),
    user_count: runtime.active_users,
    host: runtime.host || taskInfo.value.host || '',
    start_time: runtime.started_at || '--',
    runtime: buildRuntime(runtime.runtime_seconds || 0),
    runtime_seconds: runtime.runtime_seconds || 0,
    status_code_counts: runtime.status_code_counts || {},
    error_type_counts: runtime.error_type_counts || {},
    failure_samples: runtime.failure_samples || [],
  };
  metricHistory.value = runtime.history.map(item => ({
    time: buildRuntime(
      Math.max(
        0,
        Math.round((new Date(item.ts).getTime() - new Date(runtime.started_at || item.ts).getTime()) / 1000)
      )
    ),
    user_count: item.active_users,
    total_rps: item.rps,
    fail_ratio: item.success_count + item.fail_count
      ? item.fail_count / (item.success_count + item.fail_count)
      : 0,
    avg_response_time: item.avg_rt,
    p95_response_time: item.p95,
    total_fail_per_sec: item.fail_count,
  }));
};

const fetchTaskInfo = async () => {
  const response = await TaskApi.getTaskInfo({ id: currentTaskId.value });
  taskInfo.value = response.data;
};

const fetchTaskStatus = async () => {
  const response = await TaskApi.getTaskStatus({ task_id: currentTaskId.value });
  applyRuntimeStatus(response.data);
};

const fetchTaskRuns = async () => {
  const response = await TaskApi.getTaskRuns({ task_id: currentTaskId.value });
  taskRuns.value = response.data.runs || [];

  // Keep the selected run stable while still defaulting to the latest one.
  if (!taskRuns.value.length) {
    selectedTaskRunId.value = null;
    return;
  }
  if (!selectedTaskRunId.value || !taskRuns.value.some(item => item.id === selectedTaskRunId.value)) {
    selectedTaskRunId.value = taskRuns.value[0].id;
  }
};

const fetchTaskReport = async () => {
  if (!currentTaskId.value || !selectedTaskRunId.value) {
    taskReport.value = null;
    return;
  }
  const response = await TaskApi.getTaskReport({
    task_id: currentTaskId.value,
    task_run_id: selectedTaskRunId.value,
  });
  taskReport.value = response.data;
};

const resetMonitorState = () => {
  taskInfo.value = {
    ...defaultTaskInfo,
    id: currentTaskId.value,
  };
  taskReport.value = null;
  taskRuns.value = [];
  selectedTaskRunId.value = null;
  dataSource.value = [];
  metrics.value = { ...defaultMetric };
  metricHistory.value = [];
  taskRunning.value = false;
  wsConnected.value = false;
  lastReportRefreshAt = 0;
};

const refreshReportIfNeeded = async (force = false) => {
  const now = Date.now();
  if (!force && now - lastReportRefreshAt < 10000) {
    return;
  }
  await fetchTaskReport();
  lastReportRefreshAt = now;
};

const handleSelectTaskRun = async (taskRunId: number) => {
  selectedTaskRunId.value = taskRunId;
  try {
    await fetchTaskReport();
  } catch (error) {
    console.error('加载运行报告失败:', error);
    message.error('运行报告加载失败，请稍后重试');
  }
};

const refreshMonitorData = async (showError = true) => {
  if (!currentTaskId.value) {
    return;
  }

  loading.value = true;
  try {
    await Promise.all([fetchTaskInfo(), fetchTaskStatus(), fetchTaskRuns()]);
    await fetchTaskReport();
  } catch (error) {
    console.error('获取监控数据失败:', error);
    if (showError) {
      message.error('监控数据加载失败，请稍后重试');
    }
  } finally {
    loading.value = false;
  }
};

const stopFallbackPolling = () => {
  if (fallbackActivationTimer) {
    clearTimeout(fallbackActivationTimer);
    fallbackActivationTimer = null;
  }
  if (fallbackStatusPollingTimer) {
    clearInterval(fallbackStatusPollingTimer);
    fallbackStatusPollingTimer = null;
  }
  if (fallbackDetailsPollingTimer) {
    clearInterval(fallbackDetailsPollingTimer);
    fallbackDetailsPollingTimer = null;
  }
};

const pollRuntimeSnapshot = async () => {
  if (!currentTaskId.value || wsConnected.value) {
    return;
  }

  try {
    await fetchTaskStatus();
  } catch (error) {
    console.error('Fallback status polling failed:', error);
  }
};

const pollRuntimeDetails = async () => {
  if (!currentTaskId.value || wsConnected.value) {
    return;
  }

  try {
    await fetchTaskRuns();
    await refreshReportIfNeeded(true);
  } catch (error) {
    console.error('Fallback detail polling failed:', error);
  }
};

const startFallbackPolling = () => {
  if (fallbackActivationTimer || fallbackStatusPollingTimer || fallbackDetailsPollingTimer) {
    return;
  }

  fallbackActivationTimer = setTimeout(() => {
    fallbackActivationTimer = null;
    if (wsConnected.value || !currentTaskId.value) {
      return;
    }

    void pollRuntimeSnapshot();
    void pollRuntimeDetails();

    fallbackStatusPollingTimer = setInterval(() => {
      void pollRuntimeSnapshot();
    }, FALLBACK_STATUS_POLL_MS);

    fallbackDetailsPollingTimer = setInterval(() => {
      void pollRuntimeDetails();
    }, FALLBACK_DETAILS_POLL_MS);
  }, FALLBACK_ACTIVATION_DELAY_MS);
};

const connectRuntimeSocket = () => {
  const token = getToken();
  if (!currentTaskId.value || !token) {
    return;
  }

  taskRuntimeSocket.connect(currentTaskId.value, token);
};

const handleRuntimeSocketMessage = async (payload: TaskRuntimeSocketMessage) => {
  if (payload.task_id !== currentTaskId.value) {
    return;
  }

  try {
    if (payload.event === 'connected') {
      await Promise.all([fetchTaskStatus(), fetchTaskRuns()]);
      await refreshReportIfNeeded(true);
      return;
    }

    await fetchTaskStatus();

    if (payload.event === 'started' || payload.event === 'finished' || payload.event === 'failed' || payload.event === 'canceled') {
      await fetchTaskRuns();
      if (taskRuns.value.length) {
        selectedTaskRunId.value = taskRuns.value[0].id;
      }
      await refreshReportIfNeeded(true);
      return;
    }

    if (payload.event === 'snapshot') {
      await refreshReportIfNeeded(false);
    }
  } catch (error) {
    console.error('Failed to sync runtime data from websocket message:', error);
  }
};

const handleStartTest = () => {
  if (taskRunning.value) {
    message.warning("任务已在运行中");
    return;
  }

  Modal.confirm({
    title: '确认开始压测',
    content: '确定要开始性能测试吗？',
    okText: '确定',
    cancelText: '取消',
    async onOk() {
      controlLoading.value = true;
      try {
        await TaskApi.runTask({ task_id: currentTaskId.value });
        await refreshMonitorData(false);
        connectRuntimeSocket();
        message.success("任务已开始执行");
      } finally {
        controlLoading.value = false;
      }
    }
  });
};

const handleStopTest = () => {
  if (safeMetrics.value.state === 'stopping') {
    message.warning("任务正在停止中");
    return;
  }
  if (!taskRunning.value) {
    message.warning("任务未在运行中");
    return;
  }

  Modal.confirm({
    title: '确认停止压测',
    content: '确定要停止性能测试吗？',
    okText: '确定',
    cancelText: '取消',
    okType: 'danger',
    async onOk() {
      controlLoading.value = true;
      try {
        await TaskApi.stopTask({ task_id: currentTaskId.value });
        await refreshMonitorData(false);
        message.success("任务已发送停止指令");
      } finally {
        controlLoading.value = false;
      }
    }
  });
};

const handlePauseTest = () => {
  message.info("M1 暂不支持暂停，后续会在执行器控制层补上");
};

const handleResumeTest = () => {
  message.info("M1 暂不支持恢复，建议重新开始任务");
};

const openFullReport = () => {
  const query = selectedTaskRunId.value ? { taskRunId: String(selectedTaskRunId.value) } : undefined;
  router.push({
    path: `/report/${currentTaskId.value}`,
    query,
  });
};

onMounted(async () => {
  taskRuntimeSocket.setOnConnectionChange((connected) => {
    wsConnected.value = connected;
    if (connected) {
      stopFallbackPolling();
      return;
    }
    startFallbackPolling();
  });
  taskRuntimeSocket.setOnMessage((payload) => {
    void handleRuntimeSocketMessage(payload);
  });
  taskRuntimeSocket.setOnError((event) => {
    console.error('Task runtime websocket failed to connect:', event);
  });
  connectRuntimeSocket();
  await refreshMonitorData();
});

watch(
  () => route.params.taskId,
  (value) => {
    currentTaskId.value = Number(value) || 0;
    stopFallbackPolling();
    taskRuntimeSocket.disconnect();
    resetMonitorState();
    connectRuntimeSocket();
    void refreshMonitorData(false);
  }
);

onUnmounted(() => {
  stopFallbackPolling();
  taskRuntimeSocket.disconnect();
});
</script>

<template>
  <MonitorControlBar
    :taskId="currentTaskId"
    :taskInfo="safeTaskInfo"
    :metrics="safeMetrics"
    :taskRunning="taskRunning"
    :controlLoading="controlLoading"
    @startTest="handleStartTest"
    @stopTest="handleStopTest"
    @pauseTest="handlePauseTest"
    @resumeTest="handleResumeTest"
  />

  <div class="main-container">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <div class="loading-content">
        <div class="loading-spinner"></div>
        <p class="loading-text">正在加载监控数据...</p>
      </div>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="!currentTaskId" class="error-state">
      <svg class="error-icon" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
      </svg>
      <h2 class="error-title">任务未找到</h2>
      <p class="error-message">请检查任务ID是否正确，或返回任务列表重新选择。</p>
      <div class="error-actions">
        <button class="ant-btn ant-btn-primary" @click="router.push('/tasks')">返回任务列表</button>
      </div>
    </div>

    <!-- 主要内容 -->
    <template v-else>
      <MonitorStatusDisplay :metrics="safeMetrics" />

      <section class="ai-panel">
        <MonitorAiPanel
          :dataSource="dataSource"
          :metrics="safeMetrics"
          :history="metricHistory"
        />

        <MonitorHotEndpoints
          :dataSource="dataSource"
        />
      </section>

      <MonitorComponent
          :dataSource="dataSource"
          :metrics="safeMetrics"
          :history="metricHistory"
          :loading="loading"
      />
    </template>
  </div>
</template>

<style scoped>
.main-container {
  margin-top: 64px;
  flex: 1;
  padding: 24px 10% 32px;
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
}

.main-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    radial-gradient(circle at 25% 25%, rgba(59, 130, 246, 0.03) 0%, transparent 50%),
    radial-gradient(circle at 75% 75%, rgba(16, 185, 129, 0.03) 0%, transparent 50%);
  pointer-events: none;
  z-index: 0;
}

.main-container > * {
  position: relative;
  z-index: 1;
}

/* 响应式断点优化 */
@media (max-width: 1400px) {
  .main-container {
    padding: 20px 8% 28px;
  }
}

@media (max-width: 1200px) {
  .main-container {
    padding: 20px 6% 28px;
  }
}

@media (max-width: 1024px) {
  .main-container {
    padding: 16px 4% 24px;
  }
}

@media (max-width: 768px) {
  .main-container {
    padding: 12px 16px 20px;
    margin-top: 72px;
  }
}

@media (max-width: 480px) {
  .main-container {
    padding: 8px 12px 16px;
  }
}

/* 加载状态优化 */
.loading-overlay {
  position: fixed;
  top: 64px;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.loading-content {
  text-align: center;
  padding: 32px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f4f6;
  border-top: 3px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-text {
  color: #6b7280;
  font-size: 14px;
  margin: 0;
}

/* 错误状态样式 */
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  padding: 48px;
  text-align: center;
}

.error-icon {
  width: 64px;
  height: 64px;
  margin-bottom: 24px;
  opacity: 0.6;
}

.error-title {
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 8px;
}

.error-message {
  color: #6b7280;
  margin-bottom: 24px;
  max-width: 400px;
}

.error-actions {
  display: flex;
  gap: 12px;
}

.error-actions .ant-btn {
  min-width: 100px;
}

/* 连接状态指示器 */
.connection-status {
  position: fixed;
  top: 80px;
  right: 24px;
  z-index: 100;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: white;
  border-radius: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  font-size: 12px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.connection-status.connected {
  background: #ecfdf5;
  color: #065f46;
  border: 1px solid #a7f3d0;
}

.connection-status.disconnected {
  background: #fef2f2;
  color: #991b1b;
  border: 1px solid #fecaca;
}

.connection-status.connecting {
  background: #fefce8;
  color: #92400e;
  border: 1px solid #fde68a;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.connection-status.disconnected .status-dot {
  animation: none;
}

/* 性能监控指标 */
.performance-metrics {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 100;
  background: white;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  font-size: 11px;
  color: #6b7280;
  max-width: 200px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-top: 8px;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.metric-label {
  font-weight: 500;
}

.metric-value {
  font-weight: 600;
  color: #1f2937;
}

/* 深色模式支持 */
@media (prefers-color-scheme: dark) {
  .main-container {
    /* background:
        radial-gradient(circle at 20% 50%, rgba(59, 130, 246, 0.08) 0%, transparent 50%),
        radial-gradient(circle at 80% 20%, rgba(16, 185, 129, 0.08) 0%, transparent 50%),
        radial-gradient(circle at 40% 80%, rgba(245, 158, 11, 0.08) 0%, transparent 50%),
        linear-gradient(135deg, #0f172a 0%, #1e293b 100%); */
  }

  .loading-content {
    background: #1e293b;
    color: #e2e8f0;
  }

  .error-title {
    color: #f1f5f9;
  }

  .error-message {
    color: #94a3b8;
  }

  .connection-status {
    background: #1e293b;
    color: #e2e8f0;
  }

  .performance-metrics {
    background: #1e293b;
    color: #94a3b8;
  }

  .metric-value {
    color: #f1f5f9;
  }
}

/* AI面板布局样式 */
.ai-panel {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

@media (max-width: 1024px) {
  .ai-panel {
    grid-template-columns: 1fr;
    gap: 16px;
  }
}

.ai-panel {
  display: grid;
  grid-template-columns: minmax(0, 1.65fr) minmax(320px, 0.95fr);
  gap: 16px;
  margin-bottom: 18px;
}

.quality-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.quality-title {
  margin-top: 4px;
  font-size: 16px;
  font-weight: 700;
  color: #183153;
}

.quality-grid {
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.quality-metric {
  padding: 14px;
  border-radius: 14px;
  background: #f7faff;
}

.quality-metric[data-tone='warning'] {
  background: #fff7ed;
}

.quality-metric[data-tone='danger'] {
  background: #fef2f2;
}

.quality-metric[data-tone='success'] {
  background: #ecfdf5;
}

.quality-metric-title,
.quality-metric-hint,
.failure-message,
.failure-empty {
  color: #6a7b92;
}

.quality-metric-title {
  font-size: 12px;
}

.quality-metric-value {
  margin-top: 8px;
  font-size: 24px;
  font-weight: 700;
  color: #10233f;
}

.quality-metric-hint {
  margin-top: 6px;
  font-size: 12px;
}

.failure-list {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.failure-row {
  padding: 14px;
  border-radius: 14px;
  background: #f7faff;
}

.failure-main,
.failure-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: space-between;
}

.failure-name {
  flex: 1;
  color: #183153;
  font-weight: 600;
}

.failure-meta {
  margin-top: 8px;
  color: #b42318;
  font-size: 12px;
}

.failure-message {
  margin-top: 8px;
  line-height: 1.6;
  font-size: 12px;
}

.failure-empty {
  margin-top: 16px;
  font-size: 13px;
}

.report-card-lite {
  margin-top: 16px;
}

.report-lite-grid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.report-lite-item {
  padding: 12px 14px;
  border-radius: 14px;
  background: #f7faff;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.report-lite-item.full {
  grid-column: 1 / -1;
}

.report-lite-label {
  font-size: 12px;
  color: #73839a;
}

.report-lite-value {
  font-size: 14px;
  font-weight: 600;
  color: #183153;
  word-break: break-word;
}

.report-lite-value.danger {
  color: #b42318;
}

.run-history {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid rgba(20, 86, 163, 0.08);
}

.run-history-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.run-history-title {
  font-size: 14px;
  font-weight: 700;
  color: #183153;
}

.run-history-hint {
  font-size: 12px;
  color: #73839a;
}

.run-history-list {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 220px;
  overflow-y: auto;
}

.run-history-item {
  width: 100%;
  border: 1px solid rgba(20, 86, 163, 0.08);
  border-radius: 12px;
  background: #f7faff;
  padding: 10px 12px;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
}

.run-history-item:hover,
.run-history-item.active {
  border-color: rgba(20, 86, 163, 0.3);
  box-shadow: 0 8px 18px rgba(32, 60, 96, 0.08);
}

.run-history-main,
.run-history-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.run-history-id {
  font-size: 13px;
  font-weight: 700;
  color: #183153;
}

.run-history-meta {
  margin-top: 6px;
  color: #5b6b80;
  font-size: 12px;
  flex-wrap: wrap;
}

.run-history-error {
  margin-top: 10px;
  color: #b42318;
  font-size: 12px;
  line-height: 1.6;
}

.endpoint-row {
  padding: 14px;
  border-radius: 14px;
  background: #f7faff;
}

.endpoint-main {
  min-width: 0;
}

.endpoint-name {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  font-weight: 600;
  color: #183153;
}

.endpoint-method {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 48px;
  padding: 2px 8px;
  border-radius: 999px;
  background: #dbeafe;
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 700;
}

.endpoint-hint,
.risk-label {
  font-size: 12px;
  color: #6a7b92;
}

.endpoint-risk {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.risk-value {
  font-size: 20px;
  font-weight: 700;
  color: #b42318;
}

@media (max-width: 1280px) {
  .container-header,
  .main-container {
    padding-left: 5%;
    padding-right: 5%;
  }
}

@media (max-width: 1024px) {
  .container-header {
    height: auto;
    min-height: 64px;
    padding-top: 10px;
    padding-bottom: 10px;
  }

  .operation-container,
  .right-group,
  .header-menu {
    flex-wrap: wrap;
  }

  .main-container {
    margin-top: 88px;
  }

  .ai-panel,
  .ai-grid,
  .quality-panel,
  .chart-strip,
  .report-overview-bottom {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .menu-value {
    max-width: 140px;
  }

  .ai-card,
  .endpoint-card {
    padding: 16px;
  }

  .ai-title {
    font-size: 20px;
  }

  .endpoint-row {
    flex-direction: column;
  }

  .endpoint-risk {
    align-items: flex-start;
  }

  .report-lite-grid {
    grid-template-columns: 1fr;
  }

  .quality-grid {
    grid-template-columns: 1fr;
  }

  .report-overview-head {
    flex-direction: column;
  }

  .report-overview-grid {
    grid-template-columns: 1fr;
  }

  .report-overview-item.wide {
    grid-column: auto;
  }
}
</style>
