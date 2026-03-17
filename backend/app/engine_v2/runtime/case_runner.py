from typing import Any

from app.engine_v2.protocol.http_executor import HTTPExecutor
from app.engine_v2.runtime.context import RuntimeContext


class CaseRunner:
    def __init__(self) -> None:
        self.http_executor = HTTPExecutor()

    def run(self, host: str, case: dict[str, Any], context: RuntimeContext) -> dict[str, Any]:
        method = str(case.get("method") or "GET").upper()
        url = context.render_text(case.get("url")) or "/"
        headers = self.http_executor.normalize_headers(case.get("headers"))
        body = self.http_executor.normalize_body(case.get("body"))

        result = self.http_executor.execute(
            host=host,
            method=method,
            url=url,
            headers=headers,
            body=body,
        )

        expected_status = case.get("expected_status")
        if expected_status and str(result["status_code"]) != str(expected_status):
            result["success"] = False
            result["error"] = (
                result["error"]
                or f"Expected status {expected_status}, got {result['status_code']}"
            )

        return result
