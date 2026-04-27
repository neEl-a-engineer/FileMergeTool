from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from file_merge_tool.domain.config import MergeRequest
from file_merge_tool.domain.result import MergeResult
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
    summary_counts = {
        "item_count": result.item_count if result else None,
        "skipped_count": result.skipped_count if result else None,
        "excluded_count": result.excluded_count if result else None,
        "error_skipped_count": result.error_skipped_count if result else None,
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
            "exclude_folders": list(request.exclude.folder_names),
            "exclude_extensions": list(request.exclude.extensions),
            "exclude_filenames": list(request.exclude.file_names),
            "sensitivity_markers": list(request.sensitivity_markers),
            "image_output_formats": list(request.image_output_formats),
        },
        "summary": summary_counts,
        "outputs": outputs,
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
