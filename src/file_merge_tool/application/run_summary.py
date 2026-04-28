from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from file_merge_tool.domain.config import MergeRequest
from file_merge_tool.domain.result import MergeResult
from file_merge_tool.domain.extension_selection import effective_selected_extensions
from file_merge_tool.writers.json_writer import write_json


def build_run_summary_payload(
    *,
    request: MergeRequest,
    status: str,
    started_at: str,
    finished_at: str,
    history_dir: Path,
    outputs: list[dict[str, Any]],
    result: MergeResult | None,
    warnings: list[str],
    error: str | None,
) -> dict[str, Any]:
    file_results = list(result.file_results) if result else []
    error_files = [item for item in file_results if item.status == "error"]
    skipped_files = [item for item in file_results if item.status == "skipped"]
    merged_files = [item for item in file_results if item.status == "merged"]
    summary_counts = {
        "item_count": result.item_count if result else None,
        "skipped_count": result.skipped_count if result else None,
        "excluded_count": result.excluded_count if result else None,
        "error_skipped_count": result.error_skipped_count if result else None,
        "merged_file_count": len(merged_files),
        "skipped_file_count": len(skipped_files),
        "error_file_count": len(error_files),
        "warning_count": len(warnings),
        "generated_output_count": len(outputs),
    }
    return {
        "schema": "file-merge-tool/run-summary/v1",
        "run": {
            "job_kind": request.kind or "",
            "status": status,
            "started_at": started_at,
            "finished_at": finished_at,
            "duration_ms": _duration_ms(started_at, finished_at),
            "history_dir": str(history_dir),
            "history_folder_name": history_dir.name,
            "output_folder_name": request.output_folder_name,
            "setting_name": request.setting_name,
        },
        "settings": {
            "root_folder": str(request.root_path),
            "output_folder_name": request.output_folder_name,
            "selected_extensions": list(request.selected_extensions),
            "additional_extensions": list(request.additional_extensions),
            "effective_extensions": list(
                effective_selected_extensions(
                    request.selected_extensions,
                    request.additional_extensions,
                    kind=request.kind,
                )
            ),
            "exclude_folders": list(request.exclude.folder_names),
            "exclude_extensions": list(request.exclude.extensions),
            "exclude_folder_patterns": list(request.exclude.folder_patterns),
            "exclude_filenames": list(request.exclude.file_names),
            "exclude_file_patterns": list(request.exclude.file_patterns),
            "sensitivity_markers": list(request.sensitivity_markers),
            "sensitivity_patterns": list(request.sensitivity_patterns),
            "image_output_formats": list(request.image_output_formats),
        },
        "summary": summary_counts,
        "outputs": outputs,
        "files": [
            {
                "source_path": item.source_path,
                "relative_path": item.relative_path,
                "status": item.status,
                "classification": item.classification,
                "skip_reason": item.skip_reason,
                "exception_type": item.exception_type,
                "message": item.message,
                "details": item.details,
            }
            for item in file_results
        ],
        "errors": [
            {
                "source_path": item.source_path,
                "relative_path": item.relative_path,
                "exception_type": item.exception_type,
                "message": item.message,
                "details": item.details,
            }
            for item in error_files
        ],
        "warnings": warnings,
        "error": error,
    }


def write_run_summary(path: Path, payload: dict[str, Any]) -> Path:
    return write_json(path, payload)


def _duration_ms(started_at: str, finished_at: str) -> int | None:
    try:
        started = datetime.fromisoformat(started_at)
        finished = datetime.fromisoformat(finished_at)
    except ValueError:
        return None
    return max(0, int((finished - started).total_seconds() * 1000))
