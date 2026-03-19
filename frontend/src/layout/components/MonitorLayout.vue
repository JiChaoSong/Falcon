<script setup lang="ts">
import LogoComponent from "@/layout/components/LogoComponent.vue";
import MonitorComponent from "@/layout/components/MonitorComponent.vue";
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
};

const taskInfo = ref<TaskInfo>({ ...defaultTaskInfo });
const taskReport = ref<TaskReportData | null>(null);
const taskRuns = ref<TaskRunHistoryItem[]>([]);
const selectedTaskRunId = ref<number | null>(null);
const dataSource = ref<Stats[]>([]);
const metrics = ref<Metrics>({ ...defaultMetric });
const metricHistory = ref<MetricHistoryPoint[]>([]);
let lastReportRefreshAt = 0;

const safeMetrics = computed(() => metrics.value || defaultMetric);
const safeTaskInfo = computed(() => taskInfo.value || defaultTaskInfo);
const safeTaskReport = computed(() => taskReport.value);
const selectedTaskRun = computed(() =>
  taskRuns.value.find(item => item.id === selectedTaskRunId.value) || null
);

const aiInsightToneMap: Record<MonitorRiskLevel, { text: string; color: string }> = {
  success: { text: '稳定', color: 'green' },
  warning: { text: '关注', color: 'orange' },
  danger: { text: '风险', color: 'red' }
};

const aiInsight = computed<AiInsight>(() => {
  const runtimeSeconds = safeMetrics.value.runtime_seconds;
  const stats = dataSource.value;
  const failRatio = safeMetrics.value.fail_ratio;
  const totalRps = safeMetrics.value.total_rps;
  const hotspot = [...stats]
      .sort((a, b) => (b.current_fail_per_sec + b.avg_response_time / 1000) - (a.current_fail_per_sec + a.avg_response_time / 1000))[0];
  const p95 = hotspot?.["response_time_percentile_0.95"] ?? 0;

  if (!stats.length) {
    return {
      title: '等待监控数据',
      summary: '当前还没有收到压测指标，AI 将在数据进入后给出实时判断。',
      level: 'warning',
      reasons: ['指标流为空，暂时无法判断系统瓶颈。'],
      actions: ['确认任务已启动，并检查任务配置和目标服务是否可达。'],
      confidence: 0.42
    };
  }

  if (failRatio >= 0.05 || p95 >= 800) {
    return {
      title: '接口延迟与失败率正在放大',
      summary: `${hotspot?.name || '核心接口'} 已成为热点风险点，P95 ${formatNumber(p95)}ms，失败率 ${formatPercent(failRatio)}。`,
      level: 'danger',
      reasons: [
        `总失败率已达到 ${formatPercent(failRatio)}，超过常见压测告警阈值。`,
        `${hotspot?.name || '热点接口'} 当前失败 ${hotspot?.current_fail_per_sec?.toFixed(2) || '0.00'}/s。`,
        `并发用户 ${safeMetrics.value.user_count} 下，整体吞吐 ${formatNumber(totalRps)} RPS 出现波动。`
      ],
      actions: [
        '优先检查热点接口对应的数据库连接池、缓存命中率和下游超时。',
        '下一轮建议降低爬升速率，做 70% 到 100% 目标并发的阶梯压测。',
        '如果这是验收场景，可先基于 P95 和失败率设置自动止损。'
      ],
      confidence: 0.91
    };
  }

  if (failRatio >= 0.02 || p95 >= 500 || runtimeSeconds < 180) {
    return {
      title: '系统整体可用，但进入观测区间',
      summary: `当前吞吐 ${formatNumber(totalRps)} RPS，热点接口 ${hotspot?.name || '未知'} 的 P95 为 ${formatNumber(p95)}ms。`,
      level: 'warning',
      reasons: [
        `任务已运行 ${safeMetrics.value.runtime}，仍处于负载爬升后的敏感窗口。`,
        `热点接口平均响应 ${formatNumber(hotspot?.avg_response_time)}ms，建议持续观察尾延迟。`,
        `失败率 ${formatPercent(failRatio)}，尚未失控但已有抬头迹象。`
      ],
      actions: [
        '继续观测 3 到 5 分钟，确认指标是否稳定收敛。',
        '补充慢接口明细和错误码分布，便于区分容量问题与业务异常。',
        '下一步可以联动日志或 APM，做接口级根因定位。'
      ],
      confidence: 0.78
    };
  }

  return {
    title: '压测状态稳定，当前无明显风险',
    summary: `并发 ${safeMetrics.value.user_count} 下系统保持稳定，当前总吞吐 ${formatNumber(totalRps)} RPS。`,
    level: 'success',
    reasons: [
      `总失败率维持在 ${formatPercent(failRatio)}。`,
      `热点接口 ${hotspot?.name || '未知'} 的 P95 为 ${formatNumber(p95)}ms，仍在可控范围内。`,
      `任务已运行 ${safeMetrics.value.runtime}，指标曲线没有明显失真。`
    ],
    actions: [
      '可以逐步继续加压，验证系统容量上限。',
      '建议在任务结束后自动输出一份 AI 复盘报告。',
      '如果这是基线压测，可将当前结果沉淀为容量基准。'
    ],
    confidence: 0.86
  };
});

