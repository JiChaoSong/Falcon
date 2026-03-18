import argparse
import os
from pathlib import Path


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

    from app.core.config import worker_settings
    from app.core.logging_config import get_logger, setup_logging
    from app.worker.control_plane_client import worker_control_plane_client
    from app.worker.worker_server import create_worker_server
    from app.worker.worker_runtime_service import worker_runtime_service

    setup_logging(
        log_level=worker_settings.LOG_LEVEL,
        use_json=False,
        console_color=True,
    )

    logger = get_logger(__name__)
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
    server.wait_for_termination()


if __name__ == "__main__":
    main()
