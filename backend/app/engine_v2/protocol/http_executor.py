import json
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


class HTTPExecutor:
    def execute(
        self,
        host: str,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        body: str | None = None,
        timeout: int = 10,
    ) -> dict[str, Any]:
        request_url = url if url.startswith("http://") or url.startswith("https://") else urljoin(host.rstrip("/") + "/", url.lstrip("/"))
        request_headers = headers or {}
        request_body = body.encode("utf-8") if body else None

        started_at = time.perf_counter()
        try:
            request = Request(
                request_url,
                data=request_body,
                headers=request_headers,
                method=method.upper(),
            )
            with urlopen(request, timeout=timeout) as response:
                response_text = response.read().decode("utf-8", errors="ignore")
                elapsed_ms = (time.perf_counter() - started_at) * 1000
                return {
                    "success": 200 <= response.status < 400,
                    "status_code": response.status,
                    "response_time_ms": elapsed_ms,
                    "body": response_text,
                    "error": None,
                }
        except HTTPError as exc:
            elapsed_ms = (time.perf_counter() - started_at) * 1000
            body_text = exc.read().decode("utf-8", errors="ignore") if exc.fp else ""
            return {
                "success": False,
                "status_code": exc.code,
                "response_time_ms": elapsed_ms,
                "body": body_text,
                "error": str(exc),
            }
        except URLError as exc:
            elapsed_ms = (time.perf_counter() - started_at) * 1000
            return {
                "success": False,
                "status_code": 0,
                "response_time_ms": elapsed_ms,
                "body": "",
                "error": str(exc),
            }

    def normalize_headers(self, headers: Any) -> dict[str, str]:
        if isinstance(headers, dict):
            return {str(key): str(value) for key, value in headers.items()}
        if isinstance(headers, list):
            result: dict[str, str] = {}
            for item in headers:
                if isinstance(item, dict) and item.get("name"):
                    result[str(item["name"])] = str(item.get("value") or "")
            return result
        return {}

    def normalize_body(self, body: Any) -> str | None:
        if body is None:
            return None
        if isinstance(body, str):
            return body
        return json.dumps(body, ensure_ascii=False)
