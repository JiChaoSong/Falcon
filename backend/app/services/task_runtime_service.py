import asyncio
from typing import Any

from sqlalchemy import Select, false
from sqlalchemy.orm import Session

from app.core.exception import ParamException
from app.engine_v2.registry.run_registry import TaskRunControl, task_run_registry
from app.engine_v2.runtime.task_runner import TaskRunner
from app.models import TaskMetricSecond, TaskRun, TaskRunStatusEnum, Tasks, TaskScenario, TaskStatusEnum
from app.services.access_control_service import AccessControlService


class TaskRuntimeService:
    def __init__(self, db: Session):
        self.db = db
        self.access_control = AccessControlService(db)
        self.task_runner = TaskRunner()

    def run(self, task_id: int) -> dict[str, Any]:
        task = self._get_task(task_id)
        self.access_control.ensure_project_manage_access(task.project_id)

        current_control = task_run_registry.get(task_id)
        if current_control and not current_control.cancel_event.is_set():
            raise ParamException("任务已在执行中")

        if task.status == TaskStatusEnum.RUNNING:
            raise ParamException("任务已在执行中")

        task_run = TaskRun(
            task_id=task.id,
            status=TaskRunStatusEnum.PENDING,
        )
        self.db.add(task_run)
        self.db.commit()
        self.db.refresh(task_run)

        control = TaskRunControl(task_id=task.id, task_run_id=task_run.id)
        control.task = asyncio.create_task(self.task_runner.run(control))
        task_run_registry.register(control)

        return {
            "task_id": task.id,
            "task_run_id": task_run.id,
            "status": task_run.status,
        }

    def stop(self, task_id: int) -> dict[str, Any]:
        task = self._get_task(task_id)
        self.access_control.ensure_project_manage_access(task.project_id)

        control = task_run_registry.stop(task_id)
        if not control:
            latest_run = self._get_latest_task_run(task_id)
            if not latest_run or latest_run.status != TaskRunStatusEnum.RUNNING:
                raise ParamException("当前没有正在执行的任务")
            latest_run.status = TaskRunStatusEnum.CANCELED
            task.status = TaskStatusEnum.CANCELED
            self.db.commit()
            return {
                "task_id": task.id,
                "task_run_id": latest_run.id,
                "status": latest_run.status,
            }

        return {
            "task_id": task.id,
            "task_run_id": control.task_run_id,
            "status": TaskRunStatusEnum.CANCELED,
        }

    def status(self, task_id: int) -> dict[str, Any]:
        task = self._get_task(task_id)
        self.access_control.ensure_project_view_access(task.project_id)

        task_run = self._get_latest_task_run(task_id)
        return self._build_runtime_status(task=task, task_run=task_run)

    def list_runs(self, task_id: int) -> dict[str, Any]:
        task = self._get_task(task_id)
        self.access_control.ensure_project_view_access(task.project_id)

        task_runs = self.db.execute(
            Select(TaskRun).where(
                TaskRun.task_id == task_id,
                TaskRun.is_deleted == false(),
            ).order_by(TaskRun.created_at.desc()).limit(20)
        ).scalars().all()

        runs = []
        for task_run in task_runs:
            summary = dict(task_run.summary_json or {})
            total_requests = int(summary.get("total_requests") or 0)
            success_count = int(summary.get("success_count") or 0)
            fail_count = int(summary.get("fail_count") or 0)
            success_ratio = 0.0
            if total_requests > 0:
                success_ratio = round(success_count / total_requests, 4)
            runs.append({
                "id": task_run.id,
                "status": task_run.status,
                "started_at": task_run.started_at,
                "finished_at": task_run.finished_at,
                "runtime_seconds": task_run.runtime_seconds or 0,
                "total_requests": total_requests,
                "success_count": success_count,
                "fail_count": fail_count,
                "success_ratio": success_ratio,
                "latest_error": task_run.error_message or summary.get("latest_error"),
            })

        return {
            "task_id": task.id,
            "runs": runs,
        }

    def report(self, task_id: int, task_run_id: int | None = None) -> dict[str, Any]:
        task = self._get_task(task_id)
        self.access_control.ensure_project_view_access(task.project_id)

        task_run = self._get_task_run(task_id=task_id, task_run_id=task_run_id)
        status_payload = self._build_runtime_status(task=task, task_run=task_run)
        stats = list(status_payload.get("stats", []))

        def to_endpoint_payload(item: dict[str, Any] | None) -> dict[str, Any] | None:
            if not item:
                return None
            return {
                "name": item.get("name") or "-",
                "method": item.get("method") or "GET",
                "total_requests": int(item.get("num_requests") or 0),
                "total_failures": int(item.get("num_failures") or 0),
                "avg_response_time": float(item.get("avg_response_time") or 0),
                "p95": float(item.get("response_time_percentile_0.95") or 0),
                "p99": float(item.get("response_time_percentile_0.99") or 0),
            }

        hottest_endpoint = max(stats, key=lambda item: float(item.get("num_requests") or 0), default=None)
        riskiest_endpoint = max(
            stats,
            key=lambda item: (
                float(item.get("num_failures") or 0),
                float(item.get("avg_response_time") or 0),
            ),
            default=None,
        )
        scenario_count = self.db.execute(
            Select(TaskScenario).where(
                TaskScenario.task_id == task.id,
                TaskScenario.is_deleted == false(),
            )
        ).scalars().all()

        return {
            "task_id": task.id,
            "task_run_id": status_payload.get("task_run_id"),
            "task_name": task.name,
            "project": task.project,
            "owner": task.owner,
            "host": task.host,
            "execution_strategy": task.execution_strategy,
            "scenario_count": len(scenario_count),
            "status": status_payload.get("status"),
            "started_at": status_payload.get("started_at"),
            "finished_at": status_payload.get("finished_at"),
            "runtime_seconds": status_payload.get("runtime_seconds", 0),
            "total_requests": status_payload.get("total_requests", 0),
            "success_count": status_payload.get("success_count", 0),
            "fail_count": status_payload.get("fail_count", 0),
            "success_ratio": status_payload.get("success_ratio", 0),
            "avg_rt": status_payload.get("avg_rt", 0),
            "p95": status_payload.get("p95", 0),
            "p99": status_payload.get("p99", 0),
            "latest_error": status_payload.get("latest_error"),
            "hottest_endpoint": to_endpoint_payload(hottest_endpoint),
            "riskiest_endpoint": to_endpoint_payload(riskiest_endpoint),
            "stats": stats,
            "history": status_payload.get("history", []),
        }

    def _build_runtime_status(self, task: Tasks, task_run: TaskRun | None) -> dict[str, Any]:
        recent_metrics = []
        if task_run:
            recent_metrics = self.db.execute(
                Select(TaskMetricSecond).where(
                    TaskMetricSecond.task_run_id == task_run.id,
                    TaskMetricSecond.is_deleted == false(),
                ).order_by(TaskMetricSecond.ts.desc()).limit(60)
            ).scalars().all()

        history = [
            {
                "ts": item.ts,
                "rps": item.rps,
                "success_count": item.success_count,
                "fail_count": item.fail_count,
                "avg_rt": item.avg_rt,
                "p95": item.p95,
                "p99": item.p99,
                "active_users": item.active_users,
            }
            for item in reversed(recent_metrics)
        ]

        summary = dict(task_run.summary_json or {}) if task_run else {}
        if not summary:
            summary = dict(task.stats or {})

        control = task_run_registry.get(task.id)
        if control and control.last_snapshot:
            if not task_run or control.task_run_id == task_run.id:
                summary.update(control.last_snapshot)

        total_requests = int(summary.get("total_requests") or 0)
        success_count = int(summary.get("success_count") or 0)
        fail_count = int(summary.get("fail_count") or 0)
        if total_requests > 0:
            success_ratio = success_count / total_requests
        else:
            success_ratio = float(summary.get("success_ratio") or 0)

        current_rps = history[-1]["rps"] if history else 0
        avg_rt = history[-1]["avg_rt"] if history else float(summary.get("avg_rt") or 0)
        p95 = history[-1]["p95"] if history else float(summary.get("p95") or 0)
        p99 = history[-1]["p99"] if history else float(summary.get("p99") or 0)
        active_users = history[-1]["active_users"] if history else int(summary.get("active_users") or 0)

        latest_error = None
        if task_run and task_run.error_message:
            latest_error = task_run.error_message
        elif control and control.latest_error:
            latest_error = control.latest_error
        else:
            latest_error = summary.get("latest_error")

        return {
            "task_id": task.id,
            "task_run_id": task_run.id if task_run else None,
            "task_name": task.name,
            "status": task_run.status if task_run else task.status,
            "started_at": task_run.started_at if task_run else task.start_time,
            "finished_at": task_run.finished_at if task_run else task.finished_at,
            "runtime_seconds": task_run.runtime_seconds if task_run else (task.runtime_seconds or 0),
            "active_users": active_users,
            "total_requests": total_requests,
            "success_count": success_count,
            "fail_count": fail_count,
            "success_ratio": round(success_ratio, 4),
            "current_rps": round(current_rps, 2),
            "avg_rt": round(avg_rt, 2),
            "p95": round(p95, 2),
            "p99": round(p99, 2),
            "host": task.host,
            "latest_error": latest_error,
            "stats": summary.get("stats", []),
            "history": history,
        }

    def _get_task(self, task_id: int) -> Tasks:
        task = self.db.execute(
            Select(Tasks).where(
                Tasks.id == task_id,
                Tasks.is_deleted == false(),
            )
        ).scalar_one_or_none()
        if not task:
            raise ParamException("任务不存在")
        return task

    def _get_latest_task_run(self, task_id: int) -> TaskRun | None:
        return self.db.execute(
            Select(TaskRun).where(
                TaskRun.task_id == task_id,
                TaskRun.is_deleted == false(),
            ).order_by(TaskRun.created_at.desc()).limit(1)
        ).scalars().first()

    def _get_task_run(self, task_id: int, task_run_id: int | None = None) -> TaskRun | None:
        if task_run_id is None:
            return self._get_latest_task_run(task_id)

        task_run = self.db.execute(
            Select(TaskRun).where(
                TaskRun.id == task_run_id,
                TaskRun.task_id == task_id,
                TaskRun.is_deleted == false(),
            )
        ).scalar_one_or_none()
        if not task_run:
            raise ParamException("任务运行实例不存在")
        return task_run
