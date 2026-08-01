"""Background Job Queue for async repository analysis and PR reviews."""

import hashlib
import time
from typing import Any, Dict, Optional
from app.core.logging import setup_logger

logger = setup_logger("jobs.queue")


class BackgroundJobQueue:
    """Asynchronous background job queue."""

    def __init__(self) -> None:
        self.jobs: Dict[str, Dict[str, Any]] = {}

    def enqueue_job(self, job_type: str, payload: Dict[str, Any]) -> str:
        """Enqueue a background job and return job ID.

        Args:
            job_type: Job type identifier.
            payload: Payload parameter dictionary.

        Returns:
            Job ID string.
        """
        job_id = hashlib.sha256(f"job:{job_type}:{time.time()}".encode()).hexdigest()[:16]
        self.jobs[job_id] = {
            "job_id": job_id,
            "job_type": job_type,
            "status": "QUEUED",
            "payload": payload,
            "result": None,
            "created_at": time.time(),
        }
        logger.info("Enqueued job '%s' (Type: %s)", job_id, job_type)
        return job_id

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an enqueued job."""
        return self.jobs.get(job_id)
