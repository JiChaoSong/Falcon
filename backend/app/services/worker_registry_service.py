from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import itertools
from typing import Any

import grpc
from sqlalchemy import Select, false
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exception import ParamException
from app.core.logging_config import get_logger
from app.grpc.generated import worker_runtime_pb2, worker_runtime_pb2_grpc
from app.models import Worker, WorkerSchedulingStrategyEnum, WorkerStatusEnum

logger = get_logger(__name__)


class WorkerRegistryService:
    _round_robin_cycle = None
    _round_robin_source: tuple[str, ...] = ()

    def __init__(self, db: Session):
        self.db = db

    def register(
        self,
        *,
        worker_id: str,
        host: str,
        port: int,
        version: str | None,
        capacity: int,
        scheduling_weight: int,
        tags: list[str] | None,
        metadata_json: dict[str, Any] | None,
    ) -> Worker:
        self.cleanup_stale_workers()
        now = datetime.now(timezone.utc)
        worker = self._get_worker(worker_id)
        address = f"{host}:{port}"
        normalized_tags = self._normalize_tags(tags)

        if worker:
            worker.host = host
            worker.port = port
            worker.address = address
            worker.version = version
            worker.capacity = max(int(capacity or 1), 1)
            worker.scheduling_weight = max(int(scheduling_weight or 100), 1)
            worker.tags = normalized_tags
            worker.metadata_json = metadata_json or {}
            worker.status = self._derive_status(worker.status, worker.running_tasks, worker.capacity, None)
            worker.last_heartbeat_at = now
            worker.last_seen_error = None
        else:
            worker = Worker(
                worker_id=worker_id,
                host=host,
                port=port,
                address=address,
                version=version,
                status=WorkerStatusEnum.ONLINE,
                capacity=max(int(capacity or 1), 1),
                running_tasks=0,
                scheduling_weight=max(int(scheduling_weight or 100), 1),
                tags=normalized_tags,
                metadata_json=metadata_json or {},
                registered_at=now,
                last_heartbeat_at=now,
                last_seen_error=None,
            )
            self.db.add(worker)

        self.db.commit()
        return worker

    def heartbeat(
        self,
        *,
        worker_id: str,
        running_tasks: int,
        capacity: int | None,
        tags: list[str] | None,
        metadata_json: dict[str, Any] | None,
        version: str | None,
        last_seen_error: str | None,
    ) -> Worker:
        self.cleanup_stale_workers()
        worker = self._require_worker(worker_id)
        now = datetime.now(timezone.utc)

        worker.running_tasks = max(int(running_tasks or 0), 0)
        if capacity is not None:
            worker.capacity = max(int(capacity or 1), 1)
        if tags is not None:
            worker.tags = self._normalize_tags(tags)
        if metadata_json is not None:
            worker.metadata_json = metadata_json
        if version:
            worker.version = version
        worker.last_seen_error = (last_seen_error or "")[:500] or None
        worker.last_heartbeat_at = now
        worker.status = self._derive_status(worker.status, worker.running_tasks, worker.capacity, worker.last_seen_error)

        self.db.commit()
        return worker

    def list(self, *, page: int, page_size: int, worker_id: str | None, status: WorkerStatusEnum | None, tag: str | None) -> dict[str, Any]:
        self.mark_timeouts()
        self.cleanup_stale_workers()

        workers = self.db.execute(
            Select(Worker).where(Worker.is_deleted == false()).order_by(Worker.updated_at.desc(), Worker.id.desc())
        ).scalars().all()

        if worker_id:
            workers = [item for item in workers if worker_id.lower() in item.worker_id.lower()]
        if status:
            workers = [item for item in workers if item.status == status]
        if tag:
            workers = [item for item in workers if tag in (item.tags or [])]

        total = len(workers)
        start = max((page - 1) * page_size, 0)
        end = start + page_size
        results = [self._to_payload(item) for item in workers[start:end]]
        return {"results": results, "total": total}

    def info(self, worker_id: str) -> dict[str, Any]:
        self.mark_timeouts()
        self.cleanup_stale_workers()
        worker = self._require_worker(worker_id)
        return self._to_payload(worker)

    def update(
        self,
        *,
        worker_id: str,
        status: WorkerStatusEnum | None,
        capacity: int | None,
        scheduling_weight: int | None,
        tags: list[str] | None,
        metadata_json: dict[str, Any] | None,
    ) -> dict[str, Any]:
        worker = self._require_worker(worker_id)
        if status is not None:
            worker.status = status
        if capacity is not None:
            worker.capacity = max(int(capacity or 1), 1)
        if scheduling_weight is not None:
            worker.scheduling_weight = max(int(scheduling_weight or 1), 1)
        if tags is not None:
            worker.tags = self._normalize_tags(tags)
        if metadata_json is not None:
            worker.metadata_json = metadata_json
        self.db.commit()
        self.db.refresh(worker)
        return self._to_payload(worker)

    def mark_timeouts(self) -> None:
        timeout_seconds = max(int(settings.GRPC_WORKER_HEARTBEAT_TIMEOUT_SECONDS or 15), 1)
        threshold = datetime.now(timezone.utc) - timedelta(seconds=timeout_seconds)
        workers = self.db.execute(
            Select(Worker).where(
                Worker.is_deleted == false(),
                Worker.status.in_([
                    WorkerStatusEnum.ONLINE,
                    WorkerStatusEnum.BUSY,
                    WorkerStatusEnum.DEGRADED,
                ]),
            )
        ).scalars().all()

        dirty = False
        for worker in workers:
            last_seen = worker.last_heartbeat_at
            if last_seen.tzinfo is None:
                last_seen = last_seen.replace(tzinfo=timezone.utc)
            if last_seen < threshold:
                worker.status = WorkerStatusEnum.OFFLINE
                dirty = True
        if dirty:
            self.db.commit()

    def cleanup_stale_workers(self) -> None:
        retention_seconds = max(int(settings.GRPC_WORKER_HISTORY_RETENTION_SECONDS or 86400), 1)
        threshold = datetime.now(timezone.utc) - timedelta(seconds=retention_seconds)
        workers = self.db.execute(
            Select(Worker).where(
                Worker.is_deleted == false(),
                Worker.status != WorkerStatusEnum.DISABLED,
            )
        ).scalars().all()

        deleted_count = 0
        for worker in workers:
            last_seen = worker.last_heartbeat_at
            if last_seen.tzinfo is None:
                last_seen = last_seen.replace(tzinfo=timezone.utc)
            if last_seen >= threshold:
                continue

            worker.status = WorkerStatusEnum.OFFLINE
            worker.soft_delete()
            deleted_count += 1

        if deleted_count:
            self.db.commit()
            logger.info(
                "Worker history cleanup - deleted_count=%s retention_seconds=%s",
                deleted_count,
                retention_seconds,
            )

    def select_worker(self, required_tags: list[str] | None = None) -> Worker:
        self.mark_timeouts()
        self.cleanup_stale_workers()
        workers = self.db.execute(
            Select(Worker).where(
                Worker.is_deleted == false(),
                Worker.status.in_([WorkerStatusEnum.ONLINE, WorkerStatusEnum.BUSY, WorkerStatusEnum.DEGRADED]),
            )
        ).scalars().all()
        workers = [item for item in workers if int(item.running_tasks or 0) < max(int(item.capacity or 1), 1)]

        required_tags = self._normalize_tags(required_tags)
        if required_tags:
            workers = [
                item for item in workers
                if all(tag in (item.tags or []) for tag in required_tags)
            ]
        if not workers:
            raise ParamException("No available worker matched the scheduling conditions.")

        strategy = str(settings.GRPC_SCHEDULING_STRATEGY or WorkerSchedulingStrategyEnum.LEAST_LOADED)
        if strategy == WorkerSchedulingStrategyEnum.ROUND_ROBIN:
            ordered = sorted(workers, key=lambda item: item.worker_id)
            return self._next_round_robin_worker(ordered)

        if strategy == WorkerSchedulingStrategyEnum.WEIGHTED:
            workers.sort(
                key=lambda item: (
                    self._load_ratio(item),
                    -int(item.scheduling_weight or 0),
                    item.worker_id,
                )
            )
            return workers[0]

        workers.sort(
            key=lambda item: (
                self._load_ratio(item),
                int(item.running_tasks or 0),
                -int(item.capacity or 0),
                item.worker_id,
            )
        )
        return workers[0]

    def _next_round_robin_worker(self, workers: list[Worker]) -> Worker:
        addresses = tuple(item.address for item in workers)
        if not self.__class__._round_robin_cycle or self.__class__._round_robin_source != addresses:
            self.__class__._round_robin_cycle = itertools.cycle(addresses)
            self.__class__._round_robin_source = addresses
        next_address = next(self.__class__._round_robin_cycle)
        for worker in workers:
            if worker.address == next_address:
                return worker
        return workers[0]

    def _get_worker(self, worker_id: str) -> Worker | None:
        return self.db.execute(
            Select(Worker).where(
                Worker.worker_id == worker_id,
                Worker.is_deleted == false(),
            )
        ).scalar_one_or_none()

    def _require_worker(self, worker_id: str) -> Worker:
        worker = self._get_worker(worker_id)
        if not worker:
            raise ParamException("Worker not found.")
        return worker

    def _normalize_tags(self, tags: list[str] | None) -> list[str]:
        return [str(item).strip() for item in (tags or []) if str(item).strip()]

    def _derive_status(
        self,
        current_status: WorkerStatusEnum,
        running_tasks: int,
        capacity: int,
        last_seen_error: str | None,
    ) -> WorkerStatusEnum:
        if current_status == WorkerStatusEnum.DISABLED:
            return current_status
        if last_seen_error:
            return WorkerStatusEnum.DEGRADED
        if capacity > 0 and running_tasks >= capacity:
            return WorkerStatusEnum.BUSY
        return WorkerStatusEnum.ONLINE

    def _is_timeout(self, worker: Worker) -> bool:
        timeout_seconds = max(int(settings.GRPC_WORKER_HEARTBEAT_TIMEOUT_SECONDS or 15), 1)
        threshold = datetime.now(timezone.utc) - timedelta(seconds=timeout_seconds)
        last_seen = worker.last_heartbeat_at
        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        return last_seen < threshold

    def _load_ratio(self, worker: Worker) -> float:
        capacity = max(int(worker.capacity or 1), 1)
        return round(float(worker.running_tasks or 0) / capacity, 4)

    def _to_payload(self, worker: Worker) -> dict[str, Any]:
        return {
            "id": worker.id,
            "worker_id": worker.worker_id,
            "host": worker.host,
            "port": worker.port,
            "address": worker.address,
            "version": worker.version,
            "status": worker.status,
            "capacity": worker.capacity,
            "running_tasks": worker.running_tasks,
            "scheduling_weight": worker.scheduling_weight,
            "tags": list(worker.tags or []),
            "metadata_json": worker.metadata_json or {},
            "registered_at": worker.registered_at,
            "last_heartbeat_at": worker.last_heartbeat_at,
            "last_seen_error": worker.last_seen_error,
            "is_timeout": self._is_timeout(worker),
            "created_at": worker.created_at,
            "updated_at": worker.updated_at,
        }

    async def perform_health_checks(self) -> None:
        """执行主动健康检查，更新 Worker 状态"""
        workers = self.db.execute(
            Select(Worker).where(
                Worker.is_deleted == false(),
                Worker.status.in_([WorkerStatusEnum.ONLINE, WorkerStatusEnum.BUSY, WorkerStatusEnum.DEGRADED]),
            )
        ).scalars().all()

        if not workers:
            return

        # 并发执行健康检查
        tasks = [self._check_worker_health(worker) for worker in workers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 更新状态
        dirty = False
        for worker, result in zip(workers, results):
            if isinstance(result, Exception):
                logger.warning(f"Health check failed for worker {worker.worker_id}: {result}")
                if worker.status != WorkerStatusEnum.DEGRADED:
                    worker.status = WorkerStatusEnum.DEGRADED
                    worker.last_seen_error = str(result)
                    dirty = True
            else:
                health_status, response_time, error_msg = result
                if health_status:
                    # 健康检查通过
                    if worker.status == WorkerStatusEnum.DEGRADED:
                        worker.status = WorkerStatusEnum.ONLINE
                        worker.last_seen_error = None
                        dirty = True
                    # 更新性能指标到 metadata
                    metadata = worker.metadata_json or {}
                    metadata["last_health_check"] = {
                        "response_time_ms": response_time,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    worker.metadata_json = metadata
                    dirty = True
                else:
                    # 健康检查失败
                    if worker.status != WorkerStatusEnum.DEGRADED:
                        worker.status = WorkerStatusEnum.DEGRADED
                        worker.last_seen_error = error_msg
                        dirty = True

        if dirty:
            self.db.commit()

    async def _check_worker_health(self, worker: Worker) -> tuple[bool, float, str]:
        """检查单个 Worker 的健康状态"""
        channel = None
        try:
            channel = grpc.insecure_channel(worker.address, options=[
                ('grpc.keepalive_time_ms', 10000),
                ('grpc.keepalive_timeout_ms', 5000),
            ])
            stub = worker_runtime_pb2_grpc.WorkerRuntimeStub(channel)
            
            # 执行健康检查请求
            started_at = datetime.now(timezone.utc)
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: stub.Health(
                    worker_runtime_pb2.HealthRequest(),
                    timeout=5.0
                )
            )
            elapsed = (datetime.now(timezone.utc) - started_at).total_seconds() * 1000
            
            return True, elapsed, ""
            
        except grpc.RpcError as exc:
            elapsed = (datetime.now(timezone.utc) - started_at).total_seconds() * 1000 if 'started_at' in locals() else 0
            return False, elapsed, f"gRPC error: {exc.details() or exc.code().name}"
        except Exception as exc:
            elapsed = (datetime.now(timezone.utc) - started_at).total_seconds() * 1000 if 'started_at' in locals() else 0
            return False, elapsed, f"Health check error: {str(exc)}"
        finally:
            if channel:
                await asyncio.get_event_loop().run_in_executor(None, channel.close)
