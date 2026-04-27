from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import BackgroundTasks

from file_merge_tool.application.output_files import output_folder_name as resolve_output_folder_name
from file_merge_tool.application.output_files import summary_output_path
from file_merge_tool.application.run_summary import build_run_summary_payload, write_run_summary
from file_merge_tool.api.schemas.requests import JobCreateRequest
from file_merge_tool.api.services.job_store import JobRecord, put_job, update_job
from file_merge_tool.application.create_file_list import default_output_name as file_list_output_name
from file_merge_tool.application.merge_text import default_output_name as text_merge_output_name
from file_merge_tool.application.run_job import run_job
from file_merge_tool.domain.config import ExcludeConfig, MergeRequest
from file_merge_tool.domain.merge_job import MergeKind
from file_merge_tool.infrastructure.filesystem import default_output_dir, ensure_safe_output_name
from file_merge_tool.infrastructure.history import make_history_dir, write_manifest
from file_merge_tool.infrastructure.output_metadata import build_output_record


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
    resolved_output_folder_name = _resolve_output_folder_name(payload)
    history_dir = make_history_dir(payload.kind.value, job_id, resolved_output_folder_name)
    update_job(job_id, status="running", started_at=started_at, history_dir=str(history_dir))
    request = MergeRequest(
        root_path=Path(payload.root_path),
        output_dir=history_dir,
        output_name=ensure_safe_output_name(
            payload.output_name or "",
            _default_output_name(payload.kind),
        ),
        output_stem=payload.output_stem,
        output_folder_name=resolved_output_folder_name,
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
    try:
        result = run_job(payload.kind, request)
    except Exception as exc:  # noqa: BLE001
        finished_at = _now()
        error = str(exc)
        summary_path = summary_output_path(
            request,
            default_name=resolved_output_folder_name,
        )
        output_records = [build_output_record(summary_path)]
        summary_payload = build_run_summary_payload(
            request=request,
            status="failed",
            started_at=started_at,
            finished_at=finished_at,
            history_dir=history_dir,
            outputs=output_records,
            result=None,
            warnings=[],
            error=error,
        )
        write_run_summary(summary_path, summary_payload)
        update_job(job_id, status="failed", error=error, finished_at=finished_at)
        write_manifest(
            history_dir,
            _manifest(
                job_id=job_id,
                request=request,
                status="failed",
                started_at=started_at,
                finished_at=finished_at,
                history_dir=history_dir,
                outputs=output_records,
                result=None,
                warnings=[],
                error=error,
            ),
        )
        return

    finished_at = _now()
    output_records = [build_output_record(path) for path in result.output_paths]
    summary_path = summary_output_path(request, default_name=resolved_output_folder_name)
    summary_record = build_output_record(summary_path)
    summary_payload = build_run_summary_payload(
        request=request,
        status="completed",
        started_at=started_at,
        finished_at=finished_at,
        history_dir=history_dir,
        outputs=[*output_records, summary_record],
        result=result,
        warnings=list(result.warnings),
        error=None,
    )
    write_run_summary(summary_path, summary_payload)
    output_records.append(summary_record)
    update_job(
        job_id,
        status="completed",
        finished_at=finished_at,
        output_paths=[record["path"] for record in output_records],
        item_count=result.item_count,
        skipped_count=result.skipped_count,
        warnings=list(result.warnings),
    )
    write_manifest(
        history_dir,
        _manifest(
            job_id=job_id,
            request=request,
            status="completed",
            started_at=started_at,
            finished_at=finished_at,
            history_dir=history_dir,
            outputs=output_records,
            result=result,
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


def _resolve_output_folder_name(payload: JobCreateRequest) -> str:
    request = MergeRequest(
        root_path=Path(payload.root_path),
        output_dir=default_output_dir(),
        output_name=_default_output_name(payload.kind),
        output_stem=payload.output_stem,
        output_folder_name=payload.output_folder_name,
    )
    return resolve_output_folder_name(
        request,
        default_name=Path(_default_output_name(payload.kind)).stem,
    )


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _manifest(
    *,
    job_id: str,
    request: MergeRequest,
    status: str,
    started_at: str,
    finished_at: str,
    history_dir: Path,
    outputs: list[dict[str, object]],
    result: object | None,
    warnings: list[str],
    error: str | None,
) -> dict[str, object]:
    item_count = getattr(result, "item_count", None)
    skipped_count = getattr(result, "skipped_count", None)
    excluded_count = getattr(result, "excluded_count", None)
    error_skipped_count = getattr(result, "error_skipped_count", None)
    return {
        "schema": "file-merge-tool/history-manifest/v1",
        "job_id": job_id,
        "kind": request.kind,
        "status": status,
        "started_at": started_at,
        "finished_at": finished_at,
        "setting_name": request.setting_name,
        "source_root": str(request.root_path),
        "history_dir": str(history_dir),
        "output_folder_name": request.output_folder_name,
        "outputs": outputs,
        "request": {
            "output_stem": request.output_stem,
            "output_name": request.output_name,
            "output_folder_name": request.output_folder_name,
            "image_output_formats": list(request.image_output_formats),
            "exclude_dirs": list(request.exclude.folder_names),
            "exclude_extensions": list(request.exclude.extensions),
            "exclude_files": list(request.exclude.file_names),
            "additional_sensitive_markers": list(request.sensitivity_markers),
        },
        "summary": {
            "item_count": item_count,
            "skipped_count": skipped_count,
            "excluded_count": excluded_count,
            "error_skipped_count": error_skipped_count,
            "warning_count": len(warnings),
            "generated_output_count": len(outputs),
        },
        "warnings": warnings,
        "error": error,
    }


def _classification_for_path(path: Path) -> str:
    return str(build_output_record(path)["classification"])
