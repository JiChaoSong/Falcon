from datetime import datetime, timezone
from threading import Lock
from time import time_ns

from app.core.config import settings


class SafeSnowflakeGenerator:
    """
    生成 JavaScript 安全整数范围内的分布式 ID。

    结构:
    - 自定义纪元后的毫秒差值
    - 2 位节点号
    - 2 位毫秒内序列
    """

    CUSTOM_EPOCH_MS = int(datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
    NODE_MULTIPLIER = 100
    TIMESTAMP_MULTIPLIER = 10_000
    MAX_NODE_ID = 99
    MAX_SEQUENCE = 99

    def __init__(self, node_id: int = 1):
        if node_id < 0 or node_id > self.MAX_NODE_ID:
            raise ValueError(f"node_id must be between 0 and {self.MAX_NODE_ID}")
        self.node_id = node_id
        self.lock = Lock()
        self.last_timestamp = -1
        self.sequence = 0

    def next_id(self) -> int:
        with self.lock:
            timestamp = self._current_millis()

            if timestamp < self.last_timestamp:
                timestamp = self.last_timestamp

            if timestamp == self.last_timestamp:
                self.sequence += 1
                if self.sequence > self.MAX_SEQUENCE:
                    timestamp = self._wait_next_millis(self.last_timestamp)
                    self.sequence = 0
            else:
                self.sequence = 0

            self.last_timestamp = timestamp
            elapsed_ms = timestamp - self.CUSTOM_EPOCH_MS

            return (
                elapsed_ms * self.TIMESTAMP_MULTIPLIER
                + self.node_id * self.NODE_MULTIPLIER
                + self.sequence
            )

    def _current_millis(self) -> int:
        return time_ns() // 1_000_000

    def _wait_next_millis(self, last_timestamp: int) -> int:
        timestamp = self._current_millis()
        while timestamp <= last_timestamp:
            timestamp = self._current_millis()
        return timestamp


_generator = SafeSnowflakeGenerator(node_id=settings.ID_NODE_ID)


def generate_id() -> int:
    return _generator.next_id()
