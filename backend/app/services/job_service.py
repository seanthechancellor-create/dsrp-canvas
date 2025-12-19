"""
Job Service for Pipeline Progress Tracking

Stores job status in Redis for real-time tracking.
Integrates with WebSocket for live updates.
"""

import os
import json
import logging
import uuid
from datetime import datetime
from typing import Optional
from enum import Enum

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Lazy imports
_redis_client = None


def _get_redis():
    """Get or create Redis client."""
    global _redis_client
    if _redis_client is None:
        try:
            import redis
            _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
            _redis_client.ping()
            logger.info("Connected to Redis for job tracking")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            _redis_client = None
    return _redis_client


class JobStatus(str, Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobService:
    """Service for managing pipeline job progress."""

    JOB_PREFIX = "dsrp:job:"
    JOB_TTL = 86400  # 24 hours

    def create_job(
        self,
        job_type: str,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Create a new job and return its ID.

        Args:
            job_type: Type of job (e.g., "study_guide", "ingestion")
            metadata: Optional job metadata

        Returns:
            Job ID
        """
        job_id = str(uuid.uuid4())

        job_data = {
            "id": job_id,
            "type": job_type,
            "status": JobStatus.PENDING.value,
            "progress": 0,
            "stage": "initializing",
            "message": None,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "started_at": None,
            "completed_at": None,
            "error": None,
            "result": None,
        }

        redis = _get_redis()
        if redis:
            redis.setex(
                f"{self.JOB_PREFIX}{job_id}",
                self.JOB_TTL,
                json.dumps(job_data)
            )
            logger.info(f"Created job {job_id} of type {job_type}")
        else:
            logger.warning(f"Redis unavailable, job {job_id} not persisted")

        return job_id

    def get_job(self, job_id: str) -> Optional[dict]:
        """Get job data by ID."""
        redis = _get_redis()
        if not redis:
            return None

        data = redis.get(f"{self.JOB_PREFIX}{job_id}")
        if data:
            return json.loads(data)
        return None

    def update_progress(
        self,
        job_id: str,
        progress: int,
        stage: str,
        message: Optional[str] = None,
        current: Optional[int] = None,
        total: Optional[int] = None,
    ) -> bool:
        """
        Update job progress.

        Args:
            job_id: Job ID
            progress: Progress percentage (0-100)
            stage: Current stage name
            message: Optional progress message
            current: Current item number
            total: Total items

        Returns:
            True if update succeeded
        """
        job = self.get_job(job_id)
        if not job:
            return False

        job["progress"] = min(100, max(0, progress))
        job["stage"] = stage
        job["message"] = message
        job["status"] = JobStatus.RUNNING.value
        job["updated_at"] = datetime.utcnow().isoformat()

        if job["started_at"] is None:
            job["started_at"] = datetime.utcnow().isoformat()

        if current is not None:
            job["current"] = current
        if total is not None:
            job["total"] = total

        redis = _get_redis()
        if redis:
            redis.setex(
                f"{self.JOB_PREFIX}{job_id}",
                self.JOB_TTL,
                json.dumps(job)
            )

            # Send WebSocket notification
            self._notify_progress(job_id, progress, stage, message, current, total)
            return True

        return False

    def complete_job(self, job_id: str, result: Optional[dict] = None) -> bool:
        """Mark job as completed."""
        job = self.get_job(job_id)
        if not job:
            return False

        job["status"] = JobStatus.COMPLETED.value
        job["progress"] = 100
        job["stage"] = "completed"
        job["completed_at"] = datetime.utcnow().isoformat()
        job["updated_at"] = datetime.utcnow().isoformat()
        job["result"] = result

        redis = _get_redis()
        if redis:
            redis.setex(
                f"{self.JOB_PREFIX}{job_id}",
                self.JOB_TTL,
                json.dumps(job)
            )
            self._notify_complete(job_id, result or {})
            return True

        return False

    def fail_job(self, job_id: str, error: str) -> bool:
        """Mark job as failed."""
        job = self.get_job(job_id)
        if not job:
            return False

        job["status"] = JobStatus.FAILED.value
        job["stage"] = "failed"
        job["error"] = error
        job["completed_at"] = datetime.utcnow().isoformat()
        job["updated_at"] = datetime.utcnow().isoformat()

        redis = _get_redis()
        if redis:
            redis.setex(
                f"{self.JOB_PREFIX}{job_id}",
                self.JOB_TTL,
                json.dumps(job)
            )
            self._notify_error(job_id, error)
            return True

        return False

    def cancel_job(self, job_id: str) -> bool:
        """Mark job as cancelled."""
        job = self.get_job(job_id)
        if not job:
            return False

        job["status"] = JobStatus.CANCELLED.value
        job["stage"] = "cancelled"
        job["completed_at"] = datetime.utcnow().isoformat()
        job["updated_at"] = datetime.utcnow().isoformat()

        redis = _get_redis()
        if redis:
            redis.setex(
                f"{self.JOB_PREFIX}{job_id}",
                self.JOB_TTL,
                json.dumps(job)
            )
            return True

        return False

    def list_jobs(
        self,
        job_type: Optional[str] = None,
        status: Optional[JobStatus] = None,
        limit: int = 50,
    ) -> list[dict]:
        """List jobs with optional filters."""
        redis = _get_redis()
        if not redis:
            return []

        jobs = []
        for key in redis.scan_iter(f"{self.JOB_PREFIX}*"):
            data = redis.get(key)
            if data:
                job = json.loads(data)

                # Apply filters
                if job_type and job.get("type") != job_type:
                    continue
                if status and job.get("status") != status.value:
                    continue

                jobs.append(job)

                if len(jobs) >= limit:
                    break

        # Sort by created_at descending
        jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return jobs

    def _notify_progress(
        self,
        job_id: str,
        progress: int,
        stage: str,
        message: Optional[str],
        current: Optional[int],
        total: Optional[int],
    ):
        """Send WebSocket progress notification."""
        try:
            import asyncio
            from app.api.websocket import notify_job_progress

            # Run async notification in event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(
                    notify_job_progress(job_id, stage, progress, message, current, total)
                )
            else:
                loop.run_until_complete(
                    notify_job_progress(job_id, stage, progress, message, current, total)
                )
        except Exception as e:
            logger.debug(f"Could not send WebSocket notification: {e}")

    def _notify_complete(self, job_id: str, result: dict):
        """Send WebSocket completion notification."""
        try:
            import asyncio
            from app.api.websocket import notify_job_complete

            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(notify_job_complete(job_id, result))
            else:
                loop.run_until_complete(notify_job_complete(job_id, result))
        except Exception as e:
            logger.debug(f"Could not send WebSocket notification: {e}")

    def _notify_error(self, job_id: str, error: str):
        """Send WebSocket error notification."""
        try:
            import asyncio
            from app.api.websocket import notify_job_error

            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(notify_job_error(job_id, error))
            else:
                loop.run_until_complete(notify_job_error(job_id, error))
        except Exception as e:
            logger.debug(f"Could not send WebSocket notification: {e}")


# Singleton instance
_job_service: Optional[JobService] = None


def get_job_service() -> JobService:
    """Get the singleton job service instance."""
    global _job_service
    if _job_service is None:
        _job_service = JobService()
    return _job_service
