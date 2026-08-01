"""Review Memory Service maintaining historical review trends and developer feedback."""

import time
from typing import Dict, List, Optional
from app.core.logging import setup_logger
from app.memory.models import (
    DeveloperFeedback,
    FeedbackType,
    HistoricalFinding,
    RepositoryKnowledge,
    ReviewHistory,
    ReviewSnapshot,
)

logger = setup_logger("memory.service")


class ReviewMemoryService:
    """Service storing, retrieving, and learning from past PR reviews."""

    def __init__(self) -> None:
        """Initialize in-memory storage structures."""
        self._snapshots: Dict[str, ReviewSnapshot] = {}
        self._repo_histories: Dict[str, ReviewHistory] = {}

    def save_review(self, snapshot: ReviewSnapshot) -> None:
        """Store a completed review snapshot in memory.

        Args:
            snapshot: ReviewSnapshot object.
        """
        self._snapshots[snapshot.review_id] = snapshot

        repo_name = snapshot.repository_name
        if repo_name not in self._repo_histories:
            self._repo_histories[repo_name] = ReviewHistory(
                repository_name=repo_name,
                knowledge=RepositoryKnowledge(repository_name=repo_name),
            )

        history = self._repo_histories[repo_name]
        history.snapshots.append(snapshot)
        history.knowledge.total_reviews_count += 1

        logger.info(
            "Saved review snapshot '%s' for repo '%s' (Total Reviews: %d)",
            snapshot.review_id,
            repo_name,
            history.knowledge.total_reviews_count,
        )

    def get_review(self, review_id: str) -> Optional[ReviewSnapshot]:
        """Retrieve a review snapshot by ID."""
        return self._snapshots.get(review_id)

    def get_repository_history(self, repository_name: str) -> Optional[ReviewHistory]:
        """Retrieve repository historical reviews and knowledge."""
        return self._repo_histories.get(repository_name)

    def search_similar_reviews(self, repository_name: str, query: str, limit: int = 5) -> List[ReviewSnapshot]:
        """Search similar past reviews by query matching."""
        history = self._repo_histories.get(repository_name)
        if not history:
            return []

        matches = [
            snap for snap in history.snapshots
            if query.lower() in snap.pr_id.lower() or query.lower() in snap.verdict.lower()
        ]
        return matches[:limit]

    def store_feedback(self, feedback: DeveloperFeedback) -> None:
        """Store developer feedback for a review finding."""
        for history in self._repo_histories.values():
            for snap in history.snapshots:
                if snap.review_id == feedback.review_id:
                    history.feedback_logs.append(feedback)
                    logger.info(
                        "Recorded feedback '%s' (%s) for finding '%s'",
                        feedback.feedback_id,
                        feedback.feedback_type.value,
                        feedback.finding_id,
                    )
                    return

    def get_feedback(self, review_id: str) -> List[DeveloperFeedback]:
        """Get all developer feedback for a review ID."""
        result: List[DeveloperFeedback] = []
        for history in self._repo_histories.values():
            for fb in history.feedback_logs:
                if fb.review_id == review_id:
                    result.append(fb)
        return result
