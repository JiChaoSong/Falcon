import argparse
import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start Falcon master service.")
    parser.add_argument(
        "--env-file",
        dest="env_file",
        default=None,
        help="Path to the master env file. Defaults to falcon-master/.env.",
    )
    return parser.parse_args()


def _bootstrap_env_from_cli() -> None:
    if __name__ != "__main__":
        return

    cli_args = _parse_args()
    if cli_args.env_file:
        os.environ["FALCON_MASTER_ENV_FILE"] = str(Path(cli_args.env_file).expanduser().resolve())


_bootstrap_env_from_cli()


from app.api import case, dashboard, project, scenario, task, user, worker, ws
from app.core.audit import register_audit_listeners
from app.core.config import settings
from app.core.logging_config import get_logger, setup_logging
from app.db import Base
from app.grpc_master import grpc_server
from app.handler.validation_exception import register_validation_exception_handler
from app.middleware.auth import AuthMiddleware
from app.middleware.request_context import RequestContextMiddleware
from app.utils.banner import print_color_banner


setup_logging(
    log_level="INFO",
    use_json=False,
    console_color=True,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db import SessionLocal
    from app.services.worker_registry_service import WorkerRegistryService

    logger = get_logger(__name__)

    print_color_banner()
    register_audit_listeners(Base)
    grpc_server.start()

    health_check_task = None
    if settings.GRPC_WORKER_HEALTH_CHECK_ENABLED:
        async def health_check_loop() -> None:
            while True:
                db_session = SessionLocal()
                try:
                    registry = WorkerRegistryService(db_session)
                    await registry.perform_health_checks()
                except Exception as exc:
                    logger.error(f"Health check loop error: {exc}")
                finally:
                    db_session.close()

                await asyncio.sleep(max(int(settings.GRPC_WORKER_HEALTH_CHECK_INTERVAL_SECONDS or 30), 10))

        health_check_task = asyncio.create_task(health_check_loop())
        logger.info("Worker health check loop started")

    yield

    if health_check_task:
        health_check_task.cancel()
        try:
            await health_check_task
        except asyncio.CancelledError:
            pass
        logger.info("Worker health check loop stopped")

    grpc_server.stop()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        debug=settings.DEBUG,
        description="Falcon分布式压测引擎",
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        swagger_ui_css_url="https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.17.14/swagger-ui.css",
        swagger_ui_js_url="https://cdn.bootcdn.net/ajax/libs/swagger-ui/5.17.14/swagger-ui-bundle.js",
    )

    register_validation_exception_handler(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(AuthMiddleware)

    if settings.REQUEST_LOGGING:
        app.add_middleware(RequestContextMiddleware)

    app.include_router(project.router)
    app.include_router(case.router)
    app.include_router(scenario.router)
    app.include_router(task.router)
    app.include_router(dashboard.router)
    app.include_router(user.router)
    app.include_router(worker.router)
    app.include_router(ws.router)

    return app


def server() -> None:
    uvicorn.run(
        app="main:create_app",
        host=settings.HOST,
        port=settings.PORT,
        factory=True,
        reload=True,
        log_level="debug",
        access_log=True,
        loop="asyncio",
        workers=1,
        log_config=None,
    )


def main() -> None:
    server()


if __name__ == "__main__":
    main()
