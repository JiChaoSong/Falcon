import asyncio
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket


class TaskRuntimeWSManager:
    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, task_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[task_id].add(websocket)

    async def disconnect(self, task_id: int, websocket: WebSocket) -> None:
        async with self._lock:
            task_connections = self._connections.get(task_id)
            if not task_connections:
                return
            task_connections.discard(websocket)
            if not task_connections:
                self._connections.pop(task_id, None)

    async def publish(self, task_id: int, event: str, data: dict[str, Any] | None = None) -> None:
        async with self._lock:
            recipients = list(self._connections.get(task_id, set()))

        if not recipients:
            return

        payload = {
            "channel": "task_runtime",
            "event": event,
            "task_id": task_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data or {},
        }

        stale_connections: list[WebSocket] = []
        for websocket in recipients:
            try:
                await websocket.send_json(payload)
            except Exception:
                stale_connections.append(websocket)

        if stale_connections:
            async with self._lock:
                task_connections = self._connections.get(task_id)
                if not task_connections:
                    return
                for websocket in stale_connections:
                    task_connections.discard(websocket)
                if not task_connections:
                    self._connections.pop(task_id, None)


task_runtime_ws_manager = TaskRuntimeWSManager()
