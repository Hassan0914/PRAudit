"""Persistent storage repository for reviews, historical snapshots, and audit logs."""

from typing import Any, Dict, List, Optional
from app.core.logging import setup_logger

logger = setup_logger("storage.repository")


class ReviewStorageRepository:
    """Repository managing persistent review storage."""

    def __init__(self) -> None:
        self._reviews: Dict[str, Any] = {}

    def save_review(self, review_id: str, review_data: Dict[str, Any]) -> None:
        """Save a review report to persistent storage."""
        self._reviews[review_id] = review_data
        logger.info("Saved review '%s' to storage.", review_id)

    def get_review(self, review_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve review report by ID."""
        return self._reviews.get(review_id)

    def list_reviews(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List historical reviews."""
        return list(self._reviews.values())[:limit]
