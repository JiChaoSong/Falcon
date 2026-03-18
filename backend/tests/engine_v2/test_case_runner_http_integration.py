import asyncio
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from app.engine_v2.runtime.case_runner import CaseRunner
from app.engine_v2.runtime.context import RuntimeContext


class _IntegrationHandler(BaseHTTPRequestHandler):
    server_version = "FalconTestHTTP/1.0"

    def do_GET(self):
        if self.path == "/token":
            payload = {"token": "integration-token", "user": {"id": 7}}
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        if self.path != "/echo":
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        request_body = self.rfile.read(content_length).decode("utf-8") if content_length else ""
        response_payload = {
            "authorization": self.headers.get("Authorization"),
            "body": request_body,
        }
        body = json.dumps(response_payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format, *_args):
        return


def _start_test_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _IntegrationHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def test_case_runner_executes_real_http_requests_and_renders_context():
    server, thread = _start_test_server()
    base_url = f"http://127.0.0.1:{server.server_port}"

    runner = CaseRunner()
    context = RuntimeContext(
        task_id=1,
        task_run_id=1,
        host=base_url,
    )

    try:
        first_result = asyncio.run(
            runner.run(
                host=base_url,
                case={
                    "method": "GET",
                    "url": "/token",
                    "extract": {
                        "token": "$.token",
                        "user_id": "$.user.id",
                    },
                    "assertion": "json:$.token=integration-token",
                },
                context=context,
            )
        )

        second_result = asyncio.run(
            runner.run(
                host=base_url,
                case={
                    "method": "POST",
                    "url": "/echo",
                    "headers": {
                        "Authorization": "Bearer {{token}}",
                    },
                    "body": {
                        "actor": "{{user_id}}",
                        "token": "{{token}}",
                    },
                    "assertion": "contains:integration-token",
                },
                context=context,
            )
        )
    finally:
        asyncio.run(runner.close())
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)

    assert first_result["success"] is True
    assert first_result["extracted"] == {
        "token": "integration-token",
        "user_id": 7,
    }

    assert second_result["success"] is True
    assert second_result["status_code"] == 200
    response_body = json.loads(second_result["body"])
    assert response_body["authorization"] == "Bearer integration-token"
    assert json.loads(response_body["body"]) == {
        "actor": "7",
        "token": "integration-token",
    }
