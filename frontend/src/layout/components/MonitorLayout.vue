<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { message, Modal } from "ant-design-vue";
import { useRoute, useRouter } from "vue-router";

import MonitorAiPanel from "@/layout/components/MonitorAiPanel.vue";
import MonitorComponent from "@/layout/components/MonitorComponent.vue";
import MonitorControlBar from "@/layout/components/MonitorControlBar.vue";
import MonitorHotEndpoints from "@/layout/components/MonitorHotEndpoints.vue";
import MonitorStatusDisplay from "@/layout/components/MonitorStatusDisplay.vue";
import { TaskApi } from "@/api/task";
import { useTaskMonitorRuntime } from "@/layout/composables/useTaskMonitorRuntime";
import { useTaskMonitorSocket } from "@/layout/composables/useTaskMonitorSocket";
import { useTaskMonitorViewModel } from "@/layout/composables/useTaskMonitorViewModel";

const route = useRoute();
const router = useRouter();
const currentTaskId = ref<number>(Number(route.params.taskId) || 0);

const runtime = useTaskMonitorRuntime(currentTaskId);
const monitorSocket = useTaskMonitorSocket({
  taskId: currentTaskId,
  fetchTaskStatus: runtime.fetchTaskStatus,
  fetchTaskRuns: runtime.fetchTaskRuns,
  refreshReportIfNeeded: runtime.refreshReportIfNeeded,
  onResetSelectionToLatest: () => {
    if (runtime.taskRuns.value.length) {
      runtime.selectedTaskRunId.value = runtime.taskRuns.value[0].id;
    }
  },
});

const viewModel = useTaskMonitorViewModel({
  metrics: runtime.safeMetrics,
  dataSource: computed(() => runtime.dataSource.value),
  history: computed(() => runtime.metricHistory.value),
  taskReport: computed(() => runtime.taskReport.value),
  taskRuns: computed(() => runtime.taskRuns.value),
  selectedTaskRun: runtime.selectedTaskRun,
});

const loading = runtime.loading;
const controlLoading = runtime.controlLoading;
const taskRunning = runtime.taskRunning;
const safeTaskInfo = runtime.safeTaskInfo;
const safeMetrics = runtime.safeMetrics;
const dataSource = runtime.dataSource;
const statCards = viewModel.statCards;
const aiInsight = viewModel.aiInsight;
const hotEndpoints = viewModel.hotEndpoints;
const chartConfigs = viewModel.chartConfigs;
const reportSummary = viewModel.reportSummary;
const endpointSummary = viewModel.endpointSummary;
const errorSummary = viewModel.errorSummary;
const tableColumns = viewModel.tableColumns;
const wsConnected = monitorSocket.wsConnected;

const showEmptyState = computed(() => !currentTaskId.value);

const handleRefreshFailure = () => {
  message.error("任务监控数据刷新失败，请稍后重试");
};

const refreshPageData = async (showError = true) => {
  try {
    await runtime.refreshMonitorData();
  } catch (error) {
    console.error("Failed to refresh monitor page:", error);
    if (showError) {
      handleRefreshFailure();
    }
  }
};

const handleStartTest = () => {
  if (runtime.taskRunning.value) {
    message.warning("任务已经在运行中");
    return;
  }

  Modal.confirm({
    title: "确认开始压测",
    content: "开始后会创建新的运行实例，并自动建立实时监控连接。",
    okText: "开始",
    cancelText: "取消",
    async onOk() {
      runtime.setControlLoading(true);
      try {
        await TaskApi.runTask({ task_id: currentTaskId.value });
        await refreshPageData(false);
        monitorSocket.connectRuntimeSocket();
        message.success("压测任务已启动");
      } finally {
        runtime.setControlLoading(false);
      }
    },
  });
};

