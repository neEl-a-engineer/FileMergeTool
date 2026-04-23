from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException

from file_merge_tool.api.schemas.requests import JobCreateRequest
from file_merge_tool.api.schemas.responses import JobCreateResponse, JobDetailResponse
from file_merge_tool.api.services.job_runner import submit_job
from file_merge_tool.api.services.job_store import get_job


router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("", response_model=JobCreateResponse)
def create_job(payload: JobCreateRequest, background_tasks: BackgroundTasks) -> JobCreateResponse:
    job = submit_job(payload, background_tasks)
    return JobCreateResponse(job_id=job.id, status=job.status)


@router.get("/{job_id}", response_model=JobDetailResponse)
def job_detail(job_id: str) -> JobDetailResponse:
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobDetailResponse.from_record(job)

