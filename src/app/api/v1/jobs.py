"""
Job status endpoints for async task monitoring.

Provides endpoints to check status of background Celery tasks.
"""

from uuid import UUID

from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.celery_app import celery_app
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


# ============================================================================
# RESPONSE MODELS
# ============================================================================


class JobStatusResponse(BaseModel):
    """Job status response model."""

    job_id: str = Field(..., description="Celery task ID")
    status: str = Field(..., description="Task status (PENDING, STARTED, SUCCESS, FAILURE, RETRY)")
    progress: int | None = Field(None, description="Progress percentage (0-100)")
    status_message: str | None = Field(None, description="Human-readable status message")
    result: dict | None = Field(None, description="Task result (only if SUCCESS)")
    error: str | None = Field(None, description="Error message (only if FAILURE)")
    traceback: str | None = Field(None, description="Error traceback (only if FAILURE)")
    meta: dict | None = Field(None, description="Additional task metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "abc123-def456-ghi789",
                "status": "STARTED",
                "progress": 50,
                "status_message": "Processing chat message...",
                "result": None,
                "error": None,
                "traceback": None,
                "meta": {
                    "user_id": "user-123",
                    "conversation_id": "conv-456",
                },
            }
        }


class JobListResponse(BaseModel):
    """List of job IDs."""

    jobs: list[str] = Field(..., description="List of job IDs")
    count: int = Field(..., description="Total count of jobs")


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.get(
    "/{job_id}",
    response_model=JobStatusResponse,
    summary="Get job status",
    description="Check the status of an async background task",
)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """
    Get the status of a background job.

    Args:
        job_id: Celery task ID returned when task was submitted

    Returns:
        JobStatusResponse: Current job status with progress and result

    Raises:
        HTTPException: If job not found
    """
    try:
        logger.info("checking_job_status", job_id=job_id)

        # Get task result from Celery
        task = AsyncResult(job_id, app=celery_app)

        # Build response based on task state
        response = {
            "job_id": job_id,
            "status": task.state,
            "progress": None,
            "status_message": None,
            "result": None,
            "error": None,
            "traceback": None,
            "meta": None,
        }

        if task.state == "PENDING":
            # Task is waiting in queue or doesn't exist
            response["status_message"] = "Task is pending or queued"
            response["progress"] = 0

        elif task.state == "STARTED":
            # Task is currently executing
            # Get progress from task metadata
            info = task.info or {}
            response["progress"] = info.get("progress", 0)
            response["status_message"] = info.get("status", "Task is running")
            response["meta"] = info

        elif task.state == "SUCCESS":
            # Task completed successfully
            response["progress"] = 100
            response["status_message"] = "Task completed successfully"
            response["result"] = task.result
            response["meta"] = task.info

        elif task.state == "FAILURE":
            # Task failed
            response["progress"] = 0
            response["status_message"] = "Task failed"
            response["error"] = str(task.result) if task.result else "Unknown error"
            response["traceback"] = task.traceback
            logger.error("job_failed", job_id=job_id, error=response["error"])

        elif task.state == "RETRY":
            # Task is retrying after failure
            info = task.info or {}
            response["progress"] = info.get("progress", 0)
            response["status_message"] = "Task is retrying after failure"
            response["meta"] = info

        else:
            # Unknown state
            response["status_message"] = f"Unknown state: {task.state}"

        logger.info(
            "job_status_checked",
            job_id=job_id,
            status=task.state,
            progress=response["progress"],
        )

        return JobStatusResponse(**response)

    except Exception as exc:
        logger.error("job_status_error", job_id=job_id, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error checking job status: {str(exc)}",
        )


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel job",
    description="Attempt to cancel a running background task",
)
async def cancel_job(job_id: str):
    """
    Cancel a background job.

    Note: This sends a cancellation signal to the worker, but the task
    may not stop immediately if it's already executing.

    Args:
        job_id: Celery task ID to cancel

    Raises:
        HTTPException: If job cannot be cancelled
    """
    try:
        logger.info("cancelling_job", job_id=job_id)

        # Revoke task (terminate=False by default)
        celery_app.control.revoke(job_id, terminate=True)

        logger.info("job_cancelled", job_id=job_id)

    except Exception as exc:
        logger.error("job_cancel_error", job_id=job_id, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cancelling job: {str(exc)}",
        )


@router.get(
    "/",
    response_model=JobListResponse,
    summary="List active jobs",
    description="Get list of currently active jobs (PENDING, STARTED, RETRY)",
)
async def list_active_jobs() -> JobListResponse:
    """
    List all currently active jobs.

    Returns:
        JobListResponse: List of active job IDs

    Note: This may not include all jobs depending on Celery configuration.
    """
    try:
        logger.info("listing_active_jobs")

        # Get inspect instance
        inspect = celery_app.control.inspect()

        # Get active tasks from all workers
        active_tasks = inspect.active() or {}
        scheduled_tasks = inspect.scheduled() or {}
        reserved_tasks = inspect.reserved() or {}

        # Collect all task IDs
        job_ids = []

        for worker_tasks in [active_tasks, scheduled_tasks, reserved_tasks]:
            for worker_name, tasks in worker_tasks.items():
                for task in tasks:
                    task_id = task.get('id')
                    if task_id and task_id not in job_ids:
                        job_ids.append(task_id)

        logger.info("active_jobs_listed", count=len(job_ids))

        return JobListResponse(
            jobs=job_ids,
            count=len(job_ids),
        )

    except Exception as exc:
        logger.error("list_jobs_error", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing jobs: {str(exc)}",
        )
