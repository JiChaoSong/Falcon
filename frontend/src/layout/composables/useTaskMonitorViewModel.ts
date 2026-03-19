import { computed, type ComputedRef } from "vue";

import { formatNumber, formatNumberWithCommas, formatPercent } from "@/utils/tools";
import { STATE_NAMES, type MetricHistoryPoint, type Metrics, type Stats } from "@/layout/type.ts";
import type { TaskReportData, TaskRunHistoryItem } from "@/types/task";

export interface MonitorStatCard {
  label: string;
  value: string;
  foot: string;
  tone: "primary" | "success" | "warning" | "danger" | "default" | "muted";
}

export interface MonitorInsight {
  title: string;
  summary: string;
  level: "success" | "warning" | "danger";
  reasons: string[];
  actions: string[];
  confidence: number;
}

export interface HotEndpointItem extends Stats {
  p95: number;
}

export interface MonitorChartConfig {
  key: string;
  title: string;
  subtitle: string;
  legend: string[];
  values: number[];
  labels: string[];
  stroke: string;
  fill: string;
  compareValues?: number[];
  compareStroke?: string;
}

const formatTime = (time?: number): string => {
  if (time === undefined || time === null) {
    return "--";
  }
  if (time < 1000) {
    return `${time.toFixed(2)} ms`;
  }
  return `${(time / 1000).toFixed(2)} s`;
};

