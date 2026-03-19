import { computed, ref, type Ref } from "vue";

import { TaskApi } from "@/api/task";
import type { TaskInfo, TaskReportData, TaskRunHistoryItem, TaskRuntimeStatus } from "@/types/task";
import type { MetricHistoryPoint, Metrics, Stats, SystemState } from "@/layout/type.ts";

const defaultMetric: Metrics = {
  stats: [],
  host: "",
  errors: [],
  total_rps: 0,
  total_fail_per_sec: 0,
  fail_ratio: 0,
  state: "missing" as SystemState,
  user_count: 0,
  start_time: "--",
  runtime: "--",
  runtime_seconds: 0,
  status_code_counts: {},
  error_type_counts: {},
  failure_samples: [],
};

const createDefaultTaskInfo = (taskId: number): TaskInfo => ({
  id: taskId,
  name: "未命名任务",
  description: null,
  owner: "",
  owner_id: 0,
  project_id: 0,
  project: "",
  host: "",
  users: 0,
  spawn_rate: 0,
  duration: 0,
  status: "pending",
  start_time: null,
  runtime_seconds: 0,
  runtime: null,
  finished_at: null,
  stats: null,
  scenarios: [],
  created_at: "",
  created_by: 0,
  created_by_name: "",
  updated_at: "",
  updated_by: 0,
  updated_by_name: "",
  is_deleted: false,
  execution_strategy: "default",
});

const buildRuntime = (seconds: number) => {
  const hour = String(Math.floor(seconds / 3600)).padStart(2, "0");
  const minute = String(Math.floor((seconds % 3600) / 60)).padStart(2, "0");
  const second = String(seconds % 60).padStart(2, "0");
  return `${hour}:${minute}:${second}`;
};

const mapTaskStatusToSystemState = (status?: string): SystemState => {
  switch ((status || "").toLowerCase()) {
    case "running":
      return "running";
    case "stopping":
      return "stopping";
    case "pending":
      return "ready";
    case "completed":
    case "canceled":
      return "stopped";
    case "failed":
      return "missing";
    default:
      return "ready";
  }
};

const createAggregateStats = (runtime: TaskRuntimeStatus): Stats[] => {
  const runtimeStats = Array.isArray(runtime.stats) ? (runtime.stats as Stats[]) : [];
  if (runtimeStats.length) {
    return runtimeStats;
  }

  if (!runtime.total_requests && !runtime.current_rps) {
    return [];
  }

  const latestHistory = runtime.history.length ? runtime.history[runtime.history.length - 1] : null;

  return [
    {
      method: "TASK",
      name: runtime.task_name,
      num_requests: runtime.total_requests,
      num_failures: runtime.fail_count,
      min_response_time: runtime.avg_rt,
      max_response_time: runtime.p99,
      current_rps: runtime.current_rps,
      current_fail_per_sec: latestHistory?.fail_count || 0,
      avg_response_time: runtime.avg_rt,
      median_response_time: runtime.avg_rt,
      total_rps: runtime.current_rps,
      total_fail_per_sec: latestHistory?.fail_count || 0,
      avg_content_length: 0,
      "response_time_percentile_0.95": runtime.p95,
      "response_time_percentile_0.99": runtime.p99,
    },
  ];
};