const handleStopTest = () => {
  if (runtime.safeMetrics.value.state === "stopping") {
    message.warning("任务正在停止中，请稍候");
    return;
  }
  if (!runtime.taskRunning.value) {
    message.warning("当前没有正在运行的任务");
    return;
  }

  Modal.confirm({
    title: "确认停止压测",
    content: "停止后将向 worker 发送终止指令，任务会先进入“停止中”状态。",
    okText: "停止",
    cancelText: "取消",
    okType: "danger",
    async onOk() {
      runtime.setControlLoading(true);
      try {
        await TaskApi.stopTask({ task_id: currentTaskId.value });
        await refreshPageData(false);
        message.success("已发送停止指令");
      } finally {
        runtime.setControlLoading(false);
      }
    },
  });
};

const handlePauseTest = () => {
  message.info("暂停能力将在后续版本开放");
};

const handleResumeTest = () => {
  message.info("恢复能力将在后续版本开放");
};

onMounted(async () => {
  monitorSocket.connectRuntimeSocket();
  await refreshPageData();
});

watch(
  () => route.params.taskId,
  async (value) => {
    currentTaskId.value = Number(value) || 0;
    monitorSocket.disconnectRuntimeSocket();
    runtime.resetMonitorState();
    monitorSocket.connectRuntimeSocket();
    await refreshPageData(false);
  },
);
</script>

<template>
  <MonitorControlBar
    :taskId="currentTaskId"
    :taskInfo="safeTaskInfo"
    :metrics="safeMetrics"
    :taskRunning="taskRunning"
    :controlLoading="controlLoading"
    :wsConnected="wsConnected"
    @startTest="handleStartTest"
    @stopTest="handleStopTest"
    @pauseTest="handlePauseTest"
    @resumeTest="handleResumeTest"
  />

  <div class="main-container">
    <div v-if="loading" class="loading-panel">
      <div class="loading-spinner"></div>
      <p>正在加载任务监控数据...</p>
    </div>

    <div v-else-if="showEmptyState" class="empty-panel">
      <h2>缺少任务 ID</h2>
      <p>当前没有指定需要监控的任务，请从任务列表重新进入。</p>
      <a-button type="primary" @click="router.push('/task')">返回任务列表</a-button>
    </div>

    <div v-else class="monitor-shell">
      <MonitorStatusDisplay :cards="statCards" />

      <section class="ai-panel">
        <MonitorAiPanel :insight="aiInsight" />
        <MonitorHotEndpoints :endpoints="hotEndpoints" />
      </section>

      <MonitorComponent
        :chartConfigs="chartConfigs"
        :reportSummary="reportSummary"
        :endpointSummary="endpointSummary"
        :errorSummary="errorSummary"
        :tableColumns="tableColumns"
        :dataSource="dataSource"
        :loading="loading"
      />
    </div>
  </div>
</template>

<style scoped>
.main-container {
  margin-top: 88px;
  min-height: 100vh;
  padding: 28px 10% 40px;
  background:
    radial-gradient(circle at top left, rgba(219, 234, 254, 0.95), transparent 28%),
    radial-gradient(circle at top right, rgba(255, 237, 213, 0.82), transparent 24%),
    linear-gradient(180deg, #f8fbff 0%, #eef4fb 100%);
}

.monitor-shell {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.ai-panel {
  display: grid;
  grid-template-columns: minmax(0, 1.65fr) minmax(320px, 0.95fr);
  gap: 16px;
}

.loading-panel,
.empty-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  min-height: 420px;
  padding: 32px;
  border-radius: 24px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
}

.empty-panel h2,
.loading-panel p,
.empty-panel p {
  margin: 0;
}

.empty-panel h2 {
  color: #0f172a;
}

.empty-panel p,
.loading-panel p {
  color: #64748b;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border-radius: 999px;
  border: 3px solid rgba(148, 163, 184, 0.2);
  border-top-color: #2563eb;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 1280px) {
  .main-container {
    padding-left: 5%;
    padding-right: 5%;
  }
}

@media (max-width: 1024px) {
  .main-container {
    margin-top: 112px;
  }

  .ai-panel {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .main-container {
    margin-top: 156px;
    padding: 18px 16px 28px;
  }
}
</style>
