from __future__ import annotations

from file_merge_tool.api.routes import system
from file_merge_tool.api.services.restart_server import schedule_server_restart


def test_schedule_server_restart_queues_background_task(monkeypatch) -> None:
    monkeypatch.setenv("FILE_MERGE_HOST", "127.0.0.1")
    monkeypatch.setenv("FILE_MERGE_PORT", "8750")
    calls: list[tuple[int, str, int]] = []

    def fake_launch_restart_helper(*, current_pid: int, host: str, port: int) -> None:
        calls.append((current_pid, host, port))

    monkeypatch.setattr(
        "file_merge_tool.api.services.restart_server._launch_restart_helper",
        fake_launch_restart_helper,
    )

    payload = schedule_server_restart()

    assert payload["status"] == "scheduled"
    assert payload["host"] == "127.0.0.1"
    assert payload["port"] == 8750
    assert len(calls) == 1
    _, host, port = calls[0]
    assert host == "127.0.0.1"
    assert port == 8750


def test_restart_endpoint_returns_schedule_payload(monkeypatch) -> None:
    expected = {"status": "scheduled", "host": "127.0.0.1", "port": 8750, "pid": 9999}

    def fake_schedule_restart() -> dict[str, object]:
        return expected

    monkeypatch.setattr(system, "schedule_server_restart", fake_schedule_restart)

    response = system.restart_server()

    assert response == expected
