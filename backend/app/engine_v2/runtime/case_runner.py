from typing import Any

from app.engine_v2.protocol.http_executor import HTTPExecutor
from app.engine_v2.runtime.context import RuntimeContext
from app.engine_v2.runtime.response_utils import apply_extractions, evaluate_assertion


class CaseRunner:
    def __init__(self) -> None:
        self.http_executor = HTTPExecutor()

    async def close(self) -> None:
        await self.http_executor.close()

    async def run(self, host: str, case: dict[str, Any], context: RuntimeContext) -> dict[str, Any]:
        method = str(case.get("method") or "GET").upper()
        url = context.render_text(case.get("url")) or "/"
        headers = self.http_executor.normalize_headers(context.render_value(case.get("headers")))
        body = self.http_executor.normalize_body(context.render_value(case.get("body")))

        result = await self.http_executor.execute(
            host=host,
            method=method,
            url=url,
            headers=headers,
            body=body,
        )

        expected_status = case.get("expected_status")
        if expected_status and str(result["status_code"]) != str(expected_status):
            result["success"] = False
            result["error_type"] = "unexpected_status"
            result["error"] = (
                result["error"]
                or f"Expected status {expected_status}, got {result['status_code']}"
            )

        expected_response_time = case.get("expected_response_time")
        if (
            expected_response_time is not None
            and float(result["response_time_ms"]) > float(expected_response_time)
        ):
            result["success"] = False
            result["error_type"] = "slow_response"
            result["error"] = (
                result["error"]
                or f"Expected response time <= {expected_response_time}ms, got {round(float(result['response_time_ms']), 2)}ms"
            )

        assertion_ok, assertion_error = evaluate_assertion(case.get("assertion"), result.get("body"))
        if not assertion_ok:
            result["success"] = False
            result["error_type"] = "assertion_failed"
            result["error"] = result["error"] or assertion_error

        extract_rules = case.get("extract")
        if extract_rules:
            try:
                extracted = apply_extractions(result.get("body"), extract_rules)
                context.update_variables(extracted)
                result["extracted"] = extracted
            except (ValueError, KeyError, IndexError) as exc:
                result["success"] = False
                result["error_type"] = "extract_failed"
                result["error"] = result["error"] or f"Extract failed: {exc}"
                result["extracted"] = {}
        else:
            result["extracted"] = {}

        if not result.get("error_type"):
            if result["success"]:
                result["error_type"] = None
            else:
                result["error_type"] = "request_failed"

        return result
