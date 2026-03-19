import asyncio
import json
import threading
from concurrent import futures

import grpc

from app.core.config import settings
from app.core.logging_config import get_logger
from app.db import SessionLocal
from app.grpc.generated import worker_runtime_pb2, worker_runtime_pb2_grpc
from app.services.grpc_runtime_event_service import grpc_runtime_event_service
from app.services.worker_registry_service import WorkerRegistryService

logger = get_logger(__name__)


class ControlPlaneRuntimeServicer(worker_runtime_pb2_grpc.ControlPlaneRuntimeServicer):
    def ReportTaskEvent(self, request, context):
        asyncio.run(
            grpc_runtime_event_service.handle_event(
                task_id=request.task_id,
                task_run_id=request.task_run_id,
                event_type=request.event_type,
                status=request.status,
                started_at=request.started_at,
                finished_at=request.finished_at,
                runtime_seconds=request.runtime_seconds,
                active_users=request.active_users,
                latest_error=request.latest_error,
                summary_json=request.summary_json,
                metric_json=request.metric_json,
            )
        )
        return worker_runtime_pb2.CommandAck(
            accepted=True,
            message="event accepted",
            worker_id="control-plane",
            worker_task_id=request.worker_task_id,
        )

    def RegisterWorker(self, request, context):
        if request.token != settings.WORKER_SHARED_TOKEN:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid worker token.")

        db = SessionLocal()
        try:
            service = WorkerRegistryService(db)
            worker = service.register(
                worker_id=request.worker_id,
                host=request.host,
                port=request.port,
                version=request.version or None,
                capacity=request.capacity,
                scheduling_weight=request.scheduling_weight,
                tags=list(request.tags),
                metadata_json=self._parse_metadata(request.metadata_json),
            )
            logger.info(
                "Worker registered - worker_id=%s address=%s:%s capacity=%s tags=%s",
                worker.worker_id,
                worker.host,
                worker.port,
                worker.capacity,
                ",".join(worker.tags or []) or "-",
            )
            return worker_runtime_pb2.CommandAck(
                accepted=True,
                message="worker registered",
                worker_id=worker.worker_id,
                worker_task_id="",
            )
        finally:
            db.close()

    def HeartbeatWorker(self, request, context):
        if request.token != settings.WORKER_SHARED_TOKEN:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid worker token.")

        db = SessionLocal()
        try:
            service = WorkerRegistryService(db)
            worker = service.heartbeat(
                worker_id=request.worker_id,
                running_tasks=request.running_tasks,
                capacity=request.capacity if request.capacity > 0 else None,
                tags=list(request.tags) if request.tags else None,
                metadata_json=self._parse_metadata(request.metadata_json) if request.metadata_json else None,
                version=request.version or None,
                last_seen_error=request.last_seen_error or None,
            )
            logger.info(
                "Worker heartbeat - worker_id=%s status=%s running_tasks=%s capacity=%s error=%s",
                worker.worker_id,
                worker.status,
                worker.running_tasks,
                worker.capacity,
                worker.last_seen_error or "-",
            )
            return worker_runtime_pb2.CommandAck(
                accepted=True,
                message="worker heartbeat accepted",
                worker_id=worker.worker_id,
                worker_task_id="",
            )
        finally:
            db.close()

    def _parse_metadata(self, payload: str) -> dict:
        if not payload:
            return {}
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}


class ControlPlaneGrpcServer:
    def __init__(self) -> None:
        self._server: grpc.Server | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._server:
            return

        self._server = grpc.server(futures.ThreadPoolExecutor(max_workers=16))
        worker_runtime_pb2_grpc.add_ControlPlaneRuntimeServicer_to_server(
            ControlPlaneRuntimeServicer(),
            self._server,
        )
        self._server.add_insecure_port(f"{settings.GRPC_MASTER_HOST}:{settings.GRPC_MASTER_PORT}")
        self._thread = threading.Thread(target=self._server.start, name="grpc-control-plane", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if not self._server:
            return
        self._server.stop(grace=None)
        self._server = None
        self._thread = None


control_plane_grpc_server = ControlPlaneGrpcServer()
