"""
Jobs API for Pipeline Progress Tracking

Provides endpoints for:
- Listing jobs
- Getting job status
- Creating jobs (for manual triggers)
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from app.services.job_service import get_job_service, JobStatus

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobCreate(BaseModel):
    """Request to create a new job."""
    job_type: str
    metadata: Optional[dict] = None


class JobResponse(BaseModel):
    """Job response model."""
    id: str
    type: str
    status: str
    progress: int
    stage: str
    message: Optional[str] = None
    metadata: dict
    created_at: str
    updated_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    result: Optional[dict] = None
    current: Optional[int] = None
    total: Optional[int] = None


@router.get("", response_model=list[JobResponse])
async def list_jobs(
    job_type: Optional[str] = Query(None, description="Filter by job type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200, description="Maximum jobs to return"),
):
    """
    List pipeline jobs.

    Returns jobs sorted by creation time (newest first).
    """
    job_service = get_job_service()

    status_enum = None
    if status:
        try:
            status_enum = JobStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {[s.value for s in JobStatus]}"
            )

    jobs = job_service.list_jobs(job_type=job_type, status=status_enum, limit=limit)
    return jobs


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """
    Get job status by ID.

    Use WebSocket /ws/job/{job_id} for real-time updates.
    """
    job_service = get_job_service()
    job = job_service.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@router.post("", response_model=JobResponse)
async def create_job(request: JobCreate):
    """
    Create a new job manually.

    Most jobs are created automatically by pipeline scripts.
    This endpoint is for manual job creation if needed.
    """
    job_service = get_job_service()
    job_id = job_service.create_job(
        job_type=request.job_type,
        metadata=request.metadata,
    )

    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=500, detail="Failed to create job")

    return job


@router.post("/{job_id}/cancel")
async def cancel_job(job_id: str):
    """
    Cancel a running job.

    Note: This marks the job as cancelled but may not stop
    the underlying process immediately.
    """
    job_service = get_job_service()
    job = job_service.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] in [JobStatus.COMPLETED.value, JobStatus.FAILED.value]:
        raise HTTPException(status_code=400, detail="Job already finished")

    success = job_service.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to cancel job")

    return {"status": "cancelled", "job_id": job_id}


@router.get("/types/list")
async def list_job_types():
    """List available job types."""
    return {
        "types": [
            {"id": "study_guide", "name": "Study Guide Ingestion", "description": "Process study guide PDF and generate flashcards"},
            {"id": "document_ingest", "name": "Document Ingestion", "description": "Ingest document into knowledge base"},
            {"id": "dsrp_extraction", "name": "DSRP Extraction", "description": "Extract DSRP patterns from text"},
            {"id": "embedding", "name": "Embedding Generation", "description": "Generate embeddings for vector search"},
        ]
    }
