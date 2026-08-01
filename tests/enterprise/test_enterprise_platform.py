"""Unit tests for Phase 20: Enterprise Platform (Cache, Storage, Telemetry, Jobs)."""

from app.cache.service import ReviewCacheService
from app.jobs.queue import BackgroundJobQueue
from app.storage.repository import ReviewStorageRepository
from app.telemetry.tracker import TelemetryTracker


def test_review_cache_service() -> None:
    cache = ReviewCacheService()
    cache.set("key1", "val1")
    assert cache.get("key1") == "val1"
    assert cache.get("key2") is None


def test_review_storage_repository() -> None:
    repo = ReviewStorageRepository()
    repo.save_review("rev_1", {"id": "rev_1", "verdict": "APPROVE"})
    retrieved = repo.get_review("rev_1")
    assert retrieved is not None
    assert retrieved["verdict"] == "APPROVE"


def test_telemetry_tracker() -> None:
    tracker = TelemetryTracker()
    tracker.record_event("test_event", tokens_used=1000, cost_usd=0.003, latency_ms=100.0)
    summary = tracker.get_summary()
    assert summary["total_events"] == 1
    assert summary["total_tokens_used"] == 1000
    assert summary["total_cost_usd"] == 0.003


def test_background_job_queue() -> None:
    queue = BackgroundJobQueue()
    job_id = queue.enqueue_job("review_job", {"pr_id": "PR-1"})
    assert job_id is not None
    status = queue.get_job_status(job_id)
    assert status["status"] == "QUEUED"
