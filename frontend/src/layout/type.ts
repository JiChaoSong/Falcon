export interface Stats {
  method: string;
  name: string;
  num_requests: number;
  num_failures: number;
  success_ratio?: number;
  min_response_time: number;
  max_response_time: number;
  current_rps: number;
  current_fail_per_sec: number;
  avg_response_time: number;
  median_response_time: number;
  total_rps: number;
  total_fail_per_sec: number;
  avg_content_length: number;
  status_code_counts?: Record<string, number>;
  error_type_counts?: Record<string, number>;
  latest_error?: string | null;
  "response_time_percentile_0.95"?: number;
  "response_time_percentile_0.99"?: number;
}

export const STATE_INIT = "ready" as const;
export const STATE_SPAWNING = "spawning" as const;
export const STATE_RUNNING = "running" as const;
export const STATE_CLEANUP = "cleanup" as const;
export const STATE_STOPPING = "stopping" as const;
export const STATE_STOPPED = "stopped" as const;
export const STATE_MISSING = "missing" as const;

export type SystemState =
  | typeof STATE_INIT
  | typeof STATE_SPAWNING
  | typeof STATE_RUNNING
  | typeof STATE_CLEANUP
  | typeof STATE_STOPPING
  | typeof STATE_STOPPED
  | typeof STATE_MISSING;

export interface Metrics {
  stats: Stats[];
  errors: Array<Record<string, unknown>>;
  total_rps: number;
  total_fail_per_sec: number;
  fail_ratio: number;
  state: SystemState;
  user_count: number;
  host: string;
  start_time: string;
  runtime: string;
  runtime_seconds: number;
  status_code_counts?: Record<string, number>;
  error_type_counts?: Record<string, number>;
  failure_samples?: Array<Record<string, unknown>>;
}

export interface MetricHistoryPoint {
  time: string;
  user_count: number;
  total_rps: number;
  fail_ratio: number;
  avg_response_time: number;
  p95_response_time: number;
  total_fail_per_sec: number;
}

export const STATE_NAMES: Record<SystemState, string> = {
  [STATE_INIT]: "待开始",
  [STATE_SPAWNING]: "启动中",
  [STATE_RUNNING]: "压测中",
  [STATE_CLEANUP]: "收尾中",
  [STATE_STOPPING]: "正在停止",
  [STATE_STOPPED]: "已结束",
  [STATE_MISSING]: "运行异常",
};

export const STATE_COLORS: Record<SystemState, string> = {
  [STATE_INIT]: "blue",
  [STATE_SPAWNING]: "blue",
  [STATE_RUNNING]: "green",
  [STATE_CLEANUP]: "orange",
  [STATE_STOPPING]: "orange",
  [STATE_STOPPED]: "default",
  [STATE_MISSING]: "red",
};
