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
      { label: "在线用户", value: String(metrics.user_count || 0), foot: "当前虚拟用户数量", tone: "primary" },
      { label: "当前吞吐", value: `${formatNumber(metrics.total_rps)} RPS`, foot: "当前每秒请求数", tone: "success" },
      { label: "总请求数", value: formatNumberWithCommas(totalRequests), foot: "累计已发起请求", tone: "default" },
      { label: "总失败数", value: formatNumberWithCommas(totalFailures), foot: "累计错误或超时", tone: "danger" },
      { label: "失败率", value: formatPercent(metrics.fail_ratio), foot: "失败请求占比", tone: "danger" },
      { label: "平均响应时间", value: formatTime(avgRt), foot: "当前整体平均值", tone: "default" },
      { label: "P95 响应时间", value: formatTime(aggregateP95), foot: "尾延迟关键指标", tone: "warning" },
      { label: "运行时长", value: metrics.runtime || "--", foot: "从启动到当前", tone: "default" },
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
        title: "等待运行指标",
        summary: "监控链路已经就绪，但当前还没有足够的实时流量数据。压测开始后，这里会自动给出诊断结论。",
        level: "warning",
        reasons: ["当前尚未收到接口级统计，无法判断吞吐、延迟和失败趋势。"],
        actions: ["确认任务已启动，并检查目标地址是否可达。"],
        confidence: 0.42,
      };
    }

    if (failRatio >= 0.05 || p95 >= 800) {
      return {
        title: "延迟与失败压力正在上升",
        summary: `${hotspot?.name || "热点接口"} 已成为当前主要风险点，P95 为 ${p95} ms，失败率为 ${(failRatio * 100).toFixed(1)}%。`,
        level: "danger",
        reasons: [
          `失败率达到 ${(failRatio * 100).toFixed(1)}%，已经超过常见告警阈值。`,
          `${hotspot?.name || "热点接口"} 当前失败速率为 ${hotspot?.current_fail_per_sec?.toFixed(2) || "0.00"}/s。`,
          `在 ${options.metrics.value.user_count} 个虚拟用户下，${formatNumber(totalRps)} RPS 已出现不稳定迹象。`,
        ],
        actions: [
          "优先检查热点接口依赖的数据库、缓存和下游服务超时。",
          "降低加压斜率，再做一轮分段压测确认拐点。",
          "如果是验证型任务，建议增加 P95 和失败率的自动停止规则。",
        ],
        confidence: 0.91,
      };
    }

    if (failRatio >= 0.02 || p95 >= 500 || runtimeSeconds < 180) {
      return {
        title: "系统可用，但仍处于观察区间",
        summary: `当前吞吐为 ${formatNumber(totalRps)} RPS，热点接口 ${hotspot?.name || "-"} 的 P95 为 ${p95} ms。`,
        level: "warning",
        reasons: [
          `任务已运行 ${options.metrics.value.runtime}，仍可能处于预热波动期。`,
          `${hotspot?.name || "热点接口"} 平均响应时间为 ${hotspot?.avg_response_time || 0} ms，需要继续观察尾延迟变化。`,
          `当前失败率为 ${(failRatio * 100).toFixed(1)}%，还未失控，但已经有压力迹象。`,
        ],
        actions: [
          "继续观察 3 到 5 分钟，确认曲线是否回稳。",
          "拆分状态码和错误类型，区分容量问题与业务错误。",
          "结合日志或 APM 做接口级排查。",
        ],
        confidence: 0.78,
      };
    }

    return {
      title: "当前压测整体较稳定",
      summary: `在 ${options.metrics.value.user_count} 个用户下，系统维持 ${formatNumber(totalRps)} RPS，暂无明显失稳迹象。`,
      level: "success",
      reasons: [
        `失败率保持在 ${(failRatio * 100).toFixed(1)}%。`,
        `${hotspot?.name || "热点接口"} 的 P95 约为 ${p95} ms，仍在可控范围内。`,
        `运行曲线在 ${options.metrics.value.runtime} 内没有出现明显畸变。`,
      ],
      actions: [
        "逐步增加压力，继续验证容量上限。",
        "把这次运行保存为基线结果，方便后续对比。",
        "运行结束后生成报告，与更高压档位结果对照分析。",
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
        subtitle: "实时请求速率变化",
        legend: ["请求/秒"],
        values: history.map((item) => item.total_rps),
        labels: history.map((item) => item.time),
        stroke: "#2563eb",
        fill: "rgba(37, 99, 235, 0.12)",
      },
      {
        key: "users",
        title: "并发趋势",
        subtitle: "虚拟用户变化",
        legend: ["并发用户"],
        values: history.map((item) => item.user_count),
        labels: history.map((item) => item.time),
        stroke: "#0f766e",
        fill: "rgba(15, 118, 110, 0.12)",
      },
      {
        key: "response-time",
        title: "响应时间趋势",
        subtitle: "平均响应时间与 P95",
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
        subtitle: "失败率与失败速率",
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
    const slowestEndpoint = report?.hottest_endpoint?.name || [...stats].sort((a, b) => b.avg_response_time - a.avg_response_time)[0]?.name || "-";
    const riskiestEndpoint = report?.riskiest_endpoint?.name || [...stats].sort((a, b) => b.num_failures - a.num_failures)[0]?.name || "-";
    const busiestEndpoint = [...stats].sort((a, b) => b.current_rps - a.current_rps)[0]?.name || "-";
    const taskStateLabel = STATE_NAMES[options.metrics.value.state] || "未知状态";

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
    { title: "类型", dataIndex: "method", key: "method" },
    { title: "名称", dataIndex: "name", key: "name" },
    { title: "请求数", dataIndex: "num_requests", key: "num_requests", customRender: ({ text }: { text: number }) => formatNumberWithCommas(text) },
    { title: "失败数", dataIndex: "num_failures", key: "num_failures", customRender: ({ text }: { text: number }) => formatNumberWithCommas(text) },
    { title: "中位 RT(ms)", dataIndex: "median_response_time", key: "median_response_time", customRender: ({ text }: { text: number }) => formatNumber(text) },
    { title: "P95(ms)", dataIndex: "response_time_percentile_0.95", key: "response_time_percentile_0.95", customRender: ({ text }: { text: number }) => formatNumber(text) },
    { title: "P99(ms)", dataIndex: "response_time_percentile_0.99", key: "response_time_percentile_0.99", customRender: ({ text }: { text: number }) => formatNumber(text) },
    { title: "平均 RT(ms)", dataIndex: "avg_response_time", key: "avg_response_time", customRender: ({ text }: { text: number }) => formatNumber(text) },
    { title: "最小 RT(ms)", dataIndex: "min_response_time", key: "min_response_time", customRender: ({ text }: { text: number }) => formatNumber(text) },
    { title: "最大 RT(ms)", dataIndex: "max_response_time", key: "max_response_time", customRender: ({ text }: { text: number }) => formatNumber(text) },
    { title: "平均包长(bytes)", dataIndex: "avg_content_length", key: "avg_content_length", customRender: ({ text }: { text: number }) => Math.round(text || 0).toString() },
    { title: "当前吞吐", dataIndex: "current_rps", key: "current_rps", customRender: ({ text }: { text: number }) => formatNumber(text) },
    { title: "当前失败速率", dataIndex: "current_fail_per_sec", key: "current_fail_per_sec", customRender: ({ text }: { text: number }) => formatNumber(text) },
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