export const useTaskMonitorRuntime = (taskId: Ref<number>) => {
  const loading = ref(false);
  const controlLoading = ref(false);
  const taskRunning = ref(false);
  const taskInfo = ref<TaskInfo>(createDefaultTaskInfo(taskId.value));
  const taskReport = ref<TaskReportData | null>(null);
  const taskRuns = ref<TaskRunHistoryItem[]>([]);
  const selectedTaskRunId = ref<number | null>(null);
  const dataSource = ref<Stats[]>([]);
  const metrics = ref<Metrics>({ ...defaultMetric });
  const metricHistory = ref<MetricHistoryPoint[]>([]);
  const lastReportRefreshAt = ref(0);

  const safeMetrics = computed(() => metrics.value || defaultMetric);
  const safeTaskInfo = computed(() => taskInfo.value || createDefaultTaskInfo(taskId.value));
  const selectedTaskRun = computed(() =>
    taskRuns.value.find((item) => item.id === selectedTaskRunId.value) || null,
  );

  const applyRuntimeStatus = (runtime: TaskRuntimeStatus) => {
    const failRatio = runtime.total_requests ? runtime.fail_count / runtime.total_requests : 0;
    const latestHistory = runtime.history.length ? runtime.history[runtime.history.length - 1] : null;

    taskRunning.value = runtime.status === "running" || runtime.status === "stopping";
    dataSource.value = createAggregateStats(runtime);
    metrics.value = {
      stats: dataSource.value,
      errors: runtime.latest_error ? [{ message: runtime.latest_error }] : [],
      total_rps: runtime.current_rps,
      total_fail_per_sec: latestHistory?.fail_count || 0,
      fail_ratio: Number(failRatio.toFixed(4)),
      state: mapTaskStatusToSystemState(runtime.status),
      user_count: runtime.active_users,
      host: runtime.host || taskInfo.value.host || "",
      start_time: runtime.started_at || "--",
      runtime: buildRuntime(runtime.runtime_seconds || 0),
      runtime_seconds: runtime.runtime_seconds || 0,
      status_code_counts: runtime.status_code_counts || {},
      error_type_counts: runtime.error_type_counts || {},
      failure_samples: runtime.failure_samples || [],
    };
    metricHistory.value = runtime.history.map((item) => ({
      time: buildRuntime(
        Math.max(
          0,
          Math.round((new Date(item.ts).getTime() - new Date(runtime.started_at || item.ts).getTime()) / 1000),
        ),
      ),
      user_count: item.active_users,
      total_rps: item.rps,
      fail_ratio: item.success_count + item.fail_count ? item.fail_count / (item.success_count + item.fail_count) : 0,
      avg_response_time: item.avg_rt,
      p95_response_time: item.p95,
      total_fail_per_sec: item.fail_count,
    }));
  };

  const fetchTaskInfo = async () => {
    const response = await TaskApi.getTaskInfo({ id: taskId.value });
    taskInfo.value = response.data;
  };

  const fetchTaskStatus = async () => {
    const response = await TaskApi.getTaskStatus({ task_id: taskId.value });
    applyRuntimeStatus(response.data);
  };

  const fetchTaskRuns = async () => {
    const response = await TaskApi.getTaskRuns({ task_id: taskId.value });
    taskRuns.value = response.data.runs || [];

    if (!taskRuns.value.length) {
      selectedTaskRunId.value = null;
      return;
    }

    if (!selectedTaskRunId.value || !taskRuns.value.some((item) => item.id === selectedTaskRunId.value)) {
      selectedTaskRunId.value = taskRuns.value[0].id;
    }
  };

  const fetchTaskReport = async () => {
    if (!taskId.value || !selectedTaskRunId.value) {
      taskReport.value = null;
      return;
    }

    const response = await TaskApi.getTaskReport({
      task_id: taskId.value,
      task_run_id: selectedTaskRunId.value,
    });
    taskReport.value = response.data;
  };

  const refreshReportIfNeeded = async (force = false) => {
    const now = Date.now();
    if (!force && now - lastReportRefreshAt.value < 10000) {
      return;
    }

    await fetchTaskReport();
    lastReportRefreshAt.value = now;
  };

  const refreshMonitorData = async () => {
    if (!taskId.value) {
      return;
    }

    loading.value = true;
    try {
      await Promise.all([fetchTaskInfo(), fetchTaskStatus(), fetchTaskRuns()]);
      await fetchTaskReport();
    } finally {
      loading.value = false;
    }
  };

  const resetMonitorState = () => {
    taskInfo.value = createDefaultTaskInfo(taskId.value);
    taskReport.value = null;
    taskRuns.value = [];
    selectedTaskRunId.value = null;
    dataSource.value = [];
    metrics.value = { ...defaultMetric };
    metricHistory.value = [];
    taskRunning.value = false;
    lastReportRefreshAt.value = 0;
  };

  const setControlLoading = (value: boolean) => {
    controlLoading.value = value;
  };

  return {
    loading,
    controlLoading,
    taskRunning,
    taskInfo,
    taskReport,
    taskRuns,
    selectedTaskRunId,
    selectedTaskRun,
    dataSource,
    metrics,
    metricHistory,
    safeMetrics,
    safeTaskInfo,
    fetchTaskInfo,
    fetchTaskStatus,
    fetchTaskRuns,
    fetchTaskReport,
    refreshReportIfNeeded,
    refreshMonitorData,
    resetMonitorState,
    setControlLoading,
  };
};
