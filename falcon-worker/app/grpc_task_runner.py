import asyncio
import random
from datetime import datetime, timezone
from typing import Any

from app.engine_v2.metrics.local_aggregator import LocalMetricsAggregator
from app.engine_v2.registry.run_registry import TaskRunControl
from app.engine_v2.runtime.context import RuntimeContext
from app.engine_v2.runtime.scenario_runner import ScenarioRunner
from falcon_shared.runtime_enums import TaskCompletionPolicyEnum, TaskExecutionStrategyEnum, TaskRunStatusEnum
from falcon_shared.task_contracts import WorkerExecutionPlanItem
from app.control_plane_reporter import ControlPlaneReporter


class GrpcTaskRunner:
    def __init__(self) -> None:
        self.scenario_runner = ScenarioRunner()

    async def run(
        self,
        control: TaskRunControl,
        *,
        task_name: str,
        host: str,
        users: int,
        spawn_rate: int,
        duration: int,
        execution_strategy: str,
        completion_policy: str,
        execution_plan: list[WorkerExecutionPlanItem],
        reporter: ControlPlaneReporter,
    ) -> None:
        aggregator = LocalMetricsAggregator()
        latest_error: str | None = None
        active_users = 0
        started_at = datetime.now(timezone.utc)
        status = TaskRunStatusEnum.RUNNING

        await reporter.report(
            "started",
            status.value,
            started_at=started_at,
            summary=aggregator.build_snapshot(active_users=0, latest_error=None),
        )

        try:
            user_tasks: list[asyncio.Task] = []
            deadline = asyncio.get_running_loop().time() + max(duration or 1, 1)
            force_stop_on_deadline = str(completion_policy or TaskCompletionPolicyEnum.GRACEFUL).lower() == TaskCompletionPolicyEnum.FORCE
            forced_completion = False
            metrics_task = asyncio.create_task(
                self._metrics_loop(
                    aggregator=aggregator,
                    control=control,
                    reporter=reporter,
                    deadline=deadline,
                    started_at=started_at,
                    active_users_ref=lambda: active_users,
                )
            )

            while (
                asyncio.get_running_loop().time() < deadline
                and not control.cancel_event.is_set()
                and active_users < max(users, 1)
            ):
                can_spawn = min(spawn_rate, max(users - active_users, 0))
                for _ in range(can_spawn):
                    if control.cancel_event.is_set():
                        break
                    active_users += 1
                    user_task = asyncio.create_task(
                        self._virtual_user_loop(
                            host=host,
                            task_id=control.task_id,
                            task_run_id=control.task_run_id,
                            task_name=task_name,
                            execution_plan=execution_plan,
                            execution_strategy=execution_strategy,
                            aggregator=aggregator,
                            control=control,
                            deadline=deadline,
                            user_no=active_users,
                        )
                    )
                    user_tasks.append(user_task)
                await asyncio.sleep(1)

            if force_stop_on_deadline and not control.cancel_event.is_set():
                forced_completion = True
                control.cancel_event.set()
                for user_task in user_tasks:
                    if not user_task.done():
                        user_task.cancel()

            if user_tasks:
                results = await asyncio.gather(*user_tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, Exception):
                        if forced_completion and isinstance(result, asyncio.CancelledError):
                            continue
                        latest_error = str(result)

            await metrics_task

            finished_at = datetime.now(timezone.utc)
            runtime_seconds = max(int((finished_at - started_at).total_seconds()), 0)
            snapshot = aggregator.build_snapshot(active_users=active_users, latest_error=latest_error)
            control.last_snapshot = snapshot
            control.latest_error = latest_error

            status = (
                TaskRunStatusEnum.CANCELED
                if control.cancel_event.is_set() and not forced_completion
                else TaskRunStatusEnum.COMPLETED
            )
            await reporter.report(
                "canceled" if status == TaskRunStatusEnum.CANCELED else "finished",
                status.value,
                started_at=started_at,
                finished_at=finished_at,
                runtime_seconds=runtime_seconds,
                active_users=active_users,
                latest_error=latest_error,
                summary=snapshot,
            )
        except Exception as exc:
            latest_error = str(exc)
            finished_at = datetime.now(timezone.utc)
            snapshot = aggregator.build_snapshot(active_users=active_users, latest_error=latest_error)
            await reporter.report(
                "failed",
                TaskRunStatusEnum.FAILED.value,
                started_at=started_at,
                finished_at=finished_at,
                runtime_seconds=max(int((finished_at - started_at).total_seconds()), 0),
                active_users=active_users,
                latest_error=latest_error,
                summary=snapshot,
            )
        finally:
            await self.scenario_runner.close()

    async def _virtual_user_loop(
        self,
        *,
        host: str,
        task_id: int,
        task_run_id: int,
        task_name: str,
        execution_plan: list[WorkerExecutionPlanItem],
        execution_strategy: str,
        aggregator: LocalMetricsAggregator,
        control: TaskRunControl,
        deadline: float,
        user_no: int,
    ) -> None:
        context = RuntimeContext(
            task_id=task_id,
            task_run_id=task_run_id,
            host=host,
            task_variables={"user_no": user_no, "task_name": task_name},
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
                case_results = await self.scenario_runner.run(
                    host,
                    scenario_item.scenario,
                    scenario_item.cases,
                    context,
                    aggregator,
                )
                error_result = next((item for item in case_results if not item["success"]), None)
                if error_result and error_result.get("error"):
                    control.latest_error = str(error_result["error"])

    async def _metrics_loop(
        self,
        *,
        aggregator: LocalMetricsAggregator,
        control: TaskRunControl,
        reporter: ControlPlaneReporter,
        deadline: float,
        started_at: datetime,
        active_users_ref,
    ) -> None:
        while asyncio.get_running_loop().time() < deadline and not control.cancel_event.is_set():
            await asyncio.sleep(1)
            active_users = int(active_users_ref())
            latest_error = control.latest_error
            snapshot = aggregator.build_snapshot(active_users=active_users, latest_error=latest_error)
            metric = aggregator.build_second_metric(active_users=active_users)
            control.last_snapshot = snapshot
            await reporter.report(
                "snapshot",
                TaskRunStatusEnum.RUNNING.value,
                started_at=started_at,
                runtime_seconds=max(int((datetime.now(timezone.utc) - started_at).total_seconds()), 0),
                active_users=active_users,
                latest_error=latest_error,
                summary=snapshot,
                metric=metric,
            )

    def _select_scenarios_for_user(
        self,
        *,
        execution_plan: list[WorkerExecutionPlanItem],
        execution_strategy: str,
        user_no: int,
    ) -> list[WorkerExecutionPlanItem]:
        eligible_scenarios = [
            item for item in execution_plan
            if item.target_users is None or user_no <= item.target_users
        ]
        if not eligible_scenarios:
            return []

        if execution_strategy == TaskExecutionStrategyEnum.WEIGHTED:
            weights = [max(int(item.weight or 0), 0) for item in eligible_scenarios]
            if sum(weights) <= 0:
                weights = [1 for _ in eligible_scenarios]
            return [random.choices(eligible_scenarios, weights=weights, k=1)[0]]
        return eligible_scenarios
