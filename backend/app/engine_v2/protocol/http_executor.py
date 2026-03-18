import json
import time
from typing import Any
from urllib.parse import urljoin

import httpx


class HTTPExecutor:
    def __init__(self) -> None:
        self.client = httpx.AsyncClient(
            timeout=10.0,
            follow_redirects=False,
            limits=httpx.Limits(
                max_connections=1000,
                max_keepalive_connections=200,
                keepalive_expiry=30.0,
            ),
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def execute(
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
            response = await self.client.request(
                method=method.upper(),
                url=request_url,
                headers=request_headers,
                content=request_body,
                timeout=float(timeout),
            )
            elapsed_ms = (time.perf_counter() - started_at) * 1000
            return {
                "success": 200 <= response.status_code < 400,
                "status_code": response.status_code,
                "response_time_ms": elapsed_ms,
                "body": response.text,
                "error": None if 200 <= response.status_code < 400 else f"HTTP {response.status_code}",
            }
        except httpx.HTTPError as exc:
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
