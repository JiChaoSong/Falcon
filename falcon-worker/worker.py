import argparse
import os
from pathlib import Path

from app.banner import print_color_banner


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start Falcon gRPC worker.")
    parser.add_argument(
        "--env-file",
        dest="env_file",
        default=None,
        help="Path to the worker env file. Defaults to .env.worker, then .env.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.env_file:
        os.environ["FALCON_WORKER_ENV_FILE"] = str(Path(args.env_file).resolve())

    from app.logging_config import get_worker_logger, setup_worker_logging
    from app.settings import worker_settings
    from app.control_plane_client import worker_control_plane_client
    from app.worker_server import create_worker_server
    from app.worker_runtime_service import worker_runtime_service

    setup_worker_logging(worker_id=worker_settings.GRPC_WORKER_ID, log_level=worker_settings.LOG_LEVEL)
    print_color_banner()

    logger = get_worker_logger(__name__, worker_id=worker_settings.GRPC_WORKER_ID)
    if args.env_file:
        logger.info(f"Loading worker config from {Path(args.env_file).resolve()}")

    logger.info(
        f"Starting gRPC worker {worker_settings.GRPC_WORKER_ID} on "
        f"{worker_settings.GRPC_WORKER_HOST}:{worker_settings.GRPC_WORKER_PORT}"
    )
    worker_control_plane_client.register()
    server = create_worker_server()
    server.start()
    worker_control_plane_client.start_heartbeat_loop(worker_runtime_service.running_tasks)
    logger.info("gRPC worker is ready and waiting for tasks")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal, stopping gRPC worker gracefully")
    finally:
        running_task_count = worker_runtime_service.stop_all_tasks()
        if running_task_count:
            logger.info(f"Sent stop signal to {running_task_count} running task(s)")

        worker_control_plane_client.stop()
        server.stop(grace=3)
        logger.info("gRPC worker stopped")


if __name__ == "__main__":
    main()
