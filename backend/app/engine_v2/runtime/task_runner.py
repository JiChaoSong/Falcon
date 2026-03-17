import asyncio
import random
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Select, false

from app.db import SessionLocal
from app.engine_v2.metrics.local_aggregator import LocalMetricsAggregator
from app.engine_v2.registry.run_registry import TaskRunControl, task_run_registry
from app.engine_v2.runtime.context import RuntimeContext
from app.engine_v2.runtime.scenario_runner import ScenarioRunner
from app.models import (
    Case,
    Scenario,
    ScenarioCase,
    TaskExecutionStrategyEnum,
    TaskMetricSecond,
    TaskRun,
    TaskRunStatusEnum,
    Tasks,
    TaskStatusEnum,
    TaskScenario,
)


class TaskRunner:
    def __init__(self) -> None:
        self.scenario_runner = ScenarioRunner()

    async def run(self, control: TaskRunControl) -> None:
        db = SessionLocal()
        aggregator = LocalMetricsAggregator()
        latest_error: str | None = None

        try:
            task = db.execute(
                Select(Tasks).where(Tasks.id == control.task_id, Tasks.is_deleted == false())
            ).scalar_one()
            task_run = db.execute(
                Select(TaskRun).where(TaskRun.id == control.task_run_id, TaskRun.is_deleted == false())
            ).scalar_one()

            started_at = datetime.now(timezone.utc)
            task_run.status = TaskRunStatusEnum.RUNNING
            task_run.started_at = started_at
            task.status = TaskStatusEnum.RUNNING
            task.start_time = started_at
            task.finished_at = None
            task.runtime_seconds = 0
            task.runtime = "00:00:00"
            db.commit()

            execution_plan = self._load_execution_plan(db, task.id)
            active_users = 0
            user_tasks: list[asyncio.Task] = []
            metrics_task: asyncio.Task | None = None

            deadline = asyncio.get_running_loop().time() + max(task.duration or 1, 1)

            metrics_task = asyncio.create_task(
                self._metrics_loop(
                    db=db,
                    task=task,
                    task_run=task_run,
                    aggregator=aggregator,
                    control=control,
                    deadline=deadline,
                    active_users_ref=lambda: active_users,
                )
            )

            while (
                asyncio.get_running_loop().time() < deadline
                and not control.cancel_event.is_set()
                and active_users < max(task.users, 1)
            ):
                can_spawn = min(task.spawn_rate, max(task.users - active_users, 0))
                for user_index in range(can_spawn):
                    if control.cancel_event.is_set():
                        break
                    virtual_user_no = active_users + 1
                    active_users += 1
                    user_task = asyncio.create_task(
                        self._virtual_user_loop(
                            host=task.host,
                            task_id=task.id,
                            task_run_id=task_run.id,
                            execution_plan=execution_plan,
                            execution_strategy=task.execution_strategy,
                            aggregator=aggregator,
                            control=control,
                            deadline=deadline,
                            user_no=virtual_user_no,
                        )
                    )
                    user_tasks.append(user_task)
                await asyncio.sleep(1)

            if user_tasks:
                results = await asyncio.gather(*user_tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, Exception):
                        latest_error = str(result)

            if metrics_task:
                await metrics_task

            finished_at = datetime.now(timezone.utc)
            runtime_seconds = max(int((finished_at - started_at).total_seconds()), 0)
            snapshot = aggregator.build_snapshot(active_users=active_users, latest_error=latest_error)
            control.last_snapshot = snapshot
            control.latest_error = latest_error

            task_run.finished_at = finished_at
            task_run.runtime_seconds = runtime_seconds
            task_run.summary_json = snapshot
            task.finished_at = finished_at
            task.runtime_seconds = runtime_seconds
            task.runtime = self._format_runtime(runtime_seconds)
            task.stats = snapshot

            if control.cancel_event.is_set():
                task_run.status = TaskRunStatusEnum.CANCELED
                task.status = TaskStatusEnum.CANCELED
            else:
                task_run.status = TaskRunStatusEnum.COMPLETED
                task.status = TaskStatusEnum.COMPLETED
            db.commit()
        except Exception as exc:
            db.rollback()
            latest_error = str(exc)
            control.latest_error = latest_error
            self._mark_failed(db=db, task_id=control.task_id, task_run_id=control.task_run_id, error_message=latest_error)
        finally:
            db.close()
            task_run_registry.unregister(control.task_id)

    async def _virtual_user_loop(
        self,
        host: str,
        task_id: int,
        task_run_id: int,
        execution_plan: list[dict[str, Any]],
        execution_strategy: TaskExecutionStrategyEnum,
        aggregator: LocalMetricsAggregator,
        control: TaskRunControl,
        deadline: float,
        user_no: int,
    ) -> None:
        context = RuntimeContext(
            task_id=task_id,
            task_run_id=task_run_id,
            host=host,
            task_variables={"user_no": user_no},
        )

        while asyncio.get_running_loop().time() < deadline and not control.cancel_event.is_set():
            scenarios_to_run = self._select_scenarios_for_user(
                execution_plan=execution_plan,
                execution_strategy=execution_strategy,
                user_no=user_no,
            )
            for scenario_item in scenarios_to_run:
                if control.cancel_event.is_set() or asyncio.get_running_loop().time() >= deadline:
                    return
                case_results = await asyncio.to_thread(
                    self.scenario_runner.run,
                    host,
                    scenario_item["scenario"],
                    scenario_item["cases"],
                    context,
                    aggregator,
                )
                error_result = next((item for item in case_results if not item["success"]), None)
                if error_result and error_result.get("error"):
                    control.latest_error = str(error_result["error"])

    # Weighted strategy does not execute the full chain every round.
    # It picks one eligible scenario according to configured weights.
    def _select_scenarios_for_user(
        self,
        execution_plan: list[dict[str, Any]],
        execution_strategy: TaskExecutionStrategyEnum,
        user_no: int,
    ) -> list[dict[str, Any]]:
        eligible_scenarios = [
            item for item in execution_plan
            if item["target_users"] is None or user_no <= item["target_users"]
        ]
        if not eligible_scenarios:
            return []

        if execution_strategy == TaskExecutionStrategyEnum.WEIGHTED:
            weights = [max(int(item["weight"] or 0), 0) for item in eligible_scenarios]
            if sum(weights) <= 0:
                weights = [1 for _ in eligible_scenarios]
            return [random.choices(eligible_scenarios, weights=weights, k=1)[0]]

        return eligible_scenarios

    async def _metrics_loop(
        self,
        db,
        task: Tasks,
        task_run: TaskRun,
        aggregator: LocalMetricsAggregator,
        control: TaskRunControl,
        deadline: float,
        active_users_ref,
    ) -> None:
        latest_error = None
        while asyncio.get_running_loop().time() < deadline and not control.cancel_event.is_set():
            await asyncio.sleep(1)
            latest_error = control.latest_error
            await self._flush_metric(
                db=db,
                task=task,
                task_run=task_run,
                aggregator=aggregator,
                active_users=active_users_ref(),
                latest_error=latest_error,
            )

    def _load_execution_plan(self, db, task_id: int) -> list[dict[str, Any]]:
        task_scenarios = db.execute(
            Select(TaskScenario).where(
                TaskScenario.task_id == task_id,
                TaskScenario.is_deleted == false(),
            ).order_by(TaskScenario.order.asc(), TaskScenario.id.asc())
        ).scalars().all()

        execution_plan: list[dict[str, Any]] = []
        for task_scenario in task_scenarios:
            scenario = db.execute(
                Select(Scenario).where(
                    Scenario.id == task_scenario.scenario_id,
                    Scenario.is_deleted == false(),
                )
            ).scalar_one_or_none()
            if not scenario:
                continue

            scenario_cases = db.execute(
                Select(ScenarioCase).where(
                    ScenarioCase.scenario_id == scenario.id,
                    ScenarioCase.is_deleted == false(),
                ).order_by(ScenarioCase.order.asc(), ScenarioCase.id.asc())
            ).scalars().all()

            cases: list[dict[str, Any]] = []
            for scenario_case in scenario_cases:
                case = db.execute(
                    Select(Case).where(
                        Case.id == scenario_case.case_id,
                        Case.is_deleted == false(),
                    )
                ).scalar_one_or_none()
                if case:
                    cases.append(case.to_dict())

            execution_plan.append({
                "scenario": scenario.to_dict(),
                "cases": cases,
                "weight": task_scenario.weight,
                "target_users": task_scenario.target_users,
            })

        return execution_plan

    async def _flush_metric(
        self,
        db,
        task: Tasks,
        task_run: TaskRun,
        aggregator: LocalMetricsAggregator,
        active_users: int,
        latest_error: str | None,
    ) -> None:
        snapshot = aggregator.build_snapshot(active_users=active_users, latest_error=latest_error)
        metric = aggregator.build_second_metric(active_users=active_users)
        control = task_run_registry.get(task.id)
        if control:
            control.last_snapshot = snapshot
            control.latest_error = latest_error

        task.runtime_seconds = max(int((datetime.now(timezone.utc) - (task_run.started_at or datetime.now(timezone.utc))).total_seconds()), 0)
        task.runtime = self._format_runtime(task.runtime_seconds)
        task.stats = snapshot
        task_run.runtime_seconds = task.runtime_seconds
        task_run.summary_json = snapshot

        db.add(
            TaskMetricSecond(
                task_run_id=task_run.id,
                task_id=task.id,
                scenario_id=None,
                **metric,
            )
        )
        db.commit()

    def _mark_failed(self, db, task_id: int, task_run_id: int, error_message: str) -> None:
        task = db.execute(
            Select(Tasks).where(Tasks.id == task_id, Tasks.is_deleted == false())
        ).scalar_one_or_none()
        task_run = db.execute(
            Select(TaskRun).where(TaskRun.id == task_run_id, TaskRun.is_deleted == false())
        ).scalar_one_or_none()
        finished_at = datetime.now(timezone.utc)

        if task_run:
            task_run.status = TaskRunStatusEnum.FAILED
            task_run.finished_at = finished_at
            task_run.error_message = error_message[:500]

        if task:
            task.status = TaskStatusEnum.FAILED
            task.finished_at = finished_at

        db.commit()

    def _format_runtime(self, seconds: int) -> str:
        hour = str(seconds // 3600).zfill(2)
        minute = str((seconds % 3600) // 60).zfill(2)
        second = str(seconds % 60).zfill(2)
        return f"{hour}:{minute}:{second}"
