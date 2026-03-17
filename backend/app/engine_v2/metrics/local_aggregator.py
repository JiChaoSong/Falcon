from datetime import datetime, timezone
from threading import Lock
from typing import Any


class LocalMetricsAggregator:
    def __init__(self) -> None:
        self.lock = Lock()
        self.total_requests = 0
        self.success_count = 0
        self.fail_count = 0
        self.response_times: list[float] = []
        self.window_started_at = datetime.now(timezone.utc)
        self.window_response_times: list[float] = []
        self.window_success_count = 0
        self.window_fail_count = 0
        self.endpoint_metrics: dict[str, dict[str, Any]] = {}

    def record(
        self,
        method: str,
        name: str,
        response_time_ms: float,
        success: bool,
        content_length: int = 0,
    ) -> None:
        with self.lock:
            self.total_requests += 1
            self.response_times.append(response_time_ms)
            self.window_response_times.append(response_time_ms)
            if success:
                self.success_count += 1
                self.window_success_count += 1
            else:
                self.fail_count += 1
                self.window_fail_count += 1

            metric = self.endpoint_metrics.setdefault(
                f"{method}:{name}",
                {
                    "method": method,
                    "name": name,
                    "num_requests": 0,
                    "num_failures": 0,
                    "response_times": [],
                    "window_requests": 0,
                    "window_failures": 0,
                    "avg_content_length": 0,
                    "content_lengths": [],
                },
            )
            metric["num_requests"] += 1
            metric["window_requests"] += 1
            metric["response_times"].append(response_time_ms)
            metric["content_lengths"].append(content_length)
            if not success:
                metric["num_failures"] += 1
                metric["window_failures"] += 1

    def build_snapshot(self, active_users: int, latest_error: str | None = None) -> dict[str, Any]:
        with self.lock:
            total = self.total_requests
            success_ratio = (self.success_count / total) if total else 0
            avg_rt = (sum(self.response_times) / len(self.response_times)) if self.response_times else 0
            p95 = self._percentile(self.response_times, 0.95)
            p99 = self._percentile(self.response_times, 0.99)
            stats = []

            for metric in self.endpoint_metrics.values():
                response_times = list(metric["response_times"])
                content_lengths = list(metric["content_lengths"])
                total_requests = metric["num_requests"]
                total_failures = metric["num_failures"]
                avg_response_time = (sum(response_times) / len(response_times)) if response_times else 0
                stats.append({
                    "method": metric["method"],
                    "name": metric["name"],
                    "num_requests": total_requests,
                    "num_failures": total_failures,
                    "min_response_time": round(min(response_times), 2) if response_times else 0,
                    "max_response_time": round(max(response_times), 2) if response_times else 0,
                    "current_rps": float(metric["window_requests"]),
                    "current_fail_per_sec": float(metric["window_failures"]),
                    "avg_response_time": round(avg_response_time, 2),
                    "median_response_time": round(self._percentile(response_times, 0.5), 2),
                    "total_rps": float(metric["window_requests"]),
                    "total_fail_per_sec": float(metric["window_failures"]),
                    "avg_content_length": round(
                        (sum(content_lengths) / len(content_lengths)) if content_lengths else 0,
                        2,
                    ),
                    "response_time_percentile_0.95": round(self._percentile(response_times, 0.95), 2),
                    "response_time_percentile_0.99": round(self._percentile(response_times, 0.99), 2),
                })

            stats.sort(key=lambda item: (-item["num_failures"], -item["avg_response_time"], item["name"]))

            return {
                "active_users": active_users,
                "total_requests": total,
                "success_count": self.success_count,
                "fail_count": self.fail_count,
                "success_ratio": round(success_ratio, 4),
                "avg_rt": round(avg_rt, 2),
                "p95": round(p95, 2),
                "p99": round(p99, 2),
                "latest_error": latest_error,
                "stats": stats,
            }

    def build_second_metric(self, active_users: int) -> dict[str, Any]:
        with self.lock:
            window_count = len(self.window_response_times)
            metric = {
                "ts": datetime.now(timezone.utc),
                "rps": float(window_count),
                "success_count": self.window_success_count,
                "fail_count": self.window_fail_count,
                "avg_rt": round(
                    (sum(self.window_response_times) / window_count) if window_count else 0,
                    2,
                ),
                "p95": round(self._percentile(self.window_response_times, 0.95), 2),
                "p99": round(self._percentile(self.window_response_times, 0.99), 2),
                "active_users": active_users,
            }
            self.window_started_at = datetime.now(timezone.utc)
            self.window_response_times = []
            self.window_success_count = 0
            self.window_fail_count = 0
            for endpoint_metric in self.endpoint_metrics.values():
                endpoint_metric["window_requests"] = 0
                endpoint_metric["window_failures"] = 0
            return metric

    def _percentile(self, values: list[float], ratio: float) -> float:
        if not values:
            return 0
        sorted_values = sorted(values)
        index = max(0, min(len(sorted_values) - 1, int(len(sorted_values) * ratio) - 1))
        return float(sorted_values[index])
