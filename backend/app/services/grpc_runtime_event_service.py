import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Select, false

from app.db import SessionLocal
from app.models import TaskMetricSecond, TaskRun, TaskRunStatusEnum, Tasks, TaskStatusEnum
from app.services.task_runtime_ws_service import task_runtime_ws_manager


class GrpcRuntimeEventService:
    async def handle_event(
        self,
        *,
        task_id: int,
        task_run_id: int,
        event_type: str,
        status: str,
        started_at: str = "",
        finished_at: str = "",
        runtime_seconds: int = 0,
        active_users: int = 0,
        latest_error: str = "",
        summary_json: str = "",
        metric_json: str = "",
    ) -> None:
        db = SessionLocal()
        try:
            task = db.execute(
                Select(Tasks).where(Tasks.id == task_id, Tasks.is_deleted == false())
            ).scalar_one_or_none()
            task_run = db.execute(
                Select(TaskRun).where(TaskRun.id == task_run_id, TaskRun.is_deleted == false())
            ).scalar_one_or_none()
            if not task or not task_run:
                return

            summary = self._loads(summary_json)
            metric = self._loads(metric_json)
            existing_summary = dict(task_run.summary_json or {})
            merged_summary = {**existing_summary, **summary}
            started_dt = self._parse_datetime(started_at)
            finished_dt = self._parse_datetime(finished_at)
            task_status = self._to_task_status(status)
            task_run_status = self._to_task_run_status(status)

            if started_dt:
                task.start_time = started_dt
                task_run.started_at = started_dt

            if event_type == "started":
                task.status = TaskStatusEnum.RUNNING
                task.finished_at = None
                task.runtime_seconds = 0
                task.runtime = "00:00:00"
                task.stats = merged_summary
                task_run.status = TaskRunStatusEnum.RUNNING
                task_run.summary_json = merged_summary

            elif event_type == "snapshot":
                task.status = TaskStatusEnum.RUNNING
                task.runtime_seconds = runtime_seconds
                task.runtime = self._format_runtime(runtime_seconds)
                task.stats = merged_summary
                task_run.status = TaskRunStatusEnum.RUNNING
                task_run.runtime_seconds = runtime_seconds
                task_run.summary_json = merged_summary
                if metric:
                    db.add(
                        TaskMetricSecond(
                            task_run_id=task_run.id,
                            task_id=task.id,
                            scenario_id=None,
                            ts=self._parse_metric_ts(metric.get("ts")),
                            rps=float(metric.get("rps") or 0),
                            success_count=int(metric.get("success_count") or 0),
                            fail_count=int(metric.get("fail_count") or 0),
                            avg_rt=float(metric.get("avg_rt") or 0),
                            p95=float(metric.get("p95") or 0),
                            p99=float(metric.get("p99") or 0),
                            active_users=int(metric.get("active_users") or active_users or 0),
                        )
                    )

            else:
                task.status = task_status
                task.finished_at = finished_dt
                task.runtime_seconds = runtime_seconds
                task.runtime = self._format_runtime(runtime_seconds)
                task.stats = merged_summary
                task_run.status = task_run_status
                task_run.finished_at = finished_dt
                task_run.runtime_seconds = runtime_seconds
                task_run.summary_json = merged_summary
                if latest_error:
                    task_run.error_message = latest_error[:500]

            db.commit()
        finally:
            db.close()

        await task_runtime_ws_manager.publish(
            task_id,
            event_type,
            {
                "task_run_id": task_run_id,
                "status": status,
                "runtime_seconds": runtime_seconds,
                "active_users": active_users,
                "latest_error": latest_error or None,
            },
        )

    def _loads(self, value: str) -> dict[str, Any]:
        if not value:
            return {}
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def _parse_datetime(self, value: str) -> datetime | None:
        if not value:
            return None
        return datetime.fromisoformat(value)

    def _parse_metric_ts(self, value: Any) -> datetime:
        if isinstance(value, str) and value:
            return datetime.fromisoformat(value)
        return datetime.now(timezone.utc)

    def _to_task_status(self, status: str) -> TaskStatusEnum:
        return TaskStatusEnum(status.split(".")[-1].lower())

    def _to_task_run_status(self, status: str) -> TaskRunStatusEnum:
        return TaskRunStatusEnum(status.split(".")[-1].lower())

    def _format_runtime(self, seconds: int) -> str:
        hour = str(seconds // 3600).zfill(2)
        minute = str((seconds % 3600) // 60).zfill(2)
        second = str(seconds % 60).zfill(2)
        return f"{hour}:{minute}:{second}"


grpc_runtime_event_service = GrpcRuntimeEventService()
