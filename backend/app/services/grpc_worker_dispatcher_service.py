import json
import uuid
from typing import Any

import grpc
from sqlalchemy import Select, false
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exception import ParamException
from app.grpc.generated import worker_runtime_pb2, worker_runtime_pb2_grpc
from app.models import Case, CaseStatusEnum, Scenario, ScenarioCase, TaskScenario, Tasks
from app.services.worker_registry_service import WorkerRegistryService


class GrpcWorkerDispatcherService:
    def __init__(self, db: Session):
        self.db = db
        self.registry = WorkerRegistryService(db)

    def dispatch_start(self, *, task: Tasks, task_run_id: int) -> dict[str, Any]:
        worker_addr = self._select_worker()
        worker_task_id = f"{task.id}-{task_run_id}-{uuid.uuid4().hex[:12]}"
        execution_plan = self._load_execution_plan(task.id)

        channel = grpc.insecure_channel(worker_addr)
        try:
            stub = worker_runtime_pb2_grpc.WorkerRuntimeStub(channel)
            response = stub.StartTask(
                worker_runtime_pb2.StartTaskRequest(
                    worker_task_id=worker_task_id,
                    task=worker_runtime_pb2.TaskDefinition(
                        task_id=task.id,
                        task_run_id=task_run_id,
                        task_name=task.name,
                        host=task.host or "",
                        users=int(task.users or 0),
                        spawn_rate=int(task.spawn_rate or 0),
                        duration=int(task.duration or 0),
                        execution_strategy=getattr(task.execution_strategy, "value", str(task.execution_strategy)),
                        execution_plan_json=json.dumps(execution_plan, ensure_ascii=True),
                        control_plane_addr=f"{settings.GRPC_MASTER_HOST}:{settings.GRPC_MASTER_PORT}",
                    ),
                ),
                timeout=5,
            )
        except grpc.RpcError as exc:
            raise ParamException(f"Failed to dispatch task to worker: {exc.details() or exc.code().name}") from exc
        finally:
            channel.close()

        if not response.accepted:
            raise ParamException(response.message or "Worker rejected the task.")

        return {
            "worker_id": response.worker_id or worker_addr,
            "worker_task_id": response.worker_task_id or worker_task_id,
            "worker_addr": worker_addr,
        }

    def dispatch_stop(self, *, task_id: int, task_run_id: int, worker_task_id: str, worker_addr: str) -> dict[str, Any]:
        channel = grpc.insecure_channel(worker_addr)
        try:
            stub = worker_runtime_pb2_grpc.WorkerRuntimeStub(channel)
            response = stub.StopTask(
                worker_runtime_pb2.StopTaskRequest(
                    task_id=task_id,
                    task_run_id=task_run_id,
                    worker_task_id=worker_task_id,
                ),
                timeout=5,
            )
        except grpc.RpcError as exc:
            raise ParamException(f"Failed to stop task on worker: {exc.details() or exc.code().name}") from exc
        finally:
            channel.close()

        if not response.accepted:
            raise ParamException(response.message or "Worker rejected stop command.")

        return {
            "worker_id": response.worker_id or worker_addr,
            "worker_task_id": response.worker_task_id or worker_task_id,
        }

    def _select_worker(self) -> str:
        worker = self.registry.select_worker()
        return worker.address

    def _load_execution_plan(self, task_id: int) -> list[dict[str, Any]]:
        task_scenarios = self.db.execute(
            Select(TaskScenario).where(
                TaskScenario.task_id == task_id,
                TaskScenario.is_deleted == false(),
            ).order_by(TaskScenario.order.asc(), TaskScenario.id.asc())
        ).scalars().all()

        execution_plan: list[dict[str, Any]] = []
        for task_scenario in task_scenarios:
            scenario = self.db.execute(
                Select(Scenario).where(
                    Scenario.id == task_scenario.scenario_id,
                    Scenario.is_deleted == false(),
                )
            ).scalar_one_or_none()
            if not scenario:
                continue

            scenario_cases = self.db.execute(
                Select(ScenarioCase).where(
                    ScenarioCase.scenario_id == scenario.id,
                    ScenarioCase.is_deleted == false(),
                ).order_by(ScenarioCase.order.asc(), ScenarioCase.id.asc())
            ).scalars().all()

            cases: list[dict[str, Any]] = []
            for scenario_case in scenario_cases:
                case = self.db.execute(
                    Select(Case).where(
                        Case.id == scenario_case.case_id,
                        Case.is_deleted == false(),
                        Case.status == CaseStatusEnum.ACTIVE,
                    )
                ).scalar_one_or_none()
                if case:
                    cases.append(case.to_dict())

            if cases:
                execution_plan.append(
                    {
                        "scenario": scenario.to_dict(),
                        "cases": cases,
                        "weight": task_scenario.weight,
                        "target_users": task_scenario.target_users,
                    }
                )
        return execution_plan
