from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, false
from sqlalchemy.orm import Session

from app.models.case import Case
from app.models.project import Project
from app.models.scenario import Scenario
from app.models.task import Tasks
from app.models.task_runtime import TaskRun
from app.models.worker import Worker, WorkerStatusEnum
from falcon_shared.runtime_enums import TaskStatusEnum

class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def overview(self) -> dict:
        worker_summary = self._build_worker_summary()
        return {
            "overview": self._build_overview(),
            "running_tasks": [self._serialize_task(item) for item in self._list_running_tasks()],
            "attention_tasks": [self._serialize_task(item) for item in self._list_attention_tasks()],
            "recent_tasks": [self._serialize_task(item) for item in self._list_recent_tasks()],
            "worker_summary": worker_summary,
            "worker_highlights": [self._serialize_worker(item) for item in self._list_worker_highlights()],
            "today_trend": self._build_today_trend(),
            "alerts": self._build_alerts(worker_summary),
        }

    def _build_overview(self) -> dict:
        return {
            "project_count": self._count(Project),
            "case_count": self._count(Case),
            "scenario_count": self._count(Scenario),
            "task_count": self._count(Tasks),
            "running_task_count": self._count(Tasks, Tasks.status == TaskStatusEnum.RUNNING),
            "stopping_task_count": self._count(Tasks, Tasks.status == TaskStatusEnum.STOPPING),
            "failed_task_count": self._count(Tasks, Tasks.status == TaskStatusEnum.FAILED),
            "online_worker_count": self._count(
                Worker,
                Worker.status.in_([WorkerStatusEnum.ONLINE, WorkerStatusEnum.BUSY]),
            ),
        }

    def _build_worker_summary(self) -> dict:
        grouped_rows = (
            self.db.query(Worker.status, func.count(Worker.id))
            .filter(Worker.is_deleted == false())
            .group_by(Worker.status)
            .all()
        )
        grouped = {status.value if hasattr(status, "value") else status: count for status, count in grouped_rows}
        return {
            "online": grouped.get(WorkerStatusEnum.ONLINE.value, 0),
            "busy": grouped.get(WorkerStatusEnum.BUSY.value, 0),
            "degraded": grouped.get(WorkerStatusEnum.DEGRADED.value, 0),
            "offline": grouped.get(WorkerStatusEnum.OFFLINE.value, 0),
        }

    def _list_running_tasks(self) -> list[Tasks]:
        return (
            self.db.query(Tasks)
            .filter(Tasks.is_deleted == false(), Tasks.status == TaskStatusEnum.RUNNING)
            .order_by(Tasks.updated_at.desc())
            .limit(4)
            .all()
        )

    def _list_attention_tasks(self) -> list[Tasks]:
        return (
            self.db.query(Tasks)
            .filter(
                Tasks.is_deleted == false(),
                Tasks.status.in_([TaskStatusEnum.FAILED, TaskStatusEnum.STOPPING, TaskStatusEnum.CANCELED]),
            )
            .order_by(Tasks.updated_at.desc())
            .limit(4)
            .all()
        )

    def _list_recent_tasks(self) -> list[Tasks]:
        return (
            self.db.query(Tasks)
            .filter(Tasks.is_deleted == false())
            .order_by(Tasks.updated_at.desc())
            .limit(8)
            .all()
        )

    def _list_worker_highlights(self) -> list[Worker]:
        rows = (
            self.db.query(Worker)
            .filter(Worker.is_deleted == false())
            .order_by(Worker.running_tasks.desc(), Worker.updated_at.desc())
            .limit(5)
            .all()
        )
        return sorted(
            rows,
            key=lambda item: (
                1 if item.status == WorkerStatusEnum.DEGRADED else 0,
                1 if item.status == WorkerStatusEnum.OFFLINE else 0,
                item.running_tasks,
            ),
            reverse=True,
        )

    def _build_today_trend(self) -> list[dict]:
        start_of_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        runs = (
            self.db.query(TaskRun)
            .filter(TaskRun.started_at.isnot(None), TaskRun.started_at >= start_of_day)
            .order_by(TaskRun.started_at.asc())
            .all()
        )

        buckets = {
            hour: {
                "label": f"{hour:02d}:00",
                "task_runs": 0,
                "success_ratio": 0.0,
                "total_requests": 0,
                "fail_count": 0,
                "_success_ratio_sum": 0.0,
            }
            for hour in range(24)
        }

        for run in runs:
            if not run.started_at:
                continue
            hour = run.started_at.hour
            summary = run.summary_json or {}
            total_requests = int(summary.get("total_requests") or 0)
            fail_count = int(summary.get("fail_count") or 0)
            success_ratio = float(summary.get("success_ratio") or 0)

            bucket = buckets[hour]
            bucket["task_runs"] += 1
            bucket["total_requests"] += total_requests
            bucket["fail_count"] += fail_count
            bucket["_success_ratio_sum"] += success_ratio

        points: list[dict] = []
        for hour in range(24):
            bucket = buckets[hour]
            task_runs = bucket["task_runs"]
            points.append({
                "label": bucket["label"],
                "task_runs": task_runs,
                "success_ratio": round(bucket["_success_ratio_sum"] / task_runs, 2) if task_runs else 0,
                "total_requests": bucket["total_requests"],
                "fail_count": bucket["fail_count"],
            })
        return points

    def _build_alerts(self, worker_summary: dict) -> list[dict]:
        alerts: list[dict] = []
        failed_count = self._count(Tasks, Tasks.status == TaskStatusEnum.FAILED)
        stopping_count = self._count(Tasks, Tasks.status == TaskStatusEnum.STOPPING)
        running_count = self._count(Tasks, Tasks.status == TaskStatusEnum.RUNNING)
        degraded_count = int(worker_summary.get("degraded", 0))
        offline_count = int(worker_summary.get("offline", 0))
        online_count = int(worker_summary.get("online", 0)) + int(worker_summary.get("busy", 0))

        if failed_count:
            alerts.append({
                "level": "danger",
                "title": "存在失败任务",
                "summary": f"当前共有 {failed_count} 个任务处于失败状态，建议优先查看任务详情和最近报告。",
                "action": "进入任务列表排查失败任务",
            })

        if degraded_count or offline_count:
            alerts.append({
                "level": "warning",
                "title": "Worker 节点需要关注",
                "summary": f"当前有 {degraded_count} 个降级节点、{offline_count} 个离线节点，可能影响调度稳定性。",
                "action": "进入系统管理查看 Worker 状态",
            })

        if stopping_count:
            alerts.append({
                "level": "warning",
                "title": "存在停止中任务",
                "summary": f"当前有 {stopping_count} 个任务仍在停止流程中，建议关注 worker 退出和状态回收。",
                "action": "进入监控或任务详情确认停止结果",
            })

        if online_count == 0:
            alerts.append({
                "level": "danger",
                "title": "当前无可用 Worker",
                "summary": "控制台未检测到可调度的在线 Worker，新的压测任务将无法正常分发。",
                "action": "优先恢复 Worker 连接或检查控制面状态",
            })

        if running_count and not alerts:
            alerts.append({
                "level": "success",
                "title": "平台运行平稳",
                "summary": f"当前有 {running_count} 个任务正在运行，未发现失败任务或明显的 Worker 风险。",
                "action": "可继续从控制台进入监控或报告页面查看详情",
            })

        if not alerts:
            alerts.append({
                "level": "info",
                "title": "当前无明显风险",
                "summary": "平台当前没有运行中的异常任务，也没有明显的 Worker 状态告警。",
                "action": "可通过快捷入口继续进行任务编排和执行",
            })

        return alerts[:4]

    def _serialize_task(self, task: Tasks) -> dict:
        return {
            "id": task.id,
            "name": task.name,
            "project": task.project,
            "host": task.host,
            "users": task.users,
            "status": task.status,
            "runtime": task.runtime,
            "start_time": task.start_time,
        }

    def _serialize_worker(self, worker: Worker) -> dict:
        return {
            "worker_id": worker.worker_id,
            "address": worker.address,
            "status": worker.status,
            "running_tasks": worker.running_tasks,
            "capacity": worker.capacity,
        }

    def _count(self, model, *filters) -> int:
        query = self.db.query(func.count(model.id))
        query = query.filter(model.is_deleted == false())
        if filters:
            query = query.filter(*filters)
        return int(query.scalar() or 0)