const hotEndpoints = computed(() => {
  return [...dataSource.value]
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
    case 'pending':
      return 'ready';
    case 'completed':
      return 'stopped';
    case 'canceled':
      return 'stopping';
    case 'failed':
      return 'missing';
    default:
      return 'ready';
  }
};

const createAggregateStats = (runtime: TaskRuntimeStatus): Stats[] => {
  const runtimeStats = Array.isArray(runtime.stats)
    ? runtime.stats as Stats[]
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

  taskRunning.value = runtime.status === 'running';
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

    if (payload.event === 'started' || payload.event === 'finished' || payload.event === 'failed') {
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
    taskRuntimeSocket.disconnect();
    connectRuntimeSocket();
  }
);

onUnmounted(() => {
  taskRuntimeSocket.disconnect();
});
</script>

<template>
  <div class="container-header">
    <LogoComponent />
    <div class="operation-container">
      <div class="spacer"></div>
      <div class="right-group">
        <div class="header-menu">
          <div class="menu">
            <span class="menu-label">任务ID</span>
            <span class="menu-value">{{ currentTaskId }}</span>
          </div>
          <div class="menu-divider"></div>
          <div class="menu">
            <span class="menu-label">任务名称</span>
            <span class="menu-value">{{ safeTaskInfo.name }}</span>
          </div>
          <div class="menu-divider"></div>
          <div class="menu">
            <span class="menu-label">目标主机</span>
            <span class="menu-value">{{ safeTaskInfo.host }}</span>
          </div>
          <div class="menu-divider"></div>
          <div class="menu">
            <span class="menu-label">状态</span>
            <a-tag :color="getStatusColor(safeMetrics.state)">
              {{ getStatusName(safeMetrics.state) }}
            </a-tag>
          </div>
          <div class="menu-divider"></div>
          <div class="menu">
            <span class="menu-label">开始时间</span>
            <span class="menu-value">{{ formatDateTime(safeMetrics.start_time) }}</span>
          </div>
          <div class="menu-divider"></div>
          <div class="menu">
            <span class="menu-label">运行时间</span>
            <span class="menu-value">{{ safeMetrics.runtime }}</span>
          </div>
        </div>
        <div class="header-user">
          <a-button
              type="primary"
              @click="handleStartTest"
              :loading="controlLoading"
              :disabled="taskRunning"
          >
            开始压测
          </a-button>
          <a-button
              type="primary"
              danger
              @click="handleStopTest"
              :loading="controlLoading"
              :disabled="!taskRunning"
          >
            停止
          </a-button>
          <warning-button class="warning-btn" @click="handlePauseTest" :disabled="!taskRunning">
            暂停
          </warning-button>
          <a-button @click="handleResumeTest" :disabled="taskRunning">
            恢复
          </a-button>
        </div>
      </div>
    </div>
  </div>

  <div class="main-container">
    <section class="ai-panel">
      <div class="ai-card">
        <div class="ai-card-head">
          <div>
            <div class="ai-eyebrow">AI 实时分析</div>
            <h2 class="ai-title">{{ aiInsight.title }}</h2>
          </div>
          <div class="ai-meta">
            <a-tag :color="aiInsightToneMap[aiInsight.level].color">
              {{ aiInsightToneMap[aiInsight.level].text }}
            </a-tag>
            <span class="ai-confidence">置信度 {{ Math.round(aiInsight.confidence * 100) }}%</span>
          </div>
        </div>

        <p class="ai-summary">{{ aiInsight.summary }}</p>

        <div class="ai-grid">
          <div class="ai-section">
            <div class="ai-section-title">判断依据</div>
            <ul class="ai-list">
              <li v-for="reason in aiInsight.reasons" :key="reason">{{ reason }}</li>
            </ul>
          </div>

          <div class="ai-section">
            <div class="ai-section-title">建议动作</div>
            <ul class="ai-list">
              <li v-for="action in aiInsight.actions" :key="action">{{ action }}</li>
            </ul>
          </div>
        </div>
      </div>

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

    </section>

    <MonitorComponent
        :dataSource="dataSource"
        :metrics="safeMetrics"
        :history="metricHistory"
        :loading="loading"
    />
  </div>
</template>

<style scoped>
.container-header {
  position: fixed;
  top: 0;
  left: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 10%;
  height: 64px;
  border-bottom: 1px solid #e8e8e8;
  background: #fff;
  width: 100%;
  box-sizing: border-box;
}

