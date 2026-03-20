import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.worker", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "Falcon Worker"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "local"
    LOG_LEVEL: str = "INFO"

    GRPC_MASTER_HOST: str = "127.0.0.1"
    GRPC_MASTER_PORT: int = 50051
    WORKER_SHARED_TOKEN: str = "change-me-worker-token"

    GRPC_WORKER_ID: str = "worker-local"
    GRPC_WORKER_HOST: str = "127.0.0.1"
    GRPC_WORKER_PORT: int = 50061
    GRPC_WORKER_TAGS: str = ""
    GRPC_WORKER_METADATA_JSON: str = "{}"
    GRPC_WORKER_CAPACITY: int = 4
    GRPC_WORKER_HEARTBEAT_INTERVAL_SECONDS: int = 5


def _resolve_worker_env_file() -> tuple[str, ...]:
    raw = str(os.getenv("FALCON_WORKER_ENV_FILE", "")).strip()
    if not raw:
        return ".env.worker", ".env"

    return tuple(item.strip() for item in raw.split(os.pathsep) if item.strip()) or (".env.worker", ".env")


worker_settings = WorkerSettings(_env_file=_resolve_worker_env_file())
