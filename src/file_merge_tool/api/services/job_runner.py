from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import BackgroundTasks

from file_merge_tool.api.schemas.requests import JobCreateRequest
from file_merge_tool.api.services.job_store import JobRecord, put_job, update_job
from file_merge_tool.application.create_file_list import default_output_name as file_list_output_name
from file_merge_tool.application.merge_text import default_output_name as text_merge_output_name
from file_merge_tool.application.run_job import run_job
from file_merge_tool.domain.config import ExcludeConfig, MergeRequest
from file_merge_tool.domain.merge_job import MergeKind
from file_merge_tool.infrastructure.filesystem import default_output_dir, ensure_safe_output_name
from file_merge_tool.infrastructure.history import make_history_dir, write_manifest


def submit_job(payload: JobCreateRequest, background_tasks: BackgroundTasks) -> JobRecord:
    job_id = uuid4().hex
    record = JobRecord(
        id=job_id,
        kind=payload.kind.value,
        root_path=str(payload.root_path),
        setting_name=payload.setting_name,
    )
    put_job(record)
    background_tasks.add_task(_run_job, job_id, payload)
    return record


def _run_job(job_id: str, payload: JobCreateRequest) -> None:
    started_at = _now()
    history_dir = make_history_dir(payload.kind.value, job_id)
    update_job(job_id, status="running", started_at=started_at, history_dir=str(history_dir))
    try:
        output_name = ensure_safe_output_name(
            payload.output_name or "",
            _default_output_name(payload.kind),
        )
        request = MergeRequest(
            root_path=Path(payload.root_path),
            output_dir=history_dir,
            output_name=output_name,
            output_stem=payload.output_stem,
            exclude=ExcludeConfig.from_iterables(
                folder_names=payload.exclude_dirs,
                extensions=payload.exclude_extensions,
                file_names=payload.exclude_files,
            ),
            job_id=job_id,
            kind=payload.kind.value,
            setting_name=payload.setting_name,
            sensitivity_markers=tuple(payload.additional_sensitive_markers),
            image_output_formats=tuple(payload.image_output_formats),
        )
        result = run_job(payload.kind, request)
    except Exception as exc:  # noqa: BLE001
        finished_at = _now()
        error = str(exc)
        update_job(job_id, status="failed", error=error, finished_at=finished_at)
        write_manifest(
            history_dir,
            _manifest(
                job_id=job_id,
                payload=payload,
                status="failed",
                started_at=started_at,
                finished_at=finished_at,
                history_dir=history_dir,
                output_paths=[],
                item_count=None,
                skipped_count=None,
                warnings=[],
                error=error,
            ),
        )
        return

    finished_at = _now()
    update_job(
        job_id,
        status="completed",
        finished_at=finished_at,
        output_paths=[str(path) for path in result.output_paths],
        item_count=result.item_count,
        skipped_count=result.skipped_count,
        warnings=list(result.warnings),
    )
    write_manifest(
        history_dir,
        _manifest(
            job_id=job_id,
            payload=payload,
            status="completed",
            started_at=started_at,
            finished_at=finished_at,
            history_dir=history_dir,
            output_paths=list(result.output_paths),
            item_count=result.item_count,
            skipped_count=result.skipped_count,
            warnings=list(result.warnings),
            error=None,
        ),
    )


def _default_output_name(kind: MergeKind) -> str:
    if kind == MergeKind.FILE_LIST:
        return file_list_output_name()
    if kind == MergeKind.TEXT_MERGE:
        return text_merge_output_name()
    if kind == MergeKind.MAIL_MERGE:
        return "mail-merge.json"
    if kind == MergeKind.POWERPOINT_MERGE:
        return "merged.pptx"
    if kind == MergeKind.EXCEL_MERGE:
        return "merged.xlsx"
    if kind == MergeKind.WORD_MERGE:
        return "merged.docx"
    if kind == MergeKind.PDF_MERGE:
        return "merged.pdf"
    if kind == MergeKind.IMAGE_MERGE:
        return "images.html"
    return f"{kind.value}.json"


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _manifest(
    *,
    job_id: str,
    payload: JobCreateRequest,
    status: str,
    started_at: str,
    finished_at: str,
    history_dir: Path,
    output_paths: list[Path],
    item_count: int | None,
    skipped_count: int | None,
    warnings: list[str],
    error: str | None,
) -> dict[str, object]:
    return {
        "schema": "file-merge-tool/history-manifest/v1",
        "job_id": job_id,
        "kind": payload.kind.value,
        "status": status,
        "started_at": started_at,
        "finished_at": finished_at,
        "setting_name": payload.setting_name,
        "source_root": str(payload.root_path),
        "history_dir": str(history_dir),
        "outputs": [
            {
                "classification": _classification_for_path(path),
                "format": path.suffix.lstrip("."),
                "path": str(path),
                "download_name": path.name,
            }
            for path in output_paths
        ],
        "request": {
            "output_stem": payload.output_stem,
            "output_name": payload.output_name,
            "image_output_formats": payload.image_output_formats,
            "exclude_dirs": payload.exclude_dirs,
            "exclude_extensions": payload.exclude_extensions,
            "exclude_files": payload.exclude_files,
            "additional_sensitive_markers": payload.additional_sensitive_markers,
        },
        "summary": {
            "item_count": item_count,
            "skipped_count": skipped_count,
            "warning_count": len(warnings),
        },
        "warnings": warnings,
        "error": error,
    }


def _classification_for_path(path: Path) -> str:
    return "sensitive" if "_\u6a5f\u5bc6" in path.stem else "normal"
