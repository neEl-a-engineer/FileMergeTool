from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import APIRouter
from fastapi import HTTPException

from file_merge_tool.api.services.job_store import get_job
from file_merge_tool.infrastructure.history import list_history
from file_merge_tool.infrastructure.history import find_history_by_job_id
from file_merge_tool.infrastructure.output_metadata import build_output_record


router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("")
def history_list() -> dict[str, object]:
    return {
        "schema": "file-merge-tool/history-list/v1",
        "items": list_history(),
    }


@router.get("/{job_id}/outputs/{index}/preview")
def preview_output(job_id: str, index: int) -> dict[str, object]:
    output = _resolve_output(job_id, index)
    if output.get("preview_mode") != "json":
        raise HTTPException(status_code=400, detail="Preview is not available for this file type.")
    path = Path(str(output.get("path")))
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail=f"Preview could not be loaded: {exc}") from exc
    return {
        "mode": "json",
        "name": path.name,
        "path": str(path),
        "content": content,
    }


@router.post("/{job_id}/outputs/{index}/open")
def open_output(job_id: str, index: int) -> dict[str, object]:
    output = _resolve_output(job_id, index)
    if output.get("preview_mode") != "external":
        raise HTTPException(status_code=400, detail="Open preview is not available for this file type.")
    path = Path(str(output.get("path")))
    if not path.exists():
        raise HTTPException(status_code=404, detail="Output file is missing")
    if not hasattr(os, "startfile"):
        raise HTTPException(status_code=501, detail="Server-side file opening is only supported on Windows.")
    os.startfile(str(path))  # type: ignore[attr-defined]
    return {
        "mode": "external",
        "name": path.name,
        "path": str(path),
        "opened": True,
    }


def _resolve_output(job_id: str, index: int) -> dict[str, object]:
    history_item = find_history_by_job_id(job_id)
    if history_item is not None:
        outputs = history_item.get("outputs", [])
        if index < 0 or index >= len(outputs):
            raise HTTPException(status_code=404, detail="Output not found")
        output = outputs[index]
        path = Path(str(output.get("path", "")))
        if not path.exists():
            raise HTTPException(status_code=404, detail="Output file is missing")
        return output

    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if index < 0 or index >= len(job.output_paths):
        raise HTTPException(status_code=404, detail="Output not found")
    path = Path(job.output_paths[index])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Output file is missing")
    return build_output_record(path)
