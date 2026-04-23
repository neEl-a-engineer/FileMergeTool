from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from file_merge_tool.api.services.job_store import get_job
from file_merge_tool.infrastructure.history import find_history_by_job_id


router = APIRouter(prefix="/api/downloads", tags=["downloads"])


@router.get("/{job_id}/{index}")
def download(job_id: str, index: int) -> FileResponse:
    job = get_job(job_id)
    if job is None:
        history_item = find_history_by_job_id(job_id)
        if history_item is None:
            raise HTTPException(status_code=404, detail="Job not found")
        outputs = history_item.get("outputs", [])
        if index < 0 or index >= len(outputs):
            raise HTTPException(status_code=404, detail="Output not found")
        path = Path(str(outputs[index].get("path", "")))
        if not path.exists():
            raise HTTPException(status_code=404, detail="Output file is missing")
        return FileResponse(path, filename=path.name)
    if job.status != "completed":
        raise HTTPException(status_code=409, detail="Job is not completed")
    if index < 0 or index >= len(job.output_paths):
        raise HTTPException(status_code=404, detail="Output not found")

    path = Path(job.output_paths[index])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Output file is missing")
    return FileResponse(path, filename=path.name)
