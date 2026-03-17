<script setup lang="ts">
import LogoComponent from "@/layout/components/LogoComponent.vue";
import MonitorComponent from "@/layout/components/MonitorComponent.vue";
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRoute } from "vue-router";
import { MetricHistoryPoint, Metrics, STATE_COLORS, STATE_NAMES, Stats, SystemState } from "@/layout/type.ts";
import { TaskInfoResult } from "@/api/tasks.ts";
import { message, Modal } from "ant-design-vue";
import { formatNumber, formatPercent } from "@/utils/tools";

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
const loading = ref(false);
const controlLoading = ref(false);
const taskRunning = ref(false);
const useMockMode = true;
const currentTaskId = ref<number>(Number(route.params.taskId) || 10001);

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
};

const defaultTaskInfo: TaskInfoResult = {
  task_id: currentTaskId.value,
  task_name: 'PerfLocust Mock 压测任务',
  cases: [],
  run_time: 20,
  users: 420,
  spawn_time: 24,
  host: 'https://mock-api.perflocust.local',
  status: 'running'
};

const taskInfo = ref<TaskInfoResult>({ ...defaultTaskInfo });
const dataSource = ref<Stats[]>([]);
const metrics = ref<Metrics>({ ...defaultMetric });
const metricHistory = ref<MetricHistoryPoint[]>([]);
const mockTick = ref(0);

let mockTimer: ReturnType<typeof setInterval> | null = null;

const safeMetrics = computed(() => metrics.value || defaultMetric);
const safeTaskInfo = computed(() => taskInfo.value || defaultTaskInfo);

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
      actions: ['确认压测已启动，或保持当前 Mock 演示流继续输出。'],
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

const mockEndpointSeeds = [
  { method: 'GET', name: '/api/home/banner', baseRps: 220, baseRt: 82, failBase: 0.003, bytes: 1280 },
  { method: 'POST', name: '/api/user/login', baseRps: 160, baseRt: 128, failBase: 0.008, bytes: 860 },
  { method: 'GET', name: '/api/product/search', baseRps: 310, baseRt: 168, failBase: 0.012, bytes: 2340 },
  { method: 'POST', name: '/api/order/submit', baseRps: 104, baseRt: 260, failBase: 0.018, bytes: 1120 },
  { method: 'GET', name: '/api/payment/query', baseRps: 92, baseRt: 188, failBase: 0.01, bytes: 920 }
];

const createMockStats = (tick: number, users: number): Stats[] => {
  const pressure = Math.min(users / 450, 1.2);
  const drift = 1 + Math.sin(tick / 4) * 0.08;
  const riskBoost = tick > 10 ? Math.min((tick - 10) * 0.015, 0.16) : 0;

  return mockEndpointSeeds.map((item, index) => {
    const endpointPulse = 1 + Math.sin(tick / 3 + index) * 0.14;
    const rtBoost = index === 1 || index === 3 ? 1 + riskBoost : 1;
    const currentRps = Number((item.baseRps * pressure * drift * endpointPulse).toFixed(2));
    const avgResponseTime = Number((item.baseRt * (1 + pressure * 0.35) * rtBoost * endpointPulse).toFixed(2));
    const p95 = Number((avgResponseTime * (1.35 + riskBoost)).toFixed(2));
    const p99 = Number((p95 * 1.18).toFixed(2));
    const failPerSec = Number((currentRps * (item.failBase + riskBoost * (index === 1 || index === 3 ? 0.6 : 0.2))).toFixed(2));
    const requestCount = Math.round(currentRps * Math.max(tick * 6, 8));
    const failCount = Math.round(failPerSec * Math.max(tick * 4, 6));

    return {
      method: item.method,
      name: item.name,
      num_requests: requestCount,
      num_failures: failCount,
      min_response_time: Number((avgResponseTime * 0.62).toFixed(2)),
      max_response_time: Number((p99 * 1.2).toFixed(2)),
      current_rps: currentRps,
      current_fail_per_sec: failPerSec,
      avg_response_time: avgResponseTime,
      median_response_time: Number((avgResponseTime * 0.9).toFixed(2)),
      total_rps: 0,
      total_fail_per_sec: 0,
      avg_content_length: item.bytes,
      "response_time_percentile_0.95": p95,
      "response_time_percentile_0.99": p99
    } as Stats;
  });
};

