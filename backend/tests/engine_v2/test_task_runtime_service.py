from types import SimpleNamespace

from app.models import TaskRunStatusEnum, TaskStatusEnum
from app.services.task_runtime_service import TaskRuntimeService


class _FakeScalarResult:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items


class _FakeExecuteResult:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return _FakeScalarResult(self._items)


class _FakeSession:
    def execute(self, _query):
        return _FakeExecuteResult([SimpleNamespace(id=1), SimpleNamespace(id=2)])


def test_task_runtime_report_includes_runtime_distributions(monkeypatch):
    service = TaskRuntimeService(_FakeSession())
    service.access_control.ensure_project_view_access = lambda _project_id: None

    task = SimpleNamespace(
        id=101,
        name="checkout task",
        project="demo",
        owner="tester",
        host="http://example.com",
        execution_strategy="sequential",
        project_id=1,
    )
    task_run = SimpleNamespace(id=9001)
    runtime_status = {
        "task_run_id": 9001,
        "status": "running",
        "started_at": "2026-03-18T10:00:00Z",
        "finished_at": None,
        "runtime_seconds": 12,
        "total_requests": 50,
        "success_count": 47,
        "fail_count": 3,
        "success_ratio": 0.94,
        "avg_rt": 120.5,
        "p95": 240.1,
        "p99": 380.8,
        "latest_error": "HTTP 500",
        "status_code_counts": {"200": 47, "500": 3},
        "error_type_counts": {"unexpected_status": 2, "slow_response": 1},
        "failure_samples": [{"name": "login", "message": "HTTP 500"}],
        "stats": [
            {
                "name": "checkout / login",
                "method": "POST",
                "num_requests": 30,
                "num_failures": 1,
                "avg_response_time": 80,
                "response_time_percentile_0.95": 120,
                "response_time_percentile_0.99": 180,
            },
            {
                "name": "checkout / submit",
                "method": "POST",
                "num_requests": 20,
                "num_failures": 2,
                "avg_response_time": 220,
                "response_time_percentile_0.95": 320,
                "response_time_percentile_0.99": 400,
            },
        ],
        "history": [{"ts": "2026-03-18T10:00:12Z", "rps": 10}],
    }

    monkeypatch.setattr(service, "_get_task", lambda _task_id: task)
    monkeypatch.setattr(service, "_get_task_run", lambda **_kwargs: task_run)
    monkeypatch.setattr(service, "_build_runtime_status", lambda **_kwargs: runtime_status)

    report = service.report(task_id=task.id, task_run_id=task_run.id)

    assert report["task_run_id"] == 9001
    assert report["scenario_count"] == 2
    assert report["status_code_counts"] == {"200": 47, "500": 3}
    assert report["error_type_counts"] == {"unexpected_status": 2, "slow_response": 1}
    assert report["failure_samples"] == [{"name": "login", "message": "HTTP 500"}]
    assert report["hottest_endpoint"]["name"] == "checkout / login"
    assert report["riskiest_endpoint"]["name"] == "checkout / submit"


class _FakeStopSession:
    def __init__(self):
        self.commit_count = 0

    def commit(self):
        self.commit_count += 1


def test_stop_marks_task_and_run_as_stopping(monkeypatch):
    session = _FakeStopSession()
    service = TaskRuntimeService(session)
    service.access_control.ensure_project_manage_access = lambda _project_id: None

    task = SimpleNamespace(id=101, project_id=1, status=TaskStatusEnum.RUNNING)
    latest_run = SimpleNamespace(
        id=9001,
        status=TaskRunStatusEnum.RUNNING,
        summary_json={"worker_task_id": "worker-task-1", "worker_addr": "127.0.0.1:50061"},
    )
    dispatched = {}

    monkeypatch.setattr(service, "_get_task", lambda _task_id: task)
    monkeypatch.setattr(service, "_get_latest_task_run", lambda _task_id: latest_run)
    service.dispatcher.dispatch_stop = lambda **kwargs: dispatched.update(kwargs)

    result = service.stop(task.id)

    assert result["status"] == TaskRunStatusEnum.STOPPING
    assert latest_run.status == TaskRunStatusEnum.STOPPING
    assert task.status == TaskStatusEnum.STOPPING
    assert session.commit_count == 1
    assert dispatched["task_run_id"] == latest_run.id
