from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock


@dataclass
class JobRecord:
    id: str
    kind: str
    root_path: str
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    )
    started_at: str | None = None
    finished_at: str | None = None
    setting_name: str | None = None
    history_dir: str | None = None
    status: str = "queued"
    output_paths: list[str] = field(default_factory=list)
    item_count: int | None = None
    skipped_count: int | None = None
    warnings: list[str] = field(default_factory=list)
    error: str | None = None


_jobs: dict[str, JobRecord] = {}
_lock = Lock()


def put_job(record: JobRecord) -> JobRecord:
    with _lock:
        _jobs[record.id] = record
    return record


def get_job(job_id: str) -> JobRecord | None:
    with _lock:
        return _jobs.get(job_id)


def update_job(job_id: str, **changes: object) -> None:
    with _lock:
        record = _jobs[job_id]
        for key, value in changes.items():
            setattr(record, key, value)
