import asyncio
import json
from datetime import datetime
from typing import Any

import grpc

from falcon_shared.grpc.generated import worker_runtime_pb2, worker_runtime_pb2_grpc


class ControlPlaneReporter:
    def __init__(
        self,
        control_plane_addr: str,
        worker_id: str,
        worker_task_id: str,
        task_id: int,
        task_run_id: int,
    ) -> None:
        self.control_plane_addr = control_plane_addr
        self.worker_id = worker_id
        self.worker_task_id = worker_task_id
        self.task_id = task_id
        self.task_run_id = task_run_id

    async def report(
        self,
        event_type: str,
        status: str,
        *,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
        runtime_seconds: int = 0,
        active_users: int = 0,
        latest_error: str | None = None,
        summary: dict[str, Any] | None = None,
        metric: dict[str, Any] | None = None,
    ) -> None:
        await asyncio.to_thread(
            self._send,
            event_type,
            status,
            started_at,
            finished_at,
            runtime_seconds,
            active_users,
            latest_error,
            summary,
            metric,
        )

    def _send(
        self,
        event_type: str,
        status: str,
        started_at: datetime | None,
        finished_at: datetime | None,
        runtime_seconds: int,
        active_users: int,
        latest_error: str | None,
        summary: dict[str, Any] | None,
        metric: dict[str, Any] | None,
    ) -> None:
        enriched_summary = {
            **dict(summary or {}),
            "worker_id": self.worker_id,
            "worker_task_id": self.worker_task_id,
        }
        channel = grpc.insecure_channel(self.control_plane_addr)
        try:
            stub = worker_runtime_pb2_grpc.ControlPlaneRuntimeStub(channel)
            stub.ReportTaskEvent(
                worker_runtime_pb2.TaskEventRequest(
                    worker_id=self.worker_id,
                    worker_task_id=self.worker_task_id,
                    task_id=self.task_id,
                    task_run_id=self.task_run_id,
                    event_type=event_type,
                    status=status,
                    started_at=started_at.isoformat() if started_at else "",
                    finished_at=finished_at.isoformat() if finished_at else "",
                    runtime_seconds=runtime_seconds,
                    active_users=active_users,
                    latest_error=latest_error or "",
                    summary_json=json.dumps(enriched_summary, ensure_ascii=True, default=str),
                    metric_json=json.dumps(metric or {}, ensure_ascii=True, default=str),
                )
            )
        finally:
            channel.close()