const applyMockSnapshot = () => {
  mockTick.value += 1;

  const runtimeSeconds = mockTick.value * 12;
  const users = Math.min(120 + mockTick.value * 18, safeTaskInfo.value.users);
  const stats = createMockStats(mockTick.value, users);
  const totalRps = stats.reduce((sum, item) => sum + item.current_rps, 0);
  const totalFailPerSec = stats.reduce((sum, item) => sum + item.current_fail_per_sec, 0);
  const totalRequests = stats.reduce((sum, item) => sum + item.num_requests, 0);
  const totalFailures = stats.reduce((sum, item) => sum + item.num_failures, 0);
  const failRatio = totalRequests > 0 ? totalFailures / totalRequests : 0;

  dataSource.value = stats;
  metrics.value = {
    ...defaultMetric,
    stats,
    errors: failRatio > 0.03 ? [{ endpoint: '/api/order/submit', code: 504 }] : [],
    total_rps: Number(totalRps.toFixed(2)),
    total_fail_per_sec: Number(totalFailPerSec.toFixed(2)),
    fail_ratio: Number(failRatio.toFixed(4)),
    state: taskRunning.value ? 'running' : 'ready',
    user_count: users,
    host: safeTaskInfo.value.host,
    start_time: '2026-03-16 15:30:00',
    runtime: buildRuntime(runtimeSeconds),
    runtime_seconds: runtimeSeconds
  };

  metricHistory.value = [
    ...metricHistory.value.slice(-23),
    {
      time: buildRuntime(runtimeSeconds),
      user_count: users,
      total_rps: Number(totalRps.toFixed(2)),
      fail_ratio: Number(failRatio.toFixed(4)),
      avg_response_time: Number((stats.reduce((sum, item) => sum + item.avg_response_time, 0) / stats.length).toFixed(2)),
      p95_response_time: Number((Math.max(...stats.map((item) => item["response_time_percentile_0.95"] ?? 0))).toFixed(2)),
      total_fail_per_sec: Number(totalFailPerSec.toFixed(2)),
    }
  ];
};

const startMockStream = () => {
  taskRunning.value = true;
  applyMockSnapshot();

  if (mockTimer) {
    clearInterval(mockTimer);
  }

  mockTimer = setInterval(() => {
    if (taskRunning.value) {
      applyMockSnapshot();
    }
  }, 2500);
};

const stopMockStream = () => {
  taskRunning.value = false;

  if (mockTimer) {
    clearInterval(mockTimer);
    mockTimer = null;
  }

  metricHistory.value = [...metricHistory.value];

  metrics.value = {
    ...metrics.value,
    state: 'stopped',
  };
};

const handleStartTest = () => {
  if (taskRunning.value) {
    message.warning("任务已在运行中");
    return;
  }

  Modal.confirm({
    title: '确认开始压测',
    content: useMockMode ? '将启动 Mock 监控流用于页面展示。' : '确定要开始性能测试吗？',
    okText: '确定',
    cancelText: '取消',
    onOk() {
      controlLoading.value = true;

      if (useMockMode) {
        startMockStream();
      }

      setTimeout(() => {
        controlLoading.value = false;
      }, 600);
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
    content: useMockMode ? '将停止当前 Mock 监控流。' : '确定要停止性能测试吗？',
    okText: '确定',
    cancelText: '取消',
    okType: 'danger',
    onOk() {
      controlLoading.value = true;

      if (useMockMode) {
        stopMockStream();
      }

      setTimeout(() => {
        controlLoading.value = false;
      }, 600);
    }
  });
};

const handlePauseTest = () => {
  if (!taskRunning.value) {
    message.warning("任务未在运行中");
    return;
  }

  taskRunning.value = false;
  metrics.value = {
    ...metrics.value,
    state: 'cleanup'
  };
  message.success(useMockMode ? "Mock 监控流已暂停" : "已发送负载调整命令");
};

const handleResumeTest = () => {
  if (taskRunning.value) {
    return;
  }

  if (useMockMode) {
    startMockStream();
    message.success("Mock 监控流已恢复");
  }
};

onMounted(() => {
  if (useMockMode) {
    taskInfo.value = { ...defaultTaskInfo };
    startMockStream();
  }
});

onUnmounted(() => {
  if (mockTimer) {
    clearInterval(mockTimer);
  }
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
            <span class="menu-value">{{ safeTaskInfo.task_name }}</span>
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
            <span class="menu-value">{{ safeMetrics.start_time }}</span>
          </div>
          <div class="menu-divider"></div>
          <div class="menu">
            <span class="menu-label">运行时间</span>
            <span class="menu-value">{{ safeMetrics.runtime }}</span>
          </div>
        </div>
        <div class="header-user">
          <a-tag color="processing" v-if="useMockMode">MOCK</a-tag>
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

.ai-card,
.endpoint-card {
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
  .ai-grid {
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
}
</style>
