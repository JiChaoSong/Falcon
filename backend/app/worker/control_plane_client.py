import json
import threading
import time
from typing import Any

from app.core.config import worker_settings
from app.core.logging_config import get_logger
from app.grpc.generated import worker_runtime_pb2, worker_runtime_pb2_grpc
import grpc

logger = get_logger(__name__)


class WorkerControlPlaneClient:
    def __init__(self) -> None:
        self._heartbeat_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def register(self) -> None:
        self._register_via_grpc()
        logger.info(f"Registered worker_runtime {worker_settings.GRPC_WORKER_ID} to control plane")

    def start_heartbeat_loop(self, get_running_tasks) -> None:
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            return
        self._stop_event.clear()
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            args=(get_running_tasks,),
            name="worker-heartbeat",
            daemon=True,
        )
        self._heartbeat_thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def _heartbeat_loop(self, get_running_tasks) -> None:
        interval = max(int(worker_settings.GRPC_WORKER_HEARTBEAT_INTERVAL_SECONDS or 5), 1)
        while not self._stop_event.is_set():
            try:
                payload = {
                    "worker_id": worker_settings.GRPC_WORKER_ID,
                    "running_tasks": int(get_running_tasks()),
                    "capacity": worker_settings.GRPC_WORKER_CAPACITY,
                    "tags": self._parse_tags(),
                    "metadata_json": self._parse_metadata(),
                    "version": worker_settings.VERSION,
                }
                self._heartbeat_via_grpc(payload)
            except Exception as exc:
                logger.error(f"worker_runtime heartbeat failed: {exc}")
            time.sleep(interval)

    def _register_via_grpc(self) -> None:
        with self._create_channel() as channel:
            stub = worker_runtime_pb2_grpc.ControlPlaneRuntimeStub(channel)
            response = stub.RegisterWorker(
                worker_runtime_pb2.WorkerRegisterRequest(
                    token=worker_settings.WORKER_SHARED_TOKEN,
                    worker_id=worker_settings.GRPC_WORKER_ID,
                    host=worker_settings.GRPC_WORKER_HOST,
                    port=worker_settings.GRPC_WORKER_PORT,
                    version=worker_settings.VERSION,
                    capacity=worker_settings.GRPC_WORKER_CAPACITY,
                    scheduling_weight=100,
                    tags=self._parse_tags(),
                    metadata_json=json.dumps(self._parse_metadata(), ensure_ascii=True),
                ),
                timeout=5,
            )
            if not response.accepted:
                raise RuntimeError(response.message or "worker registration rejected")

    def _heartbeat_via_grpc(self, payload: dict[str, Any]) -> None:
        with self._create_channel() as channel:
            stub = worker_runtime_pb2_grpc.ControlPlaneRuntimeStub(channel)
            response = stub.HeartbeatWorker(
                worker_runtime_pb2.WorkerHeartbeatRequest(
                    token=worker_settings.WORKER_SHARED_TOKEN,
                    worker_id=str(payload["worker_id"]),
                    running_tasks=int(payload["running_tasks"]),
                    capacity=int(payload["capacity"]),
                    tags=list(payload["tags"]),
                    metadata_json=json.dumps(payload["metadata_json"], ensure_ascii=True),
                    version=str(payload["version"]),
                    last_seen_error="",
                ),
                timeout=5,
            )
            if not response.accepted:
                raise RuntimeError(response.message or "worker heartbeat rejected")

    def _create_channel(self):
        return grpc.insecure_channel(
            f"{worker_settings.GRPC_CONTROL_HOST}:{worker_settings.GRPC_CONTROL_PORT}"
        )

    def _parse_tags(self) -> list[str]:
        return [item.strip() for item in str(worker_settings.GRPC_WORKER_TAGS or "").split(",") if item.strip()]

    def _parse_metadata(self) -> dict[str, Any]:
        raw = str(worker_settings.GRPC_WORKER_METADATA_JSON or "").strip()
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}


worker_control_plane_client = WorkerControlPlaneClient()
