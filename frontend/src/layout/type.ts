export interface Stats {
    method:string;
    name:string;
    num_requests:number;
    num_failures:number;
    success_ratio?: number;
    min_response_time:number;
    max_response_time:number;
    current_rps:number;
    current_fail_per_sec:number;
    avg_response_time:number;
    median_response_time:number;
    total_rps:number;
    total_fail_per_sec:number;
    avg_content_length:number;
    status_code_counts?: Record<string, number>;
    error_type_counts?: Record<string, number>;
    latest_error?: string | null;
    "response_time_percentile_0.95"?: number;
    "response_time_percentile_0.99"?: number;
}
// 状态类型
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

// 状态常量定义
export const STATE_INIT = "ready" as const;
export const STATE_SPAWNING = "spawning" as const;
export const STATE_RUNNING = "running" as const;
export const STATE_CLEANUP = "cleanup" as const;
export const STATE_STOPPING = "stopping" as const;
export const STATE_STOPPED = "stopped" as const;
export const STATE_MISSING = "missing" as const;


// 状态名称映射
export const STATE_NAMES: Record<SystemState, string> = {
    [STATE_INIT]: "准备中",
    [STATE_SPAWNING]: "启动中",
    [STATE_RUNNING]: "运行中",
    [STATE_CLEANUP]: "清理中",
    [STATE_STOPPING]: "停止中",
    [STATE_STOPPED]: "已停止",
    [STATE_MISSING]: "已丢失",
} as const;

// 状态颜色映射
export const STATE_COLORS: Record<SystemState, string> = {
    [STATE_INIT]: "blue",
    [STATE_SPAWNING]: "blue",
    [STATE_RUNNING]: "green",
    [STATE_CLEANUP]: "orange",
    [STATE_STOPPING]: "orange",
    [STATE_STOPPED]: "red",
    [STATE_MISSING]: "red",
} as const;


// WebSocket 控制命令类型
export type ControlCommand = 'start' | 'stop' | 'scale' | 'status'

// WebSocket 请求接口
export interface WebSocketRequest {
    cmd: ControlCommand
    task_id: number
    data?: any
}

// WebSocket 响应接口
export interface WebSocketResponse {
    type: 'event'
    task_id: number
    payload: any
}

// 控制命令参数接口
export interface StartCommandData {
    users?: number
    spawn_rate?: number
    host?: string
    [key: string]: any
}

export interface ScaleCommandData {
    users: number
    spawn_rate: number
}
