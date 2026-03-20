import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any


class WorkerLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg: str, kwargs: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        extra = dict(kwargs.get("extra") or {})
        if self.extra:
            extra.update(self.extra)
        kwargs["extra"] = extra
        return msg, kwargs


class WorkerFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        worker_id = getattr(record, "worker_id", "-")
        thread_name = getattr(record, "threadName", "-")
        process_id = getattr(record, "process", "-")
        location = f"{record.name}:{record.lineno}"
        message = record.getMessage()

        if record.exc_info:
            message = f"{message}\n{self.formatException(record.exc_info)}"

        return (
            f"{timestamp} | {record.levelname:8} | "
            f"WORKER:{worker_id} | {thread_name} | PID:{process_id} | "
            f"{location} | {message}"
        )


def setup_worker_logging(*, worker_id: str, log_level: str = "INFO") -> None:
    current_file = Path(__file__).resolve()
    project_root = current_file.parents[1]
    log_dir = project_root / "logs"

    log_dir.mkdir(parents=True, exist_ok=True)

    date_suffix = datetime.now().strftime("%Y-%m-%d")
    safe_worker_id = (worker_id or "worker").replace(":", "_").replace("/", "_").replace("\\", "_")

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.filters.clear()
    root_logger.setLevel(getattr(logging, str(log_level).upper(), logging.INFO))
    root_logger.propagate = False

    formatter = WorkerFormatter()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(root_logger.level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    file_handler = RotatingFileHandler(
        filename=str(log_dir / f"worker_{safe_worker_id}_{date_suffix}.log"),
        maxBytes=20 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8",
    )
    file_handler.setLevel(root_logger.level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    error_handler = RotatingFileHandler(
        filename=str(log_dir / f"worker_error_{safe_worker_id}_{date_suffix}.log"),
        maxBytes=20 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)

    for logger_name, level in {
        "grpc": "WARNING",
        "asyncio": "WARNING",
    }.items():
        logging.getLogger(logger_name).setLevel(getattr(logging, level))


def get_worker_logger(name: str, *, worker_id: str | None = None) -> WorkerLoggerAdapter:
    return WorkerLoggerAdapter(logging.getLogger(name), {"worker_id": worker_id or "-"})
