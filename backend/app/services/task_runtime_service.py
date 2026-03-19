from typing import Any

from sqlalchemy import Select, false
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.exception import ParamException
from app.models import TaskMetricSecond, TaskRun, TaskRunStatusEnum, Tasks, TaskScenario, TaskStatusEnum, Worker
from app.services.access_control_service import AccessControlService
from app.services.grpc_worker_dispatcher_service import GrpcWorkerDispatcherService


class TaskRuntimeService:
    def __init__(self, db: Session):
        self.db = db
        self.access_control = AccessControlService(db)
        self.dispatcher = GrpcWorkerDispatcherService(db)

    def run(self, task_id: int) -> dict[str, Any]:
        task = self._get_task(task_id)
        self.access_control.ensure_project_manage_access(task.project_id)
        task_run = self._prepare_task_run(task_id)

        try:
            dispatch_result = self.dispatcher.dispatch_start(task=task, task_run_id=task_run.id)
            task_run.summary_json = {
                **dict(task_run.summary_json or {}),
                "worker_id": dispatch_result["worker_id"],
                "worker_task_id": dispatch_result["worker_task_id"],
                "worker_addr": dispatch_result["worker_addr"],
            }
            self.db.commit()
        except Exception:
            self._rollback_prepared_task_run(task_id=task_id, task_run_id=task_run.id)
            raise

        return {
            "task_id": task_id,
            "task_run_id": task_run.id,
            "status": task_run.status,
        }

    def stop(self, task_id: int) -> dict[str, Any]:
        task = self._get_task(task_id)
        self.access_control.ensure_project_manage_access(task.project_id)

        latest_run = self._get_latest_task_run(task_id)
        if not latest_run:
            raise ParamException("Task is not running.")
        if latest_run.status == TaskRunStatusEnum.STOPPING:
            raise ParamException("Task is already stopping.")
        if latest_run.status != TaskRunStatusEnum.RUNNING:
            raise ParamException("Task is not running.")

        worker_task_id = str((latest_run.summary_json or {}).get("worker_task_id") or "")
        worker_addr = str((latest_run.summary_json or {}).get("worker_addr") or "")
        if not worker_task_id:
            raise ParamException("Worker task metadata is missing for the running task.")
        if not worker_addr:
            raise ParamException("Worker address is missing for the running task.")

        self.dispatcher.dispatch_stop(
            task_id=task.id,
            task_run_id=latest_run.id,
            worker_task_id=worker_task_id,
            worker_addr=worker_addr,
        )

        latest_run.status = TaskRunStatusEnum.STOPPING
        task.status = TaskStatusEnum.STOPPING
        self.db.commit()

        return {
            "task_id": task.id,
            "task_run_id": latest_run.id,
            "status": TaskRunStatusEnum.STOPPING,
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
            success_ratio = round(success_count / total_requests, 4) if total_requests else 0.0
            runs.append(
                {
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
                }
            )

        return {"task_id": task.id, "runs": runs}

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
            "status_code_counts": status_payload.get("status_code_counts", {}),
            "error_type_counts": status_payload.get("error_type_counts", {}),
            "failure_samples": status_payload.get("failure_samples", []),
            "hottest_endpoint": to_endpoint_payload(hottest_endpoint),
            "riskiest_endpoint": to_endpoint_payload(riskiest_endpoint),
            "stats": stats,
            "history": status_payload.get("history", []),
            "worker_snapshot": status_payload.get("worker_snapshot"),
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

        total_requests = int(summary.get("total_requests") or 0)
        success_count = int(summary.get("success_count") or 0)
        fail_count = int(summary.get("fail_count") or 0)
        success_ratio = (success_count / total_requests) if total_requests else float(summary.get("success_ratio") or 0)

        current_rps = history[-1]["rps"] if history else 0
        avg_rt = history[-1]["avg_rt"] if history else float(summary.get("avg_rt") or 0)
        p95 = history[-1]["p95"] if history else float(summary.get("p95") or 0)
        p99 = history[-1]["p99"] if history else float(summary.get("p99") or 0)
        active_users = history[-1]["active_users"] if history else int(summary.get("active_users") or 0)

        latest_error = task_run.error_message if task_run and task_run.error_message else summary.get("latest_error")

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
            "status_code_counts": summary.get("status_code_counts", {}),
            "error_type_counts": summary.get("error_type_counts", {}),
            "failure_samples": summary.get("failure_samples", []),
            "stats": summary.get("stats", []),
            "history": history,
            "worker_snapshot": self._build_worker_snapshot(task_run),
        }

    def _build_worker_snapshot(self, task_run: TaskRun | None) -> dict[str, Any] | None:
        if not task_run:
            return None

        summary = dict(task_run.summary_json or {})
        worker_id = str(summary.get("worker_id") or "").strip()
        worker_addr = str(summary.get("worker_addr") or "").strip() or None
        if not worker_id:
            return None

        worker = self.db.execute(
            Select(Worker).where(
                Worker.worker_id == worker_id,
                Worker.is_deleted == false(),
            )
        ).scalar_one_or_none()

        metadata = dict((worker.metadata_json if worker else None) or {})
        system = dict(metadata.get("system") or {})
        resources = dict(metadata.get("resources") or {})
        process = dict(metadata.get("process") or {})

        return {
            "worker_id": worker_id,
            "worker_addr": worker_addr or (worker.address if worker else None),
            "worker_status": worker.status if worker else None,
            "sampled_at": metadata.get("sampled_at"),
            "system": {
                "hostname": system.get("hostname"),
                "platform": system.get("platform"),
                "ip": system.get("ip"),
            },
            "resources": {
                "cpu_percent": resources.get("cpu_percent"),
                "load_1": resources.get("load_1"),
                "memory_percent": resources.get("memory_percent"),
                "memory_used_mb": resources.get("memory_used_mb"),
                "memory_total_mb": resources.get("memory_total_mb"),
                "disk_percent": resources.get("disk_percent"),
                "disk_used_gb": resources.get("disk_used_gb"),
                "disk_total_gb": resources.get("disk_total_gb"),
                "net_sent_kbps": resources.get("net_sent_kbps"),
                "net_recv_kbps": resources.get("net_recv_kbps"),
            },
            "process": {
                "cpu_percent": process.get("cpu_percent"),
                "memory_mb": process.get("memory_mb"),
                "threads": process.get("threads"),
            },
        }

    def _get_task(self, task_id: int) -> Tasks:
        task = self.db.execute(
            Select(Tasks).where(
                Tasks.id == task_id,
                Tasks.is_deleted == false(),
            )
        ).scalar_one_or_none()
        if not task:
            raise ParamException("Task not found.")
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
            raise ParamException("Task run not found.")
        return task_run

    def _lock_task_for_runtime(self, task_id: int) -> Tasks | None:
        try:
            return self.db.execute(
                Select(Tasks).where(
                    Tasks.id == task_id,
                    Tasks.is_deleted == false(),
                ).with_for_update(nowait=True)
            ).scalar_one_or_none()
        except OperationalError as exc:
            raise ParamException("Task is busy, please retry shortly.") from exc

    def _prepare_task_run(self, task_id: int) -> TaskRun:
        locked_task = self._lock_task_for_runtime(task_id)
        if not locked_task:
            raise ParamException("Task not found.")

        if locked_task.status == TaskStatusEnum.RUNNING:
            raise ParamException("Task is already running.")

        latest_run = self.db.execute(
            Select(TaskRun).where(
                TaskRun.task_id == task_id,
                TaskRun.is_deleted == false(),
            ).order_by(TaskRun.created_at.desc()).limit(1)
        ).scalars().first()
        if latest_run and latest_run.status in {
            TaskRunStatusEnum.PENDING,
            TaskRunStatusEnum.RUNNING,
            TaskRunStatusEnum.STOPPING,
        }:
            raise ParamException("Task already has an active run.")

        task_run = TaskRun(task_id=locked_task.id, status=TaskRunStatusEnum.PENDING, summary_json={})
        locked_task.status = TaskStatusEnum.RUNNING
        locked_task.finished_at = None
        locked_task.runtime_seconds = 0
        locked_task.runtime = "00:00:00"

        self.db.add(task_run)
        self.db.commit()
        self.db.refresh(task_run)
        return task_run

    def _rollback_prepared_task_run(self, task_id: int, task_run_id: int) -> None:
        self.db.rollback()
        try:
            locked_task = self._lock_task_for_runtime(task_id)
        except ParamException:
            locked_task = None

        try:
            task_run = self.db.execute(
                Select(TaskRun).where(
                    TaskRun.id == task_run_id,
                    TaskRun.task_id == task_id,
                    TaskRun.is_deleted == false(),
                ).with_for_update(nowait=True)
            ).scalar_one_or_none()
        except OperationalError:
            task_run = None

        if locked_task and locked_task.status == TaskStatusEnum.RUNNING:
            locked_task.status = TaskStatusEnum.PENDING

        if task_run and task_run.status == TaskRunStatusEnum.PENDING:
            task_run.status = TaskRunStatusEnum.FAILED
            task_run.error_message = "Failed to dispatch task to worker."

        self.db.commit()
