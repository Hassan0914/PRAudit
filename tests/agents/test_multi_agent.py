"""Unit tests for Phase 19: Multi-Agent Review System."""

from app.agents.coordinator import ReviewCoordinator


def test_review_coordinator_execution() -> None:
    """Test ReviewCoordinator running specialized agents and deduplicating findings."""
    coordinator = ReviewCoordinator()
    report = coordinator.coordinate_review("PR-AGENT-1", "Sample context", "Sample diff")

    assert report.review_id is not None
    assert report.pr_id == "PR-AGENT-1"
    assert len(report.agent_responses) == 6
    assert len(report.consolidated_findings) >= 1
    assert report.overall_verdict in {"APPROVE", "REQUEST_CHANGES"}
