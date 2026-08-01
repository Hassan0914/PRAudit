"""Unit tests for Phase 23: Feedback Learning Engine."""

from app.learning.models import FeedbackEvent
from app.learning.service import LearningEngine


def test_learning_engine_metrics() -> None:
    engine = LearningEngine()
    engine.record_feedback(FeedbackEvent("e1", "R1", "SecurityReviewer", "ACCEPTED"))
    engine.record_feedback(FeedbackEvent("e2", "R1", "SecurityReviewer", "REJECTED", is_false_positive=True))

    metrics = engine.calculate_metrics()
    assert metrics.total_feedback_events == 2
    assert metrics.acceptance_rate == 0.5
    assert metrics.false_positive_rate == 0.5
    assert metrics.precision == 0.5
