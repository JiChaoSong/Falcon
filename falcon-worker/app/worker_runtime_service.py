import asyncio
import threading
from dataclasses import dataclass

from app.engine_v2.registry.run_registry import TaskRunControl
from falcon_shared.task_contracts import WorkerExecutionPlanItem, WorkerTaskDefinition
from app.control_plane_reporter import ControlPlaneReporter
from app.grpc_task_runner import GrpcTaskRunner
from app.settings import worker_settings


@dataclass
class WorkerTaskHandle:
    control: TaskRunControl
    thread: threading.Thread


class WorkerRuntimeService:
    def __init__(self) -> None:
        self._tasks: dict[str, WorkerTaskHandle] = {}
        self._lock = threading.Lock()

    def start_task(
        self,
        *,
        worker_task_id: str,
        task_id: int,
        task_run_id: int,
        task_name: str,
        host: str,
        users: int,
        spawn_rate: int,
        duration: int,
        execution_strategy: str,
        completion_policy: str,
        execution_plan_json: str,
        control_plane_addr: str,
    ) -> tuple[bool, str]:
        with self._lock:
            if worker_task_id in self._tasks:
                return False, "Task already running on worker."

            control = TaskRunControl(task_id=task_id, task_run_id=task_run_id)
            thread = threading.Thread(
                target=self._run_task,
                kwargs={
                    "worker_task_id": worker_task_id,
                    "control": control,
                    "task_name": task_name,
                    "host": host,
                    "users": users,
                    "spawn_rate": spawn_rate,
                    "duration": duration,
                    "execution_strategy": execution_strategy,
                    "completion_policy": completion_policy,
                    "execution_plan": WorkerTaskDefinition.load_execution_plan_json(execution_plan_json),
                    "control_plane_addr": control_plane_addr,
                },
                name=f"grpc-worker-task-{task_id}",
                daemon=True,
            )
            self._tasks[worker_task_id] = WorkerTaskHandle(control=control, thread=thread)
            thread.start()
            return True, "Task accepted by worker."

    def stop_task(self, worker_task_id: str) -> tuple[bool, str]:
        with self._lock:
            handle = self._tasks.get(worker_task_id)
            if not handle:
                return False, "Task is not running on worker."
            handle.control.cancel_event.set()
            return True, "Stop signal delivered."

    def running_tasks(self) -> int:
        with self._lock:
            return len(self._tasks)

    def stop_all_tasks(self) -> int:
        with self._lock:
            handles = list(self._tasks.values())
            for handle in handles:
                handle.control.cancel_event.set()
            return len(handles)

    def _run_task(
        self,
        *,
        worker_task_id: str,
        control: TaskRunControl,
        task_name: str,
        host: str,
        users: int,
        spawn_rate: int,
        duration: int,
        execution_strategy: str,
        completion_policy: str,
        execution_plan: list[WorkerExecutionPlanItem],
        control_plane_addr: str,
    ) -> None:
        reporter = ControlPlaneReporter(
            control_plane_addr=control_plane_addr,
            worker_id=worker_settings.GRPC_WORKER_ID,
            worker_task_id=worker_task_id,
            task_id=control.task_id,
            task_run_id=control.task_run_id,
        )
        try:
            asyncio.run(
                GrpcTaskRunner().run(
                    control,
                    task_name=task_name,
                    host=host,
                    users=users,
                    spawn_rate=spawn_rate,
                    duration=duration,
                    execution_strategy=execution_strategy,
                    completion_policy=completion_policy,
                    execution_plan=execution_plan,
                    reporter=reporter,
                )
            )
        finally:
            with self._lock:
                self._tasks.pop(worker_task_id, None)


worker_runtime_service = WorkerRuntimeService()
