<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { message, Modal } from "ant-design-vue";
import { useRoute, useRouter } from "vue-router";

import MonitorAiPanel from "@/layout/components/MonitorAiPanel.vue";
import MonitorComponent from "@/layout/components/MonitorComponent.vue";
import MonitorControlBar from "@/layout/components/MonitorControlBar.vue";
import MonitorHotEndpoints from "@/layout/components/MonitorHotEndpoints.vue";
import MonitorPerformanceDock from "@/layout/components/MonitorPerformanceDock.vue";
import MonitorStatusDisplay from "@/layout/components/MonitorStatusDisplay.vue";
import MonitorTaskInfoPanel from "@/layout/components/MonitorTaskInfoPanel.vue";
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
const workerSnapshot = runtime.workerSnapshot;
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

const refreshPageData = async (showError = true) => {
  try {
    await runtime.refreshMonitorData();
  } catch (error) {
    console.error("Failed to refresh monitor page:", error);
    if (showError) {
      message.error("任务监控数据加载失败，请稍后重试。");
    }
  }
};

const handleStartTest = () => {
  if (runtime.taskRunning.value) {
    message.warning("任务已经在运行中。");
    return;
  }

  Modal.confirm({
    title: "确认开始任务？",
    content: "开始后会按当前配置向目标主机发起压测，请确认场景和并发参数已经准备妥当。",
    okText: "开始任务",
    cancelText: "取消",
    async onOk() {
      runtime.setControlLoading(true);
      try {
        await TaskApi.runTask({ task_id: currentTaskId.value });
        await refreshPageData(false);
        monitorSocket.connectRuntimeSocket();
        message.success("任务已开始执行。");
      } finally {
        runtime.setControlLoading(false);
      }
    },
  });
};

const handleStopTest = () => {
  if (runtime.safeMetrics.value.state === "stopping") {
    message.warning("任务正在停止中，请稍候。");
    return;
  }
  if (!runtime.taskRunning.value) {
    message.warning("当前没有正在运行的任务。");
    return;
  }

  Modal.confirm({
    title: "确认停止任务？",
    content: "停止命令会通知 worker 结束当前运行，任务状态会先进入“正在停止”，随后再更新为已结束。",
    okText: "停止任务",
    cancelText: "取消",
    okType: "danger",
    async onOk() {
      runtime.setControlLoading(true);
      try {
        await TaskApi.stopTask({ task_id: currentTaskId.value });
        await refreshPageData(false);
        message.success("已发送停止命令。");
      } finally {
        runtime.setControlLoading(false);
      }
    },
  });
};

const handlePauseTest = () => {
  message.info("暂停功能暂未接入。");
};

const handleResumeTest = () => {
  message.info("恢复功能暂未接入。");
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

  <div class="workspace-shell">
    <div v-if="loading" class="state-panel">
      <div class="loading-spinner"></div>
      <p>正在加载任务监控数据...</p>
    </div>

    <div v-else-if="showEmptyState" class="state-panel">
      <h2>缺少任务 ID</h2>
      <p>当前没有可加载的任务，请从任务列表进入具体任务后再查看监控页。</p>
      <a-button type="primary" @click="router.push('/task')">返回任务列表</a-button>
    </div>

    <div v-else class="workspace-grid">
      <MonitorTaskInfoPanel :taskInfo="safeTaskInfo" :metrics="safeMetrics" />

      <main class="workspace-main">
        <MonitorStatusDisplay :cards="statCards" />

        <section class="insight-grid">
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
      </main>
    </div>
  </div>

  <MonitorPerformanceDock
    :taskInfo="safeTaskInfo"
    :metrics="safeMetrics"
    :workerSnapshot="workerSnapshot"
    :wsConnected="wsConnected"
  />
</template>

<style scoped>
.workspace-shell {
  min-height: 100vh;
  padding: 84px 28px 104px;
  background:
    radial-gradient(circle at top left, rgba(219, 234, 254, 0.95), transparent 28%),
    radial-gradient(circle at top right, rgba(255, 237, 213, 0.82), transparent 24%),
    linear-gradient(180deg, #f8fbff 0%, #eef4fb 100%);
}

.workspace-grid {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 20px;
  align-items: start;
}

.workspace-main {
  display: flex;
  flex-direction: column;
  gap: 18px;
  min-width: 0;
}

.insight-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.65fr) minmax(320px, 0.95fr);
  gap: 16px;
}

.state-panel {
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

.state-panel h2,
.state-panel p {
  margin: 0;
}

.state-panel h2 {
  color: #0f172a;
}

.state-panel p {
  color: #64748b;
}

.loading-spinner {
  width: 38px;
  height: 38px;
  border-radius: 999px;
  border: 3px solid rgba(37, 99, 235, 0.15);
  border-top-color: #2563eb;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