.main-container {
  margin-top: 64px;
  flex: 1;
  padding: 18px 10% 28px;
  background:
      radial-gradient(circle at top left, rgba(236, 244, 255, 0.95), transparent 32%),
      linear-gradient(180deg, #f7f9fc 0%, #f2f5f9 100%);
  overflow-y: auto;
  min-height: 100vh;
}

.operation-container {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  width: 100%;
  gap: 16px;
}

.right-group {
  display: flex;
  align-items: center;
  gap: 24px;
}

.header-menu {
  display: flex;
  align-items: center;
  gap: 0 16px;
}

.menu {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  height: 100%;
  min-width: 80px;
}

.menu-label {
  font-size: 12px;
  color: #8c8c8c;
  line-height: 1.2;
  margin-bottom: 4px;
}

.menu-value {
  font-size: 14px;
  color: #262626;
  font-weight: 500;
  line-height: 1.2;
  text-align: left;
  word-break: break-word;
  max-width: 220px;
}

.menu-divider {
  margin: 0;
  flex-shrink: 0;
  border-width: 0 thin 0 0;
  border-style: solid;
  border-color: rgba(0, 0, 0, 0.12);
  align-self: stretch;
  height: auto;
}

.header-user {
  display: flex;
  align-items: center;
  gap: 8px;
}

.ai-panel {
  display: grid;
  grid-template-columns: minmax(0, 1.65fr) minmax(320px, 0.95fr);
  gap: 16px;
  margin-bottom: 18px;
}

.quality-panel,
.chart-strip,
.report-overview {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 18px;
}

.report-overview {
  grid-template-columns: 1fr;
}

.ai-card,
.endpoint-card,
.quality-card {
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(20, 86, 163, 0.08);
  border-radius: 18px;
  box-shadow: 0 12px 32px rgba(32, 60, 96, 0.08);
  backdrop-filter: blur(10px);
}

.ai-card {
  padding: 20px 22px;
}

.endpoint-card {
  padding: 18px;
}

.quality-card {
  padding: 18px;
}

.report-overview-card {
  padding: 20px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(20, 86, 163, 0.08);
  border-radius: 18px;
  box-shadow: 0 12px 32px rgba(32, 60, 96, 0.08);
}

.report-overview-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.report-overview-title {
  margin-top: 4px;
  font-size: 20px;
  font-weight: 700;
  color: #10233f;
}

.report-overview-subtitle {
  margin-top: 6px;
  color: #6a7b92;
  font-size: 13px;
}

.report-overview-grid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.report-overview-item {
  padding: 14px 16px;
  border-radius: 14px;
  background: #f7faff;
}

.report-overview-item.wide {
  grid-column: span 2;
}

.report-overview-label,
.report-bottom-empty {
  color: #73839a;
}

.report-overview-label {
  display: block;
  font-size: 12px;
}

.report-overview-value {
  display: block;
  margin-top: 6px;
  font-size: 16px;
  font-weight: 700;
  color: #183153;
}

.report-overview-value.danger {
  color: #b42318;
}

.report-overview-bottom {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.report-bottom-panel {
  padding: 16px;
  border-radius: 16px;
  background: linear-gradient(180deg, #fbfdff 0%, #f5f9ff 100%);
  border: 1px solid rgba(20, 86, 163, 0.08);
}

.report-bottom-title {
  font-size: 14px;
  font-weight: 700;
  color: #183153;
}

.report-bottom-list {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.report-bottom-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-size: 13px;
  color: #4a5c76;
}

.report-bottom-row-stack {
  align-items: flex-start;
  flex-direction: column;
}

.report-bottom-strong {
  color: #10233f;
  font-weight: 600;
}

.report-bottom-empty {
  margin-top: 12px;
  font-size: 13px;
}

.ai-card-head,
.endpoint-head,
.endpoint-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.ai-eyebrow {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: #6b7a90;
  text-transform: uppercase;
}

.ai-title {
  margin: 6px 0 0;
  font-size: 24px;
  line-height: 1.2;
  color: #10233f;
}

.ai-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  white-space: nowrap;
}

.ai-confidence {
  font-size: 13px;
  color: #5b6b80;
}

.ai-summary {
  margin: 14px 0 18px;
  font-size: 15px;
  line-height: 1.7;
  color: #31445f;
}

.ai-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.ai-section {
  padding: 14px 16px;
  border-radius: 14px;
  background: linear-gradient(180deg, #f8fbff 0%, #f3f7fd 100%);
}

.ai-section-title {
  margin-bottom: 10px;
  font-size: 14px;
  font-weight: 700;
  color: #183153;
}

.ai-list {
  margin: 0;
  padding-left: 18px;
  color: #4a5c76;
  line-height: 1.7;
}

.endpoint-subtitle {
  font-size: 13px;
  color: #73839a;
}

.endpoint-list {
  margin-top: 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
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
