from __future__ import annotations

from pydantic import BaseModel

from file_merge_tool.api.services.job_store import JobRecord


class JobCreateResponse(BaseModel):
    job_id: str
    status: str


class JobDetailResponse(BaseModel):
    job_id: str
    status: str
    kind: str
    root_path: str
    created_at: str
    started_at: str | None = None
    finished_at: str | None = None
    setting_name: str | None = None
    history_dir: str | None = None
    output_paths: list[str]
    item_count: int | None = None
    skipped_count: int | None = None
    warnings: list[str]
    error: str | None = None

    @classmethod
    def from_record(cls, record: JobRecord) -> "JobDetailResponse":
        return cls(
            job_id=record.id,
            status=record.status,
            kind=record.kind,
            root_path=record.root_path,
            created_at=record.created_at,
            started_at=record.started_at,
            finished_at=record.finished_at,
            setting_name=record.setting_name,
            history_dir=record.history_dir,
            output_paths=record.output_paths,
            item_count=record.item_count,
            skipped_count=record.skipped_count,
            warnings=record.warnings,
            error=record.error,
        )
