import asyncio
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
        # 获取并发配置，默认并发数为 1 (保持向后兼容)
        concurrency = max(int(scenario.get("concurrency") or 1), 1)
        semaphore = asyncio.Semaphore(concurrency)
        
        async def run_case_with_semaphore(case: dict[str, Any]) -> dict[str, Any]:
            async with semaphore:
                return await self.case_runner.run(host=host, case=case, context=context)
        
        # 并发执行用例
        tasks = [run_case_with_semaphore(case) for case in cases]
        case_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果，确保顺序与输入一致
        ordered_results = []
        for i, result in enumerate(case_results):
            if isinstance(result, Exception):
                # 异常情况下的错误结果
                ordered_results.append({
                    "success": False,
                    "status_code": 0,
                    "response_time_ms": 0.0,
                    "body": "",
                    "error": str(result),
                    "error_type": "execution_error",
                    "extracted": {},
                    "retry_count": 0,
                })
            else:
                ordered_results.append(result)
                # 记录到聚合器
                aggregator.record(
                    method=str(cases[i].get("method") or "GET").upper(),
                    name=f"{scenario.get('name') or 'Scenario'} / {cases[i].get('name') or cases[i].get('url') or 'Case'}",
                    response_time_ms=result["response_time_ms"],
                    success=bool(result["success"]),
                    status_code=int(result.get("status_code") or 0),
                    error_type=result.get("error_type"),
                    error_message=result.get("error"),
                    content_length=len(result.get("body") or ""),
                )
        
        return ordered_results
