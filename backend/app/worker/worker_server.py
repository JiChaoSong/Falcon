from concurrent import futures

import grpc

from app.core.config import worker_settings
from app.core.logging_config import get_logger
from app.grpc.generated import worker_runtime_pb2, worker_runtime_pb2_grpc
from app.worker.worker_runtime_service import worker_runtime_service

logger = get_logger(__name__)


class WorkerRuntimeServicer(worker_runtime_pb2_grpc.WorkerRuntimeServicer):
    def StartTask(self, request, context):
        accepted, message = worker_runtime_service.start_task(
            worker_task_id=request.worker_task_id,
            task_id=request.task.task_id,
            task_run_id=request.task.task_run_id,
            task_name=request.task.task_name,
            host=request.task.host,
            users=request.task.users,
            spawn_rate=request.task.spawn_rate,
            duration=request.task.duration,
            execution_strategy=request.task.execution_strategy,
            execution_plan_json=request.task.execution_plan_json,
            control_plane_addr=request.task.control_plane_addr,
        )
        logger.info(
            f"worker_runtime received StartTask for task_id={request.task.task_id}, "
            f"task_run_id={request.task.task_run_id}, accepted={accepted}"
        )
        return worker_runtime_pb2.CommandAck(
            accepted=accepted,
            message=message,
            worker_id=worker_settings.GRPC_WORKER_ID,
            worker_task_id=request.worker_task_id,
        )

    def StopTask(self, request, context):
        accepted, message = worker_runtime_service.stop_task(request.worker_task_id)
        logger.info(
            f"worker_runtime received StopTask for task_id={request.task_id}, "
            f"task_run_id={request.task_run_id}, accepted={accepted}"
        )
        return worker_runtime_pb2.CommandAck(
            accepted=accepted,
            message=message,
            worker_id=worker_settings.GRPC_WORKER_ID,
            worker_task_id=request.worker_task_id,
        )

    def Health(self, request, context):
        return worker_runtime_pb2.HealthResponse(
            worker_id=worker_settings.GRPC_WORKER_ID,
            host=worker_settings.GRPC_WORKER_HOST,
            port=worker_settings.GRPC_WORKER_PORT,
            healthy=True,
            running_tasks=worker_runtime_service.running_tasks(),
        )


def create_worker_server() -> grpc.Server:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=16))
    worker_runtime_pb2_grpc.add_WorkerRuntimeServicer_to_server(WorkerRuntimeServicer(), server)
    server.add_insecure_port(f"{worker_settings.GRPC_WORKER_HOST}:{worker_settings.GRPC_WORKER_PORT}")
    logger.info(
        f"Registered gRPC worker_runtime server for {worker_settings.GRPC_WORKER_ID} "
        f"at {worker_settings.GRPC_WORKER_HOST}:{worker_settings.GRPC_WORKER_PORT}"
    )
    return server
