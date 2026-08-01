"""Unit tests for Phase 21: Review Memory Engine."""

from app.memory.models import DeveloperFeedback, FeedbackType, ReviewSnapshot
from app.memory.service import ReviewMemoryService


def test_review_memory_service() -> None:
    service = ReviewMemoryService()
    snap = ReviewSnapshot(
        review_id="rev_mem_1",
        pr_id="PR-MEM-1",
        repository_name="PRAudit",
        verdict="APPROVE",
        total_findings=2,
    )
    service.save_review(snap)

    retrieved = service.get_review("rev_mem_1")
    assert retrieved is not None
    assert retrieved.pr_id == "PR-MEM-1"

    history = service.get_repository_history("PRAudit")
    assert history is not None
    assert history.knowledge.total_reviews_count == 1

    similar = service.search_similar_reviews("PRAudit", "MEM")
    assert len(similar) == 1

    feedback = DeveloperFeedback(
        feedback_id="fb_1",
        review_id="rev_mem_1",
        finding_id="f_1",
        feedback_type=FeedbackType.ACCEPTED,
        developer_id="dev_1",
    )
    service.store_feedback(feedback)

    fb_list = service.get_feedback("rev_mem_1")
    assert len(fb_list) == 1
    assert fb_list[0].feedback_type == FeedbackType.ACCEPTED