export const useTaskMonitorViewModel = (options: {
  metrics: ComputedRef<Metrics>;
  dataSource: ComputedRef<Stats[]>;
  history: ComputedRef<MetricHistoryPoint[]>;
  taskReport: ComputedRef<TaskReportData | null>;
  taskRuns: ComputedRef<TaskRunHistoryItem[]>;
  selectedTaskRun: ComputedRef<TaskRunHistoryItem | null>;
}) => {
  const statCards = computed<MonitorStatCard[]>(() => {
    const metrics = options.metrics.value;
    const stats = options.dataSource.value;
    const totalRequests = stats.reduce((sum, stat) => sum + stat.num_requests, 0);
    const totalFailures = stats.reduce((sum, stat) => sum + stat.num_failures, 0);
    const avgRt = stats.length ? stats.reduce((sum, stat) => sum + stat.avg_response_time, 0) / stats.length : 0;
    const aggregateP95 = stats.length ? Math.max(...stats.map((item) => item["response_time_percentile_0.95"] ?? 0)) : 0;

    return [
      { label: "在线用户", value: String(metrics.user_count || 0), foot: "当前活跃压测用户", tone: "primary" },
      { label: "当前吞吐", value: `${formatNumber(metrics.total_rps)} RPS`, foot: "任务实时请求速率", tone: "success" },
      { label: "总请求数", value: formatNumberWithCommas(totalRequests), foot: "本次运行累计请求", tone: "default" },
      { label: "总失败数", value: formatNumberWithCommas(totalFailures), foot: "累计失败请求数量", tone: "danger" },
      { label: "失败率", value: formatPercent(metrics.fail_ratio), foot: "失败请求占比", tone: "danger" },
      { label: "平均响应时间", value: formatTime(avgRt), foot: "接口平均响应时间", tone: "default" },
      { label: "P95 响应时间", value: formatTime(aggregateP95), foot: "95 分位尾延迟", tone: "warning" },
      { label: "运行时长", value: metrics.runtime || "--", foot: "当前运行累计时长", tone: "default" },
    ];
  });

  const hotEndpoints = computed<HotEndpointItem[]>(() => {
    return [...options.dataSource.value]
      .sort((a, b) => {
        const aScore = a.current_fail_per_sec * 100 + a.avg_response_time;
        const bScore = b.current_fail_per_sec * 100 + b.avg_response_time;
        return bScore - aScore;
      })
      .slice(0, 3)
      .map((item) => ({
        ...item,
        p95: item["response_time_percentile_0.95"] ?? 0,
      }));
  });

  const aiInsight = computed<MonitorInsight>(() => {
    const runtimeSeconds = options.metrics.value.runtime_seconds;
    const stats = options.dataSource.value;
    const failRatio = options.metrics.value.fail_ratio;
    const totalRps = options.metrics.value.total_rps;
    const hotspot = hotEndpoints.value[0];
    const p95 = hotspot?.p95 ?? 0;

    if (!stats.length) {
      return {
        title: "等待实时数据",
        summary: "任务已进入监控页，但暂时还没有收到足够的运行指标。通常出现在刚启动、任务未真正施压，或当前没有活跃请求的时候。",
        level: "warning",
        reasons: ["还没有形成可分析的请求样本，图表和热点接口会先保持空态。"],
        actions: ["先确认任务是否已经开始压测，再观察 10 到 20 秒后的实时指标变化。"],
        confidence: 0.42,
      };
    }

    if (failRatio >= 0.05 || p95 >= 800) {
      return {
        title: "存在明显性能风险",
        summary: `${hotspot?.name || "热点接口"} 当前已出现较高失败或明显尾延迟，P95 达到 ${formatNumber(p95)} ms，整体失败率为 ${(failRatio * 100).toFixed(1)}%。`,
        level: "danger",
        reasons: [
          `当前失败率已升至 ${(failRatio * 100).toFixed(1)}%，说明服务端错误、超时或依赖链路抖动正在放大。`,
          `${hotspot?.name || "热点接口"} 的失败速率达到 ${hotspot?.current_fail_per_sec?.toFixed(2) || "0.00"}/s，是当前最需要关注的接口。`,
          `当前在线用户 ${options.metrics.value.user_count}，吞吐 ${formatNumber(totalRps)} RPS，系统已经进入稳定施压阶段。`,
        ],
        actions: [
          "优先查看热点接口的错误日志、超时链路和下游依赖表现。",
          "如果失败率仍持续上升，建议先降低加压速度，避免异常放大。",
          "重点核对 P95、P99 以及失败样本，确认问题集中在少数接口还是整体退化。",
        ],
        confidence: 0.91,
      };
    }

    if (failRatio >= 0.02 || p95 >= 500 || runtimeSeconds < 180) {
      return {
        title: "进入观察区间",
        summary: `当前吞吐 ${formatNumber(totalRps)} RPS，热点接口为 ${hotspot?.name || "-"}，P95 为 ${formatNumber(p95)} ms，建议继续观察一段时间。`,
        level: "warning",
        reasons: [
          `任务运行时长为 ${options.metrics.value.runtime}，当前仍可能处于升压或刚进入稳定阶段。`,
          `${hotspot?.name || "热点接口"} 的平均响应时间为 ${formatNumber(hotspot?.avg_response_time || 0)} ms，需要持续跟踪是否继续抬升。`,
          `整体失败率为 ${(failRatio * 100).toFixed(1)}%，还未到明显异常，但已经有波动迹象。`,
        ],
        actions: [
          "继续观察接下来 3 到 5 分钟内的趋势图，确认是否只是短时抖动。",
          "对热点接口做分链路排查，特别是数据库、缓存和三方依赖。",
          "如果尾延迟继续上升，提前准备一轮限流或扩容预案。",
        ],
        confidence: 0.78,
      };
    }

    return {
      title: "运行状态稳定",
      summary: `当前在线用户 ${options.metrics.value.user_count}，实时吞吐 ${formatNumber(totalRps)} RPS，整体失败率和尾延迟都处于可接受范围内。`,
      level: "success",
      reasons: [
        `当前失败率仅为 ${(failRatio * 100).toFixed(1)}%。`,
        `${hotspot?.name || "热点接口"} 的 P95 为 ${formatNumber(p95)} ms，暂未出现明显尾延迟放大。`,
        `任务已持续运行 ${options.metrics.value.runtime}，整体曲线保持平稳。`,
      ],
      actions: [
        "继续观察后续几轮采样，确认稳定状态能够持续保持。",
        "保留本次运行结果，作为后续回归压测的基线参考。",
        "如果准备继续加压，可以逐步提高并发，观察转折点出现的位置。",
      ],
      confidence: 0.86,
    };
  });

  const chartConfigs = computed<MonitorChartConfig[]>(() => {
    const history = options.history.value;
    return [
      {
        key: "rps",
        title: "吞吐趋势",
        subtitle: "按时间观察实时请求速率",
        legend: ["请求数/秒"],
        values: history.map((item) => item.total_rps),
        labels: history.map((item) => item.time),
        stroke: "#2563eb",
        fill: "rgba(37, 99, 235, 0.12)",
      },
      {
        key: "users",
        title: "在线用户趋势",
        subtitle: "当前活跃压测用户变化",
        legend: ["在线用户"],
        values: history.map((item) => item.user_count),
        labels: history.map((item) => item.time),
        stroke: "#0f766e",
        fill: "rgba(15, 118, 110, 0.12)",
      },
      {
        key: "response-time",
        title: "响应时间趋势",
        subtitle: "平均响应时间与 P95 变化",
        legend: ["平均响应时间", "P95 响应时间"],
        values: history.map((item) => item.avg_response_time),
        compareValues: history.map((item) => item.p95_response_time),
        labels: history.map((item) => item.time),
        stroke: "#f59e0b",
        fill: "rgba(245, 158, 11, 0.14)",
        compareStroke: "#dc2626",
      },
      {
        key: "failures",
        title: "失败趋势",
        subtitle: "失败率与失败次数/秒",
        legend: ["失败率", "失败次数/秒"],
        values: history.map((item) => Number((item.fail_ratio * 100).toFixed(2))),
        compareValues: history.map((item) => item.total_fail_per_sec),
        labels: history.map((item) => item.time),
        stroke: "#b91c1c",
        fill: "rgba(185, 28, 28, 0.12)",
        compareStroke: "#7c3aed",
      },
    ];
  });

  const reportSummary = computed(() => {
    const report = options.taskReport.value;
    const stats = options.dataSource.value;
    return {
      totalRequests: report?.total_requests ?? stats.reduce((sum, item) => sum + item.num_requests, 0),
      totalFailures: report?.fail_count ?? stats.reduce((sum, item) => sum + item.num_failures, 0),
      currentRps: options.metrics.value.total_rps ?? 0,
      failRatio: options.metrics.value.fail_ratio ?? 0,
      runId: options.selectedTaskRun.value?.id ?? null,
      startedAt: report?.started_at ?? options.selectedTaskRun.value?.started_at ?? null,
      finishedAt: report?.finished_at ?? options.selectedTaskRun.value?.finished_at ?? null,
      runtime: options.metrics.value.runtime,
      latestError: report?.latest_error ?? null,
    };
  });

  const endpointSummary = computed(() => {
    const report = options.taskReport.value;
    const stats = options.dataSource.value;
    const slowestEndpoint =
      report?.hottest_endpoint?.name || [...stats].sort((a, b) => b.avg_response_time - a.avg_response_time)[0]?.name || "-";
    const riskiestEndpoint =
      report?.riskiest_endpoint?.name || [...stats].sort((a, b) => b.num_failures - a.num_failures)[0]?.name || "-";
    const busiestEndpoint = [...stats].sort((a, b) => b.current_rps - a.current_rps)[0]?.name || "-";
    const taskStateLabel = STATE_NAMES[options.metrics.value.state] || "运行异常";

    return {
      slowestEndpoint,
      riskiestEndpoint,
      busiestEndpoint,
      taskState: taskStateLabel,
      runCount: options.taskRuns.value.length,
    };
  });

  const errorSummary = computed(() => {
    return options.dataSource.value
      .filter((item) => item.num_failures > 0)
      .sort((a, b) => b.num_failures - a.num_failures)
      .slice(0, 5);
  });

  const tableColumns = [
    { title: "方法", dataIndex: "method", key: "method" },
    { title: "接口", dataIndex: "name", key: "name" },
    {
      title: "请求数",
      dataIndex: "num_requests",
      key: "num_requests",
      customRender: ({ text }: { text: number }) => formatNumberWithCommas(text),
    },
    {
      title: "失败数",
      dataIndex: "num_failures",
      key: "num_failures",
      customRender: ({ text }: { text: number }) => formatNumberWithCommas(text),
    },
    {
      title: "中位 RT(ms)",
      dataIndex: "median_response_time",
      key: "median_response_time",
      customRender: ({ text }: { text: number }) => formatNumber(text),
    },
    {
      title: "P95(ms)",
      dataIndex: "response_time_percentile_0.95",
      key: "response_time_percentile_0.95",
      customRender: ({ text }: { text: number }) => formatNumber(text),
    },
    {
      title: "P99(ms)",
      dataIndex: "response_time_percentile_0.99",
      key: "response_time_percentile_0.99",
      customRender: ({ text }: { text: number }) => formatNumber(text),
    },
    {
      title: "平均 RT(ms)",
      dataIndex: "avg_response_time",
      key: "avg_response_time",
      customRender: ({ text }: { text: number }) => formatNumber(text),
    },
    {
      title: "最小 RT(ms)",
      dataIndex: "min_response_time",
      key: "min_response_time",
      customRender: ({ text }: { text: number }) => formatNumber(text),
    },
    {
      title: "最大 RT(ms)",
      dataIndex: "max_response_time",
      key: "max_response_time",
      customRender: ({ text }: { text: number }) => formatNumber(text),
    },
    {
      title: "平均包大小(bytes)",
      dataIndex: "avg_content_length",
      key: "avg_content_length",
      customRender: ({ text }: { text: number }) => Math.round(text || 0).toString(),
    },
    {
      title: "当前吞吐",
      dataIndex: "current_rps",
      key: "current_rps",
      customRender: ({ text }: { text: number }) => formatNumber(text),
    },
    {
      title: "当前失败/秒",
      dataIndex: "current_fail_per_sec",
      key: "current_fail_per_sec",
      customRender: ({ text }: { text: number }) => formatNumber(text),
    },
  ];

  return {
    statCards,
    hotEndpoints,
    aiInsight,
    chartConfigs,
    reportSummary,
    endpointSummary,
    errorSummary,
    tableColumns,
  };
};
