import asyncio
from types import SimpleNamespace

from app.models import TaskRunStatusEnum, TaskStatusEnum
from app.services.grpc_runtime_event_service import GrpcRuntimeEventService


class _FakeScalarOneOrNoneResult:
    def __init__(self, item):
        self._item = item

    def scalar_one_or_none(self):
        return self._item


class _FakeSession:
    def __init__(self, task, task_run):
        self._task = task
        self._task_run = task_run
        self.commit_count = 0

    def execute(self, query):
        text = str(query)
        if "FROM tasks" in text:
            return _FakeScalarOneOrNoneResult(self._task)
        if "FROM task_runs" in text:
            return _FakeScalarOneOrNoneResult(self._task_run)
        raise AssertionError(f"Unexpected query: {text}")

    def add(self, _item):
        return None

    def commit(self):
        self.commit_count += 1

    def close(self):
        return None


def test_snapshot_keeps_stopping_status(monkeypatch):
    task = SimpleNamespace(
        id=101,
        status=TaskStatusEnum.STOPPING,
        start_time=None,
        finished_at=None,
        runtime_seconds=0,
        runtime="00:00:00",
        stats={},
        is_deleted=False,
    )
    task_run = SimpleNamespace(
        id=9001,
        status=TaskRunStatusEnum.STOPPING,
        started_at=None,
        finished_at=None,
        runtime_seconds=0,
        summary_json={},
        error_message=None,
        is_deleted=False,
    )
    session = _FakeSession(task=task, task_run=task_run)
    published = {}

    monkeypatch.setattr(
        "app.services.grpc_runtime_event_service.SessionLocal",
        lambda: session,
    )

    async def _fake_publish(task_id, event_type, payload):
        published.update({"task_id": task_id, "event_type": event_type, "payload": payload})

    monkeypatch.setattr(
        "app.services.grpc_runtime_event_service.task_runtime_ws_manager.publish",
        _fake_publish,
    )

    asyncio.run(
        GrpcRuntimeEventService().handle_event(
            task_id=101,
            task_run_id=9001,
            event_type="snapshot",
            status="running",
            runtime_seconds=12,
            active_users=3,
            summary_json="{}",
            metric_json="{}",
        )
    )

    assert task.status == TaskStatusEnum.STOPPING
    assert task_run.status == TaskRunStatusEnum.STOPPING
    assert session.commit_count == 1
    assert published["event_type"] == "snapshot"
