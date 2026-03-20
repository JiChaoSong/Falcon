from __future__ import annotations

import os
import platform
import socket
import time
from datetime import datetime, timezone
from typing import Any

import psutil


class WorkerResourceSnapshotCollector:
    def __init__(self) -> None:
        self._process = psutil.Process(os.getpid())
        self._last_net_counters: tuple[float, int, int] | None = None

    def collect(self) -> dict[str, Any]:
        sampled_at = datetime.now(timezone.utc)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(os.getcwd())
        process_memory_mb = self._process.memory_info().rss / (1024 * 1024)
        net_sent_kbps, net_recv_kbps = self._sample_network_speed()

        return {
            "system": {
                "hostname": socket.gethostname(),
                "platform": platform.platform(),
                "ip": self._resolve_primary_ip(),
            },
            "resources": {
                "cpu_percent": round(psutil.cpu_percent(interval=None), 2),
                "load_1": self._load_average(),
                "memory_percent": round(float(memory.percent), 2),
                "memory_used_mb": round(memory.used / (1024 * 1024), 2),
                "memory_total_mb": round(memory.total / (1024 * 1024), 2),
                "disk_percent": round(float(disk.percent), 2),
                "disk_used_gb": round(disk.used / (1024 * 1024 * 1024), 2),
                "disk_total_gb": round(disk.total / (1024 * 1024 * 1024), 2),
                "net_sent_kbps": net_sent_kbps,
                "net_recv_kbps": net_recv_kbps,
            },
            "process": {
                "cpu_percent": round(self._process.cpu_percent(interval=None), 2),
                "memory_mb": round(process_memory_mb, 2),
                "threads": self._process.num_threads(),
            },
            "sampled_at": sampled_at.isoformat(),
        }

    def _sample_network_speed(self) -> tuple[float, float]:
        counters = psutil.net_io_counters()
        now = time.time()
        current = (now, int(counters.bytes_sent), int(counters.bytes_recv))
        if not self._last_net_counters:
            self._last_net_counters = current
            return 0.0, 0.0

        last_at, last_sent, last_recv = self._last_net_counters
        elapsed = max(now - last_at, 1e-6)
        self._last_net_counters = current
        sent_kbps = max((current[1] - last_sent) / 1024 / elapsed, 0.0)
        recv_kbps = max((current[2] - last_recv) / 1024 / elapsed, 0.0)
        return round(sent_kbps, 2), round(recv_kbps, 2)

    def _load_average(self) -> float | None:
        try:
            return round(float(os.getloadavg()[0]), 2)
        except (AttributeError, OSError):
            return None

    def _resolve_primary_ip(self) -> str | None:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect(("8.8.8.8", 80))
                return sock.getsockname()[0]
        except OSError:
            return None


worker_resource_snapshot_collector = WorkerResourceSnapshotCollector()
