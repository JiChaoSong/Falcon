from typing import Any

from app.engine_v2.metrics.local_aggregator import LocalMetricsAggregator
from app.engine_v2.runtime.case_runner import CaseRunner
from app.engine_v2.runtime.context import RuntimeContext


class ScenarioRunner:
    def __init__(self) -> None:
        self.case_runner = CaseRunner()

    async def close(self) -> None:
        await self.case_runner.close()

    async def run(
        self,
        host: str,
        scenario: dict[str, Any],
        cases: list[dict[str, Any]],
        context: RuntimeContext,
        aggregator: LocalMetricsAggregator,
    ) -> list[dict[str, Any]]:
        case_results: list[dict[str, Any]] = []
        for case in cases:
            result = await self.case_runner.run(host=host, case=case, context=context)
            aggregator.record(
                method=str(case.get("method") or "GET").upper(),
                name=f"{scenario.get('name') or 'Scenario'} / {case.get('name') or case.get('url') or 'Case'}",
                response_time_ms=result["response_time_ms"],
                success=bool(result["success"]),
                status_code=int(result.get("status_code") or 0),
                error_type=result.get("error_type"),
                error_message=result.get("error"),
                content_length=len(result.get("body") or ""),
            )
            case_results.append(result)
        return case_results
