"""Unit tests for AI Evaluation Engine."""

from app.evaluation.engine import AIEvaluationEngine
from app.review.review_models import ReviewFinding, ReviewFindingSeverity


def test_ai_evaluation_engine_metrics() -> None:
    """Test AIEvaluationEngine precision, recall, and false positive metrics."""
    engine = AIEvaluationEngine()

    ground_truth = [
        ReviewFinding(
            finding_id="f1",
            rule_id="R1",
            title="High Cyclomatic Complexity in 'calculate'",
            description="",
            severity=ReviewFindingSeverity.HIGH,
            file_path="src/main.py",
            line=5,
            rule_category="Complexity",
            evidence="",
            recommendation="",
        )
    ]

    ai_titles = ["High Cyclomatic Complexity in 'calculate'"]
    report = engine.evaluate_ai_review("rev-100", ai_titles, ground_truth, latency_ms=150.0, total_tokens=1200)

    assert report.review_id == "rev-100"
    assert report.precision == 1.0
    assert report.recall == 1.0
    assert report.false_positives_count == 0
    assert report.false_negatives_count == 0
    assert len(report.metrics) == 4
